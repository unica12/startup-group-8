"""Проверка сессии Supabase и доступ к закрытым данным приложения."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from threading import Lock
from time import monotonic
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from database.models import User
from database.queries import get_or_create_user, get_user_consents
from utils.config import SUPABASE_JWT_SECRET, get_supabase_url

REQUIRED_CONSENTS = {
    "terms": "prototype-1",
    "personal_data": "prototype-1",
    "cross_border": "prototype-1",
}
ASYMMETRIC_ALGORITHMS = {"ES256", "RS256"}
bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Identity:
    auth_user_id: UUID
    email: str | None
    name: str | None


class SigningKeys:
    def __init__(self, issuer: str):
        self.client = jwt.PyJWKClient(f"{issuer}/.well-known/jwks.json", lifespan=300, timeout=5)
        self.lock = Lock()
        self.last_refresh = float("-inf")

    def get(self, key_id: str, algorithm: str):
        with self.lock:
            keys = self.client.get_jwk_set().keys
            key = next((key for key in keys if key.key_id == key_id), None)
            # JWKS обновляется сразу для нового kid при ротации, с ограничением частоты.
            if key is None and monotonic() - self.last_refresh >= 10:
                self.last_refresh = monotonic()
                keys = self.client.get_jwk_set(refresh=True).keys
                key = next((key for key in keys if key.key_id == key_id), None)
        if key is None or key.algorithm_name != algorithm or key.public_key_use not in (None, "sig"):
            raise jwt.InvalidTokenError("Неизвестный ключ подписи")
        return key.key


@lru_cache(maxsize=1)
def signing_keys(issuer: str) -> SigningKeys:
    return SigningKeys(issuer)


def verify_access_token(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> Identity:
    unauthorized = HTTPException(401, "Сессия недействительна. Войди снова.", headers={"WWW-Authenticate": "Bearer"})
    if not credentials or credentials.scheme.lower() != "bearer":
        raise unauthorized

    issuer = f"{get_supabase_url()}/auth/v1"
    token = credentials.credentials
    try:
        header = jwt.get_unverified_header(token)
        algorithm = header.get("alg")
        key_id = header.get("kid")
        if isinstance(algorithm, str) and algorithm in ASYMMETRIC_ALGORITHMS and isinstance(key_id, str) and key_id:
            key = signing_keys(issuer).get(key_id, algorithm)
        elif algorithm == "HS256" and SUPABASE_JWT_SECRET:
            key = SUPABASE_JWT_SECRET
        else:
            raise unauthorized
        claims = jwt.decode(
            token, key, algorithms=[algorithm], issuer=issuer, audience="authenticated",
            options={"require": ["iss", "aud", "exp", "sub"]},
        )
        if claims.get("role") != "authenticated" or claims.get("is_anonymous") is True:
            raise unauthorized
        user_id = UUID(claims["sub"])
    except (jwt.PyJWKClientError, jwt.PyJWKSetError, jwt.PyJWKError) as exc:
        raise HTTPException(503, "Проверка сессии временно недоступна.") from exc
    except (jwt.InvalidTokenError, ValueError, TypeError) as exc:
        raise unauthorized from exc

    metadata = claims.get("user_metadata")
    name = metadata.get("name") if isinstance(metadata, dict) else None
    if isinstance(name, str):
        name = name.replace("\x00", "").strip()[:50] or None
    else:
        name = None
    email = claims.get("email")
    return Identity(user_id, email if isinstance(email, str) else None, name)


async def current_user(
    identity: Identity = Depends(verify_access_token), session: AsyncSession = Depends(get_session),
) -> User:
    return await get_or_create_user(session, identity.auth_user_id, identity.name)


async def require_consents(
    user: User = Depends(current_user), session: AsyncSession = Depends(get_session),
) -> User:
    if not await has_required_consents(session, user.id):
        raise HTTPException(403, detail={"code": "consents_required", "message": "Подтверди обязательные согласия."})
    return user


async def has_required_consents(session: AsyncSession, user_id: int) -> bool:
    return set(REQUIRED_CONSENTS.items()).issubset(await get_user_consents(session, user_id))
