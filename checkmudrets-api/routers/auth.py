"""Прикладной профиль и согласия после входа через Supabase."""
from datetime import datetime, timezone
from ipaddress import ip_address

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from database.accounts import export_consents, export_receipts, profile_totals, registration_date
from database.db import get_session
from database.models import User
from database.queries import save_consents
from schemas.models import AccountExport, ConsentRequest, ExportConsent, ExportReceipt, ProfileStats, ProfileUpdate, UserResponse
from services.account_deletion import erase_account
from services.auth import Identity, REQUIRED_CONSENTS, current_user, has_required_consents, verify_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


async def user_response(session: AsyncSession, user: User, identity: Identity, complete: bool | None = None) -> UserResponse:
    if complete is None:
        complete = await has_required_consents(session, user.id)
    return UserResponse(id=user.id, name=user.name, email=identity.email,
                        created_at=await registration_date(session, user), consents_complete=complete)


@router.get("/me", response_model=UserResponse)
async def me(
    user: User = Depends(current_user), identity: Identity = Depends(verify_access_token),
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    profile = await user_response(session, user, identity)
    await session.commit()
    return profile


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: ProfileUpdate, user: User = Depends(current_user), identity: Identity = Depends(verify_access_token),
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    # user_metadata даёт исходное имя только при первом создании прикладного профиля.
    user.name = body.name
    profile = await user_response(session, user, identity)
    await session.commit()
    return profile


@router.get("/me/stats", response_model=ProfileStats)
async def me_stats(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> ProfileStats:
    return ProfileStats(**await profile_totals(session, user.id))


@router.get("/me/export", response_model=AccountExport)
async def me_export(
    response: Response, user: User = Depends(current_user), identity: Identity = Depends(verify_access_token),
    session: AsyncSession = Depends(get_session),
) -> AccountExport:
    exported_at = datetime.now(timezone.utc)
    response.headers["Content-Disposition"] = f'attachment; filename="checkmudrets-export-{exported_at.date()}.json"'
    return AccountExport(
        profile=await user_response(session, user, identity),
        receipts=[ExportReceipt.model_validate(row) for row in await export_receipts(session, user.id)],
        consents=[ExportConsent.model_validate(row) for row in await export_consents(session, user.id)],
        exported_at=exported_at,
    )


@router.delete("/me", status_code=204, response_class=Response)
async def delete_me(
    identity: Identity = Depends(verify_access_token), session: AsyncSession = Depends(get_session),
) -> Response:
    await erase_account(session, identity)
    return Response(status_code=204)


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
    profile = await user_response(session, user, identity, complete=True)
    await session.commit()
    return profile
