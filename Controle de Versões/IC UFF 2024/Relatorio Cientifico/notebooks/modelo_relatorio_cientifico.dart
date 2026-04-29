import 'package:flutter/material.dart';

class RelatorioChecklist extends StatefulWidget {
  @override
  _RelatorioChecklistState createState() => _RelatorioChecklistState();
}

class _RelatorioChecklistState extends State<RelatorioChecklist> {
  // Mapas para controlar o estado dos checkboxes de cada sessão
  final Map<int, bool> _sessao1 = {};
  final Map<int, bool> _sessao2 = {};
  final Map<int, bool> _sessao3 = {};
  final Map<int, bool> _sessao4 = {};

  // Mapa com as tarefas de cada sessão
  final Map<String, List<String>> _tarefas = {
    'Sessão 1': [
      'Revisão do conteúdo',
      'Organização da estrutura',
      'Pesquisa complementar'
    ],
    'Sessão 2': [
      'Desenvolvimento da introdução',
      'Aprimoramento da metodologia',
      'Análise dos resultados'
    ],
    'Sessão 3': [
      'Discussão dos resultados',
      'Desenvolvimento da conclusão',
      'Revisão geral'
    ],
    'Sessão 4': [
      'Formatação final',
      'Elaboração das referências',
      'Revisão final'
    ],
  };

  // Função para atualizar o estado do checkbox
  void _updateCheckbox(String sessao, int index, bool? value) {
    setState(() {
      switch (sessao) {
        case 'Sessão 1':
          _sessao1[index] = value ?? false;
          break;
        case 'Sessão 2':
          _sessao2[index] = value ?? false;
          break;
        case 'Sessão 3':
          _sessao3[index] = value ?? false;
          break;
        case 'Sessão 4':
          _sessao4[index] = value ?? false;
          break;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Checklist Relatório Científico'),
      ),
      body: SingleChildScrollView(
        child: Column(
          children: _tarefas.keys.map((sessao) {
            return _buildChecklist(sessao, _tarefas[sessao]!);
          }).toList(),
        ),
      ),
    );
  }

  // Função para criar o checklist de cada sessão
  Widget _buildChecklist(String titulo, List<String> tarefas) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            titulo,
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 16),
          DataTable(
            columns: [
              DataColumn(
                label: Text('Tarefa'),
              ),
              DataColumn(
                label: Text('Concluído'),
              ),
            ],
            rows: tarefas.asMap().entries.map((entry) {
              final index = entry.key;
              final tarefa = entry.value;
              return _buildDataRow(titulo, index, tarefa);
            }).toList(),
          ),
        ],
      ),
    );
  }

  // Função para criar uma linha na tabela
  DataRow _buildDataRow(String sessao, int index, String tarefa) {
    return DataRow(
      cells: [
        DataCell(Text(tarefa)),
        DataCell(
          Checkbox(
            value: _getCheckboxValue(sessao, index),
            onChanged: (value) => _updateCheckbox(sessao, index, value),
          ),
        ),
      ],
    );
  }

  // Função para obter o valor do checkbox de acordo com a sessão e o índice
  bool _getCheckboxValue(String sessao, int index) {
    switch (sessao) {
      case 'Sessão 1':
        return _sessao1[index] ?? false;
      case 'Sessão 2':
        return _sessao2[index] ?? false;
      case 'Sessão 3':
        return _sessao3[index] ?? false;
      case 'Sessão 4':
        return _sessao4[index] ?? false;
      default:
        return false;
    }
  }
}

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: RelatorioChecklist(),
    );
  }
}
