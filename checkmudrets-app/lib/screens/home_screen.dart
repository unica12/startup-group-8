import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_service.dart';
import '../models/receipt.dart';
import '../models/stats.dart';
import '../theme/app_theme.dart';
import '../utils/constants.dart';
import '../utils/formatting.dart';
import '../widgets/receipt_card.dart';
import 'scan_screen.dart';
import 'stats_screen.dart';
import 'history_screen.dart';
import 'profile_screen.dart';
import 'receipt_detail_screen.dart';

/// Главный экран с нижней навигацией.
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    const screens = [
      _HomeTab(),
      StatsScreen(),
      HistoryScreen(),
      ProfileScreen(),
    ];

    return Scaffold(
      body: IndexedStack(index: _currentIndex, children: screens),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (i) => setState(() => _currentIndex = i),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home_outlined), activeIcon: Icon(Icons.home), label: 'Главная'),
          BottomNavigationBarItem(icon: Icon(Icons.bar_chart_outlined), activeIcon: Icon(Icons.bar_chart), label: 'Статистика'),
          BottomNavigationBarItem(icon: Icon(Icons.receipt_long_outlined), activeIcon: Icon(Icons.receipt_long), label: 'История'),
          BottomNavigationBarItem(icon: Icon(Icons.person_outline), activeIcon: Icon(Icons.person), label: 'Профиль'),
        ],
      ),
    );
  }
}

/// Содержимое таба «Главная».
class _HomeTab extends StatefulWidget {
  const _HomeTab();

  @override
  State<_HomeTab> createState() => _HomeTabState();
}

class _HomeTabState extends State<_HomeTab> {
  String _name = '';
  String _deviceId = '';
  Stats? _stats;
  List<Receipt> _recentReceipts = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    final prefs = await SharedPreferences.getInstance();
    _name = prefs.getString(PrefKeys.userName) ?? '';
    _deviceId = prefs.getString(PrefKeys.deviceId) ?? '';

    if (_deviceId.isEmpty) {
      setState(() => _loading = false);
      return;
    }

    try {
      final api = ApiService();
      final results = await Future.wait([
        api.getStats(_deviceId),
        api.getReceipts(_deviceId, limit: 3),
      ]);
      setState(() {
        _stats = results[0] as Stats;
        _recentReceipts = results[1] as List<Receipt>;
        _loading = false;
      });
    } catch (_) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('ЧекМудрец'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              setState(() => _loading = true);
              _loadData();
            },
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppColors.green))
          : RefreshIndicator(
              color: AppColors.green,
              onRefresh: _loadData,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // Приветствие
                  Text(
                    _name.isNotEmpty ? 'Привет, $_name! 👋' : 'Привет! 👋',
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.w700,
                      color: AppColors.darkText,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _stats != null ? formatMonthLabel(_stats!.month) : '',
                    style: const TextStyle(color: AppColors.medGray, fontSize: 15),
                  ),
                  const SizedBox(height: 16),
                  // Карточка с суммой месяца
                  if (_stats != null) _MonthCard(stats: _stats!),
                  const SizedBox(height: 20),
                  // Кнопка сканирования
                  SizedBox(
                    height: 64,
                    child: ElevatedButton.icon(
                      onPressed: () async {
                        await Navigator.of(context).push(
                          MaterialPageRoute(builder: (_) => const ScanScreen()),
                        );
                        // Обновляем данные после возврата со скана
                        setState(() => _loading = true);
                        _loadData();
                      },
                      icon: const Text('📸', style: TextStyle(fontSize: 22)),
                      label: const Text('Сканировать чек'),
                    ),
                  ),
                  const SizedBox(height: 24),
                  // Последние чеки
                  if (_recentReceipts.isNotEmpty) ...[
                    const Text(
                      'Последние чеки',
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w700,
                        color: AppColors.darkText,
                      ),
                    ),
                    const SizedBox(height: 8),
                    ..._recentReceipts.map((r) => ReceiptCard(
                          receipt: r,
                          onTap: () => Navigator.of(context).push(
                            MaterialPageRoute(
                              builder: (_) => ReceiptDetailScreen(receipt: r),
                            ),
                          ),
                        )),
                  ],
                ],
              ),
            ),
    );
  }
}

class _MonthCard extends StatelessWidget {
  final Stats stats;

  const _MonthCard({required this.stats});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.darkBlue, Color(0xFF1A4A7A)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Потрачено за месяц',
                  style: TextStyle(color: AppColors.medGray, fontSize: 13)),
              const SizedBox(height: 6),
              Text(
                formatMoney(stats.totalSpent),
                style: const TextStyle(
                  color: AppColors.white,
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ],
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: AppColors.green.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  '${stats.receiptsCount} чеков',
                  style: const TextStyle(
                    color: AppColors.green,
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
