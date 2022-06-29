from concurrent.futures import thread
from time import sleep
from client import client
import unittest


# Globals used for testing
WS_URL = "ws://localhost:50000"
METHOD = 0 # Create Point Plot
ARGS = [[1, 2, 3], [1, 2, 3], [1, 2, 3]]

def on_new(data):
    print("Injected on_new method call for delegate")

def called_back():
    print("I was called upon response from server")


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
        print("creating client...")
        del_hash = {"geometries" : TestDelegate}
        test_client = client.create_client(WS_URL, del_hash, verbose=True)
        test_client.is_connected.wait()

        # Test injecting methods
        methods_dict = {"on_new" : on_new}
        test_client.inject_methods("tables", methods_dict)

        # Test Invoke Method
        print("invoking method...")
        test_client.invoke_method(METHOD, ARGS, callback=called_back)

        # Close connection
        print("shutting down connection...")
        test_client.shutdown()


if __name__ == "__main__":
    unittest.main()