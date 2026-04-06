# 🧠 ПРОМПТ ДЛЯ CLAUDE CODE — ЧАСТЬ 1: FastAPI бэкенд «ЧекМудрец»

## КОНТЕКСТ

У нас уже есть работающий Telegram-бот в папке `checkmudrets-bot/`. Сейчас мы создаём мобильное приложение для RuStore. Для этого нужен REST API бэкенд, который переиспользует логику из бота.

**НЕ ТРОГАЙ папки `checkmudrets-bot/` и `checkmudrets-app/` — работай только в `checkmudrets-api/`.**
**НЕ ТРОГАЙ файл README.md в корне репозитория.**

---

## ЗАДАЧА

Создай FastAPI бэкенд в папке `checkmudrets-api/`. Он должен предоставлять REST API для мобильного приложения: загрузка фото чека, получение статистики, советов, истории.

---

## АРХИТЕКТУРА

```
checkmudrets-api/
├── main.py                 # Точка входа FastAPI
├── routers/
│   ├── __init__.py
│   ├── auth.py             # Регистрация / вход по device_id
│   ├── receipts.py         # POST /receipts (загрузка фото), GET /receipts (история)
│   ├── stats.py            # GET /stats (статистика за месяц)
│   ├── advice.py           # GET /advice (советы по экономии)
│   └── report.py           # GET /report (недельный отчёт)
├── services/
│   ├── __init__.py
│   ├── ocr.py              # Распознавание чека через OpenAI GPT-4o-mini Vision
│   ├── advisor.py          # Генерация советов
│   └── reporter.py         # Формирование отчёта
├── database/
│   ├── __init__.py
│   ├── models.py           # SQLAlchemy модели
│   ├── db.py               # Инициализация БД
│   └── queries.py          # CRUD-операции
├── schemas/
│   ├── __init__.py
│   └── models.py           # Pydantic-схемы для запросов/ответов
├── utils/
│   ├── __init__.py
│   ├── config.py           # Загрузка .env
│   └── formatting.py       # Форматирование, эмодзи-маппинг
├── .env.example
├── requirements.txt
├── DOCS.md
└── .gitignore
```

---

## ТЕХНОЛОГИЧЕСКИЙ СТЕК

| Компонент | Технология |
|-----------|-----------|
| Веб-фреймворк | FastAPI + uvicorn |
| OCR + советы | OpenAI GPT-4o-mini (AsyncOpenAI) |
| База данных | SQLite + SQLAlchemy 2.0 (async, aiosqlite) |
| Валидация | Pydantic v2 |
| Загрузка файлов | FastAPI UploadFile |
| CORS | fastapi.middleware.cors (разрешить все origins для MVP) |

---

## ЭНДПОИНТЫ API

### POST /auth/register
Регистрация по device_id (уникальный идентификатор устройства).
```json
// Request
{ "device_id": "abc-123-def", "name": "Андрей" }

// Response
{ "user_id": 1, "device_id": "abc-123-def", "name": "Андрей", "created_at": "2026-04-06" }
```
Если device_id уже есть — просто возвращаем существующего пользователя.

### POST /receipts
Загрузка фото чека. Принимает multipart/form-data.
```
// Request
form-data: 
  - file: image (jpeg/png)
  - device_id: "abc-123-def"

// Response
{
  "success": true,
  "receipt": {
    "id": 1,
    "store_name": "Пятёрочка",
    "date": "2026-04-05",
    "total": 1847.00,
    "items": [
      { "name": "Молоко 1л", "quantity": 1, "price": 89.00, "total": 89.00, "category": "Молочные" },
      { "name": "Хлеб белый", "quantity": 1, "price": 65.00, "total": 65.00, "category": "Хлеб" }
    ]
  },
  "mini_advice": "☕ Кофе за 459 руб. — домашний обойдётся в ~30 руб. за чашку."
}
```

### GET /receipts?device_id=abc-123-def&limit=10
История чеков.

### GET /stats?device_id=abc-123-def&month=2026-04
Статистика за месяц.
```json
{
  "month": "2026-04",
  "total_spent": 34520.00,
  "receipts_count": 23,
  "average_receipt": 1501.00,
  "by_category": [
    { "category": "Продукты", "amount": 12400.00, "percent": 36 },
    { "category": "Кофе", "amount": 4500.00, "percent": 13 }
  ],
  "largest_purchase": { "name": "Наушники", "amount": 4200.00, "category": "Электроника" }
}
```

### GET /advice?device_id=abc-123-def
Персональные советы.

### GET /report?device_id=abc-123-def
Недельный отчёт.

---

## СЕРВИСЫ — ПЕРЕИСПОЛЬЗУЙ ЛОГИКУ ИЗ БОТА

### services/ocr.py

**Тот же промпт что в боте, но адаптированный:**

```python
from openai import AsyncOpenAI
import base64

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

async def recognize_receipt(image_bytes: bytes) -> dict:
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": OCR_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high"
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
    
    return parse_json_response(response.choices[0].message.content)
```

**OCR промпт — используй этот (проверенный):**

```
Ты — система OCR для российских кассовых чеков. Твоя задача — распознать ВСЕ данные с фото чека с максимальной точностью.

КРИТИЧЕСКИ ВАЖНО:
- Перечисли АБСОЛЮТНО ВСЕ позиции с чека. Не пропускай ни одну строку.
- Если на чеке 15 позиций — в ответе должно быть 15 позиций.
- Внимательно читай каждую строку чека сверху вниз.
- Цены бери ТОЧНО как на чеке. Не округляй, не пересчитывай.
- Итоговую сумму (total) бери ТОЧНО с чека (строка ИТОГО/ИТОГ/СУММА).

Верни ТОЛЬКО валидный JSON. Без ```json, без markdown, без пояснений.

{
  "success": true,
  "store_name": "Название магазина",
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

Категории: Продукты, Молочные, Мясо, Овощи/Фрукты, Хлеб, Напитки, Алкоголь, Кофе, Сладости, Снеки, Готовая еда, Бытовая химия, Гигиена, Косметика, Одежда, Электроника, Лекарства, Транспорт, Топливо, Другое

Если не чек или нечитаемо: {"success": false, "reason": "описание"}
```

### services/advisor.py

**Промпт для советов (с фильтрацией бреда):**

```
Ты — дружелюбный финансовый помощник для обычных людей в России.

НИКОГДА не советуй экономить на: образовании, здоровье, лекарствах, аренде, ЖКХ, транспорте до работы. Эти расходы фиксированные — просто пропусти их.

Советуй ТОЛЬКО по повторяющимся необязательным тратам: кофе на вынос, доставка еды, сладости/снеки, подписки, такси, обеды в кафе.

Каждый совет: конкретная сумма траты → конкретная альтернатива → конкретная экономия.
Тон: как друг подсказывает. Не "вы должны", а "попробуй".

Если данных мало (менее 5 чеков) — скажи что нужно больше данных и дай 1-2 общих совета.

Формат: {эмодзи} {привычка и сумма} → {альтернатива и экономия}
Без вступлений и заключений. Сразу советы.
```

---

## МОДЕЛИ БД

Те же что в боте:

```python
class User:
    id, device_id (unique), name, created_at

class Receipt:
    id, user_id (FK), store_name, date, total, raw_text, created_at
    items -> relationship

class Item:
    id, receipt_id (FK), name, quantity, price, total, category
```

---

## .env.example

```
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
DATABASE_URL=sqlite+aiosqlite:///checkmudrets.db
HOST=0.0.0.0
PORT=8000
```

---

## requirements.txt

```
fastapi>=0.110.0
uvicorn>=0.27.0
openai>=1.30.0
sqlalchemy>=2.0.0
aiosqlite>=0.19.0
python-dotenv>=1.0.0
python-multipart>=0.0.9
Pillow>=10.0.0
```

---

## main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ЧекМудрец API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Для MVP — разрешаем всё
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключить роутеры
# При старте — инициализировать БД
# Запуск: uvicorn main:app --reload
```

---

## ВАЖНЫЕ ТРЕБОВАНИЯ

1. Весь код асинхронный (async/await)
2. Type hints везде
3. Обработка ошибок — пользователь никогда не видит трейсбек
4. Логирование — каждый распознанный чек логируется
5. CORS открыт для всех origins (MVP)
6. JSON-парсер GPT-ответов с очисткой markdown
7. Комментарии на русском
8. **НЕ ТРОГАЙ README.md, checkmudrets-bot/, checkmudrets-app/**
9. Документацию пиши в DOCS.md внутри checkmudrets-api/

---

## ЗАПУСК

```bash
cd checkmudrets-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Заполни OPENAI_API_KEY
uvicorn main:app --reload
```

API доступен на http://localhost:8000
Swagger-документация на http://localhost:8000/docs

---

Создай все файлы. Начни с database/, затем services/, затем schemas/, затем routers/, затем main.py, и в конце DOCS.md.
