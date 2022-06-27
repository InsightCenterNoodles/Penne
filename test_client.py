import asyncio
import client
import asyncio

async def main():
    client = client.create_client("ws://localhost:50000")

    while True:
        pass

if __name__ == "__main__":
    asyncio.run(main())