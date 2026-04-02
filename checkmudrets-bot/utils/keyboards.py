"""Клавиатуры для бота ЧекМудрец."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню — показывается после /start и после каждого действия."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="cmd_stats"),
            InlineKeyboardButton(text="💡 Советы", callback_data="cmd_advice"),
        ],
        [
            InlineKeyboardButton(text="📋 История", callback_data="cmd_history"),
            InlineKeyboardButton(text="📈 Отчёт", callback_data="cmd_report"),
        ],
    ])


def back_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата к главному меню."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Меню", callback_data="cmd_menu")],
    ])
