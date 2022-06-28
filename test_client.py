import asyncio
from time import sleep
from client import client

WS_URL = "ws://localhost:50000"
METHOD = 0 # Create Point Plot
ARGS = [[1, 2, 3], [1, 2, 3], [1, 2, 3]]


async def main():

    # Create client and connect to url
    test_client = client.create_client(WS_URL)
    await asyncio.sleep(1)

    # Test Invoke Method
    test_client.invoke_method(METHOD, ARGS)

    # Shut down client
    #await test_client.shutdown()
    

if __name__ == "__main__":
    asyncio.run(main())