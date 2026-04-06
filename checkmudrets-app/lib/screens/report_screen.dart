import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../utils/constants.dart';
import '../utils/formatting.dart';
import '../widgets/loading_widget.dart';

/// Экран недельного отчёта.
class ReportScreen extends StatefulWidget {
  const ReportScreen({super.key});

  @override
  State<ReportScreen> createState() => _ReportScreenState();
}

class _ReportScreenState extends State<ReportScreen> {
  Map<String, dynamic>? _report;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadReport();
  }

  Future<void> _loadReport() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final prefs = await SharedPreferences.getInstance();
      final deviceId = prefs.getString(PrefKeys.deviceId) ?? '';
      final report = await ApiService().getReport(deviceId);
      setState(() {
        _report = report;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Не удалось загрузить отчёт: $e';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Недельный отчёт'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadReport),
        ],
      ),
      body: _loading
          ? const LoadingWidget(message: 'Формирую отчёт...')
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
                            onPressed: _loadReport, child: const Text('Повторить')),
                      ],
                    ),
                  ),
                )
              : _buildContent(),
    );
  }

  Widget _buildContent() {
    final r = _report!;
    final period = r['period'] as Map<String, dynamic>?;
    final periodLabel = period?['label'] as String? ?? '';
    final totalSpent = (r['total_spent'] as num?)?.toDouble() ?? 0;
    final receiptsCount = r['receipts_count'] as int? ?? 0;
    final changePct = (r['change_pct'] as num?)?.toDouble() ?? 0;
    final changeText = r['change_text'] as String? ?? '';
    final topCategories = r['top_categories'] as List<dynamic>? ?? [];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Шапка периода
          Container(
            width: double.infinity,
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
                  '📈 Неделя $periodLabel',
                  style: const TextStyle(color: AppColors.medGray, fontSize: 14),
                ),
                const SizedBox(height: 8),
                Text(
                  formatMoney(totalSpent),
                  style: const TextStyle(
                    color: AppColors.white,
                    fontSize: 32,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '$receiptsCount чеков',
                  style: const TextStyle(color: AppColors.medGray, fontSize: 14),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          // Изменение по сравнению с прошлой неделей
          Container(
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
            child: Row(
              children: [
                Text(
                  changePct > 0 ? '📈' : changePct < 0 ? '📉' : '↔️',
                  style: const TextStyle(fontSize: 28),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    changeText,
                    style: const TextStyle(
                      color: AppColors.darkText,
                      fontSize: 15,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          // Топ категорий
          if (topCategories.isNotEmpty) ...[
            const Text(
              '🏆 Топ категорий',
              style: TextStyle(
                  fontSize: 17, fontWeight: FontWeight.w700, color: AppColors.darkText),
            ),
            const SizedBox(height: 12),
            ...topCategories.asMap().entries.map((entry) {
              final i = entry.key;
              final cat = entry.value as Map<String, dynamic>;
              final medals = ['1️⃣', '2️⃣', '3️⃣'];
              final medal = i < medals.length ? medals[i] : '•';
              final emoji = cat['emoji'] as String? ?? '📦';
              final name = cat['category'] as String? ?? '';
              final amount = (cat['amount'] as num?)?.toDouble() ?? 0;
              return Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.all(14),
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
                    Text(medal, style: const TextStyle(fontSize: 20)),
                    const SizedBox(width: 8),
                    Text(emoji, style: const TextStyle(fontSize: 20)),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(name,
                          style: const TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w500,
                              color: AppColors.darkText)),
                    ),
                    Text(
                      formatMoney(amount),
                      style: const TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 15,
                          color: AppColors.darkBlue),
                    ),
                  ],
                ),
              );
            }),
          ] else
            const Center(
              child: Padding(
                padding: EdgeInsets.all(32),
                child: Text(
                  '📭 Данных за эту неделю нет.\nОтсканируй чеки!',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: AppColors.medGray, fontSize: 15),
                ),
              ),
            ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}
