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
    device_id: str,
    name: Optional[str] = None,
) -> User:
    """Получить пользователя по device_id или создать нового."""
    result = await session.execute(
        select(User).where(User.device_id == device_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(device_id=device_id, name=name)
        session.add(user)
        await session.flush()
        logger.info(f"Создан новый пользователь: device_id={device_id}")

    return user


async def get_user_by_device_id(
    session: AsyncSession, device_id: str
) -> Optional[User]:
    """Получить пользователя по device_id."""
    result = await session.execute(
        select(User).where(User.device_id == device_id)
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
    session: AsyncSession,
    user_id: int,
    year: int,
    month: int,
) -> dict:
    """Получить статистику за указанный месяц (год + номер месяца)."""
    month_start = date(year, month, 1)
    # Первый день следующего месяца
    if month == 12:
        month_end = date(year + 1, 1, 1)
    else:
        month_end = date(year, month + 1, 1)

    # Общая сумма и количество чеков
    result = await session.execute(
        select(func.sum(Receipt.total), func.count(Receipt.id))
        .where(Receipt.user_id == user_id)
        .where(Receipt.date >= month_start)
        .where(Receipt.date < month_end)
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
        .where(Receipt.date < month_end)
        .group_by(Item.category)
        .order_by(func.sum(Item.total).desc())
    )
    by_category = [(row[0], row[1]) for row in result.all()]

    # Средний чек
    avg_check = total_sum / receipts_count if receipts_count > 0 else 0.0

    # Самая дорогая позиция
    result = await session.execute(
        select(Item.name, Item.total, Item.category)
        .join(Receipt, Item.receipt_id == Receipt.id)
        .where(Receipt.user_id == user_id)
        .where(Receipt.date >= month_start)
        .where(Receipt.date < month_end)
        .order_by(Item.total.desc())
        .limit(1)
    )
    largest_row = result.one_or_none()

    return {
        "total_sum": total_sum,
        "receipts_count": receipts_count,
        "by_category": by_category,
        "avg_check": avg_check,
        "largest_item_name": largest_row[0] if largest_row else None,
        "largest_item_amount": largest_row[1] if largest_row else 0.0,
        "largest_item_category": largest_row[2] if largest_row else None,
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

    # Топ-3 категорий
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
