"""Роутер статистики расходов за месяц и за всё время."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from database.models import User
from database.queries import get_spending_stats
from schemas.models import CategoryStat, LargestPurchase, StatsResponse
from services.auth import require_consents
from utils.formatting import get_category_emoji
from utils.receipt_dates import reporting_day

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
async def get_stats(
    month: str = "",
    user: User = Depends(require_consents),
    session: AsyncSession = Depends(get_session),
) -> StatsResponse:
    """Получить статистику за YYYY-MM, текущий месяц или всё время (all)."""
    bounds = None
    if month != "all":
        try:
            first = date.fromisoformat(f"{month}-01") if month else reporting_day().replace(day=1)
            if first == date.min:
                raise ValueError
            end = date(first.year + 1, 1, 1) if first.month == 12 else first.replace(month=first.month + 1)
            bounds = first, end
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Неверный период. Используй месяц в формате YYYY-MM или all.",
            ) from None

    stats = await get_spending_stats(session, user.id, bounds)

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

    return StatsResponse(
        month=bounds[0].isoformat()[:7] if bounds else None,
        total_spent=round(total_sum, 2),
        receipts_count=stats["receipts_count"],
        average_receipt=round(stats["avg_check"], 2),
        by_category=by_category,
        largest_purchase=largest,
    )
