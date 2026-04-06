import 'package:flutter/material.dart';
import '../models/receipt.dart';
import '../theme/app_theme.dart';
import '../utils/formatting.dart';

/// Карточка чека — используется в списке истории и на главном экране.
class ReceiptCard extends StatelessWidget {
  final Receipt receipt;
  final VoidCallback? onTap;

  const ReceiptCard({super.key, required this.receipt, this.onTap});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        onTap: onTap,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        leading: Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            color: AppColors.green.withOpacity(0.12),
            borderRadius: BorderRadius.circular(12),
          ),
          child: const Center(
            child: Text('🧾', style: TextStyle(fontSize: 22)),
          ),
        ),
        title: Text(
          receipt.storeName?.isNotEmpty == true ? receipt.storeName! : 'Магазин',
          style: const TextStyle(
            fontWeight: FontWeight.w600,
            fontSize: 15,
            color: AppColors.darkText,
          ),
        ),
        subtitle: Text(
          formatDate(receipt.date),
          style: const TextStyle(color: AppColors.medGray, fontSize: 13),
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              formatMoney(receipt.total),
              style: const TextStyle(
                fontWeight: FontWeight.w700,
                fontSize: 15,
                color: AppColors.darkBlue,
              ),
            ),
            Text(
              '${receipt.items.length} поз.',
              style: const TextStyle(color: AppColors.medGray, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}
