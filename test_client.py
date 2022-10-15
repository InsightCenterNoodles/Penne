"""Client Test Script

Test the functionality of the client using a custom delegate and callback functions.
Designed to interact with PlottyN server to create a 3d scatter chart
"""

from typing import Callable
import unittest
import multiprocessing
import queue

import pandas as pd
import matplotlib.pyplot as plt

from penne.client import create_client
from penne.delegates import TableDelegate



def get_plot_data(df: pd.DataFrame):
    """Helper function to extract data for the plot from the dataframe"""

    data = {
        "xs": df["x"], 
        "ys": df["y"], 
        "zs": df["z"],
        "s" : [(((sx + sy + sz) / 3) * 1000) for sx, sy, sz in zip(df["sx"], df["sy"], df["sz"])],
        "c" : [(r, g, b) for r, g, b in zip(df["r"], df["g"], df["b"])]
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
            plt.cla() # efficient? better way to set directly?
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


class TestDelegate(TableDelegate):
    """Overide Table Delegate to Add Plotting Capabilities"""

    def __init__(self, client, message, specifier) -> None:
        super().__init__(client, message, specifier)
        self.dataframe: pd.DataFrame = None
        self.plotting = None

    def _on_table_init(self, init_info, on_done=None):
        """Creates table from server response info

        Args:
            init_info (Message Obj): 
                Server response to subscribe which has columns, keys, data, 
                and possibly selections
        """

        # Extract data from init info and transpose rows to cols
        row_data = getattr(init_info, "data")
        col_data = [list(i) for i in zip(*row_data)]
        cols = getattr(init_info, "columns")
        data_dict = {getattr(col, "name"): data for col, data in zip(cols, col_data)}
        
        self.dataframe = pd.DataFrame(data_dict, index=getattr(init_info, "keys"))

        # Initialize selections if any
        selections = getattr(init_info, "selections", [])
        for selection in selections:
            self.selections[selection.name] = selection
        
        print(f"Initialized data table...\n{self.dataframe}")
        if on_done: on_done()


    def _reset_table(self):
        """Reset dataframe and selections to blank objects

        Method is linked to 'tbl_reset' signal
        """

        self.dataframe = pd.DataFrame()
        self.selections = {}

        if self.plotting:
            self._update_plot()


    def _remove_rows(self, key_list: list[int]):
        """Removes rows from table

        Method is linked to 'tbl_rows_removed' signal

        Args:
            key_list (list): list of keys corresponding to rows to be removed
        """

        self.dataframe.drop(index=key_list, inplace=True)
        print(f"Removed Rows: {key_list}...\n", self.dataframe)

        if self.plotting:
            self._update_plot()


    def _update_rows(self, keys: list[int], rows: list):
        """Update rows in table

        Method is linked to 'tbl_updated' signal

        Args:
            keys (list): 
                list of keys to update
            cols (list): 
                list of cols containing the values for each new row,
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
        except:
            return pd.DataFrame(columns=self.dataframe.columns)

        frames = []

        # Get rows already in that selection
        if sel_obj.rows:
            frames.append(self.dataframe.loc[sel_obj["rows"]])

        # Uses ranges in object to get other rows
        if sel_obj.row_ranges:
            ranges = sel_obj["row_ranges"]
            for r in ranges:
                frames.append(self.dataframe.loc[r[0]:r[1]-1])

        # Return frames concatenated
        df = pd.concat(frames)
        print(f"Got selection for {sel_obj}\n{df}")
        return df

    def _update_plot(self):
        """Update plotting process when dataframe is updated"""

        df = self.dataframe
        self.sender.send(get_plot_data(df))

    def plot(self, on_done: Callable=None):
        """Creates plot in a new window

        Uses matplotlib to plot a representation of the table
        """

        self.sender, receiver = multiprocessing.Pipe()

        self.plotting=multiprocessing.Process(target=plot_process, args=(self.dataframe, receiver))
        self.plotting.start()
        if on_done: on_done()


class Tests(unittest.TestCase):
    
    def test(self):

        # Create callback functions
        # Not sure about 'response' - cleaner way?
        points = [[1,2,3,4,5],[1,2,3,4,5],[1,2,3,4,5],[(0,1,1),(0,1,1),(0,1,1),(0,1,1),(0,1,1)]]
        create_table = lambda: client.invoke_method("new_point_plot", points, on_done=subscribe)
        subscribe = lambda response: client.state["tables"][(0, 0)].subscribe(on_done=plot)
        plot = lambda: client.state["tables"][(0, 0)].plot(on_done=insert_points)
        insert_points = lambda: client.state["tables"][(0, 0)].request_insert(
            row_list=[[8, 8, 8, .3, .2, 1, .05, .05, .05],[9,9,9,.1,.2,.5,.02,.02,.02, "Annotation"]], 
            on_done=update_rows
            )
        update_rows = lambda: client.state["tables"][(0, 0)].request_update([3],[[4,6,3,0,1,0,.1,.1,.1,"Updated this row"]], on_done=get_selection)
        get_selection = lambda: client.state["tables"][(0, 0)].request_update_selection("Test Select", [1, 2, 3], on_done=remove_row)
        remove_row = lambda: client.state["tables"][(0, 0)].request_remove([2], on_done=shutdown)
        shutdown = lambda: client.shutdown()

        # Creat client and start callback chain
        del_hash = {"tables" : TestDelegate}
        client = create_client("ws://localhost:50000", del_hash, on_connected=create_table)

        while True:
            if client.is_shutdown:
                break
            try:
                callback_info = client.callback_queue.get(block=False)
            except queue.Empty:
                continue
            callback, args = callback_info
            callback(args) if args else callback()

        # Wait for client thread to finish
        client.thread.join()
        print(f"Finished Testing")


if __name__ == "__main__":
    unittest.main()