"""Инициализация базы данных и управление сессиями."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.models import Base
from utils.config import DATABASE_URL

logger = logging.getLogger(__name__)

# Асинхронный движок SQLAlchemy
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# Фабрика сессий
AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Создать все таблицы если они не существуют."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("База данных инициализирована")


async def close_db() -> None:
    """Закрыть все соединения с базой данных."""
    await engine.dispose()
    logger.info("Соединения с базой данных закрыты")


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Контекстный менеджер для получения сессии БД."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
