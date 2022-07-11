import weakref
from cbor2 import loads

from .messages import Message

def handle_update(client, message, specifier):
    """
    Method for updating a message in the current state

    Parameters:
        client (client object)  : client to be updated
        message (message object): message containing updates
        specifier (str)         : which part of state to update
    """

    current_state = client.state[specifier][message.id[0]]
    for attribute, value in message.as_dict().items():
        if value != None:
            setattr(current_state, attribute, value)

# Put this inside core class?
def handle(client, encoded_message) -> Message:
    """
    Method for handling messages from server

    Parameters:
        encoded_message (array) : array with id and message as dictionary
    """

    # Decode message
    raw_message = loads(encoded_message)
    
    # Process message using ID from dict
    handle_info = client.server_message_map[raw_message[0]]
    action = handle_info.action
    specifier = handle_info.specifier
    message_obj = Message.from_dict(raw_message[1])

    if client.verbose: print(f"\n  {action} - {specifier}\n{message_obj}")
    
    
    # Update state based on map info
    if action == "create":

        # Create instance of delegate
        specifier = specifier
        reference = weakref.ref(client)
        reference_obj = reference()
        delegate = client.delegates[specifier](reference_obj)

        # Update state and pass message info to the delegate's handler
        client.state[specifier][message_obj.id[0]] = delegate
        delegate.on_new(message_obj)
    
    elif action == "delete":

        state_delegate = client.state[specifier][message_obj.id[0]]

        # Ensure generations match and update state / delegate
        if message_obj.id[1] == state_delegate.info.id[1]:
            state_delegate.on_remove(message_obj)
            del state_delegate
        else:
            raise Exception("Generation Mismatch")

    elif action == "update":

        if specifier != "document":
            # Ensure generations match and update state
            if message_obj.id[1] == client.state[specifier][message_obj.id[0]].info.id[1]:
                handle_update(client, message_obj, specifier)
            else:
                raise Exception("Generation Mismatch")
            
        # Inform delegate
        client.state[specifier][message_obj.id[0]].on_update(message_obj)

    elif action == "reply":

        # Handle callback functions
        if message_obj.method_exception:
            raise Exception(f"Method call ({message_obj.invoke_id}) resulted in exception from server")
        else:
            callback = client.callback_map.pop(message_obj.invoke_id)
            callback(message_obj.result)

    elif action == "invoke":

        # Handle invoke message from server
        signal_data = message_obj["signal_data"]
        context = getattr(message_obj, "context", False)
        if not context:
            client.delegates["document"].handle_signal(signal_data)
        elif hasattr(context, "table"):
            # what to do with table id?
            client.delegates["tables"].handle_signal(signal_data)
        elif hasattr(context, "entity"):
            # what to do with table id?
            client.delegates["entities"].handle_signal(signal_data)
        elif hasattr(context, "plot"):
            # what to do with table id?
            client.delegates["plots"].handle_signal(signal_data)
        else:
            raise Exception("Couldn't handle signal from server")

    else:
        # Communication messages or document messages
        # For right now just print these, could add handlers for "invoke", "reset" actions
        print(message_obj)

    return message_obj

    