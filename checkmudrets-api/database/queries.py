"""CRUD-операции для работы с базой данных."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Consent, Item, Receipt, ReceiptDraft, User
from schemas.receipt_input import ReceiptInput


# ─── Операции с пользователями ───────────────────────────────────────────────

def conflict_insert(session: AsyncSession, model):
    insert = pg_insert if session.get_bind().dialect.name == "postgresql" else sqlite_insert
    return insert(model)


async def get_or_create_user(
    session: AsyncSession,
    auth_user_id: UUID,
    name: Optional[str] = None,
) -> User:
    query = select(User).where(User.auth_user_id == auth_user_id)
    user = await session.scalar(query)
    if user is not None:
        return user

    await session.execute(
        conflict_insert(session, User).values(auth_user_id=auth_user_id, name=name)
        .on_conflict_do_nothing(index_elements=[User.auth_user_id])
    )
    result = await session.execute(query)
    return result.scalar_one()


async def get_user_consents(session: AsyncSession, user_id: int) -> set[tuple[str, str]]:
    result = await session.execute(
        select(Consent.consent_type, Consent.document_version).where(Consent.user_id == user_id)
    )
    return {(kind, version) for kind, version in result}


async def save_consents(
    session: AsyncSession, user_id: int, accepted: dict[str, str], ip_address: str | None, user_agent: str | None,
) -> None:
    await session.execute(
        conflict_insert(session, Consent).values([
            dict(user_id=user_id, consent_type=kind, document_version=version,
                 ip_address=ip_address, user_agent=user_agent)
            for kind, version in accepted.items()
        ]).on_conflict_do_nothing(index_elements=[Consent.user_id, Consent.consent_type, Consent.document_version])
    )


# ─── Операции с чеками ────────────────────────────────────────────────────────

async def get_confirmed_receipt(session: AsyncSession, user_id: int, draft_id: UUID) -> Receipt | None:
    return await session.scalar(select(Receipt).where(Receipt.user_id == user_id, Receipt.draft_id == draft_id))


async def owns_draft(session: AsyncSession, user_id: int, draft_id: UUID) -> bool:
    return await session.scalar(select(ReceiptDraft.id).where(
        ReceiptDraft.id == draft_id, ReceiptDraft.user_id == user_id,
    )) is not None


async def save_receipt(
    session: AsyncSession, user_id: int, draft_id: UUID, receipt: ReceiptInput, price_comparable: bool,
) -> Receipt:
    record_id = await session.scalar(
        conflict_insert(session, Receipt).values(
            user_id=user_id, draft_id=draft_id, store_name=receipt.store_name, date=receipt.date,
            total=receipt.total, discount=receipt.discount, price_comparable=price_comparable,
        ).on_conflict_do_nothing(index_elements=[Receipt.draft_id]).returning(Receipt.id)
    )
    if record_id is not None:
        session.add_all([Item(receipt_id=record_id, **line.model_dump()) for line in receipt.items])
        await session.flush()
    return await get_confirmed_receipt(session, user_id, draft_id)


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

def receipt_period(start: date, end: date):
    dated_purchase = and_(Receipt.draft_id.is_not(None), Receipt.date.is_not(None))
    scan_start, scan_end = (datetime.combine(day, datetime.min.time()) for day in (start, end))
    return or_(
        and_(dated_purchase, Receipt.date >= start, Receipt.date < end),
        and_(~dated_purchase, Receipt.created_at >= scan_start, Receipt.created_at < scan_end),
    )


async def get_monthly_stats(
    session: AsyncSession,
    user_id: int,
    year: int,
    month: int,
) -> dict:
    """Получить статистику за указанный месяц (год + номер месяца)."""
    month_start = date(year, month, 1)
    month_end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    period = receipt_period(month_start, month_end)

    # Общая сумма и количество чеков
    result = await session.execute(
        select(func.sum(Receipt.total), func.count(Receipt.id))
        .where(Receipt.user_id == user_id)
        .where(period)
    )
    row = result.one()
    total_sum = row[0] or 0.0
    receipts_count = row[1] or 0

    # Расходы по категориям
    result = await session.execute(
        select(Item.category, func.sum(Item.total))
        .join(Receipt, Item.receipt_id == Receipt.id)
        .where(Receipt.user_id == user_id)
        .where(period)
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
        .where(period)
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
    current_week = receipt_period(week_start, today + timedelta(days=1))
    previous_week = receipt_period(week_start - timedelta(days=7), week_start)

    # Подтверждённые чеки с датой учитываются по дате покупки.
    result = await session.execute(
        select(func.sum(Receipt.total), func.count(Receipt.id))
        .where(Receipt.user_id == user_id)
        .where(current_week)
    )
    row = result.one()
    total_sum = row[0] or 0.0
    receipts_count = row[1] or 0

    # Прошлая неделя (для сравнения)
    result = await session.execute(
        select(func.sum(Receipt.total), func.count(Receipt.id))
        .where(Receipt.user_id == user_id)
        .where(previous_week)
    )
    prev_total, prev_count = result.one()

    # Топ-3 категорий
    result = await session.execute(
        select(Item.category, func.sum(Item.total))
        .join(Receipt, Item.receipt_id == Receipt.id)
        .where(Receipt.user_id == user_id)
        .where(current_week)
        .group_by(Item.category)
        .order_by(func.sum(Item.total).desc())
        .limit(3)
    )
    top_categories = [(row[0], row[1]) for row in result.all()]

    change_pct = None
    if receipts_count and prev_count and prev_total and prev_total > 0:
        change_pct = ((total_sum - prev_total) / prev_total) * 100

    return {
        "total_sum": total_sum,
        "receipts_count": receipts_count,
        "top_categories": top_categories,
        "change_pct": change_pct,
        "week_start": week_start,
        "week_end": today,
    }


async def get_analysis_receipts(session: AsyncSession, user_id: int, today: date) -> list[Receipt]:
    receipts = await session.scalars(select(Receipt).where(
        Receipt.user_id == user_id,
        Receipt.date.between(today - timedelta(days=179), today),
    ).order_by(Receipt.date, Receipt.created_at, Receipt.id))
    return list(receipts)
