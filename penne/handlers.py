"""Module for Handling Raw Messages from the Server"""

from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from penne.delegates import Delegate
    from penne.messages import Message
    from penne.core import Client

import weakref

from . import messages

# Helper Methods
def handle_update(client, message: Message, specifier: str):
    """Update a delegate in the current state

    Args:
        client (Client): 
            client to be updated
        message (Message): 
            message containing updates
        specifier (str): 
            which part of state to update
    """

    current_state = client.state[specifier][message.id].info
    for attribute, value in message.as_dict().items():
        setattr(current_state, attribute, value)


def delegate_from_context(client: Client, context: Message) -> Delegate:
    """Get delegate object from a context message object
    
    Args:
        client (Client): client to get delegate from
        context (Message): object containing context
    
    Raises:
        Exception: Couldn't get delegate from context
    """

    if not context:
        target_delegate = client.state["document"]
    elif hasattr(context, "table"):
        target_delegate = client.state["tables"][context.table]
    elif hasattr(context, "entity"):
        target_delegate = client.state["entities"][context.entity]
    elif hasattr(context, "plot"):
        target_delegate = client.state["plots"][context.plot]
    else:
        raise Exception("Couldn't get delegate from context")
    
    return target_delegate


def handle(client: Client, id, message_dict):
    """Handle message from server

    'Handle' uses the ID attached to message to get handling info, and uses this info 
    to take proper course of action with message. The function has 5 main sections 
    handling create, delete, and update messages along with signalinvocation and reply
    messages. For now all other communication messages are simply printed.

    'Handle' is also responsible for managing the client's state and working with the
    delegates in a couple of key ways. This function creates, deletes, and updates
    delegates as well as invoking methods on the delegates using signals.

    Args:
        client (Client): client receiving the message
        encoded_message (CBOR array): array with id and message as dictionary
    """
    
    # Process message using ID from dict
    handle_info = client.server_message_map[id]
    action = handle_info.action
    specifier = handle_info.specifier
    message_obj: Message = messages.Message.from_dict(message_dict)
    print(f"Message: {action} {specifier}")

    if specifier == "plots":
        print(f"\n  {action} - {specifier}\n{message_obj}")
    
    # Update state based on map info
    if action == "create":

        # Create instance of delegate
        specifier = specifier
        reference = weakref.ref(client)
        reference_obj = reference()
        delegate: Delegate = client.delegates[specifier](reference_obj, message_obj, specifier)

        # Update state and pass message info to the delegate's handler
        client.state[specifier][message_obj.id] = delegate
        delegate.on_new(message_obj)
    
    elif action == "delete":

        state_delegate: Delegate = client.state[specifier][message_obj.id]

        # Update delegate and state
        state_delegate.on_remove(message_obj)
        del state_delegate

    elif action == "update":

        if specifier != "document":
            handle_update(client, message_obj, specifier)
            client.state[specifier][message_obj.id].on_update(message_obj)
        else:
            client.state[specifier].on_update(message_obj)

    elif action == "reply":

        # Handle callback functions
        if hasattr(message_obj, "method_exception"):
            raise Exception(f"Method call ({message_obj.invoke_id}) resulted in exception from server: {message_obj.method_exception}")
        else:
            callback = client.callback_map.pop(message_obj.invoke_id)
            if callback:
            
                callback_info = (callback, message_obj.result) if hasattr(message_obj, "result") else (callback, None)
                client.callback_queue.put(callback_info)
                #callback(message_obj.result) if hasattr(message_obj, "result") else callback()


    elif action == "invoke":

        # Handle invoke message from server
        signal_data = message_obj.signal_data
        signal: Delegate = client.state["signals"][message_obj.id]

        # Determine the delegate the signal is being invoked on
        context = getattr(message_obj, "context", False)
        target_delegate = delegate_from_context(client, context)

        # Invoke signal attached to target delegate
        print(f"Invoking {signal.info.name} w/ args: {signal_data}")
        target_delegate.signals[signal.info.name](*signal_data)

    elif action == "initialized":

        if client.on_connected:
            client.callback_queue.put((client.on_connected, None))
            #client.on_connected()

    else:
        # Document reset messages
        print(message_obj)
