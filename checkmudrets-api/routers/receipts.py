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

# Разрешённые MIME-типы изображений
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}


@router.post("", response_model=UploadReceiptResponse)
async def upload_receipt(
    file: UploadFile = File(..., description="Фото чека (jpeg/png)"),
    device_id: str = Form(..., description="Идентификатор устройства"),
    session: AsyncSession = Depends(get_session),
) -> UploadReceiptResponse:
    """
    Загрузить фото чека, распознать через OCR и сохранить в БД.

    Принимает multipart/form-data: file + device_id.
    """
    # Проверяем тип файла
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый тип файла: {file.content_type}. Используй jpeg или png.",
        )

    # Читаем байты изображения
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Файл пустой")

    # Получаем или создаём пользователя
    user = await get_or_create_user(session=session, device_id=device_id)

    # Распознаём чек через OCR
    ocr_result = await recognize_receipt(image_bytes)

    if not ocr_result.get("success"):
        reason = ocr_result.get("reason", "Не удалось распознать чек")
        logger.warning(f"OCR не распознал чек: {reason} | device_id={device_id}")
        return UploadReceiptResponse(success=False, error=reason)

    # Сохраняем чек в БД
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

    # Генерируем мини-совет по чеку
    mini_advice = await generate_mini_advice(items_data)

    # Формируем ответ
    items_response = [
        ItemResponse(
            id=item.id,
            name=item.name,
            quantity=item.quantity,
            price=item.price,
            total=item.total,
            category=item.category,
        )
        for item in receipt.items
    ]

    receipt_response = ReceiptResponse(
        id=receipt.id,
        store_name=receipt.store_name,
        date=receipt.date,
        total=receipt.total,
        items=items_response,
        created_at=receipt.created_at,
    )

    logger.info(
        f"Чек сохранён: id={receipt.id} user_id={user.id} "
        f"магазин={receipt.store_name} сумма={receipt.total}"
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
    """
    Получить историю чеков пользователя.

    Query-параметры: device_id, limit (по умолчанию 10).
    """
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
