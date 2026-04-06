import 'package:flutter/material.dart';

import '../models/item.dart';
import '../models/receipt.dart';
import '../theme/app_theme.dart';
import '../utils/constants.dart';
import '../utils/formatting.dart';
import '../widgets/category_badge.dart';
import 'home_screen.dart';

/// Экран результата распознавания чека.
class ScanResultScreen extends StatelessWidget {
  final Map<String, dynamic> result;

  const ScanResultScreen({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    final success = result['success'] as bool? ?? false;
    final error = result['error'] as String?;

    if (!success) {
      return _ErrorScreen(message: error ?? 'Не удалось распознать чек');
    }

    final receiptJson = result['receipt'] as Map<String, dynamic>?;
    final miniAdvice = result['mini_advice'] as String?;

    if (receiptJson == null) {
      return const _ErrorScreen(message: 'Данные чека отсутствуют');
    }

    final receipt = Receipt.fromJson(receiptJson);

    return Scaffold(
      appBar: AppBar(title: const Text('Результат скана')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Заголовок успеха
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.green.withOpacity(0.1),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.green.withOpacity(0.3)),
            ),
            child: const Row(
              children: [
                Text('✅', style: TextStyle(fontSize: 24)),
                SizedBox(width: 12),
                Text(
                  'Чек распознан!',
                  style: TextStyle(
                    color: AppColors.darkText,
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          // Информация о чеке
          _InfoRow(emoji: '🏪', label: 'Магазин', value: receipt.storeName ?? '—'),
          _InfoRow(emoji: '📅', label: 'Дата', value: formatDate(receipt.date)),
          _InfoRow(emoji: '💰', label: 'Итого', value: formatMoney(receipt.total), bold: true),
          const SizedBox(height: 16),
          const Divider(),
          const SizedBox(height: 8),
          // Список позиций
          const Text(
            'Позиции',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w700,
              color: AppColors.darkText,
            ),
          ),
          const SizedBox(height: 8),
          ...receipt.items.map((item) => _ItemRow(item: item)),
          const Divider(),
          const SizedBox(height: 8),
          // Итого снизу
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('ИТОГО',
                  style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
              Text(
                formatMoney(receipt.total),
                style: const TextStyle(
                  fontWeight: FontWeight.w800,
                  fontSize: 18,
                  color: AppColors.darkBlue,
                ),
              ),
            ],
          ),
          // Мини-совет
          if (miniAdvice != null && miniAdvice.isNotEmpty) ...[
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.darkBlue.withOpacity(0.05),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppColors.darkBlue.withOpacity(0.12)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('💡', style: TextStyle(fontSize: 20)),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      miniAdvice,
                      style: const TextStyle(
                        color: AppColors.darkText,
                        fontSize: 14,
                        height: 1.4,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 24),
          // Кнопка на главную
          ElevatedButton(
            onPressed: () => Navigator.of(context).pushAndRemoveUntil(
              MaterialPageRoute(builder: (_) => const HomeScreen()),
              (route) => false,
            ),
            child: const Text('🏠  На главную'),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String emoji;
  final String label;
  final String value;
  final bool bold;

  const _InfoRow({
    required this.emoji,
    required this.label,
    required this.value,
    this.bold = false,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Text(emoji, style: const TextStyle(fontSize: 18)),
          const SizedBox(width: 10),
          Text('$label: ', style: const TextStyle(color: AppColors.medGray)),
          Expanded(
            child: Text(
              value,
              style: TextStyle(
                fontWeight: bold ? FontWeight.w700 : FontWeight.w500,
                fontSize: bold ? 17 : 15,
                color: AppColors.darkText,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ItemRow extends StatelessWidget {
  final Item item;

  const _ItemRow({required this.item});

  @override
  Widget build(BuildContext context) {
    final emoji = getEmoji(item.category);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        children: [
          Text(emoji, style: const TextStyle(fontSize: 18)),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.name,
                    style: const TextStyle(fontSize: 14, color: AppColors.darkText)),
                CategoryBadge(category: item.category, small: true),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Text(
            formatMoney(item.total),
            style: const TextStyle(
              fontWeight: FontWeight.w600,
              fontSize: 14,
              color: AppColors.darkText,
            ),
          ),
        ],
      ),
    );
  }
}

class _ErrorScreen extends StatelessWidget {
  final String message;

  const _ErrorScreen({required this.message});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Ошибка')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('😕', style: TextStyle(fontSize: 64)),
            const SizedBox(height: 16),
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 16, color: AppColors.darkText),
            ),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Попробовать снова'),
            ),
          ],
        ),
      ),
    );
  }
}
