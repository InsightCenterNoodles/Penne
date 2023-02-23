"""Module with Core Implementation of Client"""

from __future__ import annotations
from typing import Any, List, Type
import asyncio
from queue import Queue

import websockets
from cbor2 import loads, dumps

from . import handlers, delegates


def uri_tag_hook(decoder, tag, shareable_index=None):
    """Hook for URI CBOR Tag"""

    if tag.tag != 32:
        return tag
    else:
        return tag.value


class HandleInfo(object):
    """Class to organize useful info for processing each type of message

    Attributes:
        specifier (str) : keyword for delegate and state maps
        action (str)    : action performed by message
    """

    def __init__(self, specifier, action):
        self.specifier = specifier
        self.action = action


class Client(object):
    """Client for communicating with server

    Attributes:
        _url (string): 
            address used to connect to server
        _loop (event loop): 
            event loop used for network thread
        delegates (dict): 
            map for delegate functions
        thread (thread object): 
            network thread used by client
        _socket (WebSocketClientProtocol): 
            socket to connect to server
        name (str): 
            name of the client
        state (dict): 
            dict keeping track of created objects
        client_message_map (dict): 
            mapping message type to corresponding id
        server_messages (dict):
            mapping message id's to handle info
        _current_invoke (str):
            id for next method invoke
        callback_map (dict): 
            mapping invoke_id to callback function
    """

    def __init__(self, url: str, loop, custom_delegate_hash: dict[str, Type[delegates.Delegate]],
                 on_connected, callback_queue: Queue):
        """Constructor for the Client Class

        Args:
            url (string):
                address used to connect to server
            loop (event loop): 
                event loop used for network thread
            custom_delegate_hash (dict): 
                map for new delegate methods
            on_connected (Callable):
                callback function to run once client is set up
            callback_queue (Queue):
                queue to store callbacks
        """

        self._url = url
        self._loop = loop
        self.on_connected = on_connected
        self.delegates = {}
        self.thread = None
        self._socket = None
        self.name = "Python Client"
        self.state = {}
        self.client_message_map = {
            "intro": 0,
            "invoke": 1
        }
        self.server_messages = [
            HandleInfo("methods", "create"),
            HandleInfo("methods", "delete"),
            HandleInfo("signals", "create"),
            HandleInfo("signals", "delete"),
            HandleInfo("entities", "create"),
            HandleInfo("entities", "update"),
            HandleInfo("entities", "delete"),
            HandleInfo("plots", "create"),
            HandleInfo("plots", "update"),
            HandleInfo("plots", "delete"),
            HandleInfo("buffers", "create"),
            HandleInfo("buffers", "delete"),
            HandleInfo("bufferviews", "create"),
            HandleInfo("bufferviews", "delete"),
            HandleInfo("materials", "create"),
            HandleInfo("materials", "update"),
            HandleInfo("materials", "delete"),
            HandleInfo("images", "create"),
            HandleInfo("images", "delete"),
            HandleInfo("textures", "create"), 
            HandleInfo("textures", "delete"),
            HandleInfo("samplers", "create"),
            HandleInfo("samplers", "delete"),
            HandleInfo("lights", "create"),
            HandleInfo("lights", "update"),
            HandleInfo("lights", "delete"),
            HandleInfo("geometries", "create"),
            HandleInfo("geometries", "delete"),
            HandleInfo("tables", "create"),
            HandleInfo("tables", "update"),
            HandleInfo("tables", "delete"),
            HandleInfo("document", "update"),
            HandleInfo("document", "reset"),  
            HandleInfo("signals", "invoke"),  
            HandleInfo("methods", "reply"),
            HandleInfo("document", "initialized")
        ]
        self._current_invoke = 0
        self.callback_map = {}
        self.callback_queue = callback_queue
        self.is_shutdown = False

        # Hook up delegate map to default or custom based on input hash
        defaults = delegates.default_delegates
        for key in defaults:
            if key not in custom_delegate_hash:
                self.delegates[key] = defaults[key]
            else:
                self.delegates[key] = custom_delegate_hash[key]

    def object_from_name(self, name: str) -> List[int]:
        """Get a delegate's id from its name

        Args:
            name (str): name of method

        Returns:
            ID group attached to the method

        Raises:
            Couldn't find method exception
        """
        state_delegates = self.state.values()
        for delegate in state_delegates:
            if delegate.name == name:
                return delegate.id
        raise Exception(f"Couldn't find object '{name}' in state")

    def get_component(self, component_id):
        """Getter to easily retrieve components from state
        
        Args:
            component_id (ID): id for the component

        Returns:
            Component delegate from state
        """

        return self.state[component_id]

    def invoke_method(self, method: delegates.MethodID | str, args: list,
                      context: dict[str, tuple] = None, on_done=None):
        """Invoke method on server

        Constructs a dictionary of arguments to use in send_message. The
        Dictionary follows the structure of an InvokeMethodMessage, but
        using a dictionary prevents from converting back and forth just
        before sending.

        Also implements callback functions attached to each invocation. By
        default, each invocation will store a None object in the callback
        map, and the handler responsible for reply messages will delete pop
        it from the map and call the method if there is one

        Args:
            method (list or str):
                id or name for method
            args (list): 
                arguments for method
            context (dict): 
                optional, target context for method call
            on_done (function):
                function to be called upon response
        """
        
        # Get proper ID
        if isinstance(method, str):
            method_id = self.object_from_name(method)
        else:
            method_id = method

        # Get invoke ID
        invoke_id = str(self._current_invoke)
        self._current_invoke += 1

        # Keep track of callback
        self.callback_map[invoke_id] = on_done

        # Construct message dict
        arg_dict = {
            "method": method_id,
            "args": args,
            "invoke_id": invoke_id
        }
        if context:
            arg_dict["context"] = context
        
        self.send_message(arg_dict, "invoke")

    def send_message(self, message_dict: dict[str, Any], kind: str):
        """Send message to server

        Args:
            message_dict (dict): dict mapping message attribute to value
            kind (str): either 'invoke' or 'intro' to indicate type of client message
        """

        # Construct message with ID from map and converted message object
        message = [self.client_message_map[kind], message_dict]
        print(f"Sending Message: {message}")
        
        asyncio.run_coroutine_threadsafe(self._socket.send(dumps(message)), self._loop)

    async def run(self):
        """Network thread for managing websocket connection"""  

        async with websockets.connect(self._url) as websocket:

            # update class
            self._socket = websocket
            self.name = f"Python Client @ {self._url}"

            # send intro message
            intro = {"client_name": self.name}
            self.send_message(intro, "intro")

            # decode, iterate over, and handle all incoming messages
            async for message in self._socket:
                raw_message = loads(message, tag_hook=uri_tag_hook)
                iterator = iter(raw_message)
                for tag in iterator:
                    try:
                        handlers.handle(self, tag, next(iterator))
                    except Exception as e:
                        print(f"Exception: {e}")

    def show_methods(self):
        """Displays Available Methods to the User"""

        print("\n-- Available Methods to call --")
        print("client.invoke_method(method_name, args, optional callback function)")
        print("-------------------------------------------------------------------")
        for method in self.state["methods"].values():
            if "noo::" not in method.name:
                print(method)

    def shutdown(self):
        """Method for shutting down the client
        
        Closes websocket connection then blocks to finish all callbacks
        """
        
        asyncio.run_coroutine_threadsafe(self._socket.close(), self._loop)
        self.is_shutdown = True
    
