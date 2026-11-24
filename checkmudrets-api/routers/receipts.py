"""Роутер чеков — загрузка фото и история."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from database.models import User
from database.queries import get_last_receipts, save_receipt
from schemas.models import (
    ReceiptResponse,
    ReceiptsListResponse,
    UploadReceiptResponse,
)
from services.advisor import generate_mini_advice
from services.auth import require_consents
from services.ocr import recognize_receipt

router = APIRouter(prefix="/receipts", tags=["receipts"])

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
    "application/octet-stream",
}


@router.post("", response_model=UploadReceiptResponse)
async def upload_receipt(
    file: UploadFile = File(...),
    user: User = Depends(require_consents),
    session: AsyncSession = Depends(get_session),
) -> UploadReceiptResponse:

    image_bytes = await file.read()

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Файл пустой")

    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый тип файла: {file.content_type}",
        )

    await session.commit()
    ocr_result = await recognize_receipt(image_bytes)

    if not ocr_result.get("success"):
        return UploadReceiptResponse(
            success=False,
            error=ocr_result.get("reason", "Ошибка OCR"),
        )

    items_data = ocr_result.get("items", [])

    receipt = await save_receipt(
        session=session,
        user_id=user.id,
        store_name=ocr_result.get("store_name", ""),
        receipt_date=ocr_result.get("date"),
        total=ocr_result.get("total", 0.0),
        items_data=items_data,
        raw_text="",
    )
    await session.commit()

    mini_advice = await generate_mini_advice(items_data)

    return UploadReceiptResponse(
        success=True,
        receipt=ReceiptResponse.model_validate(receipt),
        mini_advice=mini_advice or None,
    )


@router.get("", response_model=ReceiptsListResponse)
async def get_receipts(
    limit: int = Query(default=10, ge=1, le=100),
    user: User = Depends(require_consents),
    session: AsyncSession = Depends(get_session),
) -> ReceiptsListResponse:

    receipts = await get_last_receipts(session=session, user_id=user.id, limit=limit)

    return ReceiptsListResponse(
        receipts=[ReceiptResponse.model_validate(receipt) for receipt in receipts],
        total_count=len(receipts),
    )
