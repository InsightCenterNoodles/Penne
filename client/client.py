import asyncio
import threading
from urllib.parse import urlparse

from .core import Client 

def thread_function(loop, client):
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
 

def create_client(address, custom_delegate_hash = {}):
    """Create a client object and start background thread

    Args:
        address (str): 
            url for connecting to server
        custom_delegate_hash (dict):
            mapping specifiers to new delegate methods to override default

    Raises:
        ValueError: Address given must be a websocket
    """

    address_parts = urlparse(address)
 
    if address_parts.scheme not in ["ws", "wss"]:
        raise ValueError("Address given must be a websocket!")
 
    #loop = asyncio.get_event_loop(), https://stackoverflow.com/questions/46727787/runtimeerror-there-is-no-current-event-loop-in-thread-in-async-apscheduler
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    is_connected = threading.Event()

    client = Client(address, loop, custom_delegate_hash, is_connected)
    t = threading.Thread(target=thread_function, args=(loop, client))
 
    client.thread = t
 
    client.thread.start()
 
    return client