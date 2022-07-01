import asyncio
import websockets
from dataclasses import asdict
from cbor2 import dumps
import weakref

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
    "documents" : delegates.DocumentDelegate
}

class Client(object):
    """
    Class for representing the client

    Attributes:
        _url (string)                               : address used to connect to server
        loop (event loop )                          : event loop used for network thread
        delegates (dict)                            : map for delegate functions     
        is_connected(threading event object)        : event to signal when connection is ready
        verbose (bool)                              : flag for enabling console output
        thread (thread object)                      : network thread used by client
        _socket (WebSocketClientProtocol object)    : socket to connect to server
        name (str)                                  : name of the client
        state (dict)                                : dict keeping track of created objects
        client_message_map (dict)                   : mapping message type to corresponding id
        server_message_map (dict)                   : mapping message id's to corresponding message type
        current_invoke (str)                        : id for next method invoke
        callback_map (dict)                         : mappingn invoke_id to function to be called upon response
        
    Methods:
        inject_method(self, delegate_name, method_dict) : add custom methods to any delegate
        invoke_method(self, id, args, context = None)   : call method for server to execute
        send_message(self, message)                     : send message to the server
        run(self)                                       : main context for managing websocket connection
        shutdown(self)                                  : close websocket connection and background thread

    """

    def __init__(self, url, loop, custom_delegate_hash, is_connected, verbose):
        """
        Constructor for the Client Class

        Parameters:
            _url (string)               : address used to connect to server
            loop (event loop)           : event loop used for network thread
            custom_delegage_hash (dict) : map for new delegate methods
        """

        self._url = url
        self.loop = loop
        self.delegates = {}
        self.is_connected = is_connected
        self.verbose = verbose
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
            messages.IntroMessage : 0,
            messages.InvokeMethodMessage : 1
        }
        self.server_message_map = {
            0 : messages.MethodCreateMessage,
            1 : messages.MethodDeleteMessage,
            2 : messages.SignalCreateMessage,
            3 : messages.SignalDeleteMessage,
            4 : messages.EntityCreateMessage,
            5 : messages.EntityUpdateMessage,
            6 : messages.EntityDeleteMessage,
            7 : messages.PlotCreateMessage,
            8 : messages.PlotUpdateMessage,
            9 : messages.PlotDeleteMessage,
            10 : messages.BufferCreateMessage,
            11 : messages.BufferDeleteMessage,
            12 : messages.BufferViewCreateMessage,
            13 : messages.BufferViewDeleteMessage,
            14 : messages.MaterialCreateMessage,
            15 : messages.MaterialUpdateMessage,
            16 : messages.MaterialDeleteMessage,
            17 : messages.ImageCreateMessage,
            18 : messages.ImageDeleteMessage,
            19 : messages.TextureCreateMessage, 
            20 : messages.TextureDeleteMessage,
            21 : messages.SamplerCreateMessage,
            22 : messages.SamplerDeleteMessage,
            23 : messages.LightCreateMessage,
            24 : messages.LightUpdateMessage,
            25 : messages.LightDeleteMessage,
            26 : messages.GeometryCreateMessage,
            27 : messages.GeometryDeleteMessage,
            28 : messages.TableCreateMessage,
            29 : messages.TableUpdateMessage,
            30 : messages.TableDeleteMessage,
            31 : messages.DocumentUpdateMessage,
            32 : messages.DocumentResetMessage,   
            33 : messages.SignalInvokeMessage,   
            34 : messages.MethodReplyMessage,
        }
        self.current_invoke = 0
        self.callback_map = {}

        # Instantiate Delegates - Default or Custom based on input hash
        reference = weakref.ref(self)
        reference_obj = reference()
        for key in default_delegates:
            if key not in custom_delegate_hash:
                self.delegates[key] = default_delegates[key](reference_obj)
            else:
                self.delegates[key] = custom_delegate_hash[key](reference_obj)


    def inject_methods(self, delegate_name, method_dict):
        """
        Method to inject methods into a delegate class

        Parameters:
            delegate_name (str) : identifier for delegate to be modified
            method_dict (dict)  : dict mapping method name to function
        """

        delegate = self.delegates[delegate_name]

        # Set attributes for each method in dict
        for key, value in method_dict.items():
            setattr(delegate, key, value)
        

    def invoke_method(self, id, args, context = None, callback = lambda result: None):
        """
        Method for invokingage to server

        Parameters:
            id          : id for method
            args        : arguments for method
            context     : optional context for call
            callback    : function to be called upon response
        """
        # Get method ID
        method_id = messages.IDGroup(id, 0).id

        # Get invoke ID
        invoke_id = str(self.current_invoke)
        self.current_invoke += 1

        # Keep track of callback
        self.callback_map[invoke_id] = callback

        # Construct message and send
        message = messages.InvokeMethodMessage(method_id, args, context, invoke_id)
        if self.verbose: print(message)
        self.send_message(message)

    
    def clean(self, message_dict):
        cleaned = {}
        for key, value in message_dict.items():
            if type(value) == dict:
                value = self.clean(value)
            if value != None and value != 'None':
                cleaned[key] = value
        print(cleaned)
        return cleaned


    def send_message(self, message):
        """
        Method to send messages to server

        Parameters:
            message (Message Object) : message to be sent
        """

        # Construct message with ID from map and converted message object
        message_dict = asdict(message)
        clean_message_dict = self.clean(message_dict)
        message = [self.client_message_map[type(message)], clean_message_dict]
        
        asyncio.run_coroutine_threadsafe(self._socket.send(dumps(message)), self.loop)


    async def run(self):
        """
        Network thread for managing websocket connection
        """  

        print(f"Connecting to server @ {self._url}")
        async with websockets.connect(self._url) as websocket:
            
            # update class
            self._socket = websocket
            self.name = (f"Python Client @ {self._url}") # couldn't get self._socket.gethostname() to work from source

            # send intro message
            intro = messages.IntroMessage(self.name)
            self.send_message(intro)

            # set event indicating connection is established
            self.is_connected.set()

            # handle all incoming messages
            async for message in self._socket:
                handlers.handle(self, message)
    

    def shutdown(self):
        """
        Method for shutting down Websocket connection
        """
        
        asyncio.run_coroutine_threadsafe(self._socket.close(), self.loop)
