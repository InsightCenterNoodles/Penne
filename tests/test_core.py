
import logging
import pytest
from cbor2 import dumps

from penne.core import Client
import penne.delegates as nooobs
from .test_delegates import TableDelegate

from .fixtures import base_client, delegate_client, mock_socket, rig_base_server


logging.basicConfig(
    format="%(message)s",
    level=logging.DEBUG
)


def test_create_client(base_client):
    assert isinstance(base_client, Client)
    assert "document" in base_client.state
    assert base_client.is_active is True
    assert base_client.callback_queue.empty()
    assert len(base_client.delegates) == 14
    assert len(base_client.server_messages) == 36

    # Test connection when there is no server to connect to, note: will cause 5-second delay
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

    # Try basic call from ID
    method_id = base_client.object_from_name("test_method")
    base_client.invoke_method(method_id)

    # Try with callback and other input format
    def callback():
        return "Callback called!"
    base_client.invoke_method("test_method", [], on_done=callback)
    invoke = str(base_client._current_invoke - 1)
    assert base_client.callback_map[invoke] == callback

    # Try with context
    method_del = base_client.get_component(method_id)
    context = nooobs.get_context(method_del)
    base_client.invoke_method("test_method", [], context=context)


def test_send_message(base_client):

    # Test variations on intro and invoke messages
    test_codes = ["intro", "intro",
                  "invoke", "invoke", "invoke", "invoke", "invoke", "invoke"]
    test_messages = [
        {"client_name": "test_client"},
        {"client_name": base_client.name},
        {"method_id": (0, 0), "args": [], "invoke_id": 1},
        {"method_id": (0, 0), "args": [1, 2, 3], "invoke_id": 2},
    ]

    # can either add return statement (binary or dict?) or mock the socket (how to run async?)
    # for kind, content in zip(test_codes, test_messages):
    #     base_client.send_message(content, kind)
    #     code = 0 if kind == "intro" else 1
    #     expected = [code, content]


def test_show_methods(base_client):
    base_client.show_methods()


def test_shutdown(base_client):
    base_client.shutdown()
    assert base_client.is_active is False
    assert base_client._socket.closed is True
