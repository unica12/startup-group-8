import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../utils/constants.dart';

/// Бейдж категории с эмодзи — зелёный чип.
class CategoryBadge extends StatelessWidget {
  final String category;
  final bool small;

  const CategoryBadge({super.key, required this.category, this.small = false});

  @override
  Widget build(BuildContext context) {
    final emoji = getEmoji(category);
    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: small ? 8 : 10,
        vertical: small ? 3 : 5,
      ),
      decoration: BoxDecoration(
        color: AppColors.green.withOpacity(0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.green.withOpacity(0.3)),
      ),
      child: Text(
        '$emoji $category',
        style: TextStyle(
          color: AppColors.darkBlue,
          fontSize: small ? 11 : 13,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }
}
