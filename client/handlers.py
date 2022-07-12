from logging import raiseExceptions
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

def ensure_gen_match(id, state_id):
    if id != state_id:
        raise Exception(f"Generation mismatch {id} - {state_id}")

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
        delegate = client.delegates[specifier](reference_obj, message_obj, specifier)

        # Update state and pass message info to the delegate's handler
        client.state[specifier][message_obj.id[0]] = delegate
        delegate.on_new(message_obj)
    
    elif action == "delete":

        state_delegate = client.state[specifier][message_obj.id[0]]

        # Ensure generations match and update state / delegate
        ensure_gen_match(message_obj.id, state_delegate.info.id)
        state_delegate.on_remove(message_obj)
        del state_delegate

    elif action == "update":

        if specifier != "document":
            # Ensure generations match and update state
            ensure_gen_match(message_obj.id, client.state[specifier][message_obj.id[0]].info.id)
            handle_update(client, message_obj, specifier)
            
        # Inform delegate
        client.state[specifier][message_obj.id[0]].on_update(message_obj)

    elif action == "reply":

        # Handle callback functions
        if hasattr(message_obj, "method_exception"):
            raise Exception(f"Method call ({message_obj}) resulted in exception from server")
        else:
            callback = client.callback_map.pop(message_obj.invoke_id)
            callback(message_obj.result)

    elif action == "invoke":

        # Handle invoke message from server
        print("Handling Signal from the server...")
        id = message_obj.id
        signal_data = message_obj.signal_data
        signal = client.state["signals"][id[0]]
        ensure_gen_match(id, signal.info.id)
        print(id, signal_data, signal)

        # Determine the delegate the signal is being invoked on
        context = getattr(message_obj, "context", False)
        if not context:
            target_delegate = client.state["document"]
        elif hasattr(context, "table"):
            target_delegate = client.state["tables"][context.table[0]]
            ensure_gen_match(target_delegate.info.id, context.table)
        elif hasattr(context, "entity"):
            target_delegate = client.state["entities"][context.entity[0]]
            ensure_gen_match(target_delegate.info.id, context.entity)
        elif hasattr(context, "plot"):
            target_delegate = client.state["plots"][context.plot[0]]
            ensure_gen_match(target_delegate.info.id, context.plot)
        else:
            raise Exception("Couldn't handle signal from server")

        # Invoke signal attached to target delegate
        target_delegate.signals[signal.info.name](*signal_data) # are arguments in signal_data?

    else:
        # Communication messages or document messages
        # For right now just print these, could add handlers for "invoke", "reset" actions
        print(message_obj)

    return message_obj

    