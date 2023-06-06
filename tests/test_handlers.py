import logging

import pytest

import penne.delegates as nooobs
import penne.handlers as handlers
from tests.clients import base_client, delegate_client, mock_socket, TableDelegate
from tests.servers import rig_base_server

logging.basicConfig(
    format="%(message)s",
    level=logging.DEBUG
)


def test_update_state(base_client):

    table = base_client.get_component("test_table")
    old_methods = table.methods_list
    handlers.update_state(base_client, {"name": "new_updated_name"}, table.id)
    table = base_client.get_component(table.id)
    assert table.name == "new_updated_name"
    assert table.methods_list == old_methods

    handlers.update_state(base_client, {"methods_list": [nooobs.MethodID(1, 0)], "meta": "Description"}, table.id)
    table = base_client.get_component(table.id)
    assert table.methods_list == [nooobs.MethodID(1, 0)]
    assert table.methods_list != old_methods
    assert table.meta == "Description"


def test_delegate_from_context(base_client):

    c1 = {"table": nooobs.TableID(0, 0)}
    c2 = {"table": nooobs.TableID(0, 1)}
    c3 = {"entity": nooobs.EntityID(0, 0)}
    c4 = {"plot": nooobs.PlotID(0, 0)}
    c5 = {"method": nooobs.MethodID(0, 0)}

    assert handlers.delegate_from_context(base_client, c1) == base_client.get_component(c1["table"])
    assert handlers.delegate_from_context(base_client, c3) == base_client.get_component(c3["entity"])
    assert handlers.delegate_from_context(base_client, c4) == base_client.get_component(c4["plot"])
    with pytest.raises(Exception):
        handlers.delegate_from_context(base_client, c2)
    with pytest.raises(Exception):
        handlers.delegate_from_context(base_client, c5)
    assert handlers.delegate_from_context(base_client) == base_client.get_component("document")


def test_handle(base_client):

    # Hit creation exception
    with pytest.raises(Exception):
        handlers.handle(base_client, 0, {"name": "new_updated_name"})  # Create method without ID

    # Test deletion
    handlers.handle(base_client, 1, {"id": [1, 0]})  # Delete method
    assert nooobs.MethodID(1, 0) not in base_client.state
    with pytest.raises(KeyError):
        base_client.get_component("test_arg_method")

    # Test non-document update
    handlers.handle(base_client, 5, {"id": [0, 0], "name": "updated_name", "null_rep": 2})  # Update test entity
    entity = base_client.get_component(nooobs.EntityID(0, 0))
    assert entity.name == "updated_name"
    assert entity.null_rep == 2

    # Test reply exception
    with pytest.raises(Exception):
        handlers.handle(base_client, 34, {"invoke_id": "0",
                                          "method_exception": {"code": -32603, "message": "Internal Error"}})

    # Test document reset
    handlers.handle(base_client, 32, {})
    doc = base_client.get_component("document")
    assert base_client.state == {"document": doc}
    assert doc.methods_list == []
    assert doc.signals_list == []
