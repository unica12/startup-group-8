"""Хендлер команды /history — последние 10 чеков."""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.db import get_session
from database.queries import get_last_receipts, get_monthly_stats, get_user_by_telegram_id
from utils.formatting import format_date_short, format_money
from utils.keyboards import back_keyboard

logger = logging.getLogger(__name__)
router = Router()


async def get_history_text(user_id: int) -> str:
    """Получить текст истории чеков. Используется в /history и callback."""
    async with get_session() as session:
        user = await get_user_by_telegram_id(session, user_id)
        if user is None:
            return "👋 Сначала запусти бота командой /start и отсканируй хотя бы один чек."
        receipts = await get_last_receipts(session, user.id, limit=10)
        monthly_stats = await get_monthly_stats(session, user.id)

    if not receipts:
        return "📭 История пуста. Отправь фото чека, чтобы начать отслеживать расходы!"

    lines = ["📋 *Последние чеки:*", ""]

    for i, receipt in enumerate(receipts, start=1):
        store = receipt.store_name or "Неизвестный магазин"
        date_str = format_date_short(receipt.date)
        total_str = format_money(receipt.total)
        lines.append(f"{i}. 🏪 {store} — {total_str} ({date_str})")

    monthly_total = monthly_stats.get("total_sum", 0.0)
    monthly_count = monthly_stats.get("receipts_count", 0)
    if monthly_total > 0:
        lines.append("")
        lines.append(
            f"📊 Всего за месяц: {monthly_count} чек{'ов' if monthly_count % 10 != 1 else ''} "
            f"на *{format_money(monthly_total)}*"
        )

    return "\n".join(lines)


@router.message(Command("history"))
async def cmd_history(message: Message) -> None:
    """Обработать команду /history."""
    if message.from_user is None:
        return

    text = await get_history_text(message.from_user.id)
    await message.answer(text, parse_mode="Markdown", reply_markup=back_keyboard())
    logger.info(f"Пользователь {message.from_user.id} запросил историю")
