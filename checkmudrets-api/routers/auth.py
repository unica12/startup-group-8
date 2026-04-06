"""Роутер аутентификации — регистрация по device_id."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from database.queries import get_or_create_user
from schemas.models import RegisterRequest, UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    """
    Регистрация или вход по device_id.

    Если пользователь с таким device_id уже существует — возвращаем его.
    Иначе создаём нового.
    """
    user = await get_or_create_user(
        session=session,
        device_id=body.device_id,
        name=body.name,
    )
    logger.info(f"Авторизация: device_id={body.device_id} user_id={user.id}")
    return UserResponse.model_validate(user)
