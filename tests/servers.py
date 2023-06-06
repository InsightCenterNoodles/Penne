
import weakref

import pytest
import pandas as pd

from rigatoni import *


def simple_method(server: Server, context, *args):
    return "Method on server called!"


def move_method(server: Server, context, x, y, z):
    print(f"Moving {x}, {y}, {z}")
    return "Moved!"


def new_point_plot(server: Server, context: dict, xs, ys, zs, colors=None, sizes=None):
    # Create component and state and get delegate reference
    tbl_delegate = server.create_component(
        Table,
        name="Custom Table",
        meta="Table for testing",
        methods_list=[
            server.get_component_id(Method, "noo::tbl_subscribe"),
            server.get_component_id(Method, "noo::tbl_insert"),
            server.get_component_id(Method, "noo::tbl_update"),
            server.get_component_id(Method, "noo::tbl_remove"),
            server.get_component_id(Method, "noo::tbl_clear"),
            server.get_component_id(Method, "noo::tbl_update_selection"),
        ],
        signals_list=[
            server.get_component_id(Signal, "noo::tbl_reset"),
            server.get_component_id(Signal, "noo::tbl_updated"),
            server.get_component_id(Signal, "noo::tbl_rows_removed"),
            server.get_component_id(Signal, "noo::tbl_selection_updated")
        ]
    )

    # Set default colors and sizes
    if not colors:
        colors = [0.0, 0.0, 0.0] * len(xs)
    if not sizes:
        sizes = [[.02, .02, .02] for i in xs]
    # Get values for dataframe
    color_cols = list(zip(*colors))
    size_cols = list(zip(*sizes))

    data = {
        "x": xs,
        "y": ys,
        "z": zs,
        "r": color_cols[0],
        "g": color_cols[1],
        "b": color_cols[2],
        "sx": size_cols[0],
        "sy": size_cols[1],
        "sz": size_cols[2],
        "": [''] * len(xs)
    }

    tbl_delegate.dataframe = pd.DataFrame(data)
    print(tbl_delegate.dataframe)

    return 1


def subscribe(server: Server, context: dict):
    # Try to get delegate from context
    try:
        table_id = TableID(*context["table"])
        delegate: CustomTableDelegate = server.delegates[table_id]
    except ValueError:
        raise MethodException(code=-32600, message="Invalid Request - Invalid Context for Subscribe")

    tbl: pd.DataFrame = delegate.dataframe
    types = ["REAL", "REAL", "REAL", "REAL", "REAL", "REAL", "REAL", "REAL", "REAL", "TEXT"]

    # Arrange col info
    col_info = [TableColumnInfo(name=col, type=type) for col, type in zip(tbl.columns, types)]

    # Formulate response info for subscription
    init_info = TableInitData(columns=col_info, keys=tbl.index.values.tolist(), data=tbl.values.tolist())

    print(f"Init Info: {init_info}")
    return init_info


def insert(server: Server, context: dict, rows: list[list]):
    try:
        table_id = TableID(*context["table"])
        delegate: CustomTableDelegate = server.delegates[table_id]
    except ValueError:
        raise MethodException(-32600, "Invalid Request - Invalid Context for insert")

    # Allow for rows without annotations
    for row in rows:
        if len(row) == 9:
            row.extend([''])

    # Update state in delegate
    keys = delegate.handle_insert(rows)
    print(f"Inserted @ {keys}, \n{delegate.dataframe}")

    # Send signal to update client
    delegate.table_updated(keys, rows)

    return keys


def update(server: Server, context: dict, keys: list[int], rows: list[list]):
    try:
        table_id = TableID(*context["table"])
        delegate: CustomTableDelegate = server.delegates[table_id]
    except ValueError:
        raise MethodException(code=-32600, message="Invalid Request - Invalid Context for update")

    # Update state in delegate
    keys = delegate.handle_update(keys, rows)
    print(f"Updated @ {keys}, \n{delegate.dataframe}")

    # Send signal to update client
    delegate.table_updated(keys, rows)

    return keys


def remove(server: Server, context: dict, keys: list[int]):
    try:
        table_id = TableID(*context["table"])
        delegate: CustomTableDelegate = server.delegates[table_id]
    except Exception:
        raise MethodException(-32600, "Invalid Request - Invalid Context for delete")

    # Update state in delegate
    keys = delegate.handle_delete(keys)
    print(f"Deleted @ {keys}, \n{delegate.dataframe}")

    # Send signal to update client
    delegate.table_updated(keys, [])

    return keys


def clear(server: Server, context: dict):
    try:
        table_id = TableID(*context["table"])
        delegate: CustomTableDelegate = server.delegates[table_id]
    except Exception:
        raise MethodException(-32600, "Invalid Request - Invalid Context for clear")

    # Update state in delegate
    delegate.handle_clear()

    # Send signal to update client
    init_info = TableInitData(columns=[], keys=[], data=[])
    delegate.table_reset(init_info)


def update_selection(server: Server, context: dict, selection: dict):
    try:
        table_id = TableID(*context["table"])
        delegate: CustomTableDelegate = server.delegates[table_id]
    except Exception:
        raise MethodException(-32600, "Invalid Request - Invalid Context for selection")

    # Update state in delegate
    selection = Selection(**selection)
    delegate.handle_set_selection(selection)

    # Send signal to update client
    delegate.table_selection_updated(selection)


class CustomTableDelegate(ServerTableDelegate):

    def __init__(self, server: Server, component: weakref.ReferenceType):
        super().__init__(server, component)
        self.dataframe = pd.DataFrame()
        self.selections = {}

    def handle_insert(self, rows: list[list[int]]):
        next_index = self.dataframe.index[-1] + 1
        new_index = range(next_index, next_index + len(rows))

        new_df = pd.DataFrame(rows, columns=self.dataframe.columns.values, index=new_index)
        self.dataframe = pd.concat([self.dataframe, new_df])

        return list(new_index)

    def handle_update(self, keys: list[int], rows: list[list[int]]):
        for key, row in zip(keys, rows):
            self.dataframe.loc[key] = row

        return keys

    def handle_delete(self, keys: list[int]):
        self.dataframe.drop(index=keys, inplace=True)

        return keys

    def handle_clear(self):
        self.dataframe = pd.DataFrame()
        self.selections = {}

    def handle_set_selection(self, selection: Selection):
        self.selections[selection.name] = selection

    # Signals ---------------------------------------------------
    def table_reset(self, tbl_init: TableInitData):
        """Invoke table reset signal"""

        data = [tbl_init]

        signal = self.server.get_component_id(Signal, "noo::tbl_reset")
        self.server.invoke_signal(signal, self.component, data)

    def table_updated(self, keys: list[int], rows: list[list[int]]):
        data = [keys, rows]

        signal = self.server.get_component_id(Signal, "noo::tbl_updated")
        self.server.invoke_signal(signal, self.component, data)

    def table_rows_removed(self, keys: list[int]):
        data = [keys]

        signal = self.server.get_component_id(Signal, "noo::tbl_rows_removed")
        self.server.invoke_signal(signal, self.component, data)

    def table_selection_updated(self, selection: Selection):
        data = [selection]

        signal = self.server.get_component_id(Signal, "noo::tbl_selection_updated")
        self.server.invoke_signal(signal, self.component, data)


server_delegates = {
    Table: CustomTableDelegate
}


test_args = [
    MethodArg(name="x", doc="How far to move in x", editor_hint="noo::real"),
    MethodArg(name="y", doc="How far to move in y", editor_hint="noo::real"),
    MethodArg(name="z", doc="How far to move in z", editor_hint="noo::real")
]


starting_components = [
    StartingComponent(Method, {"name": "test_method"}, simple_method),
    StartingComponent(Method, {"name": "test_arg_method", "arg_doc": [*test_args]}, move_method),
    StartingComponent(Method, {"name": "new_point_plot", "arg_doc": []}, new_point_plot),
    StartingComponent(Method, {"name": "noo::tbl_subscribe", "arg_doc": []}, subscribe),
    StartingComponent(Method, {"name": "noo::tbl_insert", "arg_doc": []}, insert),
    StartingComponent(Method, {"name": "noo::tbl_update", "arg_doc": []}, update),
    StartingComponent(Method, {"name": "noo::tbl_remove", "arg_doc": []}, remove),
    StartingComponent(Method, {"name": "noo::tbl_clear", "arg_doc": []}, clear),
    StartingComponent(Method, {"name": "noo::tbl_update_selection", "arg_doc": []}, update_selection),
    StartingComponent(Method, {"name": "Test Method 4", "arg_doc": []}, print),

    StartingComponent(Signal, {"name": "noo::tbl_reset", "arg_doc": []}),
    StartingComponent(Signal, {"name": "noo::tbl_updated", "arg_doc": []}),
    StartingComponent(Signal, {"name": "noo::tbl_rows_removed", "arg_doc": []}),
    StartingComponent(Signal, {"name": "noo::tbl_selection_updated", "arg_doc": []}),
    StartingComponent(Signal, {"name": "test_signal"}),

    StartingComponent(Entity, {"name": "test_entity"}),
    StartingComponent(Entity, {"name": "test_method_entity", "methods_list": [[0, 0]]}),
    StartingComponent(Material, {"name": "test_material"}),
    StartingComponent(Table, {"name": "test_table", "methods_list": [[0, 0]], "signals_list": [[0, 0]]}),
    StartingComponent(Plot, {"name": "test_plot", "simple_plot": "True", "methods_list": [[0, 0]]})
]


@pytest.fixture
def rig_base_server():
    with Server(50000, starting_components, server_delegates) as server:
        yield server


def throw_error(server: Server, context: dict, args: list):
    raise MethodException(-32603, "Internal Error")


bad_starting_components = [
    StartingComponent(Method, {"name": "bad_method"}, throw_error),
]


@pytest.fixture
def bad_server():
    with Server(50001, bad_starting_components, server_delegates) as server:
        yield server
