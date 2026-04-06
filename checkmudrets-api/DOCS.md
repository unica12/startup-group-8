# ЧекМудрец API — Документация

REST API бэкенд для мобильного приложения ЧекМудрец. Принимает фото чеков, распознаёт их через OpenAI Vision, сохраняет и анализирует расходы.

## Быстрый старт

```bash
cd checkmudrets-api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Отредактируй .env — вставь OPENAI_API_KEY
uvicorn main:app --reload
```

API: http://localhost:8000  
Swagger UI: http://localhost:8000/docs  
ReDoc: http://localhost:8000/redoc

---

## Эндпоинты

### POST /auth/register
Регистрация или вход по device_id. Если пользователь уже существует — возвращает его данные.

**Request body:**
```json
{ "device_id": "abc-123-def", "name": "Андрей" }
```

**Response:**
```json
{ "user_id": 1, "device_id": "abc-123-def", "name": "Андрей", "created_at": "2026-04-07T10:00:00" }
```

---

### POST /receipts
Загрузка фото чека. Распознаёт через OCR и сохраняет в БД.

**Request:** `multipart/form-data`
- `file` — изображение (jpeg/png/webp)
- `device_id` — идентификатор устройства

**Response:**
```json
{
  "success": true,
  "receipt": {
    "id": 1,
    "store_name": "Пятёрочка",
    "date": "2026-04-05",
    "total": 1847.00,
    "items": [
      { "id": 1, "name": "Молоко 1л", "quantity": 1, "price": 89.0, "total": 89.0, "category": "Молочные" }
    ],
    "created_at": "2026-04-07T10:00:00"
  },
  "mini_advice": "☕ Кофе за 459 руб. — домашний обойдётся в ~30 руб. за чашку."
}
```

---

### GET /receipts?device_id=&limit=10
История чеков пользователя.

**Query params:**
- `device_id` (обязательный)
- `limit` (по умолчанию 10)

---

### GET /stats?device_id=&month=2026-04
Статистика расходов за месяц.

**Query params:**
- `device_id` (обязательный)
- `month` — формат `YYYY-MM` (по умолчанию текущий месяц)

**Response:**
```json
{
  "month": "2026-04",
  "total_spent": 34520.00,
  "receipts_count": 23,
  "average_receipt": 1501.00,
  "by_category": [
    { "category": "Продукты", "amount": 12400.00, "percent": 36, "emoji": "🍞" }
  ],
  "largest_purchase": { "name": "Наушники", "amount": 4200.00, "category": "Электроника" }
}
```

---

### GET /advice?device_id=
Персональные советы по экономии на основе расходов за 30 дней.

**Response:**
```json
{
  "advice": "☕ Кофе на вынос 14 раз на 4 200 руб. → Термос с домашним кофе сэкономит ~3 400 руб./мес.",
  "generated_at": "2026-04-07T10:00:00"
}
```

---

### GET /report?device_id=
Недельный отчёт (последние 7 дней).

**Response:**
```json
{
  "period": { "start": "2026-04-01", "end": "2026-04-07", "label": "01.04–07.04" },
  "total_spent": 8420.00,
  "receipts_count": 5,
  "change_pct": -12.3,
  "change_text": "📉 На 12% меньше, чем на прошлой неделе",
  "top_categories": [
    { "category": "Продукты", "amount": 3200.00, "emoji": "🍞" }
  ],
  "summary_text": "📈 Отчёт за неделю (01.04–07.04)\n..."
}
```

---

## Переменные окружения

| Переменная | Описание | По умолчанию |
|---|---|---|
| `OPENAI_API_KEY` | API-ключ OpenAI (обязательный) | — |
| `OPENAI_MODEL` | Модель GPT | `gpt-4o-mini` |
| `DATABASE_URL` | URL базы данных | `sqlite+aiosqlite:///checkmudrets.db` |
| `HOST` | Хост сервера | `0.0.0.0` |
| `PORT` | Порт сервера | `8000` |

---

## Архитектура

```
checkmudrets-api/
├── main.py               # FastAPI app, startup/shutdown, роутеры
├── routers/              # Эндпоинты по модулям
│   ├── auth.py           # POST /auth/register
│   ├── receipts.py       # POST/GET /receipts
│   ├── stats.py          # GET /stats
│   ├── advice.py         # GET /advice
│   └── report.py         # GET /report
├── services/             # Бизнес-логика
│   ├── ocr.py            # OCR через OpenAI Vision
│   ├── advisor.py        # Генерация советов
│   └── reporter.py       # Формирование отчёта
├── database/             # Слой данных
│   ├── models.py         # SQLAlchemy модели (User, Receipt, Item)
│   ├── db.py             # Движок и сессии
│   └── queries.py        # CRUD-операции
├── schemas/
│   └── models.py         # Pydantic-схемы запросов/ответов
└── utils/
    ├── config.py         # Загрузка .env
    └── formatting.py     # Форматирование, эмодзи
```
