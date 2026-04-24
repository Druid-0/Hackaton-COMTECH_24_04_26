import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const CreditScoringApp());
}

class CreditScoringApp extends StatelessWidget {
  const CreditScoringApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Credit Scoring',
      theme: ThemeData(useMaterial3: true, colorSchemeSeed: Colors.indigo),
      home: const ScoringPage(),
    );
  }
}

class ScoringPage extends StatefulWidget {
  const ScoringPage({super.key});

  @override
  State<ScoringPage> createState() => _ScoringPageState();
}

class _ScoringPageState extends State<ScoringPage> {
  final _formKey = GlobalKey<FormState>();

  final Map<String, TextEditingController> _controllers = {
    'age': TextEditingController(text: '29'),
    'monthly_income': TextEditingController(text: '32000'),
    'employment_years': TextEditingController(text: '3.5'),
    'loan_amount': TextEditingController(text: '650000'),
    'loan_term_months': TextEditingController(text: '48'),
    'interest_rate': TextEditingController(text: '33'),
    'past_due_30d': TextEditingController(text: '2'),
    'inquiries_6m': TextEditingController(text: '4'),
  };

  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _result;

  // Для Android-эмулятора localhost backend доступен по 10.0.2.2
  // Для web/desktop можно оставить localhost.
  final String _apiBaseUrl = 'http://10.0.2.2:8000';

  @override
  void dispose() {
    for (final controller in _controllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _loading = true;
      _error = null;
      _result = null;
    });

    try {
      final payload = <String, dynamic>{};
      for (final entry in _controllers.entries) {
        payload[entry.key] = double.parse(entry.value.text.trim());
      }

      final response = await http.post(
        Uri.parse('$_apiBaseUrl/predict'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );

      if (response.statusCode != 200) {
        throw Exception('HTTP ${response.statusCode}: ${response.body}');
      }

      final data = jsonDecode(response.body) as Map<String, dynamic>;
      setState(() => _result = data);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  Widget _buildInput(String key, String label) {
    return TextFormField(
      controller: _controllers[key],
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(labelText: label, border: const OutlineInputBorder()),
      validator: (value) {
        if (value == null || value.trim().isEmpty) return 'Введите значение';
        if (double.tryParse(value.trim()) == null) return 'Только число';
        return null;
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final metrics = _result?['metrics'] as Map<String, dynamic>?;

    return Scaffold(
      appBar: AppBar(title: const Text('Credit Scoring (Flutter + FastAPI)')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              _buildInput('age', 'Возраст (age)'),
              const SizedBox(height: 12),
              _buildInput('monthly_income', 'Доход в месяц (monthly_income)'),
              const SizedBox(height: 12),
              _buildInput('employment_years', 'Стаж, лет (employment_years)'),
              const SizedBox(height: 12),
              _buildInput('loan_amount', 'Сумма кредита (loan_amount)'),
              const SizedBox(height: 12),
              _buildInput('loan_term_months', 'Срок, мес (loan_term_months)'),
              const SizedBox(height: 12),
              _buildInput('interest_rate', 'Ставка % (interest_rate)'),
              const SizedBox(height: 12),
              _buildInput('past_due_30d', 'Просрочки 30d (past_due_30d)'),
              const SizedBox(height: 12),
              _buildInput('inquiries_6m', 'Запросы за 6м (inquiries_6m)'),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: _loading ? null : _submit,
                  child: _loading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Рассчитать скоринг'),
                ),
              ),
              const SizedBox(height: 20),
              if (_error != null)
                Text(_error!, style: const TextStyle(color: Colors.red)),
              if (_result != null)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Класс: ${_result!['label']}',
                            style: Theme.of(context).textTheme.titleMedium),
                        const SizedBox(height: 8),
                        Text('P(default): ${_result!['p_default']}'),
                        Text('P(non-default): ${_result!['p_non_default']}'),
                        const SizedBox(height: 12),
                        if (metrics != null) ...[
                          Text('ROC-AUC: ${metrics['roc_auc']}'),
                          Text('PR-AUC: ${metrics['pr_auc']}'),
                          Text('Accuracy@0.5: ${metrics['accuracy_at_0_5']}'),
                        ],
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
