"""Роутер статистики — расходы за месяц."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from database.models import User
from database.queries import get_monthly_stats
from schemas.models import CategoryStat, LargestPurchase, StatsResponse
from services.auth import require_consents
from utils.formatting import get_category_emoji

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
async def get_stats(
    month: str = "",
    user: User = Depends(require_consents),
    session: AsyncSession = Depends(get_session),
) -> StatsResponse:
    """
    Получить статистику расходов за месяц.

    Query-параметры:
    - month: месяц в формате YYYY-MM (по умолчанию — текущий)
    """
    # Парсим месяц, если передан
    if month:
        try:
            parsed = datetime.strptime(month, "%Y-%m")
            year, month_num = parsed.year, parsed.month
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Неверный формат месяца. Используй YYYY-MM, например 2026-04",
            )
    else:
        now = datetime.now()
        year, month_num = now.year, now.month

    stats = await get_monthly_stats(
        session=session, user_id=user.id, year=year, month=month_num
    )

    total_sum = stats["total_sum"]

    # Формируем список категорий с процентами
    by_category = []
    for cat_name, cat_amount in stats["by_category"]:
        percent = round((cat_amount / total_sum * 100)) if total_sum > 0 else 0
        by_category.append(
            CategoryStat(
                category=cat_name,
                amount=round(cat_amount, 2),
                percent=percent,
                emoji=get_category_emoji(cat_name),
            )
        )

    # Самая дорогая покупка
    largest = None
    if stats.get("largest_item_name"):
        largest = LargestPurchase(
            name=stats["largest_item_name"],
            amount=round(stats["largest_item_amount"], 2),
            category=stats["largest_item_category"] or "Другое",
        )

    month_label = f"{year:04d}-{month_num:02d}"

    return StatsResponse(
        month=month_label,
        total_spent=round(total_sum, 2),
        receipts_count=stats["receipts_count"],
        average_receipt=round(stats["avg_check"], 2),
        by_category=by_category,
        largest_purchase=largest,
    )
