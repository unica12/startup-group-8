"""Формирование еженедельного текстового отчёта."""
from __future__ import annotations

import logging

from utils.formatting import format_change, format_date_short, format_money, get_category_emoji

logger = logging.getLogger(__name__)


def build_weekly_report(stats: dict) -> str:
    """
    Сформировать текст еженедельного отчёта.

    stats — словарь из queries.get_weekly_stats().
    """
    total_sum = stats.get("total_sum", 0.0)
    receipts_count = stats.get("receipts_count", 0)
    top_categories = stats.get("top_categories", [])
    change_pct = stats.get("change_pct", 0.0)
    week_start = stats.get("week_start")
    week_end = stats.get("week_end")

    # Заголовок с датами недели
    start_str = format_date_short(week_start)
    end_str = format_date_short(week_end)

    lines = [
        f"📈 *Отчёт за неделю ({start_str}–{end_str})*",
        "",
        f"💰 Потрачено: *{format_money(total_sum)}*",
        f"🧾 Чеков: {receipts_count}",
        format_change(change_pct),
    ]

    # Топ категорий
    if top_categories:
        lines.append("")
        lines.append("🏆 *Топ категорий:*")
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
        lines.append(
            "💡 Начни сканировать чеки, чтобы получать отчёты и советы по экономии!"
        )

    return "\n".join(lines)
