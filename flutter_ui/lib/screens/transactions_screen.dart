// @ai perplexity flutter-ui-screen
// Main transaction screen for AmiFi Flutter UI  
// Human decisions: UI layout, color scheme, user experience

import 'package:flutter/material.dart';
import '../models/transaction.dart';
import '../services/api_service.dart';

class TransactionsScreen extends StatefulWidget {
  const TransactionsScreen({Key? key}) : super(key: key);

  @override
  State<TransactionsScreen> createState() => _TransactionsScreenState();
}

class _TransactionsScreenState extends State<TransactionsScreen> {
  final ApiService _apiService = ApiService();
  List<Transaction> _transactions = [];
  bool _isLoading = true;
  String? _errorMessage;
  Map<String, dynamic>? _healthStatus;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      // Load transactions and health status
      final transactions = await _apiService.getTransactions();
      final health = await _apiService.getHealthStatus();
      
      setState(() {
        _transactions = transactions;
        _healthStatus = health;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _processBulkData() async {
    try {
      await _apiService.processBulkData(fileType: 'sms');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('✅ Bulk processing completed!')),
      );
      _loadData(); // Refresh data
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('❌ Error: ${e.toString()}')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AmiFi Transactions'),
        backgroundColor: Colors.blue[800],
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
          ),
        ],
      ),
      body: _buildBody(),
      floatingActionButton: FloatingActionButton(
        onPressed: _processBulkData,
        backgroundColor: Colors.green[700],
        child: const Icon(Icons.upload, color: Colors.white),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Loading transactions...'),
          ],
        ),
      );
    }

    if (_errorMessage != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error, size: 64, color: Colors.red[400]),
            const SizedBox(height: 16),
            Text(
              'Error: $_errorMessage',
              style: TextStyle(color: Colors.red[700]),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadData,
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    return Column(
      children: [
        _buildHealthCard(),
        _buildStatsCard(),
        Expanded(
          child: _buildTransactionsList(),
        ),
      ],
    );
  }

  Widget _buildHealthCard() {
    final isHealthy = _healthStatus?['status'] == 'healthy';
    
    return Container(
      margin: const EdgeInsets.all(8),
      child: Card(
        color: isHealthy ? Colors.green[50] : Colors.orange[50],
        child: ListTile(
          leading: Icon(
            isHealthy ? Icons.check_circle : Icons.warning,
            color: isHealthy ? Colors.green : Colors.orange,
          ),
          title: Text('System Status: ${_healthStatus?['status'] ?? 'Unknown'}'),
          subtitle: Text(
            'Database: ${_healthStatus?['database_connected'] ?? false ? 'Connected' : 'Disconnected'}',
          ),
        ),
      ),
    );
  }

  Widget _buildStatsCard() {
    final totalAmount = _transactions.fold<double>(
      0, (sum, txn) => sum + (txn.type == 'debit' ? -txn.amount : txn.amount),
    );
    
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 8),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildStatItem('Transactions', _transactions.length.toString()),
              _buildStatItem('Net Amount', '₹${totalAmount.toStringAsFixed(2)}'),
              _buildStatItem('Goal Impacts', 
                _transactions.fold<int>(0, (sum, txn) => sum + txn.goalImpacts.length).toString(),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatItem(String label, String value) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
        ),
        Text(
          label,
          style: TextStyle(fontSize: 12, color: Colors.grey[600]),
        ),
      ],
    );
  }

  Widget _buildTransactionsList() {
    if (_transactions.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.inbox, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text('No transactions found'),
            Text('Try processing bulk data with the + button'),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(8),
      itemCount: _transactions.length,
      itemBuilder: (context, index) {
        final transaction = _transactions[index];
        return _buildTransactionCard(transaction);
      },
    );
  }

  Widget _buildTransactionCard(Transaction transaction) {
    final isCredit = transaction.type == 'credit';
    
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ExpansionTile(
        leading: CircleAvatar(
          backgroundColor: isCredit ? Colors.green[100] : Colors.red[100],
          child: Icon(
            isCredit ? Icons.arrow_downward : Icons.arrow_upward,
            color: isCredit ? Colors.green[700] : Colors.red[700],
          ),
        ),
        title: Text(
          '₹${transaction.amount.toStringAsFixed(2)}',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: isCredit ? Colors.green[700] : Colors.red[700],
          ),
        ),
        subtitle: Text(
          '${transaction.merchant ?? transaction.category} • ${transaction.channel.toUpperCase()}',
        ),
        trailing: Chip(
          label: Text(transaction.category),
          backgroundColor: Colors.blue[100],
        ),
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildDetailRow('Type', transaction.type),
                _buildDetailRow('Confidence', '${(transaction.confidence * 100).toInt()}%'),
                _buildDetailRow('Account', transaction.accountRef ?? 'N/A'),
                _buildDetailRow('Date', transaction.timestamp.toString().split('.')[0]),
                
                if (transaction.goalImpacts.isNotEmpty) ...[
                  const SizedBox(height: 16),
                  const Text(
                    'Goal Impacts:',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  ...transaction.goalImpacts.map((impact) => _buildGoalImpact(impact)),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 80,
            child: Text(
              '$label:',
              style: TextStyle(
                fontWeight: FontWeight.w500,
                color: Colors.grey[700],
              ),
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }

  Widget _buildGoalImpact(GoalImpact impact) {
    final isPositive = impact.impactScore > 0;
    
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isPositive ? Colors.green[50] : Colors.orange[50],
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: isPositive ? Colors.green[200]! : Colors.orange[200]!,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                isPositive ? Icons.trending_up : Icons.trending_down,
                size: 16,
                color: isPositive ? Colors.green[700] : Colors.orange[700],
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  impact.goalId,
                  style: TextStyle(
                    fontWeight: FontWeight.w500,
                    color: isPositive ? Colors.green[700] : Colors.orange[700],
                  ),
                ),
              ),
              Text(
                '${(impact.impactScore * 100).toInt()}%',
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey[600],
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            impact.message,
            style: const TextStyle(fontSize: 12),
          ),
        ],
      ),
    );
  }
}
