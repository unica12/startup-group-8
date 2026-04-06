import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';

import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../utils/constants.dart';
import '../widgets/loading_widget.dart';
import 'home_screen.dart';

/// Экран приветствия — показывается один раз при первом запуске.
class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final _nameController = TextEditingController();
  bool _loading = false;

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _start() async {
    setState(() => _loading = true);
    try {
      final prefs = await SharedPreferences.getInstance();

      // Генерируем уникальный device_id и сохраняем навсегда
      String deviceId = prefs.getString(PrefKeys.deviceId) ?? const Uuid().v4();
      await prefs.setString(PrefKeys.deviceId, deviceId);

      final name = _nameController.text.trim().isEmpty
          ? null
          : _nameController.text.trim();

      // Регистрируемся на бэкенде
      final user = await ApiService().register(deviceId, name);
      await prefs.setInt(PrefKeys.userId, user.userId);
      await prefs.setString(PrefKeys.userName, user.name ?? '');
      await prefs.setBool(PrefKeys.onboardingDone, true);

      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const HomeScreen()),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Ошибка подключения: $e')),
      );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.darkBlue,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 32),
          child: _loading
              ? const LoadingWidget(message: 'Подключаемся...')
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Spacer(),
                    // Логотип
                    Container(
                      width: 80,
                      height: 80,
                      decoration: BoxDecoration(
                        color: AppColors.green,
                        borderRadius: BorderRadius.circular(24),
                      ),
                      child: const Center(
                        child: Text('💡', style: TextStyle(fontSize: 40)),
                      ),
                    ),
                    const SizedBox(height: 28),
                    // Заголовок
                    const Text(
                      'ЧекМудрец',
                      style: TextStyle(
                        color: AppColors.white,
                        fontSize: 36,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 12),
                    const Text(
                      'Фоткай чек — ИИ покажет,\nкуда уходят деньги',
                      style: TextStyle(
                        color: AppColors.medGray,
                        fontSize: 18,
                        height: 1.4,
                      ),
                    ),
                    const Spacer(),
                    // Поле имени
                    TextField(
                      controller: _nameController,
                      style: const TextStyle(color: AppColors.darkText),
                      decoration: const InputDecoration(
                        hintText: 'Ваше имя (необязательно)',
                        hintStyle: TextStyle(color: AppColors.medGray),
                        filled: true,
                        fillColor: AppColors.white,
                      ),
                      textCapitalization: TextCapitalization.words,
                    ),
                    const SizedBox(height: 16),
                    // Кнопка «Начать»
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: _start,
                        child: const Text('Начать →'),
                      ),
                    ),
                    const SizedBox(height: 24),
                  ],
                ),
        ),
      ),
    );
  }
}
