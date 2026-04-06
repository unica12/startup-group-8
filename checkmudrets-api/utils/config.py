"""Загрузка конфигурации из переменных окружения."""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# API-ключ OpenAI
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# Модель OpenAI для Vision и текстовых запросов
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# URL базы данных (SQLite по умолчанию)
DATABASE_URL: str = os.getenv(
    "DATABASE_URL", "sqlite+aiosqlite:///checkmudrets.db"
)

# Настройки сервера
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))


def validate_config() -> None:
    """Проверить что обязательные переменные заполнены."""
    if not OPENAI_API_KEY:
        raise ValueError(
            "Отсутствует обязательная переменная OPENAI_API_KEY. "
            "Скопируй .env.example в .env и заполни значение."
        )
