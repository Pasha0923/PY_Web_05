from datetime import datetime

from aiofile import async_open
from aiopath import AsyncPath


class LoggerService:

    def __init__(
        self,
        path="logs/exchange.log"
    ):
        self.path = AsyncPath(path)

    async def log(self, message: str):

        await self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        async with async_open(
            self.path,
            "a",
            encoding="utf-8"
        ) as file:

            timestamp = (
                datetime.now()
                .strftime("%Y-%m-%d %H:%M:%S")
            )

            await file.write(
                f"{timestamp} | {message}\n"
            )