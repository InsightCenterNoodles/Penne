import asyncio
import websockets
from cbor2 import dumps

from . import messages
from . import handlers
from . import delegates


default_delegates = {
    "entities" : delegates.EntityDelegate,
    "tables" : delegates.TableDelegate,
    "plots" : delegates.PlotDelegate,
    "signals" : delegates.SignalDelegate,
    "methods" : delegates.MethodDelegate,
    "materials" : delegates.MaterialDelegate,
    "geometries" : delegates.GeometryDelegate,
    "lights" : delegates.LightDelegate,
    "images" : delegates.ImageDelegate,
    "textures" : delegates.TextureDelegate,
    "samplers" : delegates.SamplerDelegate,
    "buffers" : delegates.BufferDelegate,
    "bufferviews" : delegates.BufferViewDelegate,
    "document" : delegates.DocumentDelegate
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

    def __init__(self, url, loop, custom_delegate_hash, is_connected):
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
        self.is_connected = is_connected
        self.delegates = {}
        self.thread = None
        self._socket = None
        self.name = "Python Client"
        self.state = {
            "entities": {},
            "tables": {},
            "plots": {},
            "signals": {},
            "methods": {},
            "materials": {},
            "geometries": {},
            "lights": {},
            "images": {},
            "textures": {},
            "samplers": {},
            "buffers": {},
            "bufferviews": {}
        }
        self.client_message_map = {
            "intro": 0,
            "invoke": 1
        }
        self.server_message_map = {
            0 : messages.HandleInfo("methods", "create"),
            1 : messages.HandleInfo("methods", "delete"),
            2 : messages.HandleInfo("signals", "create"),
            3 : messages.HandleInfo("signals", "delete"),
            4 : messages.HandleInfo("entities", "create"),
            5 : messages.HandleInfo("entities", "update"),
            6 : messages.HandleInfo("entities", "delete"),
            7 : messages.HandleInfo("plots", "create"),
            8 : messages.HandleInfo("plots", "update"),
            9 : messages.HandleInfo("plots", "delete"),
            10 : messages.HandleInfo("buffers", "create"),
            11 : messages.HandleInfo("buffers", "delete"),
            12 : messages.HandleInfo("bufferviews", "create"),
            13 : messages.HandleInfo("bufferviews", "delete"),
            14 : messages.HandleInfo("materials", "create"),
            15 : messages.HandleInfo("materials", "update"),
            16 : messages.HandleInfo("materials", "delete"),
            17 : messages.HandleInfo("images", "create"),
            18 : messages.HandleInfo("images", "delete"),
            19 : messages.HandleInfo("textures", "create"), 
            20 : messages.HandleInfo("textures", "delete"),
            21 : messages.HandleInfo("samplers", "create"),
            22 : messages.HandleInfo("samplers", "delete"),
            23 : messages.HandleInfo("lights", "create"),
            24 : messages.HandleInfo("lights", "update"),
            25 : messages.HandleInfo("lights", "delete"),
            26 : messages.HandleInfo("geometries", "create"),
            27 : messages.HandleInfo("geometries", "delete"),
            28 : messages.HandleInfo("tables", "create"),
            29 : messages.HandleInfo("tables", "update"),
            30 : messages.HandleInfo("tables", "delete"),
            31 : messages.HandleInfo("document", "update"),
            32 : messages.HandleInfo("document", "reset"),  
            33 : messages.HandleInfo("signals", "invoke"),  
            34 : messages.HandleInfo("methods", "reply")
        }
        self._current_invoke = 0
        self.callback_map = {}

        # Hook up delegate map to default or custom based on input hash
        for key in default_delegates:
            if key not in custom_delegate_hash:
                self.delegates[key] = default_delegates[key]
            else:
                self.delegates[key] = custom_delegate_hash[key]
        self.state["document"] = self.delegates["document"](self)
        

    def invoke_method(self, id, args, context = None, callback = None):
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
            id (list): 
                id for method
            args (list): 
                arguments for method
            context (InvokeIDType): 
                optional, target context for method call
            callback (function): 
                function to be called upon response
        """

        # Get invoke ID
        invoke_id = str(self._current_invoke)
        self._current_invoke += 1

        # Keep track of callback
        self.callback_map[invoke_id] = callback

        # Construct message dict
        arg_dict = {
            "method": id,
            "args": args,
            "invoke_id": invoke_id
        }
        if context: arg_dict["context"] = context
        
        self.send_message(arg_dict, "invoke")


    def send_message(self, message_dict, type):
        """Send message to server

        Args:
            message (InvokeMethodMessage) : message object to be sent
        """

        # Construct message with ID from map and converted message object
        message = [self.client_message_map[type], message_dict]
        #print(f"Sending Message: {message}")
        
        asyncio.run_coroutine_threadsafe(self._socket.send(dumps(message)), self._loop)


    async def run(self):
        """Network thread for managing websocket connection"""  

        print(f"Connecting to server @ {self._url}")
        async with websockets.connect(self._url) as websocket:
            
            # update class
            self._socket = websocket
            self.name = (f"Python Client @ {self._url}") # couldn't get self._socket.gethostname() to work from source

            # send intro message
            intro = {"client_name": self.name}
            self.send_message(intro, "intro")
            self.is_connected.set()

            # handle all incoming messages
            async for message in self._socket:
                try:
                    handlers.handle(self, message)
                except Exception as e:
                    print(f"Exception: {e}")
    

    def shutdown(self):
        """Method for shutting down Websocket connection"""
        
        asyncio.run_coroutine_threadsafe(self._socket.close(), self._loop)

    
