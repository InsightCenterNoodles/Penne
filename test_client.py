import unittest
import time
import pandas as pd

from client import client
from client.delegates import TableDelegate


# Globals used for testing
WS_URL = "ws://localhost:50000"
METHOD = [0, 0]# Create Point Plot
#ARGS = [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11], [12, 13, 14, 15]]
ARGS = [[1,2,3,4,5],[1,2,3,4,5],[1,2,3,4,5]]

class style:
   CYAN = '\033[96m'
   ACCENT = '\033[92m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

def on_new(data):
    print("Injected on_new method call for delegate")

def called_back(result):
    print("I was called back")

def wait_for_callback(callback_map, client, timeout=5, period=0.25):
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
        test_client = client.create_client(WS_URL, del_hash)
        test_client.is_connected.wait()

        # Test Invoke Method
        print(f"{style.ACCENT}{style.BOLD}Creating table...{style.END}")
        test_client.invoke_method(METHOD, ARGS, callback=called_back)
        wait_for_callback(test_client.callback_map, test_client)

        # Test subscribe
        print(f"{style.ACCENT}{style.BOLD}Subscribing to table...{style.END}")
        table_delegate: TableDelegate = test_client.state["tables"][(0, 0)]
        print(table_delegate)
        table_delegate.subscribe()
        wait_for_callback(test_client.callback_map, test_client)

        # Test table delegate methods
        print(f"{style.ACCENT}{style.BOLD}Testing table delegate...{style.END}")

        table_delegate.request_remove([2, 3], on_done=called_back)
        wait_for_callback(test_client.callback_map, test_client)

        table_delegate.request_insert(row_list=[[7, 8, 8, 7, 5, 7, 7, 7, 7],[1,1,1,1,1,1,1,1,1]], on_done=called_back)
        wait_for_callback(test_client.callback_map, test_client)

        data = pd.DataFrame([[4, 4, 4, 4, 5, 4, 4, 4, 4],[1,1,1,1,1,1,1,1,1]], [4, 5])
        table_delegate.request_update(data, on_done=called_back)
        wait_for_callback(test_client.callback_map, test_client)

        table_delegate.request_update_selection("test selection", keys=[4,5,6],)
        wait_for_callback(test_client.callback_map, test_client)

        # Close connection
        print(f"{style.ACCENT}{style.BOLD}Shutting down connection...{style.END}")
        #print(test_client.state)
        test_client.shutdown()


if __name__ == "__main__":
    unittest.main()