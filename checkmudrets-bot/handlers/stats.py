"""Хендлер команды /stats — статистика расходов за месяц."""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.db import get_session
from database.queries import get_monthly_stats, get_user_by_telegram_id
from utils.formatting import format_money, get_category_emoji
from utils.keyboards import back_keyboard

logger = logging.getLogger(__name__)
router = Router()


def _build_stats_message(stats: dict) -> str:
    """Сформировать текст статистики за месяц."""
    month_name = stats.get("month_name", "")
    year = stats.get("year", "")
    total_sum = stats.get("total_sum", 0.0)
    receipts_count = stats.get("receipts_count", 0)
    by_category = stats.get("by_category", {})
    avg_check = stats.get("avg_check", 0.0)
    max_category = stats.get("max_category", "—")
    max_amount = stats.get("max_amount", 0.0)

    if receipts_count == 0:
        return (
            f"📊 *Статистика за {month_name} {year}*\n\n"
            "📭 Пока нет данных. Отправь фото чека, чтобы начать отслеживать расходы!"
        )

    lines = [
        f"📊 *Статистика за {month_name} {year}*",
        "",
        f"💰 Всего потрачено: *{format_money(total_sum)}*",
        f"🧾 Чеков отсканировано: {receipts_count}",
        "",
        "📂 *По категориям:*",
    ]

    sorted_categories = sorted(by_category.items(), key=lambda x: x[1], reverse=True)

    for category, amount in sorted_categories:
        emoji = get_category_emoji(category)
        pct = round((amount / total_sum) * 100) if total_sum > 0 else 0
        lines.append(f"• {emoji} {category} — {format_money(amount)} ({pct}%)")

    lines.append("")
    lines.append(f"📈 Средний чек: {format_money(avg_check)}")

    if max_amount > 0:
        lines.append(
            f"🔝 Самая крупная покупка: {format_money(max_amount)} ({max_category})"
        )

    return "\n".join(lines)


async def get_stats_text(user_id: int) -> str:
    """Получить текст статистики для пользователя. Используется в /stats и callback."""
    async with get_session() as session:
        user = await get_user_by_telegram_id(session, user_id)
        if user is None:
            return "👋 Сначала запусти бота командой /start и отсканируй хотя бы один чек."
        stats = await get_monthly_stats(session, user.id)
    return _build_stats_message(stats)


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Обработать команду /stats."""
    if message.from_user is None:
        return

    text = await get_stats_text(message.from_user.id)
    await message.answer(text, parse_mode="Markdown", reply_markup=back_keyboard())
    logger.info(f"Пользователь {message.from_user.id} запросил статистику")
