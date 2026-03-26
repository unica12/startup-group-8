"""Хендлер команды /advice — персональные советы по экономии."""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.db import get_session
from database.queries import get_expenses_for_advice, get_user_by_telegram_id
from services.advisor import generate_advice

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("advice"))
async def cmd_advice(message: Message) -> None:
    """Обработать команду /advice."""
    if message.from_user is None:
        return

    # Сообщение-заглушка пока генерируем советы
    status_msg = await message.answer("💡 Анализирую твои расходы...")

    async with get_session() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if user is None:
            await status_msg.edit_text(
                "👋 Сначала запусти бота командой /start и отсканируй хотя бы один чек."
            )
            return

        expenses_data = await get_expenses_for_advice(session, user.id)

    total_receipts = expenses_data.get("total_receipts", 0)

    if total_receipts == 0:
        await status_msg.edit_text(
            "📭 Пока нет данных для анализа.\n\n"
            "Отправь несколько фото чеков, и я дам тебе персональные советы по экономии!"
        )
        return

    # Генерируем советы через Claude API
    advice_text = await generate_advice(expenses_data)

    header = f"💡 *Советы по экономии*\n_(на основе {total_receipts} чек{'ов' if total_receipts % 10 != 1 else 'а'} за 30 дней)_\n\n"
    await status_msg.edit_text(header + advice_text, parse_mode="Markdown")

    logger.info(
        f"Пользователь {message.from_user.id} получил советы, "
        f"чеков: {total_receipts}"
    )
