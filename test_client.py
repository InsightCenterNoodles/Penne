import unittest
import time
import pandas as pd

from client import client
from client.delegates import TableDelegate


# Globals used for testing
WS_URL = "ws://localhost:50000"
#ARGS = [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11], [12, 13, 14, 15]]
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

class TestDelegate(object):

    def __init__(self, client, message, specifier):
        self.client = client
        self.info = message
        self.specifier = specifier

    def on_new(self, data):
        print("custom delegate on_new")
    def on_update(self, data):
        print("custom delegate on_update")
    def on_remove(self, data):
        print("custom delegate on_remove")


class Tests(unittest.TestCase):

    def test_client(self):

        # Create client and connect to url
        print(f"{style.ACCENT}{style.BOLD}Creating client...{style.END}")
        del_hash = {"geometries" : TestDelegate}
        test_client = client.create_client(WS_URL)
        test_client.is_connected.wait() # Better way? wait for client to be initialized with info from server as well
        time.sleep(1)

        # Test Invoke Method
        print(f"{style.ACCENT}{style.BOLD}Creating table...{style.END}")
        test_client.invoke_method("new_point_plot", ARGS, callback=called_back)
        wait_for_callback(test_client.callback_map)
        test_client.show_methods()

        # Test subscribe
        print(f"{style.ACCENT}{style.BOLD}Subscribing to table...{style.END}")
        table_delegate: TableDelegate = test_client.state["tables"][(0, 0)]
        table_delegate.subscribe()
        wait_for_callback(test_client.callback_map)

        # Test table delegate methods
        print(f"{style.ACCENT}{style.BOLD}Testing table delegate...{style.END}")
        table_delegate.show_methods()
        table_delegate.request_remove([2, 3], on_done=called_back)
        wait_for_callback(test_client.callback_map)

        table_delegate.request_insert(row_list=[[7, 8, 8, 1, 1, 1, .02, .02, .02],[6,6,6,.1,.2,.5,.02,.02,.02]], on_done=called_back)
        wait_for_callback(test_client.callback_map)

        data = pd.DataFrame([[4, 4, 4, .5, .5, .5, .09, .09, .09],[5,5,5,.3,.9,1,.04,.04,.04]], [4, 5])
        table_delegate.request_update(data, on_done=called_back)
        wait_for_callback(test_client.callback_map)

        table_delegate.request_update_selection("test selection", keys=[4,5,6],)
        wait_for_callback(test_client.callback_map)

         # Test Plotting
        print(f"{style.ACCENT}{style.BOLD}Attempting to plot table...{style.END}")
        table_delegate.plot()
        time.sleep(2)

        # Insert after plot created
        table_delegate.request_insert(row_list=[[8, 8, 8, .3, .2, 1, .05, .05, .05],[9,9,9,.1,.2,.5,.02,.02,.02]], on_done=called_back)
        wait_for_callback(test_client.callback_map)
        time.sleep(2)

        # Remove after plot
        table_delegate.request_remove([5], on_done=called_back)
        wait_for_callback(test_client.callback_map)
        time.sleep(2)

        # Close connection
        print(f"{style.ACCENT}{style.BOLD}Shutting down connection...{style.END}")
        test_client.shutdown()


if __name__ == "__main__":
    unittest.main()