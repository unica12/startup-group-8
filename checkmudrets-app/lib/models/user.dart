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
      userId: (json['user_id'] as num?)?.toInt() ?? 0,
      deviceId: json['device_id'] as String,
      name: json['name'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : DateTime.now(),
    );
  }
}
