"""Module with Core Implementation of Client"""

from __future__ import annotations

import asyncio
from queue import Queue
from typing import Any
import websockets
from cbor2 import loads, dumps

from . import messages, handlers, delegates

from common import ComponentType


default_delegates = {
    ComponentType.ENTITY: delegates.EntityDelegate,
    ComponentType.TABLE: delegates.TableDelegate,
    ComponentType.PLOT: delegates.PlotDelegate,
    ComponentType.SIGNAL: delegates.SignalDelegate,
    ComponentType.METHOD: delegates.MethodDelegate,
    ComponentType.MATERIAL: delegates.MaterialDelegate,
    ComponentType.GEOMETRY: delegates.GeometryDelegate,
    ComponentType.LIGHT: delegates.LightDelegate,
    ComponentType.IMAGE: delegates.ImageDelegate,
    ComponentType.TEXTURE: delegates.TextureDelegate,
    ComponentType.SAMPLER: delegates.SamplerDelegate,
    ComponentType.BUFFER: delegates.BufferDelegate,
    ComponentType.BUFFERVIEW: delegates.BufferViewDelegate,
    ComponentType.DOCUMENT: delegates.DocumentDelegate
}


class Client(object):
    """Client for communicating with server

    Attributes:
        _url (string): 
            address used to connect to server
        _loop (event loop): 
            event loop used for network thread
        delegates (dict): 
            map for delegate functions     
        is_connected(threading.Event): 
            signal when connection is ready
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
        server_message_map (dict):
            mapping message id's to handling info
        current_invoke (str):  
            id for next method invoke
        callback_map (dict): 
            mapping invoke_id to callback function
    """

    def __init__(self, url: str, loop, custom_delegate_hash: dict[str, delegates.Delegate], on_connected, callback_queue: Queue):
        """Constructor for the Client Class

        Args:
            _url (string): 
                address used to connect to server
            loop (event loop): 
                event loop used for network thread
            custom_delegate_hash (dict): 
                map for new delegate methods
            is_connected (threading Event):
                event object signaling when connection is ready
        """

        self._url = url
        self._loop = loop
        self.on_connected = on_connected
        self.delegates = {}
        self.thread = None
        self._socket = None
        self.name = "Python Client"
        self.state = {
            ComponentType.ENTITY: {},
            ComponentType.TABLE: {},
            ComponentType.PLOT: {},
            ComponentType.SIGNAL: {},
            ComponentType.METHOD: {},
            ComponentType.MATERIAL: {},
            ComponentType.GEOMETRY: {},
            ComponentType.LIGHT:  {},
            ComponentType.IMAGE:  {},
            ComponentType.TEXTURE:  {},
            ComponentType.SAMPLER: {},
            ComponentType.BUFFER:  {},
            ComponentType.BUFFERVIEW:  {},
            ComponentType.DOCUMENT:  {},
        }
        self.client_message_map = {
            "intro": 0,
            "invoke": 1
        }
        self.server_message_map = {
            0: messages.HandleInfo(ComponentType.METHOD, "create"),
            1: messages.HandleInfo(ComponentType.METHOD, "delete"),
            2: messages.HandleInfo(ComponentType.SIGNAL, "create"),
            3: messages.HandleInfo(ComponentType.SIGNAL, "delete"),
            4: messages.HandleInfo(ComponentType.ENTITY, "create"),
            5: messages.HandleInfo(ComponentType.ENTITY, "update"),
            6: messages.HandleInfo(ComponentType.ENTITY, "delete"),
            7: messages.HandleInfo(ComponentType.PLOT, "create"),
            8: messages.HandleInfo(ComponentType.PLOT, "update"),
            9: messages.HandleInfo(ComponentType.PLOT, "delete"),
            10: messages.HandleInfo(ComponentType.BUFFER, "create"),
            11: messages.HandleInfo(ComponentType.BUFFER, "delete"),
            12: messages.HandleInfo(ComponentType.BUFFERVIEW, "create"),
            13: messages.HandleInfo(ComponentType.BUFFERVIEW, "delete"),
            14: messages.HandleInfo(ComponentType.MATERIAL, "create"),
            15: messages.HandleInfo(ComponentType.MATERIAL, "update"),
            16: messages.HandleInfo(ComponentType.MATERIAL, "delete"),
            17: messages.HandleInfo(ComponentType.IMAGE, "create"),
            18: messages.HandleInfo(ComponentType.IMAGE, "delete"),
            19: messages.HandleInfo(ComponentType.TEXTURE, "create"),
            20: messages.HandleInfo(ComponentType.TEXTURE, "delete"),
            21: messages.HandleInfo(ComponentType.SAMPLER, "create"),
            22: messages.HandleInfo(ComponentType.SAMPLER, "delete"),
            23: messages.HandleInfo(ComponentType.LIGHT, "create"),
            24: messages.HandleInfo(ComponentType.LIGHT, "update"),
            25: messages.HandleInfo(ComponentType.LIGHT, "delete"),
            26: messages.HandleInfo(ComponentType.GEOMETRY, "create"),
            27: messages.HandleInfo(ComponentType.GEOMETRY, "delete"),
            28: messages.HandleInfo(ComponentType.TABLE, "create"),
            29: messages.HandleInfo(ComponentType.TABLE, "update"),
            30: messages.HandleInfo(ComponentType.TABLE, "delete"),
            31: messages.HandleInfo(ComponentType.DOCUMENT, "update"),
            32: messages.HandleInfo(ComponentType.DOCUMENT, "reset"),
            33: messages.HandleInfo(ComponentType.SIGNAL, "invoke"),
            34: messages.HandleInfo(ComponentType.METHOD, "reply"),
            35: messages.HandleInfo(ComponentType.DOCUMENT, "initialized")
        }
        self._current_invoke = 0
        self.callback_map = {}
        self.callback_queue = callback_queue
        self.is_shutdown = False

        # Hook up delegate map to default or custom based on input hash
        for key in default_delegates:
            if key not in custom_delegate_hash:
                self.delegates[key] = default_delegates[key]
            else:
                self.delegates[key] = custom_delegate_hash[key]
        self.state[ComponentType.DOCUMENT] = self.delegates[ComponentType.DOCUMENT](
            self, None, "document")

    def method_id_from_name(self, name: str, specifier: str) -> list[int]:
        """Get a method's id from its name

        Args:
            name (str): name of method

        Returns:
            Id group attached to the method

        Raises:
            Couldn't find method exception
        """
        objects: list[delegates.MethodDelegate] = self.state[specifier].values()
        for object in objects:
            if hasattr(object.info, "name") and object.info.name == name:
                return object.info.id
        raise Exception(f"Couldn't find object '{name}' in {specifier}")

    def invoke_method(self, id, args: list, context: dict[str, tuple] = None, on_done=None):
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
            id (list or str): 
                id or name for method
            args (list): 
                arguments for method
            context (dict): 
                optional, target context for method call
            callback (function): 
                function to be called upon response
        """

        # Get proper ID
        if isinstance(id, str):
            id = self.method_id_from_name(id, "methods")

        # Get invoke ID
        invoke_id = str(self._current_invoke)
        self._current_invoke += 1

        # Keep track of callback
        self.callback_map[invoke_id] = on_done

        # Construct message dict
        arg_dict = {
            "method": id,
            "args": args,
            "invoke_id": invoke_id
        }
        if context:
            arg_dict["context"] = context

        self.send_message(arg_dict, "invoke")

    def send_message(self, message_dict: dict[str, Any], type: str):
        """Send message to server

        Args:
            message_dict (dict): dict mapping message attribute to value
            type (str): either 'invoke' or 'intro' to indicate type of client message
        """

        # Construct message with ID from map and converted message object
        message = [self.client_message_map[type], message_dict]
        print(f"Sending Message: {message}")

        asyncio.run_coroutine_threadsafe(
            self._socket.send(dumps(message)), self._loop)

    async def run(self):
        """Network thread for managing websocket connection"""

        async with websockets.connect(self._url) as websocket:

            # update class
            self._socket = websocket
            self.name = (f"Python Client @ {self._url}")

            # send intro message
            intro = {"client_name": self.name}
            self.send_message(intro, "intro")

            # decode, iterate over, and handle all incoming messages
            async for message in self._socket:
                raw_message = loads(message)
                iterator = iter(raw_message)
                for id in iterator:
                    try:
                        handlers.handle(self, id, next(iterator))
                    except Exception as e:
                        print(f"Exception: {e}")

    def show_methods(self):
        """Displays Available Methods to the User"""

        print("\n-- Available Methods to call --")
        print("client.invoke_method(method_name, args, optional callback function)")
        print("-------------------------------------------------------------------")
        for method in self.state["methods"].values():
            if not "noo::" in method.info.name:
                print(method)

    def shutdown(self):
        """Method for shutting down the client

        Closes websocket connection then blocks to finish all callbacks
        """

        asyncio.run_coroutine_threadsafe(self._socket.close(), self._loop)
        self.is_shutdown = True
