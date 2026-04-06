/// Модель позиции в чеке.
class Item {
  final int id;
  final String name;
  final double quantity;
  final double price;
  final double total;
  final String category;

  const Item({
    required this.id,
    required this.name,
    required this.quantity,
    required this.price,
    required this.total,
    required this.category,
  });

  factory Item.fromJson(Map<String, dynamic> json) {
    return Item(
      id: json['id'] as int,
      name: json['name'] as String,
      quantity: (json['quantity'] as num).toDouble(),
      price: (json['price'] as num).toDouble(),
      total: (json['total'] as num).toDouble(),
      category: json['category'] as String? ?? 'Другое',
    );
  }
}
