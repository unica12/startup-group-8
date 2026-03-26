"""CRUD-операции для работы с базой данных."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Item, Receipt, User

logger = logging.getLogger(__name__)


# ─── Операции с пользователями ───────────────────────────────────────────────

async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
) -> User:
    """Получить пользователя или создать нового."""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
        )
        session.add(user)
        await session.flush()
        logger.info(f"Создан новый пользователь: telegram_id={telegram_id}")

    return user


async def get_user_by_telegram_id(
    session: AsyncSession, telegram_id: int
) -> Optional[User]:
    """Получить пользователя по Telegram ID."""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


# ─── Операции с чеками ────────────────────────────────────────────────────────

async def save_receipt(
    session: AsyncSession,
    user_id: int,
    store_name: str,
    receipt_date: Optional[date],
    total: float,
    items_data: list[dict],
    raw_text: str = "",
) -> Receipt:
    """Сохранить чек с позициями в БД."""
    receipt = Receipt(
        user_id=user_id,
        store_name=store_name,
        date=receipt_date,
        total=total,
        raw_text=raw_text,
    )
    session.add(receipt)
    await session.flush()

    # Сохраняем позиции
    for item_data in items_data:
        item = Item(
            receipt_id=receipt.id,
            name=item_data.get("name", ""),
            quantity=item_data.get("quantity", 1.0),
            price=item_data.get("price", 0.0),
            total=item_data.get("total", 0.0),
            category=item_data.get("category", "Другое"),
        )
        session.add(item)

    # Увеличиваем счётчик чеков у пользователя
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user:
        user.receipts_count = (user.receipts_count or 0) + 1

    logger.info(
        f"Сохранён чек id={receipt.id} user_id={user_id} "
        f"сумма={total} позиций={len(items_data)}"
    )
    return receipt


async def get_last_receipts(
    session: AsyncSession, user_id: int, limit: int = 10
) -> list[Receipt]:
    """Получить последние N чеков пользователя."""
    result = await session.execute(
        select(Receipt)
        .where(Receipt.user_id == user_id)
        .order_by(Receipt.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


# ─── Статистика ───────────────────────────────────────────────────────────────

async def get_monthly_stats(
    session: AsyncSession, user_id: int
) -> dict:
    """Получить статистику за текущий месяц."""
    now = datetime.now()
    month_start = date(now.year, now.month, 1)

    # Общая сумма и количество чеков
    result = await session.execute(
        select(func.sum(Receipt.total), func.count(Receipt.id))
        .where(Receipt.user_id == user_id)
        .where(Receipt.date >= month_start)
    )
    row = result.one()
    total_sum = row[0] or 0.0
    receipts_count = row[1] or 0

    # Расходы по категориям
    result = await session.execute(
        select(Item.category, func.sum(Item.total))
        .join(Receipt, Item.receipt_id == Receipt.id)
        .where(Receipt.user_id == user_id)
        .where(Receipt.date >= month_start)
        .group_by(Item.category)
        .order_by(func.sum(Item.total).desc())
    )
    by_category = {row[0]: row[1] for row in result.all()}

    # Средний чек
    avg_check = total_sum / receipts_count if receipts_count > 0 else 0.0

    # Самая крупная покупка (по позиции)
    result = await session.execute(
        select(Item.category, func.max(Item.total))
        .join(Receipt, Item.receipt_id == Receipt.id)
        .where(Receipt.user_id == user_id)
        .where(Receipt.date >= month_start)
    )
    max_row = result.one_or_none()
    max_category = max_row[0] if max_row else "—"
    max_amount = max_row[1] if max_row else 0.0

    return {
        "total_sum": total_sum,
        "receipts_count": receipts_count,
        "by_category": by_category,
        "avg_check": avg_check,
        "max_category": max_category,
        "max_amount": max_amount,
        "month_name": _month_name_ru(now.month),
        "year": now.year,
    }


async def get_weekly_stats(
    session: AsyncSession, user_id: int
) -> dict:
    """Получить статистику за последние 7 дней."""
    today = date.today()
    week_start = today - timedelta(days=6)
    prev_week_start = week_start - timedelta(days=7)

    # Текущая неделя
    result = await session.execute(
        select(func.sum(Receipt.total), func.count(Receipt.id))
        .where(Receipt.user_id == user_id)
        .where(Receipt.date >= week_start)
    )
    row = result.one()
    total_sum = row[0] or 0.0
    receipts_count = row[1] or 0

    # Прошлая неделя (для сравнения)
    result = await session.execute(
        select(func.sum(Receipt.total))
        .where(Receipt.user_id == user_id)
        .where(Receipt.date >= prev_week_start)
        .where(Receipt.date < week_start)
    )
    prev_total = result.scalar() or 0.0

    # По категориям
    result = await session.execute(
        select(Item.category, func.sum(Item.total))
        .join(Receipt, Item.receipt_id == Receipt.id)
        .where(Receipt.user_id == user_id)
        .where(Receipt.date >= week_start)
        .group_by(Item.category)
        .order_by(func.sum(Item.total).desc())
        .limit(3)
    )
    top_categories = [(row[0], row[1]) for row in result.all()]

    # Изменение по сравнению с прошлой неделей
    change_pct = 0.0
    if prev_total > 0:
        change_pct = ((total_sum - prev_total) / prev_total) * 100

    return {
        "total_sum": total_sum,
        "receipts_count": receipts_count,
        "top_categories": top_categories,
        "change_pct": change_pct,
        "week_start": week_start,
        "week_end": today,
    }


async def get_expenses_for_advice(
    session: AsyncSession, user_id: int, days: int = 30
) -> dict:
    """Получить расходы по категориям за N дней для советника."""
    since = date.today() - timedelta(days=days)

    result = await session.execute(
        select(Item.category, func.sum(Item.total), func.count(Item.id))
        .join(Receipt, Item.receipt_id == Receipt.id)
        .where(Receipt.user_id == user_id)
        .where(Receipt.date >= since)
        .group_by(Item.category)
        .order_by(func.sum(Item.total).desc())
    )
    rows = result.all()

    total_receipts_result = await session.execute(
        select(func.count(Receipt.id))
        .where(Receipt.user_id == user_id)
        .where(Receipt.date >= since)
    )
    total_receipts = total_receipts_result.scalar() or 0

    by_category = {
        row[0]: {"total": row[1], "count": row[2]} for row in rows
    }

    return {
        "by_category": by_category,
        "total_receipts": total_receipts,
        "days": days,
    }


# ─── Вспомогательные функции ─────────────────────────────────────────────────

def _month_name_ru(month: int) -> str:
    """Название месяца по-русски в родительном падеже."""
    names = [
        "", "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря",
    ]
    return names[month] if 1 <= month <= 12 else ""


MONTH_NAMES_RU = [
    "", "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
]
