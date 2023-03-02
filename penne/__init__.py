"""Python Client Library for NOODLES Protocol

The client library is based on the NOODLES messaging protocol for communicating with serverside data visualisation applications.
The client uses a websocket connection to send CBOR encoded messages. To customize its implementation, the
library offers hooks in the form of delegates classes which can be extended and overwritten.

Modules:
    client.py
    core.py
    delegates.py
    handlers.py
    messages.py
"""

__version__ = "0.3.6"


# Imports for easier user access
from .client import create_client
from .core import Client
from .delegates import *