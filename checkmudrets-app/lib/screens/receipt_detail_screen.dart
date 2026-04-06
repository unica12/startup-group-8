import 'package:flutter/material.dart';

import '../models/receipt.dart';
import '../theme/app_theme.dart';
import '../utils/constants.dart';
import '../utils/formatting.dart';
import '../widgets/category_badge.dart';

/// Детальный просмотр чека — все позиции с категориями.
class ReceiptDetailScreen extends StatelessWidget {
  final Receipt receipt;

  const ReceiptDetailScreen({super.key, required this.receipt});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(receipt.storeName?.isNotEmpty == true ? receipt.storeName! : 'Чек'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Шапка чека
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [AppColors.darkBlue, Color(0xFF1A4A7A)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  receipt.storeName?.isNotEmpty == true ? receipt.storeName! : 'Магазин',
                  style: const TextStyle(
                    color: AppColors.white,
                    fontSize: 22,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  '📅 ${formatDate(receipt.date)}',
                  style: const TextStyle(color: AppColors.medGray, fontSize: 14),
                ),
                const SizedBox(height: 12),
                Text(
                  formatMoney(receipt.total),
                  style: const TextStyle(
                    color: AppColors.green,
                    fontSize: 32,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          Text(
            'Позиции (${receipt.items.length})',
            style: const TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w700,
              color: AppColors.darkText,
            ),
          ),
          const SizedBox(height: 8),
          // Список позиций
          ...receipt.items.map((item) {
            final emoji = getEmoji(item.category);
            return Container(
              margin: const EdgeInsets.symmetric(vertical: 4),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              decoration: BoxDecoration(
                color: AppColors.white,
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(
                    color: AppColors.darkBlue.withOpacity(0.04),
                    blurRadius: 4,
                    offset: const Offset(0, 1),
                  ),
                ],
              ),
              child: Row(
                children: [
                  Text(emoji, style: const TextStyle(fontSize: 22)),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item.name,
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                            color: AppColors.darkText,
                          ),
                        ),
                        const SizedBox(height: 4),
                        CategoryBadge(category: item.category, small: true),
                        if (item.quantity != 1.0)
                          Text(
                            '${item.quantity} × ${formatMoney(item.price)}',
                            style: const TextStyle(color: AppColors.medGray, fontSize: 12),
                          ),
                      ],
                    ),
                  ),
                  Text(
                    formatMoney(item.total),
                    style: const TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 15,
                      color: AppColors.darkText,
                    ),
                  ),
                ],
              ),
            );
          }),
          const SizedBox(height: 12),
          const Divider(),
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('ИТОГО',
                    style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
                Text(
                  formatMoney(receipt.total),
                  style: const TextStyle(
                    fontWeight: FontWeight.w800,
                    fontSize: 20,
                    color: AppColors.darkBlue,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}
