"""Распознавание, подтверждение и история чеков."""
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from database.models import Item, ReceiptDraft, User
from database.queries import (
    get_analysis_receipts, get_confirmed_receipt, get_last_receipts, get_receipt, get_receipt_totals, owns_draft, save_receipt,
)
from schemas.models import ReceiptResponse, ReceiptsListResponse, RecognizeReceiptResponse, SavedReceiptResponse
from schemas.receipt_input import ConfirmReceipt, ReceiptWarning
from services.advisor import clear_advice_cache
from services.analytics import price_insights
from services.auth import ensure_account_available, require_consents
from services.ocr import MAX_IMAGE_BYTES, InvalidImage, recognize_receipt
from services.receipt_validation import validate_receipt
from utils.formatting import CATEGORY_EMOJI
from utils.receipt_dates import reporting_day

router = APIRouter(prefix="/receipts", tags=["receipts"])

ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/webp", "image/heic", "image/heif",
    "application/octet-stream",
}


async def receipt_writer(
    user: User = Depends(require_consents), session: AsyncSession = Depends(get_session),
) -> User:
    # Подтверждение, редактирование и удаление одного аккаунта выполняются последовательно.
    await session.execute(select(User.id).where(User.id == user.id).with_for_update())
    return user


def check_receipt(body: ConfirmReceipt) -> list[ReceiptWarning]:
    warnings = validate_receipt(body.receipt)
    blocking = any(issue.blocking for issue in warnings)
    if blocking or warnings and not body.accept_warnings:
        raise HTTPException(
            422 if blocking else 409,
            detail={
                "message": "Исправь обязательные поля чека." if blocking else "Проверь предупреждения перед сохранением.",
                "warnings": [issue.model_dump() for issue in warnings],
            },
        )
    return warnings


async def commit_receipt_change(session: AsyncSession, user_id: int) -> None:
    await session.commit()
    clear_advice_cache(user_id)


@router.post("/recognize", response_model=RecognizeReceiptResponse)
async def recognize(
    file: UploadFile = File(...),
    user: User = Depends(require_consents),
    session: AsyncSession = Depends(get_session),
) -> RecognizeReceiptResponse:
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(400, "Формат изображения не поддерживается.")
    image = await file.read(MAX_IMAGE_BYTES + 1)
    if not image:
        raise HTTPException(400, "Файл пустой.")
    if len(image) > MAX_IMAGE_BYTES:
        raise HTTPException(413, "Размер фото превышает 12 МБ.")
    await session.commit()
    try:
        receipt, warnings, retried = await recognize_receipt(image)
    except InvalidImage as exc:
        raise HTTPException(400, str(exc)) from None
    except RuntimeError as exc:
        raise HTTPException(502, str(exc)) from None
    if receipt is None:
        return RecognizeReceiptResponse(success=False, error="Чек не читается. Попробуй сделать новое фото.")

    await ensure_account_available(session, user.auth_user_id)
    draft_id = uuid4()
    session.add(ReceiptDraft(id=draft_id, user_id=user.id))
    await session.commit()
    return RecognizeReceiptResponse(
        success=True, draft_id=draft_id, receipt=receipt, warnings=warnings, retried=retried,
        categories=list(CATEGORY_EMOJI),
    )


@router.post("/{draft_id}/confirm", response_model=SavedReceiptResponse)
async def confirm(
    draft_id: UUID,
    body: ConfirmReceipt,
    user: User = Depends(receipt_writer),
    session: AsyncSession = Depends(get_session),
) -> SavedReceiptResponse:
    if not await owns_draft(session, user.id, draft_id):
        raise HTTPException(404, "Черновик чека не найден.")
    receipt = await get_confirmed_receipt(session, user.id, draft_id)
    if receipt is None:
        warnings = check_receipt(body)
        receipt = await save_receipt(
            session, user.id, draft_id, body.receipt, price_comparable=not any(issue.retry for issue in warnings),
        )
        await commit_receipt_change(session, user.id)

    mini_advice = []
    if receipt.price_comparable and receipt.date and not receipt.discount:
        today = reporting_day()
        history = await get_analysis_receipts(session, user.id, today)
        mini_advice = price_insights(history, today, focus_receipt_id=receipt.id)
    return SavedReceiptResponse(
        receipt=ReceiptResponse.model_validate(receipt), mini_advice=mini_advice[0] if mini_advice else None,
    )


@router.get("", response_model=ReceiptsListResponse)
async def get_receipts(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_consents),
    session: AsyncSession = Depends(get_session),
) -> ReceiptsListResponse:
    receipts = await get_last_receipts(session, user.id, limit, offset)
    _, total_count = await get_receipt_totals(session, user.id)
    return ReceiptsListResponse(
        receipts=[ReceiptResponse.model_validate(receipt) for receipt in receipts],
        total_count=total_count, categories=list(CATEGORY_EMOJI),
    )


@router.patch("/{receipt_id}", response_model=ReceiptResponse)
async def update_receipt(
    receipt_id: int,
    body: ConfirmReceipt,
    user: User = Depends(receipt_writer),
    session: AsyncSession = Depends(get_session),
) -> ReceiptResponse:
    receipt = await get_receipt(session, user.id, receipt_id)
    if receipt is None:
        raise HTTPException(404, "Чек не найден.")
    warnings = check_receipt(body)
    for field, value in body.receipt.model_dump(exclude={"items"}).items():
        setattr(receipt, field, value)
    receipt.price_comparable = not any(issue.retry for issue in warnings)
    receipt.items = [Item(**item.model_dump()) for item in body.receipt.items]
    await session.flush()
    await commit_receipt_change(session, user.id)
    return ReceiptResponse.model_validate(receipt)


@router.delete("/{receipt_id}", status_code=204, response_class=Response)
async def delete_receipt(
    receipt_id: int,
    user: User = Depends(receipt_writer),
    session: AsyncSession = Depends(get_session),
) -> Response:
    receipt = await get_receipt(session, user.id, receipt_id)
    if receipt is None:
        raise HTTPException(404, "Чек не найден.")
    draft_id = receipt.draft_id
    await session.delete(receipt)
    if draft_id is not None:
        await session.flush()
        # Старый запрос подтверждения не должен восстановить удалённый чек.
        await session.execute(delete(ReceiptDraft).where(ReceiptDraft.id == draft_id, ReceiptDraft.user_id == user.id))
    await commit_receipt_change(session, user.id)
    return Response(status_code=204)
