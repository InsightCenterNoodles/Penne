"""Client Test Script

Test that the current state on the server and the message format conforms to standards.
"""

import unittest
import logging

from penne import Client


class Tests(unittest.TestCase):

    def test(self):

        with Client("ws://localhost:50000", strict=False) as client:
            print("Finished checking state on server / their messages")


logging.basicConfig(
    format="%(message)s",
    level=logging.DEBUG
)

if __name__ == "__main__":

    with Client("ws://localhost:50000", strict=False) as client:
        print("Finished checking state on server / their messages")
