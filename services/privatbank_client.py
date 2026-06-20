# import aiohttp
# import asyncio


# async def test():
#     async with aiohttp.ClientSession() as session:
#         async with session.get(
#             "https://api.privatbank.ua/p24api/exchange_rates?json&date=20.06.2026"
#         ) as response:

#             print("STATUS:", response.status)

#             data = await response.json()

#             print(data)


# asyncio.run(test())


from datetime import datetime

import aiohttp


class PrivatBankClient:

    BASE_URL = (
        "https://api.privatbank.ua/p24api/exchange_rates?json&date={date}"
    )

    async def get_rates_for_date(self, date: str) -> dict:

        url = self.BASE_URL.format(date=date)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:

                if response.status != 200:
                    raise ConnectionError(
                        f"API error: {response.status}"
                    )

                return await response.json()