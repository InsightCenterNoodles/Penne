"""Module for Creating a Client

Functions:
    thread
    create_client
"""

from __future__ import annotations

import asyncio
import threading
from typing import Callable
from urllib.parse import urlparse
import queue

from penne.delegates import Delegate
from penne.core import Client 


def thread(loop: asyncio.AbstractEventLoop, client: Client):
    """Method for starting background thread

    Args:
        loop (event loop): event loop used for new thread
        client (client object): client used for websocket connection
    """

    try:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(client.run())
    except Exception as e:
        print(f"Connection terminated: {e}")


def create_client(address: str, custom_delegate_hash: dict[str, Delegate] = None, on_connected: Callable = None):
    """Create a client object and start background thread

    Args:
        address (str): 
            url for connecting to server
        custom_delegate_hash (dict):
            mapping specifiers to new delegate methods to override default
        on_connected (callable):
            function to be called once connection is established

    Raises:
        ValueError: Address given must be a websocket
    """

    # Process address
    address_parts = urlparse(address)
    if address_parts.scheme not in ["ws", "wss"]:
        raise ValueError("Address given must be a websocket!")

    # Create client instance and thread
    loop = asyncio.new_event_loop()
    callback_queue = queue.Queue()
    if not custom_delegate_hash:
        custom_delegate_hash = {}
    client = Client(address, loop, custom_delegate_hash, on_connected, callback_queue)
    t = threading.Thread(target=thread, args=(loop, client))
 
    client.thread = t
    client.thread.start()
 
    return client
