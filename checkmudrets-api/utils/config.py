"""Загрузка конфигурации из переменных окружения."""
from __future__ import annotations

import os
import re
from urllib.parse import urlsplit

from dotenv import load_dotenv
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

load_dotenv()

# API-ключ OpenAI
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# Модель OpenAI для Vision и текстовых запросов
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# URL базы данных (SQLite по умолчанию)
DATABASE_URL: str = os.getenv(
    "DATABASE_URL", "sqlite+aiosqlite:///checkmudrets-test.db"
)
SUPABASE_DB_CA_FILE = os.getenv("SUPABASE_DB_CA_FILE")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")


def get_database_url():
    try:
        return make_url(DATABASE_URL)
    except (ArgumentError, ValueError):
        raise RuntimeError("Проверь формат DATABASE_URL в настройках API.") from None


def get_supabase_url() -> str:
    configured = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    if configured:
        try:
            url = urlsplit(configured)
        except ValueError:
            raise ValueError("Проверь формат SUPABASE_URL в настройках API.") from None
        local_http = url.scheme == "http" and url.hostname in ("localhost", "127.0.0.1", "::1")
        if url.hostname and (url.scheme == "https" or local_http) and not (
            url.username or url.password or url.path or url.query or url.fragment
        ):
            return configured
        raise ValueError("SUPABASE_URL должен содержать базовый URL проекта.")

    database = get_database_url()
    host = database.host or ""
    if host.endswith(".pooler.supabase.com"):
        ref = (database.username or "").partition(".")[2]
        if re.fullmatch(r"[a-z0-9]{20}", ref):
            return f"https://{ref}.supabase.co"
    direct = re.fullmatch(r"db\.([a-z0-9]{20})\.supabase\.co", host)
    if direct:
        return f"https://{direct[1]}.supabase.co"
    raise ValueError("Укажи SUPABASE_URL в настройках API.")

# Настройки сервера
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))


def validate_config() -> None:
    get_supabase_url()
    """Проверить что обязательные переменные заполнены."""
    if not OPENAI_API_KEY:
        raise ValueError(
            "Отсутствует обязательная переменная OPENAI_API_KEY. "
            "Скопируй .env.example в .env и заполни значение."
        )
