"""Роутер советов по экономии."""
from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from database.queries import get_expenses_for_advice, get_or_create_user
from schemas.models import AdviceResponse
from services.advisor import generate_advice

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advice", tags=["advice"])


@router.get("", response_model=AdviceResponse)
async def get_advice(
    device_id: str,
    session: AsyncSession = Depends(get_session),
) -> AdviceResponse:
    """
    Получить персональные советы по экономии на основе расходов за 30 дней.

    Query-параметры: device_id.
    """
    user = await get_or_create_user(session=session, device_id=device_id)

    # Берём расходы за последние 30 дней
    expenses_data = await get_expenses_for_advice(
        session=session, user_id=user.id, days=30
    )

    advice_text = await generate_advice(expenses_data)

    logger.info(f"Советы выданы: device_id={device_id} user_id={user.id}")

    return AdviceResponse(
        advice=advice_text,
        generated_at=datetime.now(),
    )
