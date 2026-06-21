import asyncio
import json
import logging
import names
import websockets

from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
from services.exchange_service import ExchangeService
from services.logger_service import LoggerService


logging.basicConfig(level=logging.INFO)

class Server:

    clients = set()

    def __init__(self):

        self.exchange_service = ExchangeService()
        self.logger = LoggerService()
        self.valid_currencies = set()

    async def load_currencies(self):

        self.valid_currencies = (await self.exchange_service.get_available_currencies())

        logging.info(f"Loaded currencies: {sorted(self.valid_currencies)}")

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

    def is_exchange_command(self,parts: list[str]) -> bool:

        if not parts:
            return False

        if parts[0].lower() != "exchange":
            return False

        # exchange
        if len(parts) == 1:
            return True

        # exchange 3
        if len(parts) == 2:
            return parts[1].isdigit()

        # exchange 3 USD EUR PLN
        if len(parts) >= 3:

            if not parts[1].isdigit():
                return False

            currencies = [
                currency.upper()
                for currency in parts[2:]
            ]

            return all(
                currency in self.valid_currencies
                for currency in currencies
            )

        return False

    async def process_exchange(self,parts: list[str]):

        days = 1
        currencies = None

        # exchange
        if len(parts) == 1:
            pass

        # exchange 3
        elif len(parts) == 2:
            days = int(parts[1])

        # exchange 3 USD EUR PLN
        else:

            days = int(parts[1])

            currencies = [currency.upper() for currency in parts[2:]]

        if days < 1 or days > 10:
            return "Days must be between 1 and 10"

        data = await self.exchange_service.get_exchange(days,currencies)

        await self.logger.log(" ".join(parts))

        return json.dumps(data,ensure_ascii=False,indent=2)

    async def distribute(self,ws: WebSocketServerProtocol):

        async for message in ws:

            parts = message.strip().split()

            if not parts:
                continue

            if self.is_exchange_command(parts):

                result = await self.process_exchange(parts)

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

    await server.load_currencies()

    async with websockets.serve(server.ws_handler,"localhost",8080):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())