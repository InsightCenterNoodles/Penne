"""Client Test Script

Test the functionality of the client using a custom delegate and callback functions.
Designed to interact with PlottyN server to create a 3d scatter chart
"""

import unittest
import queue

from penne.client import create_client


class Tests(unittest.TestCase):

    def test(self):

        def shutdown():
            client.shutdown()

        # Create client and start callback chain
        client = create_client("ws://localhost:50000", on_connected=shutdown, strict=False)

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
