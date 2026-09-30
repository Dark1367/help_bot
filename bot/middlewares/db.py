from typing import Any, Awaitable, Callable

from sqlalchemy.ext.asyncio import async_sessionmaker
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


# Открывает сессию на время обработки события и передаёт её в хендлер как session
class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_maker: async_sessionmaker):
        self.session_maker = session_maker

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ):
        async with self.session_maker() as session:
            data["session"] = session
            return await handler(event, data)
