import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/stats.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../utils/constants.dart';
import '../utils/formatting.dart';
import '../widgets/loading_widget.dart';

/// Экран статистики расходов за месяц.
class StatsScreen extends StatefulWidget {
  const StatsScreen({super.key});

  @override
  State<StatsScreen> createState() => _StatsScreenState();
}

class _StatsScreenState extends State<StatsScreen> {
  Stats? _stats;
  bool _loading = true;
  String? _error;
  int _touchedIndex = -1;

  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  Future<void> _loadStats() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final prefs = await SharedPreferences.getInstance();
      final deviceId = prefs.getString(PrefKeys.deviceId) ?? '';
      final stats = await ApiService().getStats(deviceId);
      setState(() {
        _stats = stats;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Ошибка загрузки: $e';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Статистика'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadStats),
        ],
      ),
      body: _loading
          ? const LoadingWidget(message: 'Загружаем статистику...')
          : _error != null
              ? _ErrorView(message: _error!, onRetry: _loadStats)
              : _stats == null
                  ? const Center(child: Text('Нет данных'))
                  : RefreshIndicator(
                      color: AppColors.green,
                      onRefresh: _loadStats,
                      child: _buildContent(),
                    ),
    );
  }

  Widget _buildContent() {
    final stats = _stats!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Заголовок месяца
        Text(
          formatMonthLabel(stats.month),
          style: const TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.w700,
            color: AppColors.darkText,
          ),
        ),
        const SizedBox(height: 16),
        // Карточки с ключевыми показателями
        Row(
          children: [
            Expanded(
              child: _StatTile(
                emoji: '💰',
                value: formatMoney(stats.totalSpent),
                label: 'За месяц',
                color: AppColors.darkBlue,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _StatTile(
                emoji: '🧾',
                value: '${stats.receiptsCount}',
                label: 'Чеков',
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _StatTile(
                emoji: '📊',
                value: formatMoney(stats.averageReceipt),
                label: 'Средний чек',
              ),
            ),
          ],
        ),
        const SizedBox(height: 24),
        // Круговая диаграмма
        if (stats.byCategory.isNotEmpty) ...[
          const Text(
            'По категориям',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: AppColors.darkText),
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 220,
            child: PieChart(
              PieChartData(
                sections: _buildSections(stats),
                sectionsSpace: 2,
                centerSpaceRadius: 48,
                pieTouchData: PieTouchData(
                  touchCallback: (event, response) {
                    setState(() {
                      _touchedIndex = response?.touchedSection?.touchedSectionIndex ?? -1;
                    });
                  },
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),
          // Список категорий
          ...stats.byCategory.map((cat) => _CategoryRow(cat: cat)),
        ] else
          const Center(
            child: Padding(
              padding: EdgeInsets.all(32),
              child: Text(
                'Отсканируй чеки, чтобы увидеть статистику по категориям',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppColors.medGray),
              ),
            ),
          ),
        // Самая крупная покупка
        if (stats.largestPurchase != null) ...[
          const SizedBox(height: 20),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.white,
              borderRadius: BorderRadius.circular(14),
              boxShadow: [
                BoxShadow(
                  color: AppColors.darkBlue.withOpacity(0.06),
                  blurRadius: 6,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('🏆 Самая крупная покупка',
                    style: TextStyle(fontSize: 14, color: AppColors.medGray)),
                const SizedBox(height: 6),
                Text(
                  stats.largestPurchase!.name,
                  style: const TextStyle(
                      fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.darkText),
                ),
                Text(
                  formatMoney(stats.largestPurchase!.amount),
                  style: const TextStyle(
                      fontSize: 20, fontWeight: FontWeight.w800, color: AppColors.darkBlue),
                ),
              ],
            ),
          ),
        ],
        const SizedBox(height: 16),
      ],
    );
  }

  List<PieChartSectionData> _buildSections(Stats stats) {
    final colors = [
      AppColors.green,
      AppColors.darkBlue,
      const Color(0xFF3B82F6),
      const Color(0xFFF59E0B),
      const Color(0xFFEF4444),
      const Color(0xFF8B5CF6),
      const Color(0xFF06B6D4),
      const Color(0xFFEC4899),
    ];

    return stats.byCategory.asMap().entries.map((entry) {
      final i = entry.key;
      final cat = entry.value;
      final isTouched = i == _touchedIndex;
      return PieChartSectionData(
        color: colors[i % colors.length],
        value: cat.amount,
        title: '${cat.percent}%',
        radius: isTouched ? 68 : 56,
        titleStyle: TextStyle(
          fontSize: isTouched ? 14 : 12,
          fontWeight: FontWeight.w700,
          color: AppColors.white,
        ),
      );
    }).toList();
  }
}

class _StatTile extends StatelessWidget {
  final String emoji;
  final String value;
  final String label;
  final Color? color;

  const _StatTile({
    required this.emoji,
    required this.value,
    required this.label,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
            color: AppColors.darkBlue.withOpacity(0.06),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(emoji, style: const TextStyle(fontSize: 20)),
          const SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w800,
              color: color ?? AppColors.darkText,
            ),
          ),
          Text(label, style: const TextStyle(fontSize: 11, color: AppColors.medGray)),
        ],
      ),
    );
  }
}

class _CategoryRow extends StatelessWidget {
  final CategoryStat cat;

  const _CategoryRow({required this.cat});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Text(cat.emoji, style: const TextStyle(fontSize: 20)),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(cat.category,
                        style: const TextStyle(
                            fontWeight: FontWeight.w500, fontSize: 14, color: AppColors.darkText)),
                    Text(formatMoney(cat.amount),
                        style: const TextStyle(
                            fontWeight: FontWeight.w600, fontSize: 14, color: AppColors.darkText)),
                  ],
                ),
                const SizedBox(height: 4),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: cat.percent / 100,
                    backgroundColor: AppColors.lightGray,
                    color: AppColors.green,
                    minHeight: 5,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Text(
            '${cat.percent}%',
            style: const TextStyle(color: AppColors.medGray, fontSize: 12),
          ),
        ],
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('😕', style: TextStyle(fontSize: 48)),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center,
                style: const TextStyle(color: AppColors.medGray)),
            const SizedBox(height: 16),
            ElevatedButton(onPressed: onRetry, child: const Text('Повторить')),
          ],
        ),
      ),
    );
  }
}
