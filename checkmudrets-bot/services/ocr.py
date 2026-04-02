"""Распознавание чека через OpenAI Vision API."""
from __future__ import annotations

import base64
import json
import logging
import re
from datetime import date
from typing import Optional

from openai import AsyncOpenAI

from utils.config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

OCR_PROMPT = """Ты — система OCR для российских кассовых чеков. Твоя задача — распознать ВСЕ данные с фото чека с максимальной точностью.

КРИТИЧЕСКИ ВАЖНО:
- Перечисли АБСОЛЮТНО ВСЕ позиции с чека. Не пропускай ни одну строку.
- Если на чеке 15 позиций — в ответе должно быть 15 позиций.
- Внимательно читай каждую строку чека сверху вниз.
- Цены бери ТОЧНО как на чеке. Не округляй, не пересчитывай.
- Итоговую сумму (total) бери ТОЧНО с чека (строка "ИТОГО" или "ИТОГ" или "СУММА").

Верни ТОЛЬКО валидный JSON. Без ```json, без markdown, без пояснений. Только JSON.

Формат:
{
  "success": true,
  "store_name": "Название магазина (с чека)",
  "date": "YYYY-MM-DD",
  "items": [
    {
      "name": "Полное название товара",
      "quantity": 1.0,
      "price": 100.00,
      "total": 100.00,
      "category": "Продукты"
    }
  ],
  "total": 1500.00
}

Правила для items:
- name: перепиши как на чеке, но расшифруй очевидные сокращения (МОЛ. → Молоко, Х/Б → Хлеб белый)
- quantity: если указано количество/вес — укажи. Если не указано — 1.0
- price: цена ЗА ЕДИНИЦУ товара
- total: итоговая цена за эту строку (quantity × price). Если на чеке указана итоговая цена строки — бери её
- category: одна из категорий (Продукты, Молочные, Мясо, Овощи/Фрукты, Хлеб, Напитки, Алкоголь, Кофе, Сладости, Снеки, Готовая еда, Бытовая химия, Гигиена, Косметика, Одежда, Электроника, Лекарства, Транспорт, Топливо, Другое)

Правила для total (итого):
- Бери число из строки ИТОГО/ИТОГ/СУММА на чеке
- НЕ СЧИТАЙ сумму вручную — бери с чека
- Если строки ИТОГО нет — тогда посчитай сумму всех items[].total

Правила для date:
- Формат YYYY-MM-DD
- Если год не виден — ставь 2026

Если фото нечитаемое или это не чек:
{"success": false, "reason": "краткое описание проблемы"}"""


def _parse_json_response(text: str) -> dict:
    """Надёжное извлечение JSON из ответа GPT."""
    cleaned = text.strip()

    # Убираем ```json ... ```
    if cleaned.startswith("```"):
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned)
        cleaned = re.sub(r'\n?\s*```$', '', cleaned)

    # Убираем возможный текст до первого { и после последнего }
    first_brace = cleaned.find('{')
    last_brace = cleaned.rfind('}')
    if first_brace != -1 and last_brace != -1:
        cleaned = cleaned[first_brace:last_brace + 1]

    return json.loads(cleaned)


def _parse_date(date_str: Optional[str]) -> Optional[date]:
    if not date_str:
        return None
    try:
        return date.fromisoformat(date_str)
    except Exception:
        return None


async def recognize_receipt(image_bytes: bytes) -> dict:
    """Распознавание чека через OpenAI Vision API."""

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": OCR_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}",
                                "detail": "high"  # высокое разрешение для точного OCR
                            }
                        },
                        {
                            "type": "text",
                            "text": "Распознай этот кассовый чек. Перечисли ВСЕ позиции без исключений."
                        }
                    ]
                }
            ],
            max_tokens=4096,
            temperature=0.0
        )

        raw_text = response.choices[0].message.content
        logger.debug(f"OCR ответ OpenAI: {raw_text[:200]}...")

        data = _parse_json_response(raw_text)

        if data.get("success") and "date" in data:
            data["date"] = _parse_date(data["date"])

        return data

    except json.JSONDecodeError as e:
        logger.error(f"Ошибка JSON при разборе ответа OCR: {e}")
        return {"success": False, "reason": "Ошибка парсинга ответа ИИ"}

    except Exception as e:
        logger.error(f"OCR ошибка: {e}")
        return {"success": False, "reason": "Ошибка обработки чека"}
