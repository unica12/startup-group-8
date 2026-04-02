"""Обработчик нажатий на inline-кнопки."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from handlers.advice import get_advice_text
from handlers.history import get_history_text
from handlers.report import get_report_text
from handlers.stats import get_stats_text
from utils.keyboards import back_keyboard, main_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "cmd_stats")
async def cb_stats(callback: CallbackQuery) -> None:
    """Показать статистику по нажатию кнопки."""
    await callback.answer()
    text = await get_stats_text(callback.from_user.id)
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=back_keyboard())


@router.callback_query(F.data == "cmd_advice")
async def cb_advice(callback: CallbackQuery) -> None:
    """Показать советы по нажатию кнопки."""
    await callback.answer("💡 Анализирую расходы...")
    text = await get_advice_text(callback.from_user.id)
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=back_keyboard())


@router.callback_query(F.data == "cmd_history")
async def cb_history(callback: CallbackQuery) -> None:
    """Показать историю чеков по нажатию кнопки."""
    await callback.answer()
    text = await get_history_text(callback.from_user.id)
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=back_keyboard())


@router.callback_query(F.data == "cmd_report")
async def cb_report(callback: CallbackQuery) -> None:
    """Показать еженедельный отчёт по нажатию кнопки."""
    await callback.answer()
    text = await get_report_text(callback.from_user.id)
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=back_keyboard())


@router.callback_query(F.data == "cmd_menu")
async def cb_menu(callback: CallbackQuery) -> None:
    """Вернуться в главное меню."""
    await callback.answer()
    await callback.message.answer(
        "📸 Отправь фото чека или выбери действие:",
        reply_markup=main_menu_keyboard(),
    )
