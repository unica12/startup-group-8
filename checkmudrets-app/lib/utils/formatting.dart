import 'package:intl/intl.dart';

/// Форматировать сумму: 1847.5 → «1 847 ₽»
String formatMoney(double amount) {
  final formatter = NumberFormat('#,##0', 'ru_RU');
  return '${formatter.format(amount.round())} ₽';
}

/// Форматировать дату для отображения: DateTime → «05.04.2026»
String formatDate(DateTime? date) {
  if (date == null) return '—';
  return DateFormat('dd.MM.yyyy').format(date);
}

/// Форматировать месяц по-русски: «2026-04» → «Апрель 2026»
String formatMonthLabel(String month) {
  try {
    final parsed = DateFormat('yyyy-MM').parse(month);
    return DateFormat('MMMM yyyy', 'ru_RU').format(parsed);
  } catch (_) {
    return month;
  }
}

/// Текущий месяц в формате «YYYY-MM»
String currentMonthParam() {
  return DateFormat('yyyy-MM').format(DateTime.now());
}
