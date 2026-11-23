"""Генерация советов по экономии через OpenAI API."""
from __future__ import annotations

import json
import logging

from openai import AsyncOpenAI

from utils.config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

ADVICE_PROMPT = """Ты — дружелюбный финансовый помощник и нутрициолог для людей в России. Тебе дают расходы пользователя за месяц. Дай 3–5 советов: по экономии И по здоровому питанию.

ГЛАВНЫЕ ПРАВИЛА:

1. НИКОГДА не советуй экономить на:
   - Образовании (вуз, курсы, репетиторы)
   - Здоровье (лекарства, врачи)
   - Аренде / ипотеке
   - ЖКХ
   - Транспорте до работы
   Просто пропусти эти категории.

2. Советы по экономии — ТОЛЬКО повторяющиеся необязательные траты:
   - Кофе на вынос → термос
   - Доставка еды → готовить дома
   - Сладости/снеки → сократить
   - Такси → общественный транспорт
   - Подписки → отключить неиспользуемые

3. Советы по здоровому питанию — анализируй что покупает:
   - Много полуфабрикатов/готовой еды → предложи простые рецепты
   - Много сладостей/снеков → предложи полезные альтернативы (орехи, фрукты)
   - Мало овощей/фруктов → напомни добавить в рацион
   - Много газировки/сока → предложи воду
   - Не надо быть занудой — тон лёгкий, как друг подсказывает

4. Каждый совет содержит:
   - Конкретную сумму траты
   - Конкретную альтернативу
   - Сумму экономии ИЛИ пользу для здоровья

5. Если мало данных (< 5 чеков) — скажи что нужно больше данных, дай 1-2 общих совета.

ФОРМАТ:
{{эмодзи}} {{Описание}} → {{Альтернатива и выгода}}

ПРИМЕРЫ:
☕ Кофе 14 раз/мес на 4 200 ₽ → Термос с домашним: экономия ~3 400 ₽/мес.
🍕 Пицца и полуфабрикаты 8 раз на 3 200 ₽ → Готовь пасту или гречку с курицей — дешевле на ~2 000 ₽ и полезнее для желудка.
🍫 Сладости 12 покупок на 2 100 ₽ → Замени половину на бананы и орехи — минус ~800 ₽ и плюс к энергии.
🥤 Газировка 6 бутылок на 600 ₽ → Обычная вода бесплатна из фильтра. Экономия 600 ₽ + меньше сахара.
🥬 В чеках почти нет овощей и фруктов → Добавь хотя бы морковь, яблоки, капусту — это дёшево (300-500 ₽/нед) и закроет витамины.

Без вступлений. Сразу советы.

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
