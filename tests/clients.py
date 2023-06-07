# Module for test fixtures such as clients and servers
# along with their dependencies like delegates and methods

from typing import Any, Callable, List
import multiprocessing

import pandas as pd
import matplotlib.pyplot as plt
import pytest

from penne.core import Client
from penne import Table
from tests.servers import rig_base_server


def get_plot_data(df: pd.DataFrame):
    """Helper function to extract data for the plot from the dataframe"""

    data = {
        "xs": df["x"],
        "ys": df["y"],
        "zs": df["z"],
        "s": [(((sx + sy + sz) / 3) * 1000) for sx, sy, sz in zip(df["sx"], df["sy"], df["sz"])],
        "c": [(r, g, b) for r, g, b in zip(df["r"], df["g"], df["b"])]
    }
    return data


def on_close(event):
    """Event handler for when window is closed"""

    plt.close('all')


def plot_process(df: pd.DataFrame, receiver):
    """Process for plotting the table as a 3d scatter plot

    Args:
        df (DataFrame):
            the data to be plotted
        receiver (Pipe connection object):
            connection to receive updates from root process
    """

    # Enable interactive mode
    plt.ion()

    # Make initial plot
    fig = plt.figure()
    fig.canvas.mpl_connect('close_event', on_close)
    ax = fig.add_subplot(projection='3d')
    data = get_plot_data(df)
    ax.scatter(**data)

    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')

    plt.draw()
    plt.pause(.001)

    # Update loop
    while True:

        # If update received, redraw the scatter plot
        if receiver.poll(.1):
            update = receiver.recv()
            plt.cla()  # efficient? better way to set directly?
            ax.scatter(**update)
            ax.set_xlabel('X Label')
            ax.set_ylabel('Y Label')
            ax.set_zlabel('Z Label')
            plt.pause(.001)

        # Keep GUI event loop going as long as window is still open
        elif plt.fignum_exists(fig.number):
            plt.pause(.01)
        else:
            break


class TableDelegate(Table):
    """Override Table Delegate to Add Plotting Capabilities"""

    dataframe: pd.DataFrame = None
    plotting: multiprocessing.Process = None
    sender: Any = None

    def _on_table_init(self, init_info: dict, on_done=None):
        """Creates table from server response info

        Args:
            init_info (Message Obj):
                Server response to subscribe which has columns, keys, data,
                and possibly selections
        """

        # Extract data from init info and transpose rows to cols
        row_data = init_info["data"]
        col_data = [list(i) for i in zip(*row_data)]
        cols = init_info["columns"]
        data_dict = {col["name"]: data for col, data in zip(cols, col_data)}

        self.dataframe = pd.DataFrame(data_dict, index=init_info["keys"])

        # Initialize selections if any
        selections = init_info.get("selections", [])
        for selection in selections:
            self.selections[selection["name"]] = selection

        print(f"Initialized data table...\n{self.dataframe}")
        if on_done:
            on_done()

    def _reset_table(self, init_info: dict = None):
        """Reset dataframe and selections to blank objects

        Method is linked to 'tbl_reset' signal
        """

        if init_info:
            self._on_table_init(init_info)
        else:
            self.dataframe = pd.DataFrame()
            self.selections = {}

        if self.plotting:
            self._update_plot()

    def _remove_rows(self, keys: List[int]):
        """Removes rows from table

        Method is linked to 'tbl_rows_removed' signal

        Args:
            keys (list): list of keys corresponding to rows to be removed
        """

        self.dataframe.drop(index=keys, inplace=True)
        print(f"Removed Rows: {keys}...\n", self.dataframe)

        if self.plotting:
            self._update_plot()

    def _update_rows(self, keys: List[int], rows: list):
        """Update rows in table

        Method is linked to 'tbl_updated' signal

        Args:
            keys (list):
                list of keys to update
            rows (list):
                list of rows containing the values for each new row,
                should be col for each col in table, and value for each key
        """

        for key, row in zip(keys, rows):
            self.dataframe.loc[key] = row

        if self.plotting:
            self._update_plot()

        print(f"Updated Rows...{keys}\n", self.dataframe)

    def get_selection(self, name: str):
        """Get a selection object and construct Dataframe representation

        Args:
            name (str) : name of selection object to get
        """

        # Try to retrieve selection object from instance or return blank frame
        try:
            sel_obj = self.selections[name]
        except ValueError:
            return pd.DataFrame(columns=self.dataframe.columns)

        frames = []

        # Get rows already in that selection
        if sel_obj.rows:
            frames.append(self.dataframe.loc[sel_obj["rows"]])

        # Uses ranges in object to get other rows
        if sel_obj.row_ranges:
            ranges = sel_obj["row_ranges"]
            for r in ranges:
                frames.append(self.dataframe.loc[r[0]:r[1] - 1])

        # Return frames concatenated
        df = pd.concat(frames)
        print(f"Got selection for {sel_obj}\n{df}")
        return df

    def _update_plot(self):
        """Update plotting process when dataframe is updated"""

        df = self.dataframe
        self.sender.send(get_plot_data(df))

    def plot(self, on_done: Callable = None):
        """Creates plot in a new window

        Uses matplotlib to plot a representation of the table
        """

        self.sender, receiver = multiprocessing.Pipe()

        self.plotting = multiprocessing.Process(target=plot_process, args=(self.dataframe, receiver))
        self.plotting.start()
        if on_done:
            on_done()


@pytest.fixture
def base_client(rig_base_server):
    with Client("ws://localhost:50000", strict=True) as client:
        yield client


@pytest.fixture
def lenient_client(rig_base_server):
    with Client("ws://localhost:50000") as client:
        yield client


@pytest.fixture
def delegate_client(rig_base_server):
    with Client("ws://localhost:50000", custom_delegate_hash={Table: TableDelegate}, strict=True) as client:
        yield client


@pytest.fixture
def mock_socket(mocker):
    return mocker.MagicMock()
