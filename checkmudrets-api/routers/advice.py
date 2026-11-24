"""Финансовые инсайты из подтверждённых чеков."""
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from database.models import User
from database.queries import get_analysis_receipts
from schemas.models import AdviceResponse
from services.advisor import generate_advice
from services.analytics import EMPTY_MESSAGE, calculate_insights
from services.auth import require_consents

router = APIRouter(prefix="/advice", tags=["advice"])


@router.get("", response_model=AdviceResponse)
async def get_advice(
    personalize: bool = False,
    user: User = Depends(require_consents),
    session: AsyncSession = Depends(get_session),
) -> AdviceResponse:
    today = date.today()
    receipts = await get_analysis_receipts(session, user.id, today)
    await session.commit()
    insights = calculate_insights(receipts, today)
    if personalize:
        insights = await generate_advice(user.id, insights)
    return AdviceResponse(
        insights=insights, empty_message=None if insights else EMPTY_MESSAGE, generated_at=datetime.now(timezone.utc),
    )
