"""Хендлер команды /advice — персональные советы по экономии."""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.db import get_session
from database.queries import get_expenses_for_advice, get_user_by_telegram_id
from services.advisor import generate_advice
from utils.keyboards import back_keyboard

logger = logging.getLogger(__name__)
router = Router()


async def get_advice_text(user_id: int) -> str:
    """Получить текст советов для пользователя. Используется в /advice и callback."""
    async with get_session() as session:
        user = await get_user_by_telegram_id(session, user_id)
        if user is None:
            return "👋 Сначала запусти бота командой /start и отсканируй хотя бы один чек."
        expenses_data = await get_expenses_for_advice(session, user.id)

    total_receipts = expenses_data.get("total_receipts", 0)

    if total_receipts == 0:
        return (
            "📭 Пока нет данных для анализа.\n\n"
            "Отправь несколько фото чеков, и я дам тебе персональные советы по экономии!"
        )

    advice_text = await generate_advice(expenses_data)
    header = (
        f"💡 *Советы по экономии*\n"
        f"_(на основе {total_receipts} чек{'ов' if total_receipts % 10 != 1 else 'а'} за 30 дней)_\n\n"
    )
    return header + advice_text


@router.message(Command("advice"))
async def cmd_advice(message: Message) -> None:
    """Обработать команду /advice."""
    if message.from_user is None:
        return

    status_msg = await message.answer("💡 Анализирую твои расходы...")
    text = await get_advice_text(message.from_user.id)
    await status_msg.edit_text(text, parse_mode="Markdown", reply_markup=back_keyboard())

    logger.info(f"Пользователь {message.from_user.id} получил советы")
