/// Модель пользователя приложения.
class User {
  final int userId;
  final String deviceId;
  final String? name;
  final DateTime createdAt;

  const User({
    required this.userId,
    required this.deviceId,
    this.name,
    required this.createdAt,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      userId: json['user_id'] as int,
      deviceId: json['device_id'] as String,
      name: json['name'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}
