from typing import Callable
import unittest
import time
import multiprocessing

import pandas as pd
import matplotlib.pyplot as plt

from penne.client import create_client
from penne.delegates import TableDelegate


# Globals used for testing
ARGS = [[1,2,3,4,5],[1,2,3,4,5],[1,2,3,4,5],[(0,1,1),(0,1,1),(0,1,1),(0,1,1),(0,1,1)]]

class style:
   CYAN = '\033[96m'
   ACCENT = '\033[92m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'


def called_back(result):
    pass

def wait_for_callback(callback_map, timeout=5, period=0.25):
  mustend = time.time() + timeout
  while time.time() < mustend:
    if not callback_map: return True
    time.sleep(period)
  raise Exception("Didn't receive reply")


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
            plt.pause(.001)

        # Keep GUI event loop going as long as window is still open
        elif plt.fignum_exists(fig.number):
            plt.pause(.001)
        else:
            break


class TestDelegate(TableDelegate):
    """Overide Table Delegate to Add Plotting Capabilities"""

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
        create_table = lambda: client.invoke_method("new_point_plot", ARGS, on_done=subscribe)
        subscribe = lambda response: client.state["tables"][(0, 0)].subscribe(on_done=plot)
        plot = lambda: client.state["tables"][(0, 0)].plot(on_done=insert_points)
        insert_points = lambda: client.state["tables"][(0, 0)].request_insert(
            row_list=[[8, 8, 8, .3, .2, 1, .05, .05, .05],[9,9,9,.1,.2,.5,.02,.02,.02]], 
            on_done=update_rows
            )
        update_rows = lambda response: client.state["tables"][(0, 0)].request_update([3],[[4,6,3,0,1,0,.1,.1,.1]], on_done=shutdown)
        shutdown = lambda response: client.shutdown()

        # Creat client and start callback chain
        del_hash = {"tables" : TestDelegate}
        client = create_client("ws://localhost:50000", del_hash, on_connected=create_table)

        client.thread.join()
        print(f"Finished Testing")

if __name__ == "__main__":
    #main()
    unittest.main()