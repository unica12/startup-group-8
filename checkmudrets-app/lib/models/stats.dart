/// Модель статистики по категории.
class CategoryStat {
  final String category;
  final double amount;
  final int percent;
  final String emoji;

  const CategoryStat({
    required this.category,
    required this.amount,
    required this.percent,
    required this.emoji,
  });

  factory CategoryStat.fromJson(Map<String, dynamic> json) {
    return CategoryStat(
      category: json['category'] as String,
      amount: (json['amount'] as num).toDouble(),
      percent: json['percent'] as int,
      emoji: json['emoji'] as String? ?? '📦',
    );
  }
}

/// Самая крупная покупка.
class LargestPurchase {
  final String name;
  final double amount;
  final String category;

  const LargestPurchase({
    required this.name,
    required this.amount,
    required this.category,
  });

  factory LargestPurchase.fromJson(Map<String, dynamic> json) {
    return LargestPurchase(
      name: json['name'] as String,
      amount: (json['amount'] as num).toDouble(),
      category: json['category'] as String,
    );
  }
}

/// Модель статистики за месяц.
class Stats {
  final String month;
  final double totalSpent;
  final int receiptsCount;
  final double averageReceipt;
  final List<CategoryStat> byCategory;
  final LargestPurchase? largestPurchase;

  const Stats({
    required this.month,
    required this.totalSpent,
    required this.receiptsCount,
    required this.averageReceipt,
    required this.byCategory,
    this.largestPurchase,
  });

  factory Stats.fromJson(Map<String, dynamic> json) {
    final catList = json['by_category'] as List<dynamic>? ?? [];
    final largestJson = json['largest_purchase'] as Map<String, dynamic>?;
    return Stats(
      month: json['month'] as String,
      totalSpent: (json['total_spent'] as num).toDouble(),
      receiptsCount: json['receipts_count'] as int,
      averageReceipt: (json['average_receipt'] as num).toDouble(),
      byCategory: catList.map((e) => CategoryStat.fromJson(e as Map<String, dynamic>)).toList(),
      largestPurchase: largestJson != null ? LargestPurchase.fromJson(largestJson) : null,
    );
  }
}
