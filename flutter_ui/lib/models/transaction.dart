// @ai perplexity flutter-models
// Transaction data models for AmiFi Flutter UI
// Human decisions: Model structure, field mapping

class Transaction {
  final String id;
  final String userId;
  final DateTime timestamp;
  final double amount;
  final String currency;
  final String? accountRef;
  final String channel;
  final String type;
  final String category;
  final double confidence;
  final String? merchant;
  final List<GoalImpact> goalImpacts;

  Transaction({
    required this.id,
    required this.userId,
    required this.timestamp,
    required this.amount,
    required this.currency,
    this.accountRef,
    required this.channel,
    required this.type,
    required this.category,
    required this.confidence,
    this.merchant,
    required this.goalImpacts,
  });

  factory Transaction.fromJson(Map<String, dynamic> json) {
    return Transaction(
      id: json['id'],
      userId: json['userid'],
      timestamp: DateTime.parse(json['ts']),
      amount: json['amount'].toDouble(),
      currency: json['currency'],
      accountRef: json['account_ref'],
      channel: json['channel'],
      type: json['type'],
      category: json['category'],
      confidence: json['confidence'].toDouble(),
      merchant: json['meta'] != null ? _extractMerchant(json['meta']) : null,
      goalImpacts: (json['goal_impacts'] as List?)
          ?.map((impact) => GoalImpact.fromJson(impact))
          .toList() ?? [],
    );
  }

  static String? _extractMerchant(dynamic meta) {
    if (meta is String) {
      try {
        final parsed = json.decode(meta);
        return parsed['merchant'];
      } catch (e) {
        return null;
      }
    }
    return meta['merchant'];
  }
}

class GoalImpact {
  final String id;
  final String goalId;
  final double impactScore;
  final String message;

  GoalImpact({
    required this.id,
    required this.goalId,
    required this.impactScore,
    required this.message,
  });

  factory GoalImpact.fromJson(Map<String, dynamic> json) {
    return GoalImpact(
      id: json['id'],
      goalId: json['goal_id'],
      impactScore: json['impact_score'].toDouble(),
      message: json['message'],
    );
  }
}

class ApiResponse<T> {
  final List<T> transactions;
  final int count;
  final int limit;

  ApiResponse({
    required this.transactions,
    required this.count,
    required this.limit,
  });
}
