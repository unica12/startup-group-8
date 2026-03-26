"""Хендлеры команд /start и /help."""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.db import get_session
from database.queries import get_or_create_user

logger = logging.getLogger(__name__)
router = Router()

WELCOME_TEXT = """👋 Привет! Я *ЧекМудрец* — твой ИИ-помощник по расходам.

📸 Отправь мне фото чека — я распознаю все покупки за секунды.

Что я умею:
• 📸 Фото чека → мгновенное распознавание
• 📊 /stats — статистика расходов
• 💡 /advice — советы, где сэкономить
• 📋 /history — последние чеки
• 📈 /report — недельный отчёт

Просто сфоткай чек и отправь мне!"""

HELP_TEXT = """📖 *Справка по ЧекМудрецу*

*Команды:*
• /start — начало работы
• /stats — статистика за текущий месяц
• /advice — персональные советы по экономии
• /history — последние 10 чеков
• /report — еженедельный отчёт
• /help — эта справка

*Как использовать:*
Просто сфотографируй кассовый чек и отправь мне как фото. Я распознаю все позиции, определю категории и сохраню в твою историю расходов.

*Советы для лучшего распознавания:*
• Фотографируй при хорошем освещении
• Держи чек ровно, не наклонно
• Убедись, что весь чек попал в кадр"""


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Обработать команду /start."""
    if message.from_user is None:
        return

    # Регистрируем пользователя в БД
    async with get_session() as session:
        await get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )

    logger.info(f"Пользователь {message.from_user.id} запустил бота")
    await message.answer(WELCOME_TEXT, parse_mode="Markdown")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Обработать команду /help."""
    await message.answer(HELP_TEXT, parse_mode="Markdown")
