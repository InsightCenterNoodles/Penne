
import logging
import pytest

from rigatoni import Server, StartingComponent, Method, Entity, Material
from penne.core import Client
import penne.delegates as nooobs

from .test_delegates import TableDelegate


logging.basicConfig(
    format="%(message)s",
    level=logging.DEBUG
)


def print_method():
    print("Method on server called!")
    return "Method on server called!"


starting_components = [
    StartingComponent(Method, {"name": "test_method"}, print_method),
    StartingComponent(Entity, {}),
    StartingComponent(Material, {"name": "test_material"})
]


@pytest.fixture
def rig_base_server():

    with Server(50000, starting_components) as server:
        yield server


@pytest.fixture
def base_client(rig_base_server):

    with Client("ws://localhost:50000", strict=True) as client:
        yield client


@pytest.fixture
def delegate_client(rig_base_server):
    with Client("ws://localhost:50000", custom_delegate_hash={"tables": TableDelegate}, strict=True) as client:
        yield client


def test_create_client(base_client):
    assert isinstance(base_client, Client)
    assert "document" in base_client.state
    assert base_client.is_active is True
    assert base_client.callback_queue.empty()
    assert len(base_client.delegates) == 14
    assert len(base_client.server_messages) == 36

    # Test connection when there is no server to connect to, note: will cause 5 second delay
    with pytest.raises(ConnectionError):
        with Client("ws://localhost:50001", strict=True) as client:
            pass


def test_create_delegate_client(delegate_client):
    assert isinstance(delegate_client, Client)
    assert "document" in delegate_client.state
    assert delegate_client.is_active is True
    assert delegate_client.callback_queue.empty()
    assert len(delegate_client.delegates) == 14
    assert len(delegate_client.server_messages) == 36
    assert delegate_client.delegates["tables"] == TableDelegate


def test_object_from_name(base_client):
    method_id = base_client.object_from_name("test_method")
    assert isinstance(method_id, nooobs.MethodID)
    with pytest.raises(KeyError):
        base_client.object_from_name("not_a_method")


def test_get_component(base_client):
    method_id = base_client.object_from_name("test_method")
    method = base_client.get_component(method_id)
    check = base_client.state[method_id]
    assert isinstance(method, nooobs.Method)
    assert method == check
    with pytest.raises(KeyError):
        base_client.get_component("not_a_method")


def test_invoke_method(base_client):
    method_id = base_client.object_from_name("test_method")
    base_client.invoke_method(method_id)
    base_client.invoke_method("test_method", [])

