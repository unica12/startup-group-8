import 'package:flutter/material.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'screens/home_screen.dart';
import 'screens/onboarding_screen.dart';
import 'theme/app_theme.dart';
import 'utils/constants.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Инициализируем русскую локаль для intl (форматирование дат и чисел)
  await initializeDateFormatting('ru_RU', null);
  runApp(const CheckMudretsApp());
}

class CheckMudretsApp extends StatelessWidget {
  const CheckMudretsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ЧекМудрец',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.theme,
      home: const _RootRouter(),
    );
  }
}

/// Роутер: показывает онбординг при первом запуске, иначе — главный экран.
class _RootRouter extends StatefulWidget {
  const _RootRouter();

  @override
  State<_RootRouter> createState() => _RootRouterState();
}

class _RootRouterState extends State<_RootRouter> {
  bool? _onboardingDone;

  @override
  void initState() {
    super.initState();
    _checkOnboarding();
  }

  Future<void> _checkOnboarding() async {
    final prefs = await SharedPreferences.getInstance();
    final done = prefs.getBool(PrefKeys.onboardingDone) ?? false;
    setState(() => _onboardingDone = done);
  }

  @override
  Widget build(BuildContext context) {
    // Пока проверяем SharedPreferences — показываем сплэш
    if (_onboardingDone == null) {
      return const Scaffold(
        backgroundColor: AppColors.darkBlue,
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('💡', style: TextStyle(fontSize: 64)),
              SizedBox(height: 16),
              Text(
                'ЧекМудрец',
                style: TextStyle(
                  color: AppColors.white,
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ],
          ),
        ),
      );
    }

    return _onboardingDone! ? const HomeScreen() : const OnboardingScreen();
  }
}
