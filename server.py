import asyncio
import json
import logging
import names
import websockets

from websockets import (WebSocketServerProtocol)
from websockets.exceptions import (ConnectionClosedOK)
from services.exchange_service import (ExchangeService)

from services.logger_service import (LoggerService)
logging.basicConfig(level=logging.INFO)


class Server:

    clients = set()

    def __init__(self):

        self.exchange_service = (ExchangeService())
        self.logger = LoggerService()

    async def register(self,ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()

        self.clients.add(ws)

        logging.info(f"{ws.remote_address} connects")

    async def unregister(self,ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f"{ws.remote_address} disconnects")

    async def send_to_clients(self,message: str):
        if self.clients:
            await asyncio.gather(*[client.send(message) for client in self.clients])

    async def process_exchange(self,message: str):

        parts = message.split()
        days = 1
        if len(parts) > 1:

            try:
                days = int(parts[1])

            except ValueError:
                pass

        data = await (self.exchange_service.get_exchange(days))

        await self.logger.log(message)

        return json.dumps(data,ensure_ascii=False,indent=2)

    async def distribute(self,ws: WebSocketServerProtocol):

        async for message in ws:

            if message.startswith("exchange"):

                result = (await self.process_exchange(message))

                await self.send_to_clients(result)

            else:
                await self.send_to_clients(f"{ws.name}: {message}")

    async def ws_handler(self,ws: WebSocketServerProtocol):

        await self.register(ws)

        try:
            await self.distribute(ws)

        except ConnectionClosedOK:
            pass

        finally:
            await self.unregister(ws)


async def main():

    server = Server()

    async with websockets.serve(server.ws_handler,"localhost",8080):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())