import asyncio
from datetime import datetime, timedelta
from services.privatbank_client import PrivatBankClient


class ExchangeService:

    DEFAULT_CURRENCIES = ["USD", "EUR"]

    def __init__(self):
        self.client = PrivatBankClient()


    async def get_available_currencies(self) -> set[str]:
        response = await self.client.get_rates_for_date(datetime.now().strftime("%d.%m.%Y"))

        currencies = set()

        for item in response["exchangeRate"]:

            currency = item.get("currency")

            if currency:
                currencies.add(currency.upper())

        return currencies
    
    async def get_exchange(self,days: int,currencies: list[str] | None = None):
        # защита от неправильного диапазона дней
        if days < 1 or days > 10:
            raise ValueError("Days must be between 1 and 10")
        # если валюты не передали — берём дефолтные
        currencies = (
            currencies
            if currencies
            else self.DEFAULT_CURRENCIES
        )
        # формируем список дат для получения курсов валют
        dates = []

        for i in range(days):

            day = (
                datetime.now() - timedelta(days=i)
            ).strftime("%d.%m.%Y")

            dates.append(day)

        # запускаем асинхронные запросы к API для каждой даты
        tasks = [
            self.client.get_rates_for_date(date)
            for date in dates
        ]

        responses = await asyncio.gather(*tasks)

        # собираем все доступные валюты из API (для проверки)
        available_currencies = {
            item.get("currency")
            for response in responses
            for item in response.get("exchangeRate", [])
            if item.get("currency")
        }

        # проверяем неправильные валюты
        invalid = set(currencies) - available_currencies

        if invalid:
            print(f"Warning: unknown currencies ignored -> {invalid}")

            # fallback на дефолтные валюты, если переданные невалидные
            print(f"Using default currencies: {', '.join(self.DEFAULT_CURRENCIES)}")
            currencies = self.DEFAULT_CURRENCIES

        result = []

        # проходим по каждому ответу от API и фильтруем валюты
        for response in responses:

            date = response.get("date")
            day_data = {}

            for item in response.get("exchangeRate", []):

                currency = item.get("currency")
                # print(item["currency"])
                
                if not currency:
                    continue

                if currency in ("UAH", None, ""):
                    continue

                # фильтрация валют
                if currency not in currencies:
                    continue

                day_data[currency] = {
                    "sale": (
                        item.get("saleRate")
                        if item.get("saleRate") is not None
                        else item.get("saleRateNB")
                    ),
                    "purchase": (
                        item.get("purchaseRate")
                        if item.get("purchaseRate") is not None
                        else item.get("purchaseRateNB")
                    )
                }

            result.append({date: day_data})

        return result