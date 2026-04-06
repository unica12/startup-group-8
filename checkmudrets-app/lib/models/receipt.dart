import 'item.dart';

/// Модель кассового чека.
class Receipt {
  final int id;
  final String? storeName;
  final DateTime? date;
  final double total;
  final List<Item> items;
  final DateTime createdAt;

  const Receipt({
    required this.id,
    this.storeName,
    this.date,
    required this.total,
    required this.items,
    required this.createdAt,
  });

  factory Receipt.fromJson(Map<String, dynamic> json) {
    final itemsJson = json['items'] as List<dynamic>? ?? [];
    return Receipt(
      id: json['id'] as int,
      storeName: json['store_name'] as String?,
      date: json['date'] != null ? DateTime.tryParse(json['date'] as String) : null,
      total: (json['total'] as num).toDouble(),
      items: itemsJson.map((e) => Item.fromJson(e as Map<String, dynamic>)).toList(),
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}
