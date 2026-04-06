"""Формирование недельного отчёта."""
from __future__ import annotations

import logging

from utils.formatting import format_change, format_date_short, format_money, get_category_emoji

logger = logging.getLogger(__name__)


def build_weekly_report(stats: dict) -> dict:
    """
    Сформировать структурированный недельный отчёт.

    stats — словарь из queries.get_weekly_stats().
    Возвращает dict для JSON-ответа API.
    """
    total_sum = stats.get("total_sum", 0.0)
    receipts_count = stats.get("receipts_count", 0)
    top_categories = stats.get("top_categories", [])
    change_pct = stats.get("change_pct", 0.0)
    week_start = stats.get("week_start")
    week_end = stats.get("week_end")

    # Формируем человекочитаемый текст отчёта
    start_str = format_date_short(week_start)
    end_str = format_date_short(week_end)

    lines = [
        f"📈 Отчёт за неделю ({start_str}–{end_str})",
        "",
        f"💰 Потрачено: {format_money(total_sum)}",
        f"🧾 Чеков: {receipts_count}",
        format_change(change_pct),
    ]

    if top_categories:
        lines.append("")
        lines.append("🏆 Топ категорий:")
        medals = ["1️⃣", "2️⃣", "3️⃣"]
        for i, (category, amount) in enumerate(top_categories[:3]):
            emoji = get_category_emoji(category)
            medal = medals[i] if i < len(medals) else "•"
            lines.append(f"{medal} {emoji} {category} — {format_money(amount)}")
    else:
        lines.append("")
        lines.append("📭 Данных за неделю нет.")

    if receipts_count == 0:
        lines.append("")
        lines.append("💡 Начни сканировать чеки, чтобы получать отчёты и советы по экономии!")

    # Структурированные данные для API
    top_categories_data = [
        {
            "category": cat,
            "amount": round(amount, 2),
            "emoji": get_category_emoji(cat),
        }
        for cat, amount in top_categories
    ]

    return {
        "period": {
            "start": str(week_start) if week_start else None,
            "end": str(week_end) if week_end else None,
            "label": f"{start_str}–{end_str}",
        },
        "total_spent": round(total_sum, 2),
        "receipts_count": receipts_count,
        "change_pct": round(change_pct, 1),
        "change_text": format_change(change_pct),
        "top_categories": top_categories_data,
        "summary_text": "\n".join(lines),
    }
