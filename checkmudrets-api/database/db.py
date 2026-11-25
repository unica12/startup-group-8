"""Инициализация базы данных и управление сессиями."""
from __future__ import annotations

import logging
import ssl
from pathlib import Path
from stat import S_ISREG
from typing import AsyncGenerator

from sqlalchemy import inspect, text
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.models import Base
from database.migrations import add_receipt_details
from database.startup import startup_failure
from utils.config import SUPABASE_DB_CA_FILE, get_database_url

logger = logging.getLogger(__name__)


def _postgres_tls_context(ca_file: str | tuple[str, ...] | None) -> ssl.SSLContext:
    try:
        context = ssl.create_default_context()
    except (OSError, ValueError):
        raise RuntimeError("Не удалось создать системный TLS-контекст PostgreSQL.") from None

    if not ca_file:
        return context
    if not isinstance(ca_file, str):
        raise RuntimeError("Укажи один sslrootcert в DATABASE_URL или задай SUPABASE_DB_CA_FILE.")

    try:
        path = Path(ca_file).expanduser()
    except RuntimeError:
        raise RuntimeError("Не удалось раскрыть домашний каталог в пути к CA PostgreSQL.") from None

    try:
        if not S_ISREG(path.stat().st_mode):
            raise RuntimeError("Путь к CA PostgreSQL должен указывать на обычный PEM-файл.")
        context.load_verify_locations(cafile=path)
    except (FileNotFoundError, NotADirectoryError):
        raise RuntimeError("Файл CA PostgreSQL не найден. Проверь SUPABASE_DB_CA_FILE или sslrootcert.") from None
    except PermissionError:
        raise RuntimeError("Файл CA PostgreSQL недоступен для чтения.") from None
    except ssl.SSLError:
        raise RuntimeError("Не удалось загрузить CA PostgreSQL. Нужен действительный сертификат в формате PEM.") from None
    except (OSError, ValueError):
        raise RuntimeError("Не удалось прочитать файл CA PostgreSQL. Проверь путь и доступ к файлу.") from None
    return context


# Асинхронный движок SQLAlchemy
def create_engine():
    try:
        url = get_database_url()
        if url.get_backend_name() == "sqlite":
            return create_async_engine(url.set(drivername="sqlite+aiosqlite"), hide_parameters=True)
        if url.get_backend_name() == "postgresql" or url.drivername == "postgres":
            context = _postgres_tls_context(SUPABASE_DB_CA_FILE or url.query.get("sslrootcert"))
            url = url.set(drivername="postgresql+asyncpg").difference_update_query(
                ["ssl", "sslmode", "sslrootcert"]
            )
            return create_async_engine(
                url, hide_parameters=True, pool_pre_ping=True,
                pool_size=3, max_overflow=2, pool_timeout=10, pool_recycle=900,
                connect_args={"ssl": context, "timeout": 12, "server_settings": {"timezone": "UTC"}},
            )
    except (ArgumentError, ValueError, OSError):
        raise RuntimeError("Не удалось создать движок БД. Проверь параметры DATABASE_URL и драйвер.") from None
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
    stage = "connect"
    postgres = engine.dialect.name == "postgresql"
    try:
        async with engine.connect() as conn:
            if postgres:
                logger.info("PostgreSQL: подключение, TLS и аутентификация прошли.")
            stage = "select_1"
            async with conn.begin():
                await conn.execute(text("SELECT 1"))
                if postgres:
                    logger.info("PostgreSQL: SELECT 1 выполнен.")
                    stage = "migration.lock"
                    await conn.execute(text("SET LOCAL lock_timeout TO '5s'"))
                    await conn.execute(text("SELECT pg_advisory_xact_lock(45086023)"))
                    await conn.execute(text("SET LOCAL search_path TO public"))
                stage = "migration.tables"
                await conn.run_sync(Base.metadata.create_all)
                stage = "migration.receipts"
                await add_receipt_details(conn)
                if postgres:
                    stage = "migration.users"
                    await conn.execute(text("ALTER TABLE public.users ADD COLUMN IF NOT EXISTS auth_user_id uuid"))
                    columns = await conn.run_sync(lambda sync: inspect(sync).get_columns("users", schema="public"))
                    if any(column["name"] == "device_id" and not column["nullable"] for column in columns):
                        await conn.execute(text("ALTER TABLE public.users ALTER COLUMN device_id DROP NOT NULL"))
                    await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_auth_user_id ON public.users (auth_user_id)"))
                    stage = "migration.rls"
                    for table in Base.metadata.sorted_tables:
                        name = f"public.{table.name}"
                        await conn.execute(text(f"ALTER TABLE {name} ENABLE ROW LEVEL SECURITY"))
                        await conn.execute(text(f"REVOKE ALL ON TABLE {name} FROM PUBLIC, anon, authenticated, service_role"))
                        # PostgreSQL возвращает экранированное имя связанной sequence.
                        sequence = await conn.scalar(text("SELECT pg_get_serial_sequence(:name, 'id')"), {"name": name})
                        if sequence:
                            await conn.execute(text(f"REVOKE ALL ON SEQUENCE {sequence} FROM PUBLIC, anon, authenticated, service_role"))
                stage = "migration.commit"
            stage = "release"
    except Exception as exc:
        raise RuntimeError(startup_failure(stage, exc)) from None
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
