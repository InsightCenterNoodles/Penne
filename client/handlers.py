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
    message_obj = Message.from_dict(raw_message[1])

    if client.verbose: print(f"\n  {handle_info.action} - {handle_info.specifier}\n{message_obj}")
    
    # Update state based on map info
    if handle_info.action == "create":

        # Update state and inform delegate
        client.state[handle_info.specifier][message_obj.id[0]] = message_obj
        client.delegates[handle_info.specifier].on_new(message_obj)
    
    elif handle_info.action == "delete":

        state_message = client.state[handle_info.specifier][message_obj.id[0]]
        delegate = client.delegates[handle_info.specifier]

        # Ensure generations match and update state / delegate
        if message_obj.id[1] == state_message.id[1]:
            del state_message
            delegate.on_remove(message_obj)
        else:
            raise Exception("Generation Mismatch")

    elif handle_info.action == "update":

        if handle_info.specifier != "document":
            # Ensure generations match and update state
            if message_obj.id[1] == client.state[handle_info.specifier][message_obj.id[0]].id[1]:
                handle_update(client, message_obj, handle_info.specifier)
            else:
                raise Exception("Generation Mismatch")
            
        # Inform delegate
        client.delegates[handle_info.specifier].on_update(message_obj)

    elif handle_info.action == "reply":

        # Handle callback functions
        if message_obj.method_exception:
            raise Exception(f"Method call ({message_obj.invoke_id}) resulted in exception from server")
        else:
            callback = client.callback_map.pop(message_obj.invoke_id)
            callback(message_obj.result)

    else:
        # Communication messages or document messages
        # For right now just print these, could add handlers for "invoke", "reset" actions
        print(message_obj)

    return message_obj

    