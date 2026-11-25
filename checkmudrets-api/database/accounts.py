"""Агрегаты, экспорт и состояние удаления аккаунта."""
from datetime import timezone
from hashlib import sha256
from uuid import UUID

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AccountDeletion, Consent, Item, Receipt, ReceiptDraft, User
from database.queries import amount_in_kopecks, get_receipt_totals


def account_fingerprint(auth_user_id: UUID) -> str:
    return sha256(auth_user_id.bytes).hexdigest()


async def lock_account(session: AsyncSession, fingerprint: str, *, exclusive: bool = False) -> None:
    if session.get_bind().dialect.name == "postgresql":
        key = int.from_bytes(bytes.fromhex(fingerprint[:16]), "big", signed=True)
        lock = "pg_advisory_xact_lock" if exclusive else "pg_advisory_xact_lock_shared"
        await session.execute(text(f"SELECT {lock}(CAST(:key AS bigint))"), {"key": key})


async def registration_date(session: AsyncSession, user: User):
    if session.get_bind().dialect.name == "postgresql":
        # PostgreSQL и Auth находятся в одном проекте Supabase.
        registered = await session.scalar(text("SELECT created_at FROM auth.users WHERE id = :id"), {"id": user.auth_user_id})
        if registered:
            return registered.astimezone(timezone.utc)
    return user.created_at.replace(tzinfo=timezone.utc) if not user.created_at.tzinfo else user.created_at


async def profile_totals(session: AsyncSession, user_id: int) -> dict:
    total, count = await get_receipt_totals(session, user_id)
    items = await session.scalar(select(func.count(Item.id)).join(Receipt).where(Receipt.user_id == user_id))

    category = func.trim(Item.category)
    category_amount = func.sum(amount_in_kopecks(Item.total))
    top = await session.scalar(select(category).join(Receipt).where(Receipt.user_id == user_id, category != "")
                               .group_by(category).having(category_amount > 0)
                               .order_by(category_amount.desc(), category).limit(1))
    return dict(receipts_count=count, total_spent=total, items_count=items, top_category=top)


async def export_receipts(session: AsyncSession, user_id: int) -> list[Receipt]:
    return list(await session.scalars(select(Receipt).where(Receipt.user_id == user_id).order_by(Receipt.id)))


async def export_consents(session: AsyncSession, user_id: int) -> list[Consent]:
    return list(await session.scalars(select(Consent).where(Consent.user_id == user_id).order_by(Consent.id)))


async def erase_app_data(session: AsyncSession, auth_user_id: UUID) -> int | None:
    user_id = await session.scalar(select(User.id).where(User.auth_user_id == auth_user_id))
    if user_id is None:
        return None
    receipt_ids = select(Receipt.id).where(Receipt.user_id == user_id)
    await session.execute(delete(Item).where(Item.receipt_id.in_(receipt_ids)))
    for model in (Receipt, ReceiptDraft, Consent):
        await session.execute(delete(model).where(model.user_id == user_id))
    await session.execute(delete(User).where(User.id == user_id))
    return user_id
