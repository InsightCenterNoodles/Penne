"""Client Test Script

Test the functionality of the client using a custom delegate and callback functions.
Designed to interact with PlottyN server to create a 3d scatter chart
"""

import unittest
import queue

from penne import Client, TableID
from penne.delegates import TableID
from .test_delegates import TableDelegate

# Create callback functions
# Not sure about 'response' - cleaner way?
table = TableID(0, 0)
points = [[1, 2, 3, 4, 5], [1, 2, 3, 4, 5], [1, 2, 3, 4, 5],
          [(0, 1, 1), (0, 1, 1), (0, 1, 1), (0, 1, 1), (0, 1, 1)]]


# Callbacks
def create_table():
    client.invoke_method("new_point_plot", points, on_done=subscribe)


def subscribe(response):
    client.state[table].subscribe(on_done=plot)


def plot():
    client.state[table].plot(on_done=insert_points)


def insert_points():
    client.state[table].request_insert(
        row_list=[[8, 8, 8, .3, .2, 1, .05, .05, .05], [9, 9, 9, .1, .2, .5, .02, .02, .02, "Annotation"]],
        on_done=update_rows
    )


def update_rows():
    client.state[table].request_update([3], [[4, 6, 3, 0, 1, 0, .1, .1, .1, "Updated this row"]],
                                       on_done=get_selection)


def get_selection():
    client.state[table].request_update_selection("Test Select", [1, 2, 3], on_done=remove_row)


def remove_row():
    client.state[table].request_remove([2], on_done=shutdown)


def shutdown():
    client.shutdown()


del_hash = {"tables": TableDelegate}
with Client("ws://localhost:50000", del_hash, strict=True) as client:
    while client.is_active:
        try:
            callback_info = client.callback_queue.get(block=False)
        except queue.Empty:
            continue
        callback, args = callback_info
        callback(args) if args else callback()

print(f"Finished Testing")
