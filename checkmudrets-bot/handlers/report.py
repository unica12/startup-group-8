"""Хендлер команды /report — еженедельный отчёт."""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.db import get_session
from database.queries import get_user_by_telegram_id, get_weekly_stats
from services.reporter import build_weekly_report
from utils.keyboards import back_keyboard

logger = logging.getLogger(__name__)
router = Router()


async def get_report_text(user_id: int) -> str:
    """Получить текст еженедельного отчёта. Используется в /report и callback."""
    async with get_session() as session:
        user = await get_user_by_telegram_id(session, user_id)
        if user is None:
            return "👋 Сначала запусти бота командой /start и отсканируй хотя бы один чек."
        stats = await get_weekly_stats(session, user.id)
    return build_weekly_report(stats)


@router.message(Command("report"))
async def cmd_report(message: Message) -> None:
    """Обработать команду /report."""
    if message.from_user is None:
        return

    text = await get_report_text(message.from_user.id)
    await message.answer(text, parse_mode="Markdown", reply_markup=back_keyboard())

    logger.info(f"Пользователь {message.from_user.id} запросил недельный отчёт")
