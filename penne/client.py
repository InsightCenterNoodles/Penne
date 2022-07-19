# Allow type hinting
from __future__ import annotations

import asyncio
import threading
from typing import Callable
from urllib.parse import urlparse

from penne.delegates import Delegate
from penne.core import Client 

def thread_function(loop: asyncio.AbstractEventLoop, client: Client):
    """Method for starting background thread

    Args:
        loop (event loop): event loop used for new thread
        client (client object): client used for websocket connection
    """

    try:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(client.run())
    except:
        print("Connection terminated")
 

def create_client(address: str, custom_delegate_hash: dict[str, Delegate] = {}, on_connected: Callable=None):
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

    loop = asyncio.new_event_loop()
    

    # Create client instance and thread
    client = Client(address, loop, custom_delegate_hash, on_connected)
    t = threading.Thread(target=thread_function, args=(loop, client))
 
    client.thread = t
    client.thread.start()
 
    return client