"""Форматирование сообщений, эмодзи и вспомогательные функции."""
from __future__ import annotations

# Маппинг категорий на эмодзи
CATEGORY_EMOJI: dict[str, str] = {
    "Продукты": "🍞",
    "Молочные": "🥛",
    "Мясо": "🥩",
    "Овощи/Фрукты": "🥬",
    "Хлеб": "🍞",
    "Напитки": "🧃",
    "Алкоголь": "🍷",
    "Кофе": "☕",
    "Сладости": "🍬",
    "Снеки": "🍿",
    "Готовая еда": "🥡",
    "Доставка еды": "🛵",
    "Кафе/Рестораны": "🍕",
    "Бытовая химия": "🧹",
    "Гигиена": "🧴",
    "Косметика": "💄",
    "Одежда": "👕",
    "Обувь": "👟",
    "Электроника": "📱",
    "Техника": "🔧",
    "Канцелярия": "📎",
    "Книги": "📚",
    "Игрушки": "🧸",
    "Зоотовары": "🐾",
    "Лекарства": "💊",
    "Спорт": "🏋️",
    "Транспорт": "🚗",
    "Топливо": "⛽",
    "Подписки": "📺",
    "Развлечения": "🎮",
    "Связь/Интернет": "📡",
    "ЖКХ": "🏠",
    "Ремонт": "🔨",
    "Мебель": "🛋️",
    "Другое": "📦",
}


def format_money(amount: float) -> str:
    """Форматировать сумму: 1847.5 -> '1 847 руб.'"""
    rounded = round(amount)
    formatted = f"{rounded:,}".replace(",", " ")
    return f"{formatted} руб."


def format_money_short(amount: float) -> str:
    """Форматировать без 'руб.' для вставки в текст."""
    rounded = round(amount)
    return f"{rounded:,}".replace(",", " ")


def get_category_emoji(category: str) -> str:
    """Получить эмодзи для категории."""
    return CATEGORY_EMOJI.get(category, "📦")


def format_date_ru(d) -> str:
    """Форматировать дату в русский формат: 2026-03-25 -> '25.03.2026'"""
    if d is None:
        return "—"
    if hasattr(d, "strftime"):
        return d.strftime("%d.%m.%Y")
    return str(d)


def format_date_short(d) -> str:
    """Короткий формат даты: 25.03"""
    if d is None:
        return "—"
    if hasattr(d, "strftime"):
        return d.strftime("%d.%m")
    return str(d)


def progress_bar(value: float, total: float, width: int = 10) -> str:
    """Текстовый прогресс-бар из блоков.

    Пример: ████████░░ 80%
    """
    if total <= 0:
        return "░" * width
    ratio = min(value / total, 1.0)
    filled = round(ratio * width)
    empty = width - filled
    pct = round(ratio * 100)
    return f"{'█' * filled}{'░' * empty} {pct}%"


def format_change(pct: float) -> str:
    """Форматировать изменение в процентах со знаком."""
    if pct > 0:
        return f"📈 На {abs(pct):.0f}% больше, чем на прошлой неделе"
    elif pct < 0:
        return f"📉 На {abs(pct):.0f}% меньше, чем на прошлой неделе"
    else:
        return "↔️ Столько же, как на прошлой неделе"
