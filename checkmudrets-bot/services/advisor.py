"""Генерация персональных советов по экономии через OpenAI API."""
from __future__ import annotations

import json
import logging

import openai

from utils.config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

ADVICE_PROMPT = """Ты — финансовый советник, помогающий людям экономить деньги. Проанализируй расходы пользователя и дай 3–5 конкретных советов.

Расходы за последние 30 дней:
{expenses_json}

Правила:
- Каждый совет должен содержать конкретную сумму экономии
- Советы должны быть реалистичными и применимыми в России
- Тон — дружелюбный, без нравоучений
- Формат: эмодзи + совет + сумма
- Если данных мало (менее 5 чеков) — скажи, что нужно больше данных для точного анализа, но дай общие советы

Пример хорошего совета:
☕ Ты покупаешь кофе 12 раз в месяц на ~3 600 руб. Термос с домашним кофе сэкономит ~2 800 руб./мес.

Пример плохого совета:
"Тратьте меньше" — слишком абстрактно.

Ответь только текстом советов, без JSON."""


async def generate_advice(expenses_data: dict) -> str:
    """
    Сгенерировать персональные советы по экономии через OpenAI GPT.

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
        openai.api_key = OPENAI_API_KEY

        response = await openai.ChatCompletion.acreate(
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
        logger.info(
            f"Сгенерированы советы для пользователя. "
            f"Чеков: {total_receipts}, категорий: {len(by_category)}"
        )
        return advice_text

    except openai.error.OpenAIError as e:
        logger.error(f"Ошибка OpenAI API при генерации советов: {e}")
        return "😕 Не удалось получить советы. Попробуй позже."
    except Exception as e:
        logger.error(f"Ошибка генерации советов: {e}")
        return "😕 Не удалось получить советы. Попробуй позже."