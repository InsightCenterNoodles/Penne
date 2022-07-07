# PENNE
Python Client for NOODLES protocol  
(Python Encoded Native NOODLES Endpoint)

## Description
Client which implements the NOODLES messaging protocol for interfacing with serverside data visualisation applications.
The client uses a websocket connection to send CBOR encoded messages. To customize its implementation, the
library offers hooks in the form of delegates which can be overwritten and injected with 
new methods.

## Getting Started
1. Install the library
2. Create a client
3. Use default methods or create custom delegates
