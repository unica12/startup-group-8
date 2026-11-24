"""Роутер недельного отчёта."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from database.models import User
from database.queries import get_weekly_stats
from schemas.models import ReportResponse
from services.auth import require_consents
from services.reporter import build_weekly_report

router = APIRouter(prefix="/report", tags=["report"])


@router.get("", response_model=ReportResponse)
async def get_report(
    user: User = Depends(require_consents),
    session: AsyncSession = Depends(get_session),
) -> ReportResponse:
    """Получить отчёт о расходах за последние 7 дней."""
    stats = await get_weekly_stats(session=session, user_id=user.id)

    return ReportResponse(**build_weekly_report(stats))
