"""Хендлер приёма и обработки фото чеков."""
from __future__ import annotations

import logging
import time
from typing import Optional

from aiogram import Bot, F, Router
from aiogram.types import Message

from database.db import get_session
from database.queries import get_monthly_stats, get_or_create_user, save_receipt
from services.categorizer import categorize_items
from services.ocr import recognize_receipt
from utils.formatting import format_date_ru, format_money, get_category_emoji

logger = logging.getLogger(__name__)
router = Router()

# Кулдаун между фото: user_id -> timestamp последнего запроса
_last_photo_time: dict[int, float] = {}
COOLDOWN_SECONDS = 5


def _check_cooldown(user_id: int) -> Optional[int]:
    """Проверить кулдаун. Вернуть оставшиеся секунды или None если ОК."""
    last = _last_photo_time.get(user_id, 0)
    elapsed = time.time() - last
    if elapsed < COOLDOWN_SECONDS:
        return int(COOLDOWN_SECONDS - elapsed) + 1
    return None


def _format_receipt_response(data: dict, monthly_stats: dict) -> str:
    """Сформировать красивый ответ с распознанным чеком."""
    lines = ["✅ *Чек распознан!*", ""]

    # Магазин и дата
    store = data.get("store_name") or "Неизвестно"
    lines.append(f"🏪 Магазин: {store}")

    receipt_date = data.get("date")
    lines.append(f"📅 Дата: {format_date_ru(receipt_date)}")
    lines.append(f"💰 Итого: *{format_money(data.get('total', 0))}*")

    # Позиции
    items = data.get("items", [])
    if items:
        lines.append("")
        lines.append("📝 *Позиции:*")
        for item in items:
            emoji = get_category_emoji(item.get("category", "Другое"))
            name = item.get("name", "—")
            total = item.get("total", 0)
            category = item.get("category", "Другое")
            lines.append(f"• {emoji} {name} — {format_money(total)} [{category}]")

    # Подсказка по самой дорогой позиции (>300 руб)
    if items:
        expensive = max(items, key=lambda x: x.get("total", 0))
        if expensive.get("total", 0) > 300:
            lines.append("")
            lines.append(
                f"💡 *Совет:* {expensive['name']} стоит "
                f"{format_money(expensive['total'])}. "
                "Поищи аналог дешевле или купи оптом."
            )

    # Итог по месяцу
    monthly_total = monthly_stats.get("total_sum", 0.0)
    monthly_count = monthly_stats.get("receipts_count", 0)
    if monthly_total > 0:
        lines.append("")
        lines.append(
            f"📊 Всего в этом месяце: *{format_money(monthly_total)}* "
            f"({monthly_count} чек{'ов' if monthly_count % 10 != 1 else ''})"
        )

    return "\n".join(lines)


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot) -> None:
    """Обработать фото чека от пользователя."""
    if message.from_user is None:
        return

    user_id = message.from_user.id

    # Проверяем кулдаун
    remaining = _check_cooldown(user_id)
    if remaining is not None:
        await message.answer(
            f"⏳ Подожди {remaining} сек. перед отправкой следующего чека."
        )
        return

    # Обновляем время последнего запроса
    _last_photo_time[user_id] = time.time()

    # Сообщение-заглушка
    status_msg = await message.answer("🔍 Распознаю чек... подожди 3–5 секунд")

    try:
        # Скачиваем фото в максимальном разрешении
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        file_bytes = await bot.download_file(file.file_path)
        image_bytes = file_bytes.read()

        # Распознаём чек через Claude Vision
        receipt_data = await recognize_receipt(image_bytes)

        if not receipt_data.get("success"):
            reason = receipt_data.get("reason", "")
            if "не чек" in reason.lower() or "not a receipt" in reason.lower():
                await status_msg.edit_text(
                    "🤔 Это не похоже на чек. Отправь фото кассового чека."
                )
            else:
                await status_msg.edit_text(
                    "😕 Не удалось распознать чек. "
                    "Попробуй сделать фото ровнее и при хорошем освещении."
                )
            return

        items = receipt_data.get("items", [])

        # Если OCR не вернул категории — запускаем fallback-категоризацию
        needs_categorization = any(
            not item.get("category") or item.get("category") == "Другое"
            for item in items
        )
        if needs_categorization and items:
            items = await categorize_items(items)
            receipt_data["items"] = items

        # Сохраняем в БД
        async with get_session() as session:
            user = await get_or_create_user(
                session=session,
                telegram_id=user_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
            )

            await save_receipt(
                session=session,
                user_id=user.id,
                store_name=receipt_data.get("store_name", ""),
                receipt_date=receipt_data.get("date"),
                total=receipt_data.get("total", 0.0),
                items_data=items,
                raw_text=str(receipt_data),
            )

            monthly_stats = await get_monthly_stats(session, user.id)

        # Формируем и отправляем ответ
        response_text = _format_receipt_response(receipt_data, monthly_stats)
        await status_msg.edit_text(response_text, parse_mode="Markdown")

        logger.info(
            f"Чек обработан: user_id={user_id} "
            f"магазин={receipt_data.get('store_name')} "
            f"сумма={receipt_data.get('total')} "
            f"позиций={len(items)}"
        )

    except Exception as e:
        logger.error(f"Ошибка обработки фото user_id={user_id}: {e}")
        await status_msg.edit_text(
            "😕 Произошла ошибка при обработке чека. Попробуй ещё раз."
        )
