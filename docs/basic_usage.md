
1. Define delegates
2. Start up the client

## Working with delegates

>What are delegates? 

NOODLES messages deal with many objects ranging from tables and plots to lights and materials. To help with 
using these objects, each type has its own delegate class. Each object in a scene corresponds with an instance of a delegate
which is stored in the client's state. Delegates provide methods specific to each type of object. These objects can contain 
injected methods and signals from the server. All delegates come with methods `on_new()`, `on_update()`, and `on_remove()`
which are called automatically when the server sends a message to create, update, or delete an object.

>How can I customize delegates?

To work with your own delegates, simply create a class that inherits from the base delegate. Then, pass a dictionary as
an argument to the server that maps the delegate's type to the new class. In `tests/clients.py` there is a more
involved example that extends the table delegate. In that example, the delegate class 
inherits from `Table` and uses pandas and matplotlib to add plotting functionality. Below is an even more basic example
that prints a message whenever a new method is created.

```python
from penne import Method, Client


class CustomMethod(Method):
  
  def on_new(self, message: dict):
    print(f"New method named {self.name} was created")
    
      
with Client("ws://localhost:50000", {Method: CustomMethod}) as client:
  # do stuff

```

>How do you call methods on a delegate?

Once instantiated, delegates are injected with methods designated by the server. These methods can be called by using
public methods on the delegate that essentially wrap the injected ones. Once the method is invoked, the server will 
respond with a signal that updates the client. Each signal is linked to a method in the delegate which keeps the state of 
the client up to date. To customize the client's behavior, these methods can be overwritten in a custom delegate. Each 
public method also accepts a callback function to be executed once a response is received from the server. 
This way, method calls can be chained together and run in sequence. A common example is the `Table` delegate. The server
by default will define methods to insert, remove, and update rows in the table. The client can request to call these 
injected methods, and then the server will send a signal back to the client to update the table if the call was 
successful. An example is provided in `tests/plottyn_integration.py`.

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

## Starting up the client

The easiest way to create a client instance is to use the context manager. This will automatically start the websocket
connection and communication thread while closing it when the client goes out of scope. To add custom delegates,
simply use the optional parameter `delegate_hash` to map the delegate type to a custom class. The context manager
also manages an 'is_active' flag to signify whether the connection is open and the client is still running. This can be
used to poll for callbacks. The client also has a couple of other optional parameters. Users can specify a method to 
be called as soon as the client is connected with `on_connected`. The client validates incoming messages and coerces
them into the correct type. By default, this will log an error to indicate that the server is not conforming to the
protocol exactly. To change these warnings into hard exceptions, set `strict` to `True`. Lastly, putting a file path for
the json parameter will cause the client to write all incoming messages to that file. This can be useful for debugging
or logging purposes.
```python
from penne import Client

with Client(address, delegate_hash) as client:
    # do stuff
```

However, you can also instantiate the client and manage the communication thread manually. This may be useful if you
want to run the client from the REPL.
```python
client = Client(address, delegate_hash)
client.thread.start()  # Starts websocket connection in new thread
client.connection_established.wait()  # Usually isn't a problem when using the REPL
# do stuff
client.shutdown()  # Close websocket connection and join the thread
```
