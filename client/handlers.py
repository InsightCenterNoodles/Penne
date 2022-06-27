from messages import *
from cbor2 import loads
from re import findall
from dataclasses import asdict


def handle_update(client, message, specifier):
    """
    Method for updating a message in the current state
    """

    current_state = client.state[specifier][message.id]
    for attribute, value in asdict(message).items():
        if value:
            current_state.attribute = value


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


def message_from_dict(message_name, arg_dict):
    """
    Function for converting a dictionary to a message object of specified type
        also converts the id to an IDGroup object

    Parameters:
        message_name (Type Object)  : Type of desired message object
        arg_dict (dict)             : dictionary to be converted
    """
    return message_name(**arg_dict)


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
    message = message_from_dict(message_type, message[1])
    print(type(message))

    # Convert to string and process based on type name
    message_type = str(message_type)
    specifier = get_specifier(message_type)
    
    # Update state based on message type and specifier
    if "Create" in message_type:
        message.id = IDGroup(*message.id)
        client.state[specifier][message.id] = message

        # Inform delegate with specifier
        client.delegates[specifier].on_new(message)
    
    elif "Delete" in message_type:
        id = IDGroup(*message.id)
        del client.state[specifier][id]

        # Inform delegate with specifier
        client.delegates[specifier].on_remove(message)

    elif "Update" in message_type and not "Document" in message_type:
        message.id = IDGroup(*message.id)
        handle_update(client, message, specifier)

        # Inform delegate with specifier
        client.delegates[specifier].on_update(message)
    
    return message

    