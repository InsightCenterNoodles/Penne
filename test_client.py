from client import client
import unittest
import time

from client.delegates import Selection, SelectionRange


# Globals used for testing
WS_URL = "ws://localhost:50000"
METHOD = 0 # Create Point Plot
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

    def __init__(self, client):
        self.client = self

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
        test_client = client.create_client(WS_URL, del_hash, verbose=False)
        test_client.is_connected.wait()

        # Test injecting methods
        print(f"{style.ACCENT}{style.BOLD}Injecting methods...{style.END}")
        methods_dict = {"on_new" : on_new}
        test_client.inject_methods("tables", methods_dict)

        # Test Invoke Method
        print(f"{style.ACCENT}{style.BOLD}Creating table...{style.END}")
        test_client.invoke_method(METHOD, ARGS, callback=called_back)
        wait_for_callback(test_client.callback_map, test_client)
        print("Should be done creating table...")

        # Test subscribe
        print(f"{style.ACCENT}{style.BOLD}Subscribing to table...{style.END}")
        test_client.delegates["tables"].subscribe([0, 0])
        wait_for_callback(test_client.callback_map, test_client)

        # Test table delegate methods
        print(f"{style.ACCENT}{style.BOLD}Testing table delegates...{style.END}")
        test_client.delegates["tables"].remove_rows([2])
        test_client.delegates["tables"].update_rows([5, 6], [[1,1],[2,2],[3,3],[4,4],[4,4],[4,4],[4,4],[4,4],[4,4]])
        test_client.delegates["tables"].update_cols({"y": [7, 7, 7]})
        test_client.delegates["tables"].update_rows([1],[[1],[2],[3],[4],[5],[6],[7]])
        test_client.delegates["tables"].update_rows2({1: [7, 8, 8, 7, 5, 7, 7, 7, 7]})
        test_client.delegates["tables"].insert_rows([[7, 8, 8, 7, 5, 7, 7, 7, 7],[1,1,1,1,1,1,1,1,1]])
        # can we assume update will have values for every column?
        selection = Selection("Tester", [0], [SelectionRange(1,4)])
        test_client.delegates["tables"].make_selection(selection)
        test_selection = test_client.delegates["tables"].get_selection("Tester")

        # Close connection
        print(f"{style.ACCENT}{style.BOLD}Shutting down connection...{style.END}")
        test_client.shutdown()


if __name__ == "__main__":
    unittest.main()