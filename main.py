import asyncio
import json
import sys

from services.exchange_service import (ExchangeService)


async def main():

    if len(sys.argv) < 2:

        print("Usage: python main.py DAYS [CURRENCIES]")

        return

    days = int(sys.argv[1])

    currencies = sys.argv[2:]

    service = ExchangeService()

    result = await service.get_exchange(days,currencies)

    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    asyncio.run(main())