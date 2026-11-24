# ЧекМудрец — PWA трекер расходов по фото чека

Курсовой проект РТУ МИРЭА, курс «Стартап в информационных технологиях», группа ЭФБО-06-23, команда №8.
Команда: Земсков А.В., Викторов А.Д., Демидов И.С.
Репозиторий: https://github.com/unica12/startup-group-8
Дедлайн: сжатый (пара дней) — приоритет на рабочий результат, а не на идеальную архитектуру.

Пользователь фотографирует чек → GPT-4o-mini Vision распознаёт товары → траты раскладываются по категориям → приложение показывает статистику и советы по экономии.

Согласованная архитектура — React 19/Vite/Tailwind CSS v4, FastAPI с асинхронным SQLAlchemy, PostgreSQL и Auth в Supabase (`checkmudrets`, Stockholm, eu-north-1). План размещения — FastAPI на Render, PWA на GitHub Pages рядом с лендингом.

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
├── checkmudrets-api/       # FastAPI + async SQLAlchemy + asyncpg, SQLite для тестов
├── checkmudrets-app/       # ЛЕГАСИ (Flutter), не трогать
└── CLAUDE1.md
```

### Frontend (`checkmudrets-pwa/`)
- Навигация без react-router: состояние `page` в `src/App.jsx` + `src/components/BottomNav.jsx` (5 вкладок: Главная, История, Скан, Статистика, Профиль; «Скан» — поднятая круглая кнопка).
- Страницы: `src/pages/{Home,History,Scan,Stats,Profile}.jsx`. Компоненты: `Loader`, `EmptyState`.
- `src/auth/` закрывает основные экраны до восстановления сессии и фиксации согласий. Supabase SDK хранит и обновляет сессию.
- `src/services/supabase.js` использует `VITE_SUPABASE_URL` и `VITE_SUPABASE_PUBLISHABLE_KEY`. `src/services/api.js` передаёт Bearer-токен на `VITE_API_URL`. Service worker кэширует файлы приложения, защищённые ответы загружаются с сервера.
- Шрифт Manrope и токены палитры лендинга — в `src/index.css` через `@theme` (Tailwind v4).
- Иконки интерфейса — `lucide-react`. PWA-иконки с маскотом — `public/icons/`.
- `vercel.json` — остаток от старого плана, можно удалить.

### Backend (`checkmudrets-api/`)
- `main.py` — FastAPI, CORS `allow_origins=["*"]`, роутеры auth/receipts/stats/advice/report, `/health`.
- `services/ocr.py` — промпт для GPT Vision, возвращает магазин, дату, позиции с категориями.
- `services/advisor.py` — советы по экономии + мини-совет после скана.
- `services/reporter.py` — недельный отчёт с изменением к прошлой неделе.
- `database/models.py` — User(id, auth_user_id UUID unique, name, created_at), Receipt, Item, Consent. Внешние ключи чеков и позиций используют прежние целочисленные ID.
- `database/db.py` подключается к PostgreSQL с проверкой сертификата и имени хоста. На старте создаёт таблицы, добавляет недостающий UUID в существующую `users`, включает RLS и отзывает права Data API для прикладных таблиц и их последовательностей. Старые строки остаются в базе без привязки к новым сессиям. SQLite используется для изолированных тестов.
- `services/auth.py` проверяет JWT по JWKS Supabase, включая подпись, issuer, audience, срок действия и `sub`. API привязывает данные к проверенному UUID.
- `utils/config.py` читает `OPENAI_API_KEY`, `OPENAI_MODEL`, `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_DB_CA_FILE`, `HOST`, `PORT`. У Session pooler URL проекта определяется из имени пользователя БД, если `SUPABASE_URL` опущен. `SUPABASE_JWT_SECRET` используется только при явной поддержке legacy HS256 на сервере. Для `checkmudrets` JWKS публикует ES256.
- Swagger: `http://localhost:8000/docs` — источник правды по контракту, если этот файл с ним расходится.

---

## API-контракт (текущий, сверен с `schemas/models.py`)

Для `/auth/me`, `/auth/consents`, `/receipts`, `/stats`, `/advice` и `/report` нужен `Authorization: Bearer <access_token>` из Supabase Auth. При отсутствующем, неверном или просроченном токене API возвращает `401`. Для операций с расходами без обязательных согласий API возвращает `403` с кодом `consents_required`.

**GET /auth/me** — идемпотентно создаёт прикладной профиль и возвращает `{ id, name, email, created_at, consents_complete }`. Вход и регистрация выполняются через Supabase Auth.

**POST /auth/consents** — принимает `{ "consents": { "terms": "prototype-1", "personal_data": "prototype-1", "cross_border": "prototype-1" } }` и возвращает профиль. Сохраняет тип, версию, дату принятия, IP и User-Agent. Повторная отправка той же версии не дублирует согласия. Неполный или устаревший набор даёт `422`.

**POST /receipts** — multipart с единственным полем `file` (изображение) →
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

**GET /receipts?limit=10** → `{ receipts: Receipt[], total_count }`. `total_count` — число чеков в ответе с учётом `limit` от 1 до 100.

**GET /stats?month=YYYY-MM** →
```json
{
  "month": "2026-11", "total_spent": 18420.0, "receipts_count": 15, "average_receipt": 1228.0,
  "by_category": [{ "category": "Продукты", "amount": 8500.0, "percent": 46, "emoji": "🍞" }],
  "largest_purchase": { "name": "Сыр", "amount": 890.0, "category": "Молочные" }
}
```

**GET /advice** → `{ advice: string, generated_at }` (текст с эмодзи, несколько строк)

**GET /report** → `{ period: {start, end, label}, total_spent, receipts_count, change_pct, change_text, top_categories: [{category, amount, emoji}], summary_text }`

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
- [x] Экраны «Регистрация» и «Вход» в дизайн-системе лендинга. Имя, email, повтор и показ пароля, валидация и ошибки на русском.
- [x] Три отдельных обязательных чекбокса и просмотр предварительных документов. Согласия фиксируются после проверки сессии, включая вход после подтверждения email с другого устройства.
- [x] Supabase Auth с восстановлением и обновлением сессии, подтверждением email и выходом. Закрытые экраны и нижняя навигация доступны после подтверждения согласий.
- [x] FastAPI проверяет Bearer JWT с кешированием и обновлением JWKS. Добавлены идемпотентный профиль по UUID и `GET /auth/me`. Идентификация по `device_id` удалена из API и PWA.
- [x] Подключение к Supabase PostgreSQL через Session pooler с проверкой TLS, сохранение связей чеков и позиций, идемпотентная инициализация, RLS и ограничение прав Data API. Сохранены автотесты на SQLite.
- [x] Изоляция двух аккаунтов, сохранение чеков и согласий, JWT, вход, сессия и верстка 375 px проверены на локальном Supabase с PostgreSQL и почтовой песочницей. Подключение и права таблиц проверены также в облачном проекте.
- [ ] Финальная проверка доставки писем подтверждения в облачном проекте на адрес участника команды.

### Этап 3 — Профиль
- [ ] Аватар с инициалами, имя, email, «С нами с <дата>».
- [ ] Реальная статистика: всего чеков, всего потрачено, любимая категория (добавить эндпоинт `GET /me/summary`, если нужно). **Не показывать «Сэкономлено»** — таких данных нет.
- [ ] Редактирование имени, смена пароля.
- [ ] Ссылки: Политика конфиденциальности, Пользовательское соглашение, О проекте (команда, курс).
- [ ] «Скачать мои данные» (JSON-экспорт) и «Удалить аккаунт» (с подтверждением, каскадно удаляет чеки и позиции).
- [ ] Кнопка установки PWA (`beforeinstallprompt`, уже есть) + подсказка для iOS («Поделиться → На экран Домой»).
- [x] Выход реализован в Этапе 2.

### Этап 4 — Деплой
FastAPI будет размещён на Render и подключён к уже подготовленному PostgreSQL через Session pooler (порт 5432) с проверкой TLS. PWA будет размещена на GitHub Pages и будет обращаться к Supabase Auth и FastAPI.
- [ ] Настроить переменные окружения Render, включая путь к CA, и проверить запуск приложения.
- [ ] Ограничить CORS адресами опубликованной PWA и локальной разработки.

Риски, о которых надо помнить:
- Free-tier Supabase засыпает после недели без активности → нужен keep-alive (GitHub Actions cron раз в несколько дней пингует БД/эндпоинт).
- Free-tier Render засыпает → первый запрос ~30–50 сек. Перед защитой «разбудить».
- Проверить доступность Supabase Auth, FastAPI и распознавания на устройстве, которое будет использоваться на защите.

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
- [x] Таблица `consents` и фиксация принятия предварительных документов реализованы в Этапе 2.
- [ ] Отзыв согласия = удаление аккаунта и всех данных (из Этапа 3); экспорт данных.
- [ ] Фото чеков не хранить после распознавания (сейчас хранится только `raw_text` — проверить и указать в политике).
- [ ] Если в PWA будет аналитика (Яндекс.Метрика, как на лендинге) — cookie-баннер и упоминание в политике.
- [ ] Честно указать в политике/README: формально 152-ФЗ требует хранить ПД граждан РФ первично в РФ (ст. 18 ч. 5), а также уведомлять РКН о трансграничной передаче. Для учебного проекта это отмечаем как известное ограничение; для продакшна нужен российский хостинг БД + уведомление РКН (как сделано для МусорВон).

---

## Текущее состояние
- ✅ Backend подключён к Supabase PostgreSQL. SQLite используется в автоматизированных тестах.
- ✅ PWA: редизайн 5 экранов завершён, `npm run build` и `npm run lint` проходят. Навигация, загрузка, ошибки, пустые состояния и офлайн-запуск оболочки проверены в Chromium на 375 px.
- ✅ Вход, регистрация и согласия реализованы и проверены в Chromium с локальными Supabase Auth, Mailpit и PostgreSQL. Для OCR и советов в этой проверке подставлялись ответы OpenAI. Реальное распознавание было проверено командой на Этапе 1.
- ✅ Лендинг задеплоен на GitHub Pages (ветка `week14`).
- ⏳ Управление аккаунтом, деплой PWA и API, окончательные документы — следующие этапы.

## Настройки Supabase Dashboard

1. В проекте `checkmudrets` открой **Connect** и скопируй Project URL. Добавь его в `checkmudrets-pwa/.env` как `VITE_SUPABASE_URL`. В **Project Settings → API Keys → Publishable key** возьми `sb_publishable_…` для `VITE_SUPABASE_PUBLISHABLE_KEY`. [API keys](https://supabase.com/docs/guides/getting-started/api-keys)
2. В **Connect → Session pooler** скопируй строку подключения с портом `5432` в `checkmudrets-api/.env` как `DATABASE_URL`. Замени весь плейсхолдер пароля вместе со скобками. Специальные символы пароля в URI должны быть URL-кодированы. В **Database → Settings → SSL Configuration → Download certificate** скачай сертификат и укажи локальный путь в `SUPABASE_DB_CA_FILE`. [Postgres и SSL](https://supabase.com/docs/guides/database/connecting-to-postgres)
3. В **Authentication → Sign In / Providers** оставь включённым Allow new users to sign up. В разделе **Email** включи Email и Confirm Email. В **Authentication → URL Configuration** установи Site URL `http://localhost:5173/` для локальной демонстрации и добавь этот же точный адрес в Redirect URLs. Если открываешь PWA по `http://127.0.0.1:5173/`, добавь и этот адрес. Адрес GitHub Pages добавляется на Этапе 4. [Настройки Auth](https://supabase.com/docs/guides/auth/general-configuration)
4. Для проверки письма в облачном проекте используй адрес участника команды проекта. Для демонстрации регистрации на сторонние адреса настрой **Authentication → SMTP Settings**. Встроенная отправка ограничена адресами участников команды. [Настройка SMTP](https://supabase.com/docs/guides/auth/auth-smtp)
5. Если проект используется только ЧекМудрецом, можно отключить весь Data API через **Integrations → Data API → Enable Data API**. Прикладные таблицы уже закрыты правами и RLS при запуске FastAPI. [Доступ к таблицам](https://supabase.com/docs/guides/api/securing-your-api)

## Команды
Выполни команды в двух терминалах из корня репозитория. Для фронтенда нужен Node.js 22.12+.

```bash
# Backend (Python 3.13)
cd checkmudrets-api
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -r requirements.txt
test -f .env || cp .env.example .env
# Заполни OPENAI_API_KEY, DATABASE_URL и путь к CA в .env.
.venv/bin/python -m uvicorn main:app --reload   # http://localhost:8000/docs
```

```bash
# Frontend
cd checkmudrets-pwa
npm ci
test -f .env || cp .env.example .env
# Заполни URL и publishable key Supabase в .env.
VITE_API_URL=http://localhost:8000 npm run dev -- --strictPort   # http://localhost:5173
npm run build
npm run lint
```

Автотесты FastAPI создают временную SQLite и локальный JWKS. Они проверяют проверку JWT, ротацию ключей, отсутствие дубликатов, согласия и изоляцию чеков, статистики, советов и отчётов.

```bash
cd checkmudrets-api
uv pip install --python .venv/bin/python -r requirements-test.txt
.venv/bin/python -m unittest discover -s tests -v
```

Vite слушает локальную сеть. Для проверки с телефона укажи адрес API, доступный с телефона. Для проверки камеры и установки PWA используй HTTPS или localhost.
