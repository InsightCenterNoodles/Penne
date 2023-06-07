"""Client Test Script

Test the functionality of the client using a custom delegate and callback functions.
Designed to interact with PlottyN server to create a 3d scatter chart
"""

import logging
import queue

import matplotlib.pyplot as plt

from penne import Client
from penne.delegates import TableID, Table
from tests.clients import TableDelegate

# Create callback functions
# Not sure about 'response' - cleaner way?
points = [[1, 2, 3, 4, 5], [1, 2, 3, 4, 5], [1, 2, 3, 4, 5],
          [(0, 1, 1), (0, 1, 1), (0, 1, 1), (0, 1, 1), (0, 1, 1)]]


def run_basic_operations(table: TableID, plotting: bool = True):

    # Callbacks
    def create_table():
        client.invoke_method("new_point_plot", points, on_done=subscribe)

    def subscribe(*args):
        if plotting:
            client.state[table].subscribe(on_done=plot)
        else:
            client.state[table].subscribe(on_done=insert_points)

    def plot(*args):
        client.state[table].plot(on_done=insert_points)

    def insert_points(*args):
        client.state[table].request_insert(
            row_list=[[8, 8, 8, .3, .2, 1, .05, .05, .05], [9, 9, 9, .1, .2, .5, .02, .02, .02, "Annotation"]],
            on_done=update_rows
        )

    def update_rows(*args):
        client.state[table].request_update([3], [[4, 6, 3, 0, 1, 0, .1, .1, .1, "Updated this row"]],
                                           on_done=get_selection)

    def get_selection(*args):
        client.state[table].request_update_selection("Test Select", [1, 2, 3], on_done=remove_row)

    def remove_row(*args):
        client.state[table].request_remove([2], on_done=clear)

    def clear(*args):
        client.state[table].request_clear(on_done=shutdown)

    def shutdown(*args):
        client.is_active = False
        plt.close('all')
        print("Made it to the end!")

    # Set up logging
    logging.basicConfig(
        format="%(message)s",
        level=logging.DEBUG
    )

    # Main execution loop
    del_hash = {Table: TableDelegate}
    with Client("ws://localhost:50000", del_hash, on_connected=create_table, strict=True) as client:
        while client.is_active:
            try:
                callback_info = client.callback_queue.get(block=False)
            except queue.Empty:
                continue
            print(f"Callback: {callback_info}")
            callback, args = callback_info
            callback(args) if args else callback()

    print(f"Finished Testing")


if __name__ == "__main__":
    table = TableID(0, 0)
    run_basic_operations(table)
