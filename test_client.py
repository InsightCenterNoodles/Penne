import unittest
import time
import pandas as pd

from penne.client import create_client
from penne.delegates import TableDelegate

import multiprocessing
import matplotlib as plt

# Globals used for testing
ARGS = [[1,2,3,4,5],[1,2,3,4,5],[1,2,3,4,5],[(0,1,1),(0,1,1),(0,1,1),(0,1,1),(0,1,1)]]

class style:
   CYAN = '\033[96m'
   ACCENT = '\033[92m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

def on_new(data):
    print("Injected on_new method call for delegate")

def called_back(result):
    pass

def wait_for_callback(callback_map, timeout=5, period=0.25):
  mustend = time.time() + timeout
  while time.time() < mustend:
    if not callback_map: return True
    time.sleep(period)
  raise Exception("Didn't receive reply")

class TestDelegate(TableDelegate):

    def _update_plot(self):
        """Update plotting process when dataframe is updated"""

        df = self.dataframe
        self.sender.send(self.get_plot_data(df))

    def plot(self):
        """Creates plot in a new window

        Uses matplotlib to plot a representation of the table
        """

        self.sender, receiver = multiprocessing.Pipe()

        self.plotting=multiprocessing.Process(target=self.plot_process, args=(self.dataframe, receiver))
        self.plotting.start()

        
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


    def plot_process(self, df: pd.DataFrame, receiver):
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
        fig.canvas.mpl_connect('close_event', self.on_close)
        ax = fig.add_subplot(projection='3d')
        data = self.get_plot_data(df)
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
                plt.pause(1)
            else:
                break



def main():
    print("Finished Testing")


class Tests(unittest.TestCase):
    
    def test_create_table(self):

        # Create callback functions
        subscribe = lambda data: client.state["tables"][(0, 0)].subscribe()
        create_table = lambda: client.invoke_method("new_point_plot", ARGS, callback=subscribe)

        print(f"{style.ACCENT}{style.BOLD}Creating client...{style.END}")
        del_hash = {"tables" : TestDelegate}
        client = create_client("ws://localhost:50000", del_hash, on_connected=create_table)

        #time.sleep(2)

        # # Test Invoke Method
        # print(f"{style.ACCENT}{style.BOLD}Creating table...{style.END}")
        # client.invoke_method("new_point_plot", ARGS, callback=subscribe)
        # self.__class__.table = client.state["tables"][(0, 0)]
        # time.sleep(2)

        # # Test subscribe
        # print(f"{style.ACCENT}{style.BOLD}Subscribing to table...{style.END}")
        # table_delegate: TableDelegate = client.state["tables"][(0, 0)]
        # #table_delegate.subscribe()

        # # Test table delegate methods
        # print(f"{style.ACCENT}{style.BOLD}Testing table delegate...{style.END}")
        # table_delegate.show_methods()
        # table_delegate.request_remove([2, 3], on_done=called_back)


        # table_delegate.request_insert(row_list=[[7, 8, 8, 1, 1, 1, .02, .02, .02],[6,6,6,.1,.2,.5,.02,.02,.02]], on_done=called_back)
        # wait_for_callback(test_client.callback_map)

        # data = pd.DataFrame([[4, 4, 4, .5, .5, .5, .09, .09, .09],[5,5,5,.3,.9,1,.04,.04,.04]], [4, 5])
        # table_delegate.request_update(data, on_done=called_back)
        # wait_for_callback(test_client.callback_map)

        # table_delegate.request_update_selection("test selection", keys=[4,5,6],)
        # wait_for_callback(test_client.callback_map)

        #  # Test Plotting
        # print(f"{style.ACCENT}{style.BOLD}Attempting to plot table...{style.END}")
        # table_delegate.plot()
        # time.sleep(2)

        # # Insert after plot created
        # table_delegate.request_insert(row_list=[[8, 8, 8, .3, .2, 1, .05, .05, .05],[9,9,9,.1,.2,.5,.02,.02,.02]], on_done=called_back)
        # wait_for_callback(test_client.callback_map)
        # time.sleep(2)

        # # Remove after plot
        # table_delegate.request_remove([5], on_done=called_back)
        # table_delegate.request_insert(col_list=[[3],[3],[3],[0],[0],[0],[.1],[.1],[.1]], on_done=called_back)
        # wait_for_callback(test_client.callback_map)
        # time.sleep(2)

        # # Close connection
        # print(f"{style.ACCENT}{style.BOLD}Shutting down connection...{style.END}")
        # test_client.shutdown()


if __name__ == "__main__":
    #main()
    unittest.main()