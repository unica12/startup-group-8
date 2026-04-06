import 'package:flutter/foundation.dart';

/// Константы приложения.
class ApiConstants {
  // Для Android-эмулятора: 10.0.2.2 = localhost хоста
  // Для реального телефона в той же сети: замени на IP-адрес компьютера
  static const String baseUrl = String.fromEnvironment(
    'API_URL',
    defaultValue: kIsWeb ? 'http://localhost:8000' : 'http://10.0.2.2:8000',
  );

  static const timeout = Duration(seconds: 30);
  static const uploadTimeout = Duration(seconds: 120); // OCR занимает время
}

/// Маппинг категорий на эмодзи.
const Map<String, String> categoryEmoji = {
  'Продукты': '🍞',
  'Молочные': '🥛',
  'Мясо': '🥩',
  'Овощи/Фрукты': '🥬',
  'Хлеб': '🍞',
  'Напитки': '🧃',
  'Алкоголь': '🍷',
  'Кофе': '☕',
  'Сладости': '🍬',
  'Снеки': '🍿',
  'Готовая еда': '🥡',
  'Доставка еды': '🛵',
  'Кафе/Рестораны': '🍕',
  'Бытовая химия': '🧹',
  'Гигиена': '🧴',
  'Косметика': '💄',
  'Одежда': '👕',
  'Обувь': '👟',
  'Электроника': '📱',
  'Техника': '🔧',
  'Лекарства': '💊',
  'Транспорт': '🚗',
  'Топливо': '⛽',
  'Подписки': '📺',
  'Развлечения': '🎮',
  'Другое': '📦',
};

/// Получить эмодзи для категории (с фоллбэком).
String getEmoji(String category) => categoryEmoji[category] ?? '📦';

/// Ключи SharedPreferences.
class PrefKeys {
  static const deviceId = 'device_id';
  static const userName = 'user_name';
  static const userId = 'user_id';
  static const onboardingDone = 'onboarding_done';
}
