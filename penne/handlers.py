"""Module for Handling Raw Messages from the Server"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from penne.core import Client

import weakref
import warnings
import logging
from pydantic import ValidationError

from penne.delegates import Delegate, id_map, default_delegates
from penne.delegates import TableID, PlotID, EntityID, ID


# Helper Methods
def update_state(client, message: dict, component_id: ID):
    """Update a delegate in the current state

    Args:
        client (Client): 
            client to be updated
        message (Message): 
            message containing updates
        component_id (ID):
            ID of the component to be updated
    """

    current_state = client.state[component_id].dict()
    current_state.update(message)

    delegate_type = type(client.state[component_id])
    client.state[component_id] = delegate_type(**current_state)


def delegate_from_context(client: Client, context: dict) -> Delegate:
    """Get delegate object from a context message object
    
    Args:
        client (Client): client to get delegate from
        context (Message): object containing context
    
    Raises:
        Exception: Couldn't get delegate from context
    """

    if not context:
        target_delegate = client.state["document"]
        return target_delegate

    table = context.get("table")
    entity = context.get("entity")
    plot = context.get("plot")

    if table:
        target_delegate = client.state[TableID(*table)]
    elif hasattr(context, "entity"):
        target_delegate = client.state[EntityID(*entity)]
    elif hasattr(context, "plot"):
        target_delegate = client.state[PlotID(*plot)]
    else:
        raise Exception("Couldn't get delegate from context")
    
    return target_delegate


def handle(client: Client, message_id, message: dict[str, Any]):
    """Handle message from server

    'Handle' uses the ID attached to message to get handling info, and uses this info 
    to take proper course of action with message. The function has 5 main sections 
    handling create, delete, and update messages along with signal invocation and reply
    messages.

    'Handle' is also responsible for managing the client's state and working with the
    delegates in a couple of key ways. This function creates, deletes, and updates
    delegates as well as invoking methods on the delegates using signals.

    Args:
        client (Client): client receiving the message
        message_id (int): id mapping to handle info in client
        message (dict): dict with the message's contents
    """
    
    # Process message using ID from dict
    handle_info = client.server_messages[message_id]
    action = handle_info.action
    specifier = handle_info.specifier
    id_type = id_map[default_delegates[specifier]]
    logging.debug(f"Received Message: {action} {specifier} {message}")

    # Update state based on map info
    if action == "create":

        # Create instance of delegate
        reference = weakref.ref(client)
        reference_obj = reference()
        try:
            delegate: Delegate = client.delegates[specifier](client=reference_obj, **message)
            delegate.client = client
            client.state[delegate.id] = delegate
            delegate.on_new(message)
        except ValidationError as e:

            warnings.warn(str(e))

            if client.strict:
                raise Exception(f"Could not Create Delegate of type {specifier}")
    
    elif action == "delete":
        
        component_id = id_type(*message["id"])
        state_delegate: Delegate = client.state[component_id]

        # Update delegate and state
        state_delegate.on_remove(message)
        del state_delegate

    elif action == "update":

        if specifier != "document":
            component_id = id_type(*message["id"])
            update_state(client, message, component_id)
            client.state[component_id].on_update(message)
        else:
            client.state[specifier].on_update(message)

    elif action == "reply":

        # Handle callback functions
        exception = message.get("method_exception", False)
        invoke_id = message.get("invoke_id")
        result = message.get("result")

        if exception:
            raise Exception(f"Method call ({invoke_id}) resulted in exception from server: {exception}")
        else:
            callback = client.callback_map.pop(invoke_id)
            if callback:
            
                callback_info = (callback, result)
                client.callback_queue.put(callback_info)

    elif action == "invoke":

        # Handle invoke message from server
        signal_data = message["signal_data"]
        signal_id = id_type(*message["id"])
        signal: Delegate = client.state[signal_id]

        # Determine the delegate the signal is being invoked on
        context = message.get("context")
        target_delegate = delegate_from_context(client, context)

        # Invoke signal attached to target delegate
        logging.debug(f"Invoking {signal.name} w/ args: {signal_data}")
        target_delegate.signals[signal.name](*signal_data)

    elif action == "initialized":

        if client.on_connected:
            client.callback_queue.put((client.on_connected, None))

    else:
        # Document reset messages
        client.state["document"].reset()
        logging.debug("Document Reset")
