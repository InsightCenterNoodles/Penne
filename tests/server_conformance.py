"""Client Test Script

Test that the current state on the server and the message format conforms to standards.
"""

import unittest
import logging

from penne import Client


class Tests(unittest.TestCase):

    def test(self):

        # def shutdown():
        #     client.shutdown()
        #
        # # Create client and start callback chain
        # client = create_client("ws://localhost:50000", on_connected=shutdown, strict=False)
        #
        # while True:
        #     if client.is_shutdown:
        #         break
        #     try:
        #         callback_info = client.callback_queue.get(block=False)
        #     except queue.Empty:
        #         continue
        #     callback, args = callback_info
        #     callback(args) if args else callback()
        #
        # # Wait for client thread to finish
        # client.thread.join()
        # print(f"Finished Testing")

        with Client("ws://localhost:50000", strict=False) as client:
            print("Finished checking state on server / their messages")


logging.basicConfig(
    format="%(message)s",
    level=logging.DEBUG
)

if __name__ == "__main__":

    with Client("ws://localhost:50000", strict=False) as client:
        print("Finished checking state on server / their messages")
