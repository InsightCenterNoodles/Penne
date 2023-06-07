# PENNE

![Build Status](https://github.com/InsightCenterNoodles/Penne/workflows/CI/badge.svg)
![PyPI](https://img.shields.io/pypi/v/Penne)
[![Coverage badge](https://raw.githubusercontent.com/InsightCenterNoodles/Penne/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/InsightCenterNoodles/Penne/blob/python-coverage-comment-action-data/htmlcov/index.html)


Python Client for NOODLES protocol  
(Python Encoded Native NOODLES Endpoint)

## Description
The client library is based on the NOODLES messaging protocol for communicating with serverside data visualisation applications. The client uses a websocket connection to send CBOR encoded messages. To customize its implementation, the
library offers hooks in the form of delegates classes which can be extended.

## How does the client work?
When a message is received from the server, the client passes the CBOR encoded message to a handler function which uses
the message's ID to process it accordingly. Based on this ID, the message can be classified as either a create, delete, 
update, reply, or invoke message. Upon receiving a create message, the handler creates a new delegate for that object
which is then stored in the client's state. Delete and update messages manipulate delegates in the client's state as expected. 
Reply messages indicate whether a method was invoked on the server successfully, and then a callback function can be 
executed if applicable. Lastly, invoke messages represent signals from the server which are being called on a delegate. 
The handler sends this signal to the target delegate so it can call a corresponding function. 

To send a message, the user calls a method on a delegate or the document more broadly. Delegates may have injected 
methods from the server, and the client can send a message invoking the method. For example, the server can define a
method like insert_row() on a table delegate. The client can then call this method on the delegate, and the server will
get a message requesting to invoke the method. The server will then respond by updating the state, invoking signals, 
and sending a reply message to the client. If the server is unable to invoke the method, it will send a reply message
that contains an exception.

A diagram representing the simplified relationships between the client, server, and delegates is depicted below. 

```mermaid
sequenceDiagram
    participant User
    participant Delegate
    participant Client
    participant Server
    User->>Delegate: Create Custom Delegates
    User->>Client: Starts Server with Custom Delegates
    Client->>Server: Sends Intro Message
    Server->>Client: Updates the Client with Current State
    loop until end of session
        User->>Delegate: Invoke Injected or Custom Method on Delegate or...
        User->>Client: Invoke Method on Client Directly
        Client->>Server: Request to Invoke Method
        Server->>Client: Responds to Update State
        Client->>Delegate: Invokes Signals, Creates, Updates, and Deletes Delegates
        Client->>User: Show Current State
    end
```

## Working with delegates
>What are delegates? 

NOODLES messages deal with many objects ranging from tables and plots to lights and materials. To help with 
using these objects, each type has its own delegate class. Each object in a scene corresponds with an instance of a delegate
which is stored in the client's state. Delegates provide methods specific to each type of object. These objects can contain 
injected methods and signals from the server. All delegates come with methods `on_new()`, `on_update()`, and `on_remove()`
which are called automatically when the server sends a message to create, update, or delete an object.

>How can I use custom delegates?

To work with your own delegates, simply create a class that inherits from the base delegate. Then, pass a dictionary as
an argument to the constructor that maps the delegate's type to the new class. In `tests/clients.py` there is a more
involved example that extends the table delegate. Here, the delegate class 
inherits from `Table` and uses pandas and matplotlib to add plotting functionality. Below is an even more basic example
that prints a message whenever a new method is created.

```python
from penne import Method, Client


class CustomMethod(Method):
  
  def on_new(self, message: dict):
    print(f"New method named {self.name} was created")
    
      
with Client(address, {Method: CustomMethod}) as client:
  # do stuff

```

>How do you call methods on a delegate?

Once instantiated, delegates are injected with methods designated by the server. These methods can be called by using
public methods on the delegate that essentially wrap the injected ones. Once the method is invoked, the server will 
respond with a signal that updates the client. Each signal is linked to a method in the delegate which keeps the state of 
the client up to date. To customize the client's behavior, these methods can be overwritten in a custom delegate. Each 
public method also accepts a callback function to be executed once a response is received from the server. 
This way, method calls can be chained together and run in sequence. An example is provided in `tests/plottyn_integration.py`.

### Tables
The table delegate comes with several built in methods covering basic table manipulation. The delegate includes...
```python
subscribe(on_done=None)
request_insert(row_list: list=None, on_done=None)
request_remove(keys: list, on_done=None)
request_update(keys: List[int], rows: List[List[int]], on_done=None)
request_clear(on_done=None)
request_update_selection(name: str, keys: list, on_done=None)
```
When using these methods, the user has the option of including a callback function (on_done) that will execute once complete.
Once invoked, signals from the server will update the table in the delegate. For the table thereare several signals that
can be overwritten in a custom delegate. While you can inherit and customize them for your specif implementation of the
table, they should not be called directly by users. They will be called when indicated by a message from the server. 
These include...
```python
_on_table_init(init_info: dict, on_done=None)
_reset_table(init_info: dict)
_remove_rows(keys: list[int])
_update_rows(keys: list[int], rows: list[list])
_update_selection(selection: dict)
```

## Getting Started
1. Install the library
```python
pip install penne
```
2. Create a client using 
```python
from penne import Client

with Client(address, delegate_hash) as client:
    # do stuff
```
- (Optional) use delegate hash to map custom delegates
- This is the recommended way to create a client as it will automatically close the connection when the client goes out of scope
- It also manages an 'is_active' flag to signify whether the connection is open and the client is still running
  - This can be used to poll for callbacks
- However, you can also instantiate the client and manage the communication thread manually
```python
client = Client(address, delegate_hash)
client.thread.start()  # Starts websocket connection in new thread
client.connection_established.wait() 
# do stuff
client.shutdown()  # Close websocket connection
client.thread.join()
```
3. Explore and manipulate data on the server using client or delegate methods
- call `show_methods()` on the client to see a list of available methods with documentation
- call `show_methods()` on a delegate to see a list of available methods for that instance
