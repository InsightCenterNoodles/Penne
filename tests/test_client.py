
import multiprocessing
import logging

import pytest
from xprocess import ProcessStarter
import rigatoni

import penne
from penne.client import create_client
from penne.handlers import handle

from delegates import TableDelegate


logging.basicConfig(
    format="%(message)s",
    level=logging.DEBUG
)


@pytest.fixture
def rig_base_server(xprocess):

    class Starter(ProcessStarter):
        pattern = "Starting up Server..."
        args = ["python3", "/Users/aracape/development/penne/tests/base_server.py"]

    logfile = xprocess.ensure("rig_base_server", Starter)

    #conn = multiprocessing.Process(target=run_test_server)
    conn = 50000
    yield conn

    x = xprocess.getinfo("rig_base_server")
    x.terminate()


def print_method():
    print("Method on server called!")


starting_components = [
    rigatoni.StartingComponent(rigatoni.Method, {"name": "print", "arg_doc": []}, print_method)
]


# def run_test_server():
#     asyncio.run(rigatoni.start_server(50000, starting_state=starting_components))


# @pytest.fixture
# def rig_base_server():
#     p = multiprocessing.Process(target=run_test_server)
#     p.start()
#     yield p
#     #p.terminate()


@pytest.fixture
def base_client(rig_base_server):
    client = create_client("ws://localhost:50000", strict=True)
    yield client
    client.shutdown()


@pytest.fixture
def delegate_client(rig_base_server):
    client = create_client("ws://localhost:50000", {"tables": TableDelegate}, strict=True)
    yield client
    client.shutdown()


def test_create_client(base_client):
    assert isinstance(base_client, penne.Client)
    assert "document" in base_client.state
    assert base_client.is_shutdown is False
    assert base_client.callback_queue.empty()
    assert len(base_client.delegates) == 14
    assert len(base_client.server_messages) == 36


def test_create_delegate_client(delegate_client):
    assert isinstance(delegate_client, penne.Client)
    assert "document" in delegate_client.state
    assert delegate_client.is_shutdown is False
    assert delegate_client.callback_queue.empty()
    assert len(delegate_client.delegates) == 14
    assert len(delegate_client.server_messages) == 36
    assert delegate_client.delegates["tables"] == TableDelegate
