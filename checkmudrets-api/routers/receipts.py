"""Роутер чеков — загрузка фото и история."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from database.queries import get_last_receipts, get_or_create_user, save_receipt
from schemas.models import (
    ItemResponse,
    ReceiptResponse,
    ReceiptsListResponse,
    UploadReceiptResponse,
)
from services.advisor import generate_mini_advice
from services.ocr import recognize_receipt

logger = logging.getLogger(__name__)

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
    device_id: str = Form(...),
    session: AsyncSession = Depends(get_session),
) -> UploadReceiptResponse:

    logger.info(
        f"Загрузка чека | device_id={device_id!r} "
        f"filename={file.filename!r} "
        f"content_type={file.content_type!r}"
    )

    image_bytes = await file.read()

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Файл пустой")

    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый тип файла: {file.content_type}",
        )

    user = await get_or_create_user(session=session, device_id=device_id)

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

    mini_advice = await generate_mini_advice(items_data)

    # ✅ ИСПРАВЛЕНИЕ ЗДЕСЬ
    items_response = [
        ItemResponse(
            id=0,  # временно, чтобы не ломать схему
            name=item["name"],
            quantity=item["quantity"],
            price=item["price"],
            total=item["total"],
            category=item["category"],
        )
        for item in items_data
    ]

    receipt_response = ReceiptResponse(
        id=receipt.id,
        store_name=receipt.store_name,
        date=receipt.date,
        total=receipt.total,
        items=items_response,
        created_at=receipt.created_at,
    )

    return UploadReceiptResponse(
        success=True,
        receipt=receipt_response,
        mini_advice=mini_advice or None,
    )


@router.get("", response_model=ReceiptsListResponse)
async def get_receipts(
    device_id: str,
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
) -> ReceiptsListResponse:

    user = await get_or_create_user(session=session, device_id=device_id)
    receipts = await get_last_receipts(session=session, user_id=user.id, limit=limit)

    receipts_response = [
        ReceiptResponse(
            id=r.id,
            store_name=r.store_name,
            date=r.date,
            total=r.total,
            items=[
                ItemResponse(
                    id=item.id,
                    name=item.name,
                    quantity=item.quantity,
                    price=item.price,
                    total=item.total,
                    category=item.category,
                )
                for item in r.items
            ],
            created_at=r.created_at,
        )
        for r in receipts
    ]

    return ReceiptsListResponse(
        receipts=receipts_response,
        total_count=len(receipts_response),
    )