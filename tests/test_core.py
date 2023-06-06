
import logging
import time
import queue

import penne.delegates as nooobs

from .clients import *
from tests.servers import bad_server


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
    assert base_client.strict is True

    # Test connection when there is no server to connect to, note: will cause 5-second delay
    with pytest.raises(ConnectionError):
        with Client("ws://localhost:50001", strict=True) as client:
            pass


def test_create_lenient_client(lenient_client):
    assert isinstance(lenient_client, Client)
    assert "document" in lenient_client.state
    assert lenient_client.is_active is True
    assert lenient_client.callback_queue.empty()
    assert len(lenient_client.delegates) == 14
    assert len(lenient_client.server_messages) == 36
    assert lenient_client.strict is False

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


def test_id_from_name(base_client):
    method_id = base_client.id_from_name("test_method")
    assert isinstance(method_id, nooobs.MethodID)
    with pytest.raises(KeyError):
        base_client.id_from_name("not_a_method")


def test_get_component(base_client):
    method_id = base_client.id_from_name("test_method")
    method = base_client.get_component(method_id)
    check = base_client.state[method_id]
    other_way = base_client.get_component("test_method")
    assert isinstance(method, nooobs.Method)
    assert isinstance(other_way, nooobs.Method)
    assert method == check
    assert other_way == check
    with pytest.raises(KeyError):
        base_client.get_component("not_a_method")
    with pytest.raises(TypeError):
        base_client.get_component(1)


def test_invoke_method(base_client):

    # Try basic call from ID
    method_id = base_client.id_from_name("test_method")
    message = base_client.invoke_method(method_id)
    assert message == [1, {"method": method_id, "args": [], "invoke_id": "0"}]

    # Try with callback and other input format
    def callback():
        return "Callback called!"
    base_client.invoke_method("test_method", [], on_done=callback)
    invoke = str(base_client._current_invoke - 1)
    assert base_client.callback_map[invoke] == callback

    # Try with context
    entity_id = base_client.id_from_name("test_entity")
    entity_del = base_client.get_component(entity_id)
    context = nooobs.get_context(entity_del)
    message = base_client.invoke_method("test_method", [], context=context)
    assert message == [1, {"method": method_id, "args": [], "invoke_id": "2", "context": context}]


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

    for kind, content in zip(test_codes, test_messages):
        message = base_client.send_message(content, kind)
        code = 0 if kind == "intro" else 1
        expected = [code, content]
        assert message == expected


def test_exception_handling(bad_server):

    def invoke_bad():
        client.invoke_method(nooobs.MethodID(0, 0), [])

    with Client("ws://localhost:50001", on_connected=invoke_bad, strict=True) as client:
        while client.is_active:
            try:
                callback_info = client.callback_queue.get(block=False)
            except queue.Empty:
                continue
            print(f"Callback: {callback_info}")
            callback, args = callback_info
            callback(args) if args else callback()


def test_show_methods(base_client):
    base_client.show_methods()


def test_shutdown(base_client):
    base_client.shutdown()
    assert base_client.is_active is False
    assert base_client._socket.closed is True
