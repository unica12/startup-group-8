# 🧠 ПРОМПТ ДЛЯ CLAUDE CODE — ЧАСТЬ 2: Flutter-приложение «ЧекМудрец»

## КОНТЕКСТ

Бэкенд (FastAPI) уже работает на http://localhost:8000. Swagger доступен на /docs. Теперь нужно создать Flutter-приложение в папке `checkmudrets-app/`.

**НЕ ТРОГАЙ папки `checkmudrets-bot/`, `checkmudrets-api/` и файл README.md.**

---

## ЗАДАЧА

Создай мобильное приложение на Flutter в папке `checkmudrets-app/`. Приложение общается с FastAPI бэкендом через HTTP. Дизайн — чистый, минималистичный, тёмно-синий (#0A2540) + зелёный (#00C853) + белый.

---

## ЭКРАНЫ ПРИЛОЖЕНИЯ

### 1. Экран приветствия (Onboarding) — показывается один раз
- Логотип «ЧекМудрец» (зелёный кошелёк с камерой — можно иконкой)
- Слоган: «Фоткай чек — ИИ покажет, куда уходят деньги»
- Поле ввода имени (необязательное)
- Кнопка «Начать» → регистрация по device_id → переход на главный экран

### 2. Главный экран (Home)
- Вверху: приветствие «Привет, Андрей!» + сумма за текущий месяц
- По центру: большая кнопка «📸 Сканировать чек» (открывает камеру)
- Внизу: навигация (4 таба):
  - 🏠 Главная
  - 📊 Статистика
  - 📋 История
  - 👤 Профиль

### 3. Экран сканирования чека
- Открывается камера телефона
- Пользователь фоткает чек
- Показывается лоадер: «🔍 Распознаю чек...»
- POST /receipts → получаем результат
- Показываем результат:
  - Магазин, дата, итого
  - Список позиций с категориями и эмодзи
  - Мини-совет (если есть)
  - Кнопка «🏠 На главную»

### 4. Экран статистики
- GET /stats → показываем:
  - Сумма за месяц (большая цифра)
  - Количество чеков
  - Круговая диаграмма по категориям (используй fl_chart)
  - Список категорий с суммами и процентами
  - Средний чек

### 5. Экран истории
- GET /receipts → список чеков
- Каждый чек — карточка: магазин, дата, сумма
- Нажатие → детали чека (позиции)

### 6. Экран профиля
- Имя пользователя
- Чеков отсканировано (всего)
- Потрачено за всё время
- Кнопка «💡 Советы по экономии» → GET /advice → показать советы
- Кнопка «📈 Недельный отчёт» → GET /report → показать отчёт

---

## ЦВЕТОВАЯ СХЕМА

```dart
// lib/theme/colors.dart
class AppColors {
  static const darkBlue = Color(0xFF0A2540);
  static const green = Color(0xFF00C853);
  static const white = Color(0xFFFFFFFF);
  static const offWhite = Color(0xFFF5F7FA);
  static const lightGray = Color(0xFFE8ECF0);
  static const medGray = Color(0xFF94A3B8);
  static const darkText = Color(0xFF1E293B);
}
```

Тема: светлый фон, тёмно-синий AppBar, зелёные акценты (кнопки, индикаторы, бейджи категорий).

---

## СТРУКТУРА ПРОЕКТА

```
checkmudrets-app/
├── lib/
│   ├── main.dart                    # Точка входа
│   ├── theme/
│   │   └── app_theme.dart           # Тема, цвета, шрифты
│   ├── models/
│   │   ├── user.dart                # Модель пользователя
│   │   ├── receipt.dart             # Модель чека
│   │   ├── item.dart                # Модель позиции
│   │   └── stats.dart               # Модель статистики
│   ├── services/
│   │   └── api_service.dart         # HTTP-клиент к FastAPI
│   ├── screens/
│   │   ├── onboarding_screen.dart   # Приветствие
│   │   ├── home_screen.dart         # Главный экран
│   │   ├── scan_screen.dart         # Сканирование чека
│   │   ├── scan_result_screen.dart  # Результат скана
│   │   ├── stats_screen.dart        # Статистика
│   │   ├── history_screen.dart      # История чеков
│   │   ├── receipt_detail_screen.dart # Детали чека
│   │   ├── profile_screen.dart      # Профиль
│   │   ├── advice_screen.dart       # Советы
│   │   └── report_screen.dart       # Отчёт
│   ├── widgets/
│   │   ├── category_badge.dart      # Бейдж категории с эмодзи
│   │   ├── receipt_card.dart        # Карточка чека в истории
│   │   ├── stat_card.dart           # Карточка статистики
│   │   └── loading_widget.dart      # Лоадер с анимацией
│   └── utils/
│       ├── constants.dart           # API_URL, эмодзи-маппинг
│       └── formatting.dart          # Форматирование сумм
├── pubspec.yaml
└── ...
```

---

## ЗАВИСИМОСТИ (pubspec.yaml)

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.2.0              # HTTP-запросы к API
  image_picker: ^1.0.7      # Камера / галерея
  fl_chart: ^0.68.0         # Круговая диаграмма
  shared_preferences: ^2.2.2 # Хранение device_id и имени
  uuid: ^4.3.3              # Генерация device_id
  intl: ^0.19.0             # Форматирование дат и чисел
```

---

## API SERVICE

```dart
// lib/services/api_service.dart

class ApiService {
  // Для эмулятора Android используй 10.0.2.2 вместо localhost
  static const String baseUrl = 'http://10.0.2.2:8000';
  // Для реального телефона в той же Wi-Fi сети: http://192.168.X.X:8000
  
  // POST /auth/register
  Future<Map<String, dynamic>> register(String deviceId, String? name);
  
  // POST /receipts (multipart с фото)
  Future<Map<String, dynamic>> uploadReceipt(String deviceId, File imageFile);
  
  // GET /receipts?device_id=...&limit=10
  Future<List<Map<String, dynamic>>> getReceipts(String deviceId, {int limit = 10});
  
  // GET /stats?device_id=...&month=2026-04
  Future<Map<String, dynamic>> getStats(String deviceId, {String? month});
  
  // GET /advice?device_id=...
  Future<String> getAdvice(String deviceId);
  
  // GET /report?device_id=...
  Future<String> getReport(String deviceId);
}
```

---

## ЭМОДЗИ-МАППИНГ ДЛЯ КАТЕГОРИЙ

```dart
const categoryEmoji = {
  'Продукты': '🍞', 'Молочные': '🥛', 'Мясо': '🥩',
  'Овощи/Фрукты': '🥬', 'Хлеб': '🍞', 'Напитки': '🧃',
  'Алкоголь': '🍷', 'Кофе': '☕', 'Сладости': '🍬',
  'Снеки': '🍿', 'Готовая еда': '🥡', 'Бытовая химия': '🧹',
  'Гигиена': '🧴', 'Косметика': '💄', 'Одежда': '👕',
  'Электроника': '📱', 'Лекарства': '💊', 'Транспорт': '🚗',
  'Топливо': '⛽', 'Другое': '📦',
};
```

---

## ДИЗАЙН-ПРИМЕРЫ

### Главный экран
```
┌─────────────────────────────┐
│  ЧекМудрец         👤       │  ← AppBar тёмно-синий
├─────────────────────────────┤
│                             │
│  Привет, Андрей! 👋         │
│                             │
│  Апрель 2026               │
│  ┌─────────────────────┐   │
│  │   34 520 ₽           │   │  ← Карточка с суммой
│  │   23 чека             │   │
│  └─────────────────────┘   │
│                             │
│  ┌─────────────────────┐   │
│  │   📸 Сканировать      │   │  ← Большая зелёная кнопка
│  │      чек              │   │
│  └─────────────────────┘   │
│                             │
│  Последние чеки:            │
│  ┌─ Пятёрочка  1 847₽ ──┐  │
│  ├─ Wildberries 3 200₽ ─┤  │
│  └─ Лавка       890₽ ──┘  │
│                             │
├──────┬───────┬──────┬──────┤
│ 🏠   │ 📊    │ 📋   │ 👤   │  ← Bottom Navigation
│Главная│Стат. │Истор.│Проф. │
└──────┴───────┴──────┴──────┘
```

### Результат скана
```
┌─────────────────────────────┐
│  ← Результат скана          │
├─────────────────────────────┤
│  ✅ Чек распознан!           │
│                             │
│  🏪 Пятёрочка               │
│  📅 05.04.2026              │
│  💰 1 847 ₽                 │
│                             │
│  ─────────────────────      │
│  🍞 Хлеб белый      65 ₽   │
│  🥛 Молоко 1л       89 ₽   │
│  ☕ Кофе раствор.   459 ₽   │
│  🧴 Шампунь        312 ₽   │
│  🍕 Пицца заморож. 289 ₽   │
│  ─────────────────────      │
│                             │
│  💡 Кофе за 459 ₽ — домашний│
│  обойдётся в ~30 ₽/чашку.  │
│                             │
│  [    🏠 На главную    ]    │
└─────────────────────────────┘
```

---

## ВАЖНЫЕ ТРЕБОВАНИЯ

1. Используй `image_picker` для камеры — `ImageSource.camera` по умолчанию, с фоллбэком на `ImageSource.gallery`
2. Все HTTP-вызовы обёрнуты в try/catch — при ошибке показывай SnackBar
3. Лоадер при загрузке данных — CircularProgressIndicator в зелёном цвете
4. Форматирование сумм: `1847.50` → `1 847 ₽` (используй intl NumberFormat)
5. device_id генерируется при первом запуске через uuid и сохраняется в SharedPreferences
6. API URL — вынести в константу, легко менять между localhost / продакшн
7. **НЕ ТРОГАЙ README.md, checkmudrets-bot/, checkmudrets-api/**
8. Комментарии на русском

---

## ЗАПУСК

```bash
cd checkmudrets-app
flutter pub get
flutter run
```

---

Создай все файлы. Начни с models/, затем services/, затем widgets/, затем screens/, затем main.dart.
