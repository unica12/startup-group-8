"""Загрузка конфигурации из переменных окружения."""
from __future__ import annotations

import os
import re
from urllib.parse import urlsplit

from dotenv import load_dotenv
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

load_dotenv()

ON_RENDER = os.getenv("RENDER") == "true"

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
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY", "").strip()
LOCAL_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173"
CORS_ORIGINS = [origin.strip().rstrip("/") for origin in os.getenv("CORS_ORIGINS", LOCAL_ORIGINS).split(",") if origin.strip()]


def get_database_url():
    try:
        url = make_url(DATABASE_URL)
    except (ArgumentError, ValueError):
        raise RuntimeError("Проверь формат DATABASE_URL в настройках API.") from None
    if ON_RENDER and url.get_backend_name() not in ("postgresql", "postgres"):
        raise RuntimeError("На Render укажи PostgreSQL Session pooler в DATABASE_URL.")
    return url


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
    """Проверить что обязательные переменные заполнены."""
    get_supabase_url()
    if ON_RENDER and "*" in CORS_ORIGINS:
        raise ValueError("На Render перечисли точные источники в CORS_ORIGINS.")
    if SUPABASE_SECRET_KEY and not SUPABASE_SECRET_KEY.startswith("sb_secret_"):
        raise ValueError("SUPABASE_SECRET_KEY должен быть серверным ключом Supabase (sb_secret_…).")
    if not OPENAI_API_KEY:
        raise ValueError(
            "Отсутствует обязательная переменная OPENAI_API_KEY. "
            "Скопируй .env.example в .env и заполни значение."
        )
