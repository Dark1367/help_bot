import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from config import DB_PATH

DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

engine = create_async_engine(DATABASE_URL, echo=False)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

# Создаём файл базы и таблицы, если их ещё нет
async def init_db():
    import data.models # noqa: F401 — чтобы модели попали в Base.metadata
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logging.info(msg="База данных инициализирована.")
    except Exception as e:
        logging.error(msg=f"Ошибка при инициализации базы данных: {e}")
        raise
