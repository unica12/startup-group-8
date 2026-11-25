"""Два идемпотентных шага удаления без общей транзакции с Supabase Auth."""
import asyncio
import logging
from time import time
from uuid import UUID

import httpx
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.accounts import account_fingerprint, erase_app_data, lock_account
from database.db import AsyncSessionFactory
from database.models import AccountDeletion
from database.queries import conflict_insert
from services.advisor import clear_advice_cache
from services.auth import Identity
from utils.config import SUPABASE_SECRET_KEY, get_supabase_url

logger = logging.getLogger(__name__)


class AuthDeletionUnavailable(RuntimeError):
    pass


async def delete_auth_user(auth_user_id: UUID) -> None:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.request(
                "DELETE", f"{get_supabase_url()}/auth/v1/admin/users/{auth_user_id}",
                headers={"apikey": SUPABASE_SECRET_KEY}, json={"should_soft_delete": False},
            )
        if response.status_code in (200, 204):
            return
        if response.status_code == 404 and response.json().get("error_code") == "user_not_found":
            return
    except (httpx.HTTPError, ValueError, AttributeError):
        pass
    raise AuthDeletionUnavailable


async def finish_deletion(session: AsyncSession, key: str) -> None:
    # UPDATE захватывает строку и допускает только одного исполнителя внешнего запроса.
    auth_user_id = await session.scalar(update(AccountDeletion).where(
        AccountDeletion.id == key, AccountDeletion.auth_user_id.is_not(None),
    ).values(auth_user_id=AccountDeletion.auth_user_id).returning(AccountDeletion.auth_user_id))
    if auth_user_id is not None:
        await delete_auth_user(auth_user_id)
        await session.execute(update(AccountDeletion).where(AccountDeletion.id == key).values(auth_user_id=None))
    await session.commit()


async def erase_account(session: AsyncSession, identity: Identity) -> None:
    key = account_fingerprint(identity.auth_user_id)
    await lock_account(session, key, exclusive=True)
    marker = await session.get(AccountDeletion, key)
    if marker and marker.auth_user_id is None:
        return
    if not SUPABASE_SECRET_KEY:
        detail = {"code": "account_deletion_pending", "message": "Завершить удаление пока не удалось."} if marker else "Удаление аккаунта временно недоступно."
        raise HTTPException(503, detail=detail)
    if marker is None:
        timestamp = identity.password_authenticated_at
        if timestamp is None or not -5 <= time() - timestamp <= 300:
            raise HTTPException(403, detail={"code": "reauth_required", "message": "Подтверди текущий пароль ещё раз."})
        await session.execute(conflict_insert(session, AccountDeletion).values(
            id=key, auth_user_id=identity.auth_user_id,
        ).on_conflict_do_nothing(index_elements=[AccountDeletion.id]))
        user_id = await erase_app_data(session, identity.auth_user_id)
        await session.commit()
        if user_id is not None:
            clear_advice_cache(user_id)
    else:
        await session.commit()

    try:
        await finish_deletion(session, key)
    except Exception as exc:
        # Прикладные данные уже удалены. Сохраняем задачу, даже если Auth ответил,
        # но подтверждение операции потерялось на пути к базе.
        logger.warning("Завершение удаления отложено (%s)", type(exc).__name__)
        raise HTTPException(503, detail={
            "code": "account_deletion_pending", "message": "Завершить удаление пока не удалось. Повтори попытку.",
        }) from None


async def retry_pending_deletions() -> None:
    while True:
        await asyncio.sleep(60)
        try:
            async with AsyncSessionFactory() as session:
                keys = list(await session.scalars(select(AccountDeletion.id).where(
                    AccountDeletion.auth_user_id.is_not(None),
                ).order_by(AccountDeletion.id).limit(10)))
            for key in keys:
                async with AsyncSessionFactory() as session:
                    try:
                        await finish_deletion(session, key)
                    except AuthDeletionUnavailable:
                        logger.warning("Supabase Auth пока не завершил удаление.")
        except Exception as exc:
            logger.warning("Проверка отложенных удалений недоступна (%s)", type(exc).__name__)
