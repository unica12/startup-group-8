import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../utils/constants.dart';
import '../utils/formatting.dart';
import '../widgets/loading_widget.dart';
import 'advice_screen.dart';
import 'report_screen.dart';

/// Экран профиля пользователя.
class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  String _name = '';
  String _deviceId = '';
  int _receiptsCount = 0;
  double _totalSpent = 0;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    setState(() => _loading = true);
    try {
      final prefs = await SharedPreferences.getInstance();
      _name = prefs.getString(PrefKeys.userName) ?? '';
      _deviceId = prefs.getString(PrefKeys.deviceId) ?? '';

      // Загружаем статистику для отображения в профиле
      if (_deviceId.isNotEmpty) {
        final stats = await ApiService().getStats(_deviceId);
        setState(() {
          _receiptsCount = stats.receiptsCount;
          _totalSpent = stats.totalSpent;
        });
      }
    } catch (_) {
      // Не критично, показываем что есть
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Профиль')),
      body: _loading
          ? const LoadingWidget(message: 'Загрузка...')
          : RefreshIndicator(
              color: AppColors.green,
              onRefresh: _loadProfile,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // Аватар и имя
                  Center(
                    child: Column(
                      children: [
                        Container(
                          width: 80,
                          height: 80,
                          decoration: BoxDecoration(
                            color: AppColors.green,
                            shape: BoxShape.circle,
                          ),
                          child: Center(
                            child: Text(
                              _name.isNotEmpty ? _name[0].toUpperCase() : '👤',
                              style: const TextStyle(
                                fontSize: 36,
                                color: AppColors.white,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 12),
                        Text(
                          _name.isNotEmpty ? _name : 'Пользователь',
                          style: const TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.w700,
                            color: AppColors.darkText,
                          ),
                        ),
                        Text(
                          _deviceId.length > 8 ? _deviceId.substring(0, 8) + '...' : _deviceId,
                          style: const TextStyle(color: AppColors.medGray, fontSize: 13),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),
                  // Статистика профиля
                  Row(
                    children: [
                      Expanded(
                        child: _ProfileStat(
                          emoji: '🧾',
                          value: '$_receiptsCount',
                          label: 'чеков этот месяц',
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: _ProfileStat(
                          emoji: '💰',
                          value: formatMoney(_totalSpent),
                          label: 'за этот месяц',
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'Инструменты',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: AppColors.darkText,
                    ),
                  ),
                  const SizedBox(height: 12),
                  // Кнопка советов
                  _ActionButton(
                    emoji: '💡',
                    title: 'Советы по экономии',
                    subtitle: 'Персональный анализ расходов от ИИ',
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const AdviceScreen()),
                    ),
                  ),
                  const SizedBox(height: 10),
                  // Кнопка отчёта
                  _ActionButton(
                    emoji: '📈',
                    title: 'Недельный отчёт',
                    subtitle: 'Сравнение с прошлой неделей',
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const ReportScreen()),
                    ),
                  ),
                  const SizedBox(height: 24),
                ],
              ),
            ),
    );
  }
}

class _ProfileStat extends StatelessWidget {
  final String emoji;
  final String value;
  final String label;

  const _ProfileStat({required this.emoji, required this.value, required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
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
        children: [
          Text(emoji, style: const TextStyle(fontSize: 26)),
          const SizedBox(height: 6),
          Text(value,
              style: const TextStyle(
                  fontSize: 18, fontWeight: FontWeight.w800, color: AppColors.darkBlue)),
          Text(label,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 12, color: AppColors.medGray)),
        ],
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  final String emoji;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _ActionButton({
    required this.emoji,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
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
        child: Row(
          children: [
            Text(emoji, style: const TextStyle(fontSize: 26)),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title,
                      style: const TextStyle(
                          fontSize: 15, fontWeight: FontWeight.w600, color: AppColors.darkText)),
                  Text(subtitle,
                      style: const TextStyle(fontSize: 12, color: AppColors.medGray)),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: AppColors.medGray),
          ],
        ),
      ),
    );
  }
}
