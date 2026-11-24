"""Роутер советов по экономии."""
from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from database.models import User
from database.queries import get_expenses_for_advice
from schemas.models import AdviceResponse
from services.advisor import generate_advice
from services.auth import require_consents

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advice", tags=["advice"])


@router.get("", response_model=AdviceResponse)
async def get_advice(
    user: User = Depends(require_consents),
    session: AsyncSession = Depends(get_session),
) -> AdviceResponse:
    """Получить персональные советы по расходам за последние 30 дней."""

    # Берём расходы за последние 30 дней
    expenses_data = await get_expenses_for_advice(
        session=session, user_id=user.id, days=30
    )
    await session.commit()

    advice_text = await generate_advice(expenses_data)

    logger.info("Советы выданы | user_id=%s", user.id)

    return AdviceResponse(
        advice=advice_text,
        generated_at=datetime.now(),
    )
