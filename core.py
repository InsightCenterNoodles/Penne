import asyncio
import websockets
from dataclasses import asdict
from cbor2 import dumps
from messages import *
from handlers import * 
from delegates import *


default_delegates = {
    "entities" : EntityDelegate,
    "tables" : TableDelegate,
    "plots" : PlotDelegate,
    "signals" : SignalDelegate,
    "methods": MethodDelegate,
    "materials" : MaterialDelegate,
    "geometries" : GeometryDelegate,
    "lights" : LightDelegate,
    "images" : ImageDelegate,
    "textures" : TextureDelegate,
    "samplers" : SamplerDelegate,
    "buffers" : BufferDelegate,
    "bufferviews" : BufferViewDelegate,
    "documents"  : DocumentDelegate
}

class Client(object):
    """
    Class for representing the client

    Attributes:
        _url (string)                               : address used to connect to server
        loop (event loop )                          : event loop used for network thread
        thread (thread object)                      : network thread used by client
        _socket (WebSocketClientProtocol object)    : socket to connect to server
    """

    def __init__(self, url, loop, custom_delegate_hash = {}):
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
            IntroMessage : 0,
            InvokeMethodMessage : 1
        }
        self.server_message_map = {
            0 : MethodCreateMessage,
            1 : MethodDeleteMessage,
            2 : SignalCreateMessage,
            3 : SignalDeleteMessage,
            4 : EntityCreateMessage,
            5 : EntityUpdateMessage,
            6 : EntityDeleteMessage,
            7 : PlotCreateMessage,
            8 : PlotUpdateMessage,
            9 : PlotDeleteMessage,
            10 : BufferCreateMessage,
            11 : BufferDeleteMessage,
            12 : BufferViewCreateMessage,
            13 : BufferViewDeleteMessage,
            14 : MaterialCreateMessage,
            15 : MaterialUpdateMessage,
            16 : MaterialDeleteMessage,
            17 : ImageCreateMessage,
            18 : ImageDeleteMessage,
            19 : TextureCreateMessage, 
            20 : TextureDeleteMessage,
            21 : SamplerCreateMessage,
            22 : SamplerDeleteMessage,
            23 : LightCreateMessage,
            24 : LightUpdateMessage,
            25 : LightDeleteMessage,
            26 : GeometryCreateMessage,
            27 : GeometryDeleteMessage,
            28 : TableCreateMessage,
            29 : TableUpdateMessage,
            30 : TableDeleteMessage,
            31 : DocumentUpdateMessage,
            32 : DocumentResetMessage,   
            33 : SignalInvokeMessage,   
            34 : MethodReplyMessage,
        }
        self.current_invoke = 0

        # Instantiate Delegates - Default or Custom based on input hash
        for key in default_delegates:
            if key not in custom_delegate_hash:
                self.delegates[key] = default_delegates[key]()
            else:
                self.delegates[key] = custom_delegate_hash[key]()


    def InvokeMethod(self, id, args, context = None):
        """
        Method for invokingage to server

        Parameters:
            method_id   : id for method
            context     : optional context for call
            invoke_id   : string to identi 
            args        : arguments for method
        """
        # Get method ID
        method_id = IDGroup(id, 0).id

        # Get invoke ID
        invoke_id = str(self.current_invoke)
        self.current_invoke += 1

        # Construct message and send
        message = InvokeMethodMessage(method_id, args, context, invoke_id)
        print(message)
        self.send_message(message)


    def send_message(self, message):
        """
        Method to send messages to server

        Parameters:
            message (Message Object) : message to be sent
        """

        # Construct message with ID from map and converted message object
        message = [self.client_message_map[type(message)], asdict(message)]
        
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
            print(self.name)

            # send intro message
            intro = IntroMessage(self.name)
            self.send_message(intro)

            # handle all incoming messages
            async for message in self._socket:
                handle(self, message)
        