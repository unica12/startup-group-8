"""Прикладной профиль и согласия после входа через Supabase."""
from ipaddress import ip_address

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from database.models import User
from database.queries import save_consents
from schemas.models import ConsentRequest, UserResponse
from services.auth import Identity, REQUIRED_CONSENTS, current_user, has_required_consents, verify_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserResponse)
async def me(
    user: User = Depends(current_user), identity: Identity = Depends(verify_access_token),
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    complete = await has_required_consents(session, user.id)
    await session.commit()
    return UserResponse(id=user.id, name=user.name, email=identity.email,
                        created_at=user.created_at, consents_complete=complete)


@router.post("/consents", response_model=UserResponse)
async def accept_consents(
    body: ConsentRequest, request: Request, user: User = Depends(current_user),
    identity: Identity = Depends(verify_access_token), session: AsyncSession = Depends(get_session),
) -> UserResponse:
    if body.consents != REQUIRED_CONSENTS:
        raise HTTPException(422, "Нужно принять все обязательные документы актуальных версий.")

    try:
        client_ip = str(ip_address(request.client.host)) if request.client else None
    except ValueError:
        client_ip = None
    agent = request.headers.get("user-agent", "")[:512] or None
    await save_consents(session, user.id, body.consents, client_ip, agent)
    await session.commit()
    return UserResponse(id=user.id, name=user.name, email=identity.email,
                        created_at=user.created_at, consents_complete=True)
