import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/receipt.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../utils/constants.dart';
import '../widgets/loading_widget.dart';
import '../widgets/receipt_card.dart';
import 'receipt_detail_screen.dart';

/// Экран истории чеков.
class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  List<Receipt> _receipts = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadReceipts();
  }

  Future<void> _loadReceipts() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final prefs = await SharedPreferences.getInstance();
      final deviceId = prefs.getString(PrefKeys.deviceId) ?? '';
      final receipts = await ApiService().getReceipts(deviceId, limit: 50);
      setState(() {
        _receipts = receipts;
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
        title: const Text('История'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadReceipts),
        ],
      ),
      body: _loading
          ? const LoadingWidget(message: 'Загружаем историю...')
          : _error != null
              ? _center(Text(_error!, style: const TextStyle(color: AppColors.medGray)))
              : _receipts.isEmpty
                  ? _center(const Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text('🧾', style: TextStyle(fontSize: 48)),
                        SizedBox(height: 12),
                        Text('Нет отсканированных чеков',
                            style: TextStyle(color: AppColors.medGray, fontSize: 16)),
                      ],
                    ))
                  : RefreshIndicator(
                      color: AppColors.green,
                      onRefresh: _loadReceipts,
                      child: ListView.builder(
                        padding: const EdgeInsets.symmetric(vertical: 8),
                        itemCount: _receipts.length,
                        itemBuilder: (context, i) => ReceiptCard(
                          receipt: _receipts[i],
                          onTap: () => Navigator.of(context).push(
                            MaterialPageRoute(
                              builder: (_) => ReceiptDetailScreen(receipt: _receipts[i]),
                            ),
                          ),
                        ),
                      ),
                    ),
    );
  }

  Widget _center(Widget child) => Center(child: Padding(padding: const EdgeInsets.all(24), child: child));
}
