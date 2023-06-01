
import logging
import pytest
from cbor2 import dumps

from penne.core import Client
import penne.delegates as nooobs

from .fixtures import base_client, delegate_client, mock_socket, rig_base_server, TableDelegate


logging.basicConfig(
    format="%(message)s",
    level=logging.DEBUG
)


def test_ids():
    generic = nooobs.ID(0, 0)
    generic2 = nooobs.ID(0, 0)
    m = nooobs.MethodID(0, 0)
    m1 = nooobs.MethodID(slot=0, gen=0)
    m2 = nooobs.MethodID(slot=0, gen=1)
    m3 = nooobs.MethodID(slot=1, gen=0)
    s = nooobs.SignalID(slot=0, gen=0)
    assert generic == generic2
    assert generic != m
    assert m != generic
    assert m == m1
    assert m != m2
    assert m != m3
    assert m1 != m2
    assert m1 != m3
    assert m2 != m3
    assert s != m
    assert s != generic
    assert str(m) == "MethodID|0/0|"
    assert str(generic) == "ID|0/0|"
    assert m.compact_str() == "|0/0|"
    assert generic.compact_str() == "|0/0|"
    assert m2.compact_str() == "|0/1|"


def test_delegate(base_client):
    x = nooobs.Delegate(client=base_client, id=nooobs.ID(slot=0, gen=0))
    y = nooobs.Delegate(client=base_client, id=nooobs.ID(slot=1, gen=0), name="Test")
    m = {"message": "contents"}
    x.on_new(m)
    x.on_update(m)
    x.on_remove(m)
    assert str(x) == "No-Name - Delegate - |0/0|"
    assert str(y) == "Test - Delegate - |1/0|"


def test_pbr_info_validation(caplog):
    nooobs.PBRInfo(base_color=(0, 0, 0))
    assert "Base Color is Wrong Color Format:" in caplog.text


def test_invoke_id_validation():
    nooobs.InvokeIDType(entity=nooobs.EntityID(slot=0, gen=0))
    with pytest.raises(ValueError):
        nooobs.InvokeIDType(entity=nooobs.EntityID(slot=0, gen=0), table=nooobs.TableID(slot=0, gen=0))
    with pytest.raises(ValueError):
        nooobs.InvokeIDType()


def test_table_init_validation():

    # Test ints
    int_cols = [nooobs.TableColumnInfo(name="test", type="INTEGER")]
    keys = [0, 1, 2]
    data = [[5], [5], [5]]
    nooobs.TableInitData(columns=int_cols, keys=keys, data=data)

    # Test floats
    real_cols = [nooobs.TableColumnInfo(name="test", type="REAL")]
    keys = [0, 1, 2]
    data = [[5.0], [5.0], [5.0]]
    nooobs.TableInitData(columns=real_cols, keys=keys, data=data)

    # Test strings
    str_cols = [nooobs.TableColumnInfo(name="test", type="TEXT")]
    keys = [0, 1, 2]
    data = [["5"], ["5"], ["5"]]
    nooobs.TableInitData(columns=str_cols, keys=keys, data=data)

    # Test Mismatches
    with pytest.raises(ValueError):
        nooobs.TableInitData(columns=int_cols, keys=keys, data=data)
    with pytest.raises(ValueError):
        nooobs.TableInitData(columns=real_cols, keys=keys, data=data)


def test_method(base_client):
    method = base_client.get_component("test_method")
    arg_method = base_client.get_component("test_arg_method")
    plot = base_client.get_component("test_plot")
    table = base_client.get_component("test_table")
    entity = base_client.get_component("test_entity")
    method.invoke(plot)
    method.invoke(table)
    method.invoke(entity)
    with pytest.raises(ValueError):
        method.invoke(1)
    assert str(method) == "test_method:\n\tNone\n\tReturns: None\n\tArgs:"
    assert str(arg_method) == "test_arg_method:\n\tNone\n\tReturns: None\n\tArgs:\n\t\t" \
                              "x: How far to move in x\n\t\ty: How far to move in y\n\t\tz: How far to move in z"


def test_entity(base_client):
    entity = base_client.get_component("test_entity")
    assert entity.show_methods() == "No methods available"
    entity = base_client.get_component("test_method_entity")
    assert entity.show_methods() == "-- Methods on test_method_entity --\n--------------------------------------\n" \
                                    ">> test_method:\n\tNone\n\tReturns: None\n\tArgs:"


def test_plot():
    # Test the validator
    pass

