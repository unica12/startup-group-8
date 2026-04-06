import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../utils/constants.dart';
import '../widgets/loading_widget.dart';

/// Экран персональных советов по экономии.
class AdviceScreen extends StatefulWidget {
  const AdviceScreen({super.key});

  @override
  State<AdviceScreen> createState() => _AdviceScreenState();
}

class _AdviceScreenState extends State<AdviceScreen> {
  String? _advice;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadAdvice();
  }

  Future<void> _loadAdvice() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final prefs = await SharedPreferences.getInstance();
      final deviceId = prefs.getString(PrefKeys.deviceId) ?? '';
      final advice = await ApiService().getAdvice(deviceId);
      setState(() {
        _advice = advice;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Не удалось загрузить советы: $e';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Советы по экономии'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadAdvice),
        ],
      ),
      body: _loading
          ? const LoadingWidget(message: '🤔 Анализирую расходы...')
          : _error != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Text('😕', style: TextStyle(fontSize: 48)),
                        const SizedBox(height: 12),
                        Text(_error!,
                            textAlign: TextAlign.center,
                            style: const TextStyle(color: AppColors.medGray)),
                        const SizedBox(height: 16),
                        ElevatedButton(
                            onPressed: _loadAdvice, child: const Text('Повторить')),
                      ],
                    ),
                  ),
                )
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Заголовок
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: AppColors.green.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: AppColors.green.withOpacity(0.3)),
                        ),
                        child: const Row(
                          children: [
                            Text('💡', style: TextStyle(fontSize: 28)),
                            SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                'Персональные советы на основе ваших расходов за 30 дней',
                                style: TextStyle(
                                    color: AppColors.darkText, fontSize: 14, height: 1.4),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 20),
                      // Текст советов
                      if (_advice != null) ..._buildAdviceBlocks(_advice!),
                    ],
                  ),
                ),
    );
  }

  /// Разбиваем текст советов на отдельные блоки по абзацам.
  List<Widget> _buildAdviceBlocks(String advice) {
    final paragraphs = advice
        .split('\n')
        .map((l) => l.trim())
        .where((l) => l.isNotEmpty)
        .toList();

    return paragraphs.map((p) {
      return Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.white,
          borderRadius: BorderRadius.circular(14),
          boxShadow: [
            BoxShadow(
              color: AppColors.darkBlue.withOpacity(0.05),
              blurRadius: 6,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Text(
          p,
          style: const TextStyle(
            color: AppColors.darkText,
            fontSize: 15,
            height: 1.5,
          ),
        ),
      );
    }).toList();
  }
}
