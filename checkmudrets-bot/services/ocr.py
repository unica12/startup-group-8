"""Распознавание чека через OpenAI Vision API."""
from __future__ import annotations

import base64
import json
import logging
import re
import asyncio
from datetime import date
from typing import Optional

from openai import OpenAI

from utils.config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)

OCR_PROMPT = """Ты — система распознавания кассовых чеков. Проанализируй фото чека и верни ТОЛЬКО валидный JSON без markdown-разметки.

Формат ответа:
{
  "success": true,
  "store_name": "Название магазина",
  "date": "YYYY-MM-DD",
  "items": [
    {
      "name": "Название товара",
      "quantity": 1.0,
      "price": 100.00,
      "total": 100.00,
      "category": "Продукты"
    }
  ],
  "total": 500.00
}

Доступные категории:
Продукты, Молочные, Мясо, Овощи/Фрукты, Хлеб, Напитки, Алкоголь, Кофе, Сладости, Снеки, Готовая еда, Доставка еды, Кафе/Рестораны, Бытовая химия, Гигиена, Косметика, Одежда, Обувь, Электроника, Техника, Канцелярия, Книги, Игрушки, Зоотовары, Лекарства, Спорт, Транспорт, Топливо, Подписки, Развлечения, Связь/Интернет, ЖКХ, Ремонт, Мебель, Другое

Правила:
- Если чек нечитаемый или это не чек — верни {"success": false, "reason": "описание проблемы"}
- Дата YYYY-MM-DD, если год не виден — 2026
- Цены float
- quantity = 1.0 по умолчанию
- total = quantity × price
- Если итого нет — посчитай
- Для каждой позиции обязательно category
"""


def _clean_json(text: str) -> str:
    """Удаление markdown-обёрток."""
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```\s*$", "", text)
    return text.strip()


def _parse_date(date_str: Optional[str]) -> Optional[date]:
    if not date_str:
        return None
    try:
        return date.fromisoformat(date_str)
    except Exception:
        return None


async def recognize_receipt(image_bytes: bytes) -> dict:
    """Распознавание чека через OpenAI."""

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    loop = asyncio.get_event_loop()

    try:
        # ВАЖНО: OpenAI sync → оборачиваем в executor
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": OCR_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=1500,
            ),
        )

        raw_text = response.choices[0].message.content
        logger.debug(f"OCR ответ OpenAI: {raw_text[:200]}...")

        cleaned = _clean_json(raw_text)
        data = json.loads(cleaned)

        if data.get("success") and "date" in data:
            data["date"] = _parse_date(data["date"])

        return data

    except json.JSONDecodeError as e:
        logger.error(f"Ошибка JSON: {e}")
        return {"success": False, "reason": "Ошибка парсинга ответа ИИ"}

    except Exception as e:
        logger.error(f"OCR ошибка: {e}")
        return {"success": False, "reason": "Ошибка обработки чека"}