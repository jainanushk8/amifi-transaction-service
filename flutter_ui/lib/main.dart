// @ai perplexity flutter-main
// AmiFi Transaction Processing Flutter UI
// Human decisions: App theme, navigation, startup flow

import 'package:flutter/material.dart';
import 'screens/transactions_screen.dart';

void main() {
  runApp(const AmiFiApp());
}

class AmiFiApp extends StatelessWidget {
  const AmiFiApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AmiFi Transactions',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
        appBarTheme: AppBarTheme(
          backgroundColor: Colors.blue[800],
          foregroundColor: Colors.white,
        ),
      ),
      home: const TransactionsScreen(),
    );
  }
}
