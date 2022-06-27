import asyncio
from struct import unpack
import websockets
from cbor2 import loads, dumps
from messages import IntroMessage, InvokeMethodMessage
from dataclasses import asdict

def cast_message(message):
    """
    Method for casting messages to their proper objects

    Parameters:
        message (array) : array with id and message as dictionary
    """
    
    # Cast message to message object based on ID
    if message[0] == 0:
        return IntroMessage(message[1])
    elif message[0] == 1:
        return InvokeMethodMessage(message[1])


async def handler(websocket):
    """
    Coroutine for handling messages from client
    """

    async for message in websocket:

        # Decode and print raw message
        message = loads(message)
        print(f"Message from client: {message}")

        # Verify message has even number of elements, and cast to message object
        if len(message) % 2 == 0:
            message = cast_message(message)
            print(message)
        else:
            print("Malformed Message")

        # Send response to client
        await websocket.send(f"Sever received the message: {dumps(message)}")


async def main():
    """
    Main method for maintaining websocket connection
    """

    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())