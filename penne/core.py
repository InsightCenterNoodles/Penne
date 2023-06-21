"""Module with Core Implementation of Client"""

from __future__ import annotations
from typing import Any, Type, Union, Dict

import queue
import asyncio
import logging
import threading

import websockets
from cbor2 import loads, dumps

from . import handlers, delegates


class HandleInfo(object):
    """Class to organize useful info for processing each type of message

    Attributes:
        delegate (delegate) : keyword for delegate and state maps
        action (str)    : action performed by message
    """

    def __init__(self, specifier, action):
        self.delegate = specifier
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

    def __init__(self, url: str, custom_delegate_hash: dict[Type[delegates.Delegate], Type[delegates.Delegate]] = None,
                 on_connected=None, strict=False, json=None):
        """Constructor for the Client Class

        Args:
            url (string):
                address used to connect to server
            custom_delegate_hash (dict):
                map for new delegates to be used on client
            on_connected (Callable):
                callback function to run once client is set up
            strict (bool):
                flag for strict data validation and throwing hard exceptions
            json (str):
                path for outputting json log of messages
        """

        if not custom_delegate_hash:
            custom_delegate_hash = {}

        self._url = url
        self._loop = asyncio.new_event_loop()
        self.on_connected = on_connected
        self.delegates = delegates.default_delegates.copy()
        self.strict = strict
        self.json = json
        self.thread = threading.Thread(target=self._start_communication_thread)
        self.connection_established = threading.Event()
        self._socket = None
        self.name = "Python Client"
        self.state = {}
        self.client_message_map = {
            "intro": 0,
            "invoke": 1
        }
        self.server_messages = [
            HandleInfo(delegates.Method, "create"),
            HandleInfo(delegates.Method, "delete"),
            HandleInfo(delegates.Signal, "create"),
            HandleInfo(delegates.Signal, "delete"),
            HandleInfo(delegates.Entity, "create"),
            HandleInfo(delegates.Entity, "update"),
            HandleInfo(delegates.Entity, "delete"),
            HandleInfo(delegates.Plot, "create"),
            HandleInfo(delegates.Plot, "update"),
            HandleInfo(delegates.Plot, "delete"),
            HandleInfo(delegates.Buffer, "create"),
            HandleInfo(delegates.Buffer, "delete"),
            HandleInfo(delegates.BufferView, "create"),
            HandleInfo(delegates.BufferView, "delete"),
            HandleInfo(delegates.Material, "create"),
            HandleInfo(delegates.Material, "update"),
            HandleInfo(delegates.Material, "delete"),
            HandleInfo(delegates.Image, "create"),
            HandleInfo(delegates.Image, "delete"),
            HandleInfo(delegates.Texture, "create"),
            HandleInfo(delegates.Texture, "delete"),
            HandleInfo(delegates.Sampler, "create"),
            HandleInfo(delegates.Sampler, "delete"),
            HandleInfo(delegates.Light, "create"),
            HandleInfo(delegates.Light, "update"),
            HandleInfo(delegates.Light, "delete"),
            HandleInfo(delegates.Geometry, "create"),
            HandleInfo(delegates.Geometry, "delete"),
            HandleInfo(delegates.Table, "create"),
            HandleInfo(delegates.Table, "update"),
            HandleInfo(delegates.Table, "delete"),
            HandleInfo(delegates.Document, "update"),
            HandleInfo(delegates.Document, "reset"),
            HandleInfo(delegates.Signal, "invoke"),
            HandleInfo(delegates.Method, "reply"),
            HandleInfo(delegates.Document, "initialized")
        ]
        self._current_invoke = 0
        self.callback_map = {}
        self.callback_queue = queue.Queue()
        self.is_active = False

        # Hook up delegate map to customs
        self.delegates.update(custom_delegate_hash)

        # Add document delegate as starting element in state
        self.state["document"] = self.delegates[delegates.Document](client=self)

    def __enter__(self):
        """Enter method for context manager

        Waits for 5 seconds for connection to be established, otherwise throws exception
        """
        self.thread.start()
        flag = self.connection_established.wait(timeout=1)
        if not flag:
            raise ConnectionError("Couldn't connect to server")

        self.is_active = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit method for context manager"""
        self.shutdown()
        self.is_active = False

    def _start_communication_thread(self):
        """Starts the communication thread for the client"""
        try:
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._run())
        except Exception as e:
            self.is_active = False
            logging.warning(f"Connection terminated in communication thread: {e}")

    def get_delegate_id(self, name: str) -> Type[delegates.ID]:
        """Get a delegate's id from its name. Assumes names are unique, or returns the first match

        Args:
            name (str): name of method

        Returns:
            ID (ID): ID for the delegate

        Raises:
            KeyError: if no match is found
        """
        if name == "document":
            return name

        state_delegates = self.state.values()
        for delegate in state_delegates:
            if delegate.name == name:
                return delegate.id
        raise KeyError(f"Couldn't find object '{name}' in state")

    def get_delegate(self, identifier: Union[delegates.ID, str, Dict[str, delegates.ID]]) -> Type[delegates.Delegate]:
        """Getter to easily retrieve components from state

        Accepts multiple types of identifiers for flexibility

        Args:
            identifier (ID | str | dict): id, name, or context for the component

        Returns:
            Delegate (Delegate): delegate object from state

        Raises:
            TypeError: if identifier is not a valid type
            KeyError: if id or name is not found in state
            ValueError: if context is not found in state
        """
        if isinstance(identifier, delegates.ID):
            return self.state[identifier]
        elif isinstance(identifier, str):
            return self.state[self.get_delegate_id(identifier)]
        elif isinstance(identifier, dict):
            return self.get_delegate_by_context(identifier)
        else:
            raise TypeError(f"Invalid type for identifier: {type(identifier)}")

    def get_delegate_by_context(self, context: dict = None) -> delegates.Delegate:
        """Get delegate object from a context object

        Contexts are of the form {"table": TableID}, {"entity": EntityID}, or {"plot": PlotID}.
        They are only applicable for tables, entities, and plots

        Args:
            context (dict): dict containing context

        Returns:
            Delegate (Delegate): delegate object from state

        Raises:
            ValueError: Couldn't get delegate from context
        """

        if not context:
            target_delegate = self.state["document"]
            return target_delegate

        table = context.get("table")
        entity = context.get("entity")
        plot = context.get("plot")

        if table:
            target_delegate = self.state[delegates.TableID(*table)]
        elif entity:
            target_delegate = self.state[delegates.EntityID(*entity)]
        elif plot:
            target_delegate = self.state[delegates.PlotID(*plot)]
        else:
            raise ValueError("Couldn't get delegate from context")

        return target_delegate

    def invoke_method(self, method: Union[delegates.MethodID, str], args: list = None,
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
            method (ID | str):
                id or name for method
            args (list): 
                arguments for method
            context (dict): 
                optional, target context for method call
            on_done (Callable):
                function to be called upon response

        Returns:
            message (list): message to be sent to server in the form of [tag, {content}]
        """

        # Handle default args
        if not args:
            args = []
        
        # Get proper ID
        if isinstance(method, str):
            method_id = self.get_delegate_id(method)
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
        
        return self.send_message(arg_dict, "invoke")

    def send_message(self, message_dict: dict[str, Any], kind: str):
        """Send message to server

        Args:
            message_dict (dict): dict mapping message attribute to value
            kind (str): either 'invoke' or 'intro' to indicate type of client message
        """

        # Construct message with ID from map and converted message object
        message = [self.client_message_map[kind], message_dict]
        logging.debug(f"Sending Message: {message}")
        
        asyncio.run_coroutine_threadsafe(self._socket.send(dumps(message)), self._loop)
        return message

    def _process_message(self, message):
        """Prep message for handling

        Messages here are of form: [tag, {content}, tag, {content}, ...]
        """

        content = iter(message)
        for tag in content:
            try:
                handlers.handle(self, tag, next(content))
            except Exception as e:
                if self.strict:
                    raise e
                else:
                    logging.error(f"Exception: {e} for message {message}")

    async def _run(self):
        """Network thread for managing websocket connection"""  

        async with websockets.connect(self._url) as websocket:

            # update class
            self._socket = websocket
            self.name = f"Python Client @ {self._url}"
            self.is_active = True

            # send intro message
            intro = {"client_name": self.name}
            self.send_message(intro, "intro")

            # decode and handle all incoming messages
            async for message in self._socket:
                message = loads(message)
                self._process_message(message)

    def show_methods(self):
        """Displays Available Methods to the User on the document

        Uses the document delegate's show_methods function to display
        """
        self.state["document"].show_methods()

    def shutdown(self):
        """Method for shutting down the client
        
        Closes websocket connection then blocks to finish all callbacks, joins thread as well
        """
        asyncio.run_coroutine_threadsafe(self._socket.close(), self._loop)
        self.is_active = False
        self.thread.join()
