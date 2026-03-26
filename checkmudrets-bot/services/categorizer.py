"""Категоризация позиций чека через OpenAI API (fallback-сервис).

Используется если OCR-промпт не вернул категории для позиций.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

import openai

from utils.config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

CATEGORIZE_PROMPT = """Ты — система категоризации товаров из кассовых чеков. Для каждого товара определи категорию.

Доступные категории:
Продукты, Молочные, Мясо, Овощи/Фрукты, Хлеб, Напитки, Алкоголь, Кофе, Сладости, Снеки, Готовая еда, Доставка еды, Кафе/Рестораны, Бытовая химия, Гигиена, Косметика, Одежда, Обувь, Электроника, Техника, Канцелярия, Книги, Игрушки, Зоотовары, Лекарства, Спорт, Транспорт, Топливо, Подписки, Развлечения, Связь/Интернет, ЖКХ, Ремонт, Мебель, Другое

Вход (JSON):
{items_json}

Ответ — ТОЛЬКО JSON без markdown:
[{{"name": "Молоко 1л", "category": "Молочные"}}, ...]"""


def _clean_json(text: str) -> str:
    """Удалить markdown-блоки из ответа."""
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```\s*$", "", text)
    return text.strip()


async def categorize_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Добавить категории к позициям чека через OpenAI API.

    Принимает список позиций (name, price, ...).
    Возвращает тот же список с добавленным полем category.
    """
    if not items:
        return items

    items_for_api = [{"name": item["name"], "price": item.get("price", 0)} for item in items]
    items_json = json.dumps(items_for_api, ensure_ascii=False)

    try:
        response = await openai.ChatCompletion.acreate(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": CATEGORIZE_PROMPT.format(items_json=items_json),
                }
            ],
            temperature=0,
            max_tokens=1024,
            api_key=OPENAI_API_KEY,
        )

        raw_text = response.choices[0].message.content
        cleaned = _clean_json(raw_text)
        categorized = json.loads(cleaned)

        # Создаём маппинг name -> category
        category_map: dict[str, str] = {
            entry["name"]: entry.get("category", "Другое")
            for entry in categorized
            if isinstance(entry, dict)
        }

        # Обновляем категории в исходных позициях
        for item in items:
            if not item.get("category") or item["category"] == "Другое":
                item["category"] = category_map.get(item["name"], "Другое")

        logger.info(f"Категоризировано {len(items)} позиций")
        return items

    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга категорий: {e}")
        for item in items:
            if not item.get("category"):
                item["category"] = "Другое"
        return items
    except Exception as e:
        logger.error(f"Ошибка категоризации: {e}")
        for item in items:
            if not item.get("category"):
                item["category"] = "Другое"
        return items