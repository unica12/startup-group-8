"""Инициализация базы данных и управление сессиями."""
from __future__ import annotations

import logging
import ssl
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.models import Base
from database.migrations import add_receipt_details
from utils.config import SUPABASE_DB_CA_FILE, get_database_url

logger = logging.getLogger(__name__)

# Асинхронный движок SQLAlchemy
def create_engine():
    try:
        url = get_database_url()
        if url.get_backend_name() == "sqlite":
            return create_async_engine(url.set(drivername="sqlite+aiosqlite"), hide_parameters=True)
        if url.get_backend_name() == "postgresql" or url.drivername == "postgres":
            ca_file = SUPABASE_DB_CA_FILE or url.query.get("sslrootcert")
            context = ssl.create_default_context()
            if ca_file:
                context.load_verify_locations(cafile=Path(ca_file).expanduser())
            url = url.set(drivername="postgresql+asyncpg").difference_update_query(
                ["ssl", "sslmode", "sslrootcert"]
            )
            return create_async_engine(
                url, hide_parameters=True, pool_pre_ping=True,
                pool_size=3, max_overflow=2, pool_timeout=10, pool_recycle=900,
                connect_args={"ssl": context, "timeout": 12, "server_settings": {"timezone": "UTC"}},
            )
    except (ValueError, OSError):
        raise RuntimeError("Не удалось прочитать настройки подключения к базе.") from None
    raise RuntimeError("DATABASE_URL должен указывать на PostgreSQL или SQLite.")


engine = create_engine()

# Фабрика сессий
AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Создать схему и закрыть доступ к прикладным таблицам через Data API."""
    try:
        async with engine.begin() as conn:
            postgres = conn.dialect.name == "postgresql"
            if postgres:
                await conn.execute(text("SET LOCAL lock_timeout TO '5s'"))
                await conn.execute(text("SELECT pg_advisory_xact_lock(45086023)"))
                await conn.execute(text("SET LOCAL search_path TO public"))
            await conn.run_sync(Base.metadata.create_all)
            await add_receipt_details(conn)
            if postgres:
                await conn.execute(text("ALTER TABLE public.users ADD COLUMN IF NOT EXISTS auth_user_id uuid"))
                columns = await conn.run_sync(lambda sync: inspect(sync).get_columns("users", schema="public"))
                if any(column["name"] == "device_id" and not column["nullable"] for column in columns):
                    await conn.execute(text("ALTER TABLE public.users ALTER COLUMN device_id DROP NOT NULL"))
                await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_auth_user_id ON public.users (auth_user_id)"))
                for table in Base.metadata.sorted_tables:
                    name = f"public.{table.name}"
                    await conn.execute(text(f"ALTER TABLE {name} ENABLE ROW LEVEL SECURITY"))
                    await conn.execute(text(f"REVOKE ALL ON TABLE {name} FROM PUBLIC, anon, authenticated, service_role"))
                    # Запрос возвращает экранированное PostgreSQL имя связанной sequence.
                    sequence = await conn.scalar(text("SELECT pg_get_serial_sequence(:name, 'id')"), {"name": name})
                    if sequence:
                        await conn.execute(text(f"REVOKE ALL ON SEQUENCE {sequence} FROM PUBLIC, anon, authenticated, service_role"))
    except ssl.SSLCertVerificationError:
        raise RuntimeError("Сертификат PostgreSQL не прошёл проверку. Проверь SUPABASE_DB_CA_FILE.") from None
    except Exception as exc:
        raise RuntimeError(f"Не удалось подключить или подготовить базу ({type(exc).__name__}).") from None
    logger.info("База данных инициализирована")


async def close_db() -> None:
    """Закрыть все соединения с базой данных."""
    await engine.dispose()
    logger.info("Соединения с базой данных закрыты")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для FastAPI: получить сессию БД."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
