"""Генерация советов по экономии через OpenAI API."""
from __future__ import annotations

import json
import logging

from openai import AsyncOpenAI

from utils.config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

ADVICE_PROMPT = """Ты — дружелюбный финансовый помощник для обычных людей в России.

НИКОГДА не советуй экономить на: образовании, здоровье, лекарствах, аренде, ЖКХ, транспорте до работы. Эти расходы фиксированные — просто пропусти их.

Советуй ТОЛЬКО по повторяющимся необязательным тратам: кофе на вынос, доставка еды, сладости/снеки, подписки, такси, обеды в кафе.

Каждый совет: конкретная сумма траты → конкретная альтернатива → конкретная экономия.
Тон: как друг подсказывает. Не "вы должны", а "попробуй".

Если данных мало (менее 5 чеков) — скажи что нужно больше данных и дай 1-2 общих совета.

Формат: {{эмодзи}} {{привычка и сумма}} → {{альтернатива и экономия}}
Без вступлений и заключений. Сразу советы.

Расходы пользователя:
{expenses_json}"""

MINI_ADVICE_PROMPT = """Дай ОДИН короткий совет по экономии на основе этого чека.

Позиции чека:
{items_summary}

Правила:
- Только если есть явно необязательная трата (кофе, сладости, снеки, готовая еда, алкоголь)
- Если в чеке только базовые продукты/лекарства/необходимое — ответь: "none"
- Формат: одно предложение, дружелюбно, с конкретной суммой
- НИКОГДА не советуй экономить на лекарствах, образовании, ЖКХ

Пример: "☕ Кофе за 459 руб. — домашний обойдётся в ~30 руб. за чашку."
Пример: "none" (если в чеке только молоко, хлеб, яйца)"""


async def generate_advice(expenses_data: dict) -> str:
    """
    Сгенерировать персональные советы по экономии через GPT.

    expenses_data — словарь из queries.get_expenses_for_advice().
    Возвращает готовый текст советов.
    """
    by_category = expenses_data.get("by_category", {})
    total_receipts = expenses_data.get("total_receipts", 0)
    days = expenses_data.get("days", 30)

    expenses_for_prompt = {
        "период_дней": days,
        "количество_чеков": total_receipts,
        "расходы_по_категориям": {
            cat: {
                "сумма_руб": round(data["total"], 2),
                "количество_покупок": data["count"],
            }
            for cat, data in by_category.items()
        },
    }

    expenses_json = json.dumps(expenses_for_prompt, ensure_ascii=False, indent=2)

    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": ADVICE_PROMPT.format(expenses_json=expenses_json),
                }
            ],
            max_tokens=1024,
        )

        advice_text = response.choices[0].message.content.strip()
        logger.info(f"Советы сгенерированы. Чеков: {total_receipts}, категорий: {len(by_category)}")
        return advice_text

    except Exception as e:
        logger.error(f"Ошибка OpenAI при генерации советов: {e}")
        return "😕 Не удалось получить советы. Попробуй позже."


async def generate_mini_advice(items: list) -> str:
    """
    Сгенерировать короткий мини-совет после скана чека.

    Возвращает одно предложение или пустую строку если совет неуместен.
    """
    if not items:
        return ""

    items_summary = "\n".join(
        f"- {item.get('name', '')} [{item.get('category', '')}]: {item.get('total', 0):.2f} руб."
        for item in items[:15]
    )

    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": MINI_ADVICE_PROMPT.format(items_summary=items_summary),
                }
            ],
            max_tokens=100,
            temperature=0.3,
        )
        result = response.choices[0].message.content.strip()

        # Если модель ответила "none" — совет неуместен
        if result.lower().startswith("none"):
            return ""
        return result

    except Exception as e:
        logger.error(f"Ошибка генерации мини-совета: {e}")
        return ""
