
import asyncio
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

    xprocess.getinfo("rig_base_server").terminate()


def print_method():
    print("Method on server called!")


starting_components = [
    rigatoni.StartingComponent(rigatoni.Method, {"name": "print", "arg_doc": []}, print_method)
]


def run_test_server():
    asyncio.run(rigatoni.start_server(50000, starting_state=starting_components))


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

#
# class TestCreateClient:
#
#     server_process = multiprocessing.Process(target=run_test_server)
#     server_process.start()
#     test_client = create_client("ws://localhost:50000", {"tables": TableDelegate}, strict=True)
#     test_messages = [
#         (0, {})
#     ]
#
#     def test_client_init(self, client):
#         assert isinstance(client, client)
#         assert "document" in client.state
#         assert client.is_shutdown is False
#         assert client.callback_queue.empty()
#         assert len(client.delegates) == 14
#         assert len(client.server_messages) == 36
#
#     def test_create_client_with_delegates(self):
#         delegates = {"tables": TableDelegate}
#         client = create_client("ws://localhost:50000", strict=False, custom_delegate_hash=delegates)
#         self.test_client_init(client)
#         assert client.strict is False
#         assert client.delegates["tables"] == TableDelegate
#         client.shutdown()
#         client.thread.join()
#
#     def test_create_client_with_delegates_and_on_connected(self):
#         delegates = {"tables": TableDelegate}
#         client = create_client("ws://localhost:50000", strict=True, custom_delegate_hash=delegates, on_connected=lambda: print())
#         self.test_client_init(client)
#         assert client.strict is True
#         assert client.delegates["tables"] == TableDelegate
#         assert client.on_connected is not None
#         client.shutdown()
#         client.thread.join()
#
#     def test_handle(self, tag, message):
#         pass
#
#     def test_handle_messages(self):
#         for message_tuple in self.test_messages:
#             handle(self.test_client, *message_tuple)
#             self.test_handle(*message_tuple)
#
#     def test_client_object_from_name(self):
#         assert self.test_client.get_object_from_name("Test Method") == self.test_client.state[MethodID(0, 0)]
#
