import sys
sys.dont_write_bytecode = True

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, init_logger
from data.database import init_db, async_session_maker
from bot.handlers.user_handlers import router as user_router
from bot.middlewares.db import DbSessionMiddleware

init_logger()

async def main():
    await init_db()

    dp = Dispatcher(storage=MemoryStorage())
    bot = Bot(token=BOT_TOKEN)

    db_middleware = DbSessionMiddleware(async_session_maker)
    user_router.business_connection.middleware(db_middleware)
    user_router.business_message.middleware(db_middleware)
    user_router.message.middleware(db_middleware)
    user_router.callback_query.middleware(db_middleware)

    dp.include_router(user_router)

    logging.info(msg="Бот запущен.")

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    logging.info(msg="Бот запускается...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info(msg="Бот выключен разработчиком.")
    except Exception as e:
        logging.error(msg=f"Бот не запустился, ошибка: {e}")
