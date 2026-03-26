"""Хендлер команды /report — еженедельный отчёт."""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.db import get_session
from database.queries import get_user_by_telegram_id, get_weekly_stats
from services.reporter import build_weekly_report

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("report"))
async def cmd_report(message: Message) -> None:
    """Обработать команду /report."""
    if message.from_user is None:
        return

    async with get_session() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if user is None:
            await message.answer(
                "👋 Сначала запусти бота командой /start и отсканируй хотя бы один чек."
            )
            return

        stats = await get_weekly_stats(session, user.id)

    report_text = build_weekly_report(stats)
    await message.answer(report_text, parse_mode="Markdown")

    logger.info(
        f"Пользователь {message.from_user.id} запросил недельный отчёт, "
        f"чеков за неделю: {stats.get('receipts_count', 0)}"
    )
