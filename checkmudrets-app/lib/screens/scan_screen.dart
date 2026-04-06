import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../utils/constants.dart';
import '../widgets/loading_widget.dart';
import 'scan_result_screen.dart';

/// Экран сканирования чека — открывает камеру и отправляет фото на сервер.
class ScanScreen extends StatefulWidget {
  const ScanScreen({super.key});

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> {
  bool _loading = false;
  String _loadingMessage = '🔍 Распознаю чек...';

  @override
  void initState() {
    super.initState();
    // Автоматически открываем камеру при входе на экран
    WidgetsBinding.instance.addPostFrameCallback((_) => _pickAndUpload());
  }

  Future<void> _pickAndUpload({ImageSource source = ImageSource.camera}) async {
    final picker = ImagePicker();
    XFile? pickedFile;

    try {
      pickedFile = await picker.pickImage(
        source: source,
        imageQuality: 85,
        maxWidth: 1920,
        maxHeight: 2560,
      );
    } catch (e) {
      // Если камера недоступна — предлагаем галерею
      if (mounted && source == ImageSource.camera) {
        await _pickAndUpload(source: ImageSource.gallery);
      }
      return;
    }

    if (pickedFile == null) {
      // Пользователь отменил — возвращаемся
      if (mounted) Navigator.of(context).pop();
      return;
    }

    setState(() {
      _loading = true;
      _loadingMessage = '🔍 Распознаю чек...';
    });

    try {
      final prefs = await SharedPreferences.getInstance();
      final deviceId = prefs.getString(PrefKeys.deviceId) ?? '';

      final result = await ApiService().uploadReceipt(
        deviceId,
        File(pickedFile.path),
      );

      if (!mounted) return;

      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => ScanResultScreen(result: result),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _loading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Ошибка: $e')),
      );
      Navigator.of(context).pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.darkBlue,
      appBar: AppBar(
        title: const Text('Сканирование'),
        backgroundColor: AppColors.darkBlue,
      ),
      body: _loading
          ? LoadingWidget(message: _loadingMessage)
          : Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text('📸', style: TextStyle(fontSize: 64)),
                  const SizedBox(height: 24),
                  const Text(
                    'Сфотографируй чек',
                    style: TextStyle(
                      color: AppColors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 32),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 32),
                    child: ElevatedButton.icon(
                      onPressed: () => _pickAndUpload(),
                      icon: const Icon(Icons.camera_alt),
                      label: const Text('Открыть камеру'),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 32),
                    child: OutlinedButton.icon(
                      onPressed: () => _pickAndUpload(source: ImageSource.gallery),
                      icon: const Icon(Icons.photo_library, color: AppColors.white),
                      label: const Text('Выбрать из галереи',
                          style: TextStyle(color: AppColors.white)),
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: AppColors.white),
                        minimumSize: const Size.fromHeight(52),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}
