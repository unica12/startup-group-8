import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Лоадер с текстом — используется при запросах к API.
class LoadingWidget extends StatelessWidget {
  final String message;

  const LoadingWidget({super.key, this.message = 'Загрузка...'});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const CircularProgressIndicator(color: AppColors.green, strokeWidth: 3),
          const SizedBox(height: 16),
          Text(
            message,
            style: const TextStyle(
              color: AppColors.medGray,
              fontSize: 15,
            ),
          ),
        ],
      ),
    );
  }
}
