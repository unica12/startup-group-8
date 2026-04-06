"""Роутер недельного отчёта."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from database.queries import get_or_create_user, get_weekly_stats
from schemas.models import ReportResponse
from services.reporter import build_weekly_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/report", tags=["report"])


@router.get("", response_model=ReportResponse)
async def get_report(
    device_id: str,
    session: AsyncSession = Depends(get_session),
) -> ReportResponse:
    """
    Получить недельный отчёт о расходах (последние 7 дней).

    Query-параметры: device_id.
    """
    user = await get_or_create_user(session=session, device_id=device_id)
    stats = await get_weekly_stats(session=session, user_id=user.id)

    report = build_weekly_report(stats)

    logger.info(
        f"Отчёт выдан: device_id={device_id} user_id={user.id} "
        f"потрачено={report['total_spent']}"
    )

    return ReportResponse(**report)
