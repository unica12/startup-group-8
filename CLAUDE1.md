# ЧекМудрец — PWA трекер расходов по фото чека

Курсовой проект РТУ МИРЭА, курс «Стартап в информационных технологиях», группа ЭФБО-06-23, команда №8.
Команда: Земсков А.В., Викторов А.Д., Демидов И.С.
Репозиторий: https://github.com/unica12/startup-group-8
Дедлайн: сжатый (пара дней) — приоритет на рабочий результат, а не на идеальную архитектуру.

Пользователь фотографирует чек → GPT-4o-mini Vision распознаёт товары → траты раскладываются по категориям → приложение показывает статистику и советы по экономии.

---

## Правила работы

- Весь UI — на русском. Деньги форматируем как `1 234 ₽` (пробел-разделитель тысяч, знак ₽).
- Mobile-first: проверяй вёрстку на ширине 375px. Это PWA, основное использование — с телефона.
- После каждого изменения фронта: `npm run build` в `checkmudrets-pwa/` должен проходить без ошибок.
- Работаем по этапам ниже, по порядку. После каждого этапа — отдельный коммит.
- **Никогда не коммить `.env`** — в `checkmudrets-api/.env` лежит реальный ключ OpenAI. Только `.env.example`.
- Не трогай легаси-папки: `checkmudrets-app/` (старый Flutter) и `checkmudrets-bot/` (старый Telegram-бот, ветки week*). Лендинг живёт в ветке `week14`, папка `docs/` — его тоже не ломать.
- Не выдумывай данные в UI: если у бэкенда нет поля — либо добавь его в API, либо не показывай.
- Если решение неоднозначное (архитектура, хостинг, юр. тексты) — спроси, а не угадывай.

---

## Структура

```
startup-group-8/            (ветка main)
├── checkmudrets-pwa/       # Frontend — React 19 + Vite + Tailwind CSS v4 + vite-plugin-pwa
├── checkmudrets-api/       # Backend — FastAPI + async SQLAlchemy + aiosqlite (SQLite)
├── checkmudrets-app/       # ЛЕГАСИ (Flutter), не трогать
└── CLAUDE1.md
```

### Frontend (`checkmudrets-pwa/`)
- Навигация без react-router: состояние `page` в `src/App.jsx` + `src/components/BottomNav.jsx` (5 вкладок: Главная, История, Скан, Статистика, Профиль; «Скан» — поднятая круглая кнопка).
- Страницы: `src/pages/{Home,History,Scan,Stats,Profile}.jsx`. Компоненты: `Loader`, `EmptyState`.
- API-клиент: `src/services/api.js`. Сейчас пользователь = `device_id` (`web_<uuid>` в localStorage), передаётся в query/form каждого запроса. `API_BASE` из `VITE_API_URL`.
- Шрифт Manrope и токены палитры лендинга — в `src/index.css` через `@theme` (Tailwind v4).
- Иконки интерфейса — `lucide-react`. PWA-иконки с маскотом — `public/icons/`.
- `vercel.json` — остаток от старого плана, можно удалить.

### Backend (`checkmudrets-api/`)
- `main.py` — FastAPI, CORS `allow_origins=["*"]`, роутеры auth/receipts/stats/advice/report, `/health`.
- `services/ocr.py` — промпт для GPT Vision, возвращает магазин, дату, позиции с категориями.
- `services/advisor.py` — советы по экономии + мини-совет после скана.
- `services/reporter.py` — недельный отчёт с изменением к прошлой неделе.
- `database/models.py` — User(id, device_id unique, name, created_at), Receipt(id, user_id, store_name, date, total, raw_text, created_at), Item(id, receipt_id, name, quantity, price, total, category).
- `utils/config.py` — env: `OPENAI_API_KEY`, `OPENAI_MODEL` (gpt-4o-mini), `DATABASE_URL`, `HOST`, `PORT`.
- Swagger: `http://localhost:8000/docs` — источник правды по контракту, если этот файл с ним расходится.

---

## API-контракт (текущий, сверен с `schemas/models.py`)

Все эндпоинты сейчас идентифицируют пользователя по `device_id`.

**POST /auth/register** — JSON `{ device_id, name? }` → `{ id, device_id, name, created_at }`. Это get-or-create, не настоящая регистрация.

**POST /receipts** — multipart: `file` (изображение), `device_id` →
```json
{
  "success": true,
  "receipt": {
    "id": 1, "store_name": "Пятёрочка", "date": "2026-11-20", "total": 1250.5,
    "created_at": "2026-11-20T18:03:00",
    "items": [{ "id": 1, "name": "Молоко", "quantity": 2, "price": 89.9, "total": 179.8, "category": "Молочные" }]
  },
  "mini_advice": "☕ Кофе за 459 руб. — домашний обойдётся в ~30 руб.",
  "error": null
}
```
`mini_advice` может быть пустой строкой/null. При неудачном OCR — `success: false` + `error`.

**GET /receipts?device_id=&limit=10** → `{ receipts: Receipt[], total_count }`. `total_count` — число чеков в ответе с учётом `limit`.

**GET /stats?device_id=&month=YYYY-MM** →
```json
{
  "month": "2026-11", "total_spent": 18420.0, "receipts_count": 15, "average_receipt": 1228.0,
  "by_category": [{ "category": "Продукты", "amount": 8500.0, "percent": 46, "emoji": "🍞" }],
  "largest_purchase": { "name": "Сыр", "amount": 890.0, "category": "Молочные" }
}
```

**GET /advice?device_id=** → `{ advice: string, generated_at }` (текст с эмодзи, несколько строк)

**GET /report?device_id=** → `{ period: {start, end, label}, total_spent, receipts_count, change_pct, change_text, top_categories: [{category, amount, emoji}], summary_text }`

Категории OCR: Продукты, Молочные, Мясо, Овощи/Фрукты, Хлеб, Напитки, Алкоголь, Кофе, Сладости, Снеки, Готовая еда, Бытовая химия, Гигиена, Косметика, Одежда, Электроника, Лекарства, Транспорт, Топливо, Другое. Эмодзи — `utils/formatting.py::CATEGORY_EMOJI`.

### Известные проблемы бэкенда
- Статистика и отчёт определяют период по `Receipt.created_at` (дате сканирования). Дата `Receipt.date` используется для отображения чека и может быть пустой.
- OpenAI API блокирует запросы с российских IP → бэкенд нельзя хостить на российском сервере без прокси.

---

## Дизайн-система (из лендинга)

Лендинг: https://unica12.github.io/startup-group-8/
Исходники: ветка `week14` → `docs/index.html`, `docs/styles.css`, `docs/app.js`.
Посмотреть: `git show origin/week14:docs/styles.css`, `git show origin/week14:docs/index.html`.

> В `styles.css` в конце есть блок `/* Unified typography... */`, который **переопределяет** часть переменных и стили кнопок. Ниже — итоговые значения с учётом переопределений.

### Шрифт
**Manrope** (Google Fonts), веса 400–800 — и для заголовков, и для текста.

### Цвета
```css
--green:        #58CC02;  /* яркий бренд-зелёный: акценты, кнопка «Сфоткать», карточка-баннер */
--green-shadow: #46a302;  /* тень/нажатие яркого зелёного */
--brand:        #2E7D32;  /* основной цвет кнопок (btn-primary), иконки, тёмные блоки */
--brand-hover:  #236327;
--text:         #193C2B;  /* основной цвет текста и заголовков (переопределённый --green-dark) */
--green-light:  #8BE04E;  /* вторичный акцент, графики */
--coin:         #F2D84C;  /* жёлтый — ТОЛЬКО про экономию/деньги */
--coin-text:    #6B5A00;
--bg:           #F7FAF5;  /* фон страницы */
--surface:      #FFFFFF;  /* карточки */
--text-soft:    #506157;  /* параграфы */
--text-muted:   #617568;  /* подписи, теги */
--pill-bg:      #E9F7DC;  /* фон тегов, иконок, ghost-кнопок */
--line:         #DCECD2;  /* бордеры, разделители */
--danger:       #C0392B;  /* ошибки; фон ошибки #FDECEB */
```
Палитра графиков (кольцевая диаграмма лендинга): `#2E7D32`, `#8BE04E`, `#F2D84C`, `#B9CEC0`, далее можно `#58CC02`, `#46A302`.

### Формы и компоненты
- Радиусы: 16px (инпуты, мелкие блоки), 22px (карточки), 28px (крупные блоки), 14px (кнопки), 999px (теги/пилюли).
- **Кнопка primary**: фон `#2E7D32`, белый текст, `font-weight: 800`, `14px`, `padding: 15px 22px`, `radius: 14px`, min-height ~52px. Hover: `#236327`, `translateY(-2px)`, `box-shadow: 0 8px 22px #193c2b1a`.
- **Кнопка secondary**: белый фон, `border: 1px solid #C9D7C9`, текст `--text`.
- **Кнопка ghost**: фон `--pill-bg`, текст `--text`.
- **Карточка**: белый фон, `border: 1px solid var(--line)`, `box-shadow: 0 6px 24px #193c2b03`, `radius: 22px`, `padding: 20–28px`.
- **Тег (section-tag)**: `10px`, `800`, `letter-spacing: .14em`, uppercase, фон `--pill-bg`, цвет `--text-muted`, `padding: 6px 14px`, `radius: 999px`.
- **Инпут**: фон `--bg`, `border: 2px solid var(--bg)`, `radius: 16px`, `padding: 14px 16px`; focus — `border-color: #58CC02`, фон белый. Label: `13.5px`, `800`. Ошибка — `#C0392B`, `12.5px`.
- **Тёмный блок** (как CTA/«решение»): фон `#2E7D32` или `#193C2B`, текст белый, вторичный текст `#CFE9C6`.
- Заголовки: `letter-spacing: -0.045em`, `line-height: 1.15`. Текст: `line-height: 1.65`. Цифры — `font-variant-numeric: tabular-nums`.
- Фокус: `outline: 3px solid #377BDA; outline-offset: 5px` (как на лендинге, для доступности).
- Уважать `prefers-reduced-motion`.

### Референс главного экрана
В `docs/index.html` (секция `.hero-visual`) есть SVG-мокап экрана приложения — **это и есть целевой вид Home**:
- шапка «Мой бюджет»;
- ярко-зелёная (`#58CC02`) карточка «Расходы за <месяц>» с крупной суммой и пилюлей на полупрозрачном белом;
- белая карточка с кольцевой диаграммой по категориям + легенда с процентами;
- «ПОСЛЕДНИЕ ЧЕКИ» — магазин слева, сумма справа;
- плашка совета (фон `#E9F7DC`) с маскотом, текст `#46A302`;
- круглая зелёная кнопка «Сфоткать» с «3D»-тенью (`#46A302` снизу).

### Маскот и логотип
Маскот — чек-свиток с лицом и колпаком мудреца. SVG — в `docs/index.html` (логотип в `.logo-badge`, большой — `.hero-mascot`, также `docs/favicon.svg`). Вынести в компонент `src/components/Mascot.jsx`. Логотип-текст: «Чек» цветом `--text`, «Мудрец» цветом `#58CC02`.

---

## Этапы

### Этап 1 — Редизайн под лендинг
- [x] Подключить Manrope, заменить токены в `src/index.css` на палитру выше.
- [x] Компоненты-примитивы: `Button` (primary/secondary/ghost), `Card`, `Tag`, `Input` — и перевести на них все страницы.
- [x] Home по референсу из мокапа: карточка месяца (данные `/stats`), кольцевая диаграмма (conic-gradient или SVG, без тяжёлых библиотек), последние чеки, плашка совета с маскотом (данные `/report` или последний `mini_advice`).
- [x] BottomNav: светлый фон, активная вкладка `--brand`, кнопка «Скан» — `#58CC02` с тенью `0 5px 0 #46A302`.
- [x] Scan, History, Stats, Profile — в новом стиле; Stats — кольцевая диаграмма вместо/вместе с полосками.
- [x] Маскот на пустых состояниях (EmptyState) и экране загрузки при распознавании.
- [x] Новые PWA-иконки 192/512 (+ maskable) из маскота на зелёном фоне; `theme_color`/`background_color` в `vite.config.js` → `#2E7D32` / `#F7FAF5`.

### Этап 2 — Регистрация
Зависит от решения по хостингу (Этап 4) — **уточни у пользователя перед началом.** Варианты:
- **A (рекомендуется, если БД в Supabase):** Supabase Auth (email + пароль) через `@supabase/supabase-js` на фронте; FastAPI проверяет Supabase JWT (`Authorization: Bearer`) и берёт `user_id` из токена.
- **B:** своя авторизация в FastAPI: `POST /auth/register` (email, пароль, имя, согласия), `POST /auth/login`, `GET /auth/me`; пароли — bcrypt (passlib), токен — JWT (python-jose/pyjwt).

В обоих случаях:
- [ ] Экраны «Регистрация» и «Вход» в стиле лендинга (форма как `.form-card`), валидация, понятные ошибки на русском.
- [ ] На регистрации — **отдельные** чекбоксы согласий (см. Этап 5), без них кнопка неактивна.
- [ ] Неавторизованный пользователь видит только онбординг/вход; токен в localStorage, автологин, выход.
- [ ] Все эндпоинты бэкенда берут пользователя из токена, а не из `device_id`. `device_id` убрать из API.

### Этап 3 — Профиль
- [ ] Аватар с инициалами, имя, email, «С нами с <дата>».
- [ ] Реальная статистика: всего чеков, всего потрачено, любимая категория (добавить эндпоинт `GET /me/summary`, если нужно). **Не показывать «Сэкономлено»** — таких данных нет.
- [ ] Редактирование имени, смена пароля.
- [ ] Ссылки: Политика конфиденциальности, Пользовательское соглашение, О проекте (команда, курс).
- [ ] «Скачать мои данные» (JSON-экспорт) и «Удалить аккаунт» (с подтверждением, каскадно удаляет чеки и позиции).
- [ ] Кнопка установки PWA (`beforeinstallprompt`, уже есть) + подсказка для iOS («Поделиться → На экран Домой»).
- [ ] Выход.

### Этап 4 — Деплой
**Важно: Supabase не умеет запускать FastAPI/Python.** Edge Functions у Supabase — только TypeScript/Deno. Поэтому «бэкенд на Supabase» = одно из:
- **A (рекомендуется, меньше всего переписывать):** Supabase = PostgreSQL (+ Auth). FastAPI хостится отдельно на зарубежном хостинге (Render / Railway / Fly.io), подключается к Supabase Postgres.
  - `DATABASE_URL=postgresql+asyncpg://...` (Supabase → Connect → Session pooler, порт 5432), `asyncpg` вместо `aiosqlite` в `requirements.txt`.
  - Таблицы создавать через `Base.metadata.create_all` на старте или SQL в Supabase.
  - CORS: `allow_origins=["https://unica12.github.io", "http://localhost:5173"]`.
- **B:** переписать бэкенд на Supabase Edge Functions (TS) + прямой доступ к БД с фронта через supabase-js и RLS. Чище, но это полный рерайт — не успеть за пару дней.

Риски, о которых надо помнить:
- Free-tier Supabase засыпает после недели без активности → нужен keep-alive (GitHub Actions cron раз в несколько дней пингует БД/эндпоинт).
- Free-tier Render засыпает → первый запрос ~30–50 сек. Перед защитой «разбудить».
- Из РФ Supabase бывает медленным/нестабильным без VPN — проверить с телефона без VPN до защиты. Если фронт ходит только в FastAPI (вариант A без supabase-js), эта проблема касается только сервера, не пользователя.

**Фронт → GitHub Pages.** Сейчас Pages этого репо уже отдаёт лендинг из ветки `week14` (`/docs`) по адресу `/startup-group-8/`. PWA кладём рядом, не ломая лендинг:
- [ ] PWA по адресу `https://unica12.github.io/startup-group-8/app/`.
- [ ] `vite.config.js`: `base: '/startup-group-8/app/'`; в manifest `start_url` и `scope` → `'/startup-group-8/app/'`; пути к иконкам без ведущего `/` (или с base).
- [ ] GitHub Actions workflow (`.github/workflows/deploy.yml`): собирает PWA, берёт `docs/` лендинга из `week14`, кладёт PWA `dist/` в `app/`, публикует через `actions/deploy-pages`. Источник Pages в настройках репо переключить на «GitHub Actions» (это делает пользователь вручную).
- [ ] `VITE_API_URL` — через GitHub Secrets/Variables в workflow.
- [ ] На лендинге кнопки «Хочу попробовать» можно направить на `/app/` (согласовать с пользователем, правка в ветке `week14`).

### Этап 5 — 152-ФЗ «О персональных данных» (Роскомнадзор)
Делаем по аналогии с проектом МусорВон. Это учебный проект — тексты-шаблоны, но структурно корректные.
- [ ] **Политика обработки ПД** (страница в приложении + ссылка в футере/профиле): оператор, перечень ПД (имя, email, фото чеков и их содержимое, данные об устройстве), цели, правовое основание (согласие), сроки хранения, способы обработки, третьи лица и трансграничная передача (OpenAI — США, Supabase/хостинг — где фактически расположены серверы), права субъекта (доступ, исправление, удаление, отзыв согласия), контакты для обращений.
- [ ] **Пользовательское соглашение.**
- [ ] **Согласие на обработку ПД — отдельным документом и отдельным чекбоксом** (с 01.09.2025 согласие нельзя прятать внутрь политики/соглашения). Отдельный чекбокс — согласие на трансграничную передачу (OpenAI).
- [ ] Таблица `consents` в БД: `user_id, consent_type, document_version, accepted_at, ip/user_agent` — фиксируем факт и версию согласия.
- [ ] Отзыв согласия = удаление аккаунта и всех данных (из Этапа 3); экспорт данных.
- [ ] Фото чеков не хранить после распознавания (сейчас хранится только `raw_text` — проверить и указать в политике).
- [ ] Если в PWA будет аналитика (Яндекс.Метрика, как на лендинге) — cookie-баннер и упоминание в политике.
- [ ] Честно указать в политике/README: формально 152-ФЗ требует хранить ПД граждан РФ первично в РФ (ст. 18 ч. 5), а также уведомлять РКН о трансграничной передаче. Для учебного проекта это отмечаем как известное ограничение; для продакшна нужен российский хостинг БД + уведомление РКН (как сделано для МусорВон).

---

## Текущее состояние
- ✅ Backend написан, работает локально (SQLite).
- ✅ PWA: редизайн 5 экранов завершён, `npm run build` и `npm run lint` проходят. Навигация, загрузка, ошибки, пустые состояния и офлайн-запуск оболочки проверены в Chromium на 375 px.
- ✅ Лендинг задеплоен на GitHub Pages (ветка `week14`).
- ⏳ Регистрация, управление аккаунтом, деплой PWA и API, 152-ФЗ — следующие этапы.

## Команды
Выполни команды в двух терминалах из корня репозитория. Для фронтенда нужен Node.js 20.19+ (ветка 20) или 22.12+.

```bash
# Backend (Python 3.13)
cd checkmudrets-api
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -r requirements.txt
test -f .env || cp .env.example .env
# Заполни OPENAI_API_KEY в .env, затем запусти API.
.venv/bin/python -m uvicorn main:app --reload   # http://localhost:8000/docs
```

```bash
# Frontend
cd checkmudrets-pwa
npm ci
VITE_API_URL=http://localhost:8000 npm run dev   # http://localhost:5173
npm run build
```

Vite слушает локальную сеть. Для проверки с телефона укажи адрес API, доступный с телефона. Для проверки камеры и установки PWA используй HTTPS или localhost.
