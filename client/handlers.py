from cbor2 import loads
from re import findall
from dataclasses import asdict, is_dataclass
from dacite import from_dict

from . import messages


def handle_update(client, message, specifier):
    """
    Method for updating a message in the current state

    Parameters:
        client (client object)  : client to be updated
        message (message object): message containing updates
        specifier (str)         : which part of state to update
    """

    current_state = client.state[specifier][message.id]
    for attribute, value in asdict(message).items():
        if value != None:
            setattr(current_state, attribute, value)


def get_specifier(message_name):
    """
    Function to get first word or specifier for a message type

    Parameters:
        message_name (str) : name to parsed
    """

    # Split at capital letters and get first word
    words = findall('[A-Z][^A-Z]*', message_name)
    if words[0] == "Buffer" and words[1] == "View": # Two word edge case
        specifier = (words[0] + words[1]).lower()
    else:
        specifier = words[0].lower()
    

    # Modify to match state keys\
    if specifier[-1] == 'y':
        specifier = specifier[:-1] + 'ies'
    else:
        specifier = specifier + 's'
    return specifier


def messages_from_list(message_name, list):
    message_list = []
    return message_list


def message_from_data(message_name, data):
    """
    Function for converting a dictionary to a message object of specified type
        also converts the id to an IDGroup object

    Parameters:
        message_name (Type Object)  : Type of desired message object
        arg_dict (dict / list)      : Raw data to be converted
    """
    # Cover list base case
    if isinstance(data, list):
        message_obj = message_name(*data)
        return message_obj

    to_remove = []
    message_obj = message_name(**data)
    annotations = message_obj.__annotations__
    print(message_name)
    print(annotations)
    for attr, val in vars(message_obj).items():
        print(f"--{attr}--{type(val) is list}")
        if val == None:
            to_remove.append(attr)
        elif is_dataclass(annotations[attr]):
            setattr(message_obj, attr, message_from_data(annotations[attr], val))
        elif type(val) is list and isinstance(val[0], dict):
            print("Found list of messages...")
            print(annotations[attr])
            #setattr(message_obj, attr, messages_from_list(val))            
    
    # print(to_remove)
    # for key in to_remove:
    #     print(f"deleting: {key}")
    #     delattr(message_obj, key)
    print(message_obj)
    return message_obj


def handle(client, message):
    """
    Method for handling messages from server

    Parameters:
        message (array) : array with id and message as dictionary
    """

    # Decode message
    message = loads(message)

    # Process message using ID from dict
    message_type = client.server_message_map[message[0]]
    message = message_from_data(message_type, message[1])
    print(message_type)
    if client.verbose: print(type(message))

    # Convert to string and process based on type name
    message_type = str(message_type)
    specifier = get_specifier(message_type)
    
    # Update state based on message type and specifier
    if "Create" in message_type:

        client.state[specifier][message.id] = message

        # Inform delegate with specifier
        client.delegates[specifier].on_new(message)
    
    elif "Delete" in message_type:

        del client.state[specifier][id]

        # Inform delegate with specifier
        client.delegates[specifier].on_remove(message)

    elif "Update" in message_type and not "Document" in message_type:

        print("handling update...")
        handle_update(client, message, specifier)

        # Inform delegate with specifier
        client.delegates[specifier].on_update(message)
    else:
        # Communication messages or document messages
        print(message)

        # Handle callback
        if type(message) == messages.MethodReplyMessage:
            if message.method_exception:
                print(f"Method call ({message.invoke_id}) resulted in exception from server ")
            else:
                callback = client.callback_map.pop(message.invoke_id)
                callback(message.result)
    
    return message

    