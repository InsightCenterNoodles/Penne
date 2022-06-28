import asyncio
from concurrent.futures import thread
from time import sleep
from client import client
import unittest
import threading


# Globals used for testing
WS_URL = "ws://localhost:50000"
METHOD = 0 # Create Point Plot
ARGS = [[1, 2, 3], [1, 2, 3], [1, 2, 3]]

def on_new(data):
    print("Injected on_new method call for tables delegate")


class TestDelegate(object):
    def on_new(data):
        pass
    def on_update(data):
        pass
    def on_remove(data):
        pass

class Tests(unittest.TestCase):

    def test_client(self):

        # Create client and connect to url
        print("creating client...")
        test_client = client.create_client(WS_URL)
        test_client.event.wait()

        # Testing custom delegates
        # TODO

        # Test injecting methods
        methods_dict = {"on_new" : on_new}
        test_client.inject_methods("tables", methods_dict)

        # Test Invoke Method
        print("invoking method...")
        test_client.invoke_method(METHOD, ARGS)

        # Close connection
        test_client.shutdown()


if __name__ == "__main__":
    unittest.main()