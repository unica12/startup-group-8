"""Загрузка конфигурации из переменных окружения."""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# Токен Telegram-бота
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# API-ключ Openai
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# URL базы данных (SQLite по умолчанию)
DATABASE_URL: str = os.getenv(
    "DATABASE_URL", "sqlite+aiosqlite:///checkmudrets.db"
)

# Модель Openai для Vision и текстовых запросов
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
PHOTO_COOLDOWN: int = int(os.getenv("PHOTO_COOLDOWN", "5"))


def validate_config() -> None:
    """Проверить что обязательные переменные заполнены."""
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if missing:
        raise ValueError(
            f"Отсутствуют обязательные переменные окружения: {', '.join(missing)}. "
            f"Скопируй .env.example в .env и заполни значения."
        )
