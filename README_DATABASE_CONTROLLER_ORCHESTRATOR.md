# 🎯 DatabaseController + FileOutputOrchestrator

## 📋 Visão Geral

O `DatabaseController` agora inclui funcionalidades avançadas de orquestração de arquivos através da classe interna `FileOutputOrchestrator`, implementando **Design Patterns** modernos e **boas práticas** do Python.

## 🏗️ Arquitetura e Design Patterns

### **1. Composition Pattern**
```python
class DatabaseController:
    def __init__(self, base_dir: Path = None):
        # ... código existente ...
        
        # Composição: DatabaseController contém FileOutputOrchestrator
        self._file_orchestrator = FileOutputOrchestrator(self.output_dir)
```

### **2. Strategy Pattern**
- **DatabaseController**: Responsável pela lógica principal de dados
- **FileOutputOrchestrator**: Estratégia especializada para orquestração de arquivos
- **Separação de Responsabilidades**: Cada classe tem uma responsabilidade específica

### **3. Facade Pattern**
- **DatabaseController** atua como uma fachada, expondo métodos de orquestração
- Interface unificada para todas as funcionalidades
- Mantém compatibilidade com código existente

## 🚀 Funcionalidades Integradas

### **Funcionalidades Existentes (Mantidas)**
- ✅ Gerenciamento de parâmetros (`params.json`, `options.json`)
- ✅ Leitura de resultados individuais
- ✅ Consolidação de dados
- ✅ Geração de Excel consolidado

### **Novas Funcionalidades de Orquestração**
- 🔍 **Descoberta Automática**: Detecta diretórios `run_YYYY-MM-DD_HH-MM-SS`
- 📊 **Resumo Inteligente**: Estatísticas por tipo de arquivo
- 🗂️ **Organização**: Agrupa arquivos por configuração
- 📋 **Relatórios**: Gera relatórios detalhados em Excel
- 🧹 **Manutenção**: Limpeza automática de execuções antigas
- 📦 **Exportação**: Exporta execuções para ZIP

## 📁 Estrutura de Arquivos Suportada

```
src/output/
├── run_2025-08-25_21-46-02/
│   ├── config_1_exec_1_results.json
│   ├── config_1_exec_1_visualization.json
│   ├── dashboard_data_config1_exec1.pkl
│   └── grafico_execucao_config1_exec1.html
├── run_2025-08-25_21-37-33/
│   └── ...
├── resultados_consolidados.xlsx
├── pop_final.xlsx
└── organized_by_config/          # ← Novo diretório organizado
    ├── config_1/
    ├── config_2/
    └── ...
```

## 🛠️ Como Usar

### **Importação e Inicialização**
```python
from database_controller import DatabaseController
from pathlib import Path

# Inicializa o controlador (inclui orquestrador automaticamente)
base_dir = Path(__file__).resolve().parent
controller = DatabaseController(base_dir=base_dir)
```

### **1. Funcionalidades Existentes (Sem Mudanças)**
```python
# Consolidação tradicional
controller.run_consolidation()

# Leitura de dados
data = controller.get_run_data(1, 1)
params = controller.get_params()
```

### **2. Novas Funcionalidades de Orquestração**
```python
# Resumo geral das execuções
summary = controller.get_execution_summary()
print(f"Total de execuções: {summary['total_runs']}")

# Lista arquivos por tipo
json_files = controller.get_all_output_files('json')
html_files = controller.get_all_output_files('html')

# Busca por padrões
config1_files = controller.find_files_by_pattern("*config1*")
best_files = controller.find_files_by_pattern("*best*")

# Organização automática
controller.organize_outputs_by_config()

# Relatório detalhado
controller.create_output_report()

# Manutenção
controller.cleanup_old_runs(keep_last_n=3)

# Exportação
controller.export_run_to_zip('run_2025-08-25_21-46-02')
```

## 📊 Métodos Disponíveis

### **Métodos Existentes (DatabaseController)**
| Método | Descrição |
|--------|-----------|
| `get_params()` | Carrega parâmetros de `params.json` |
| `save_params(data)` | Salva parâmetros em `params.json` |
| `get_options()` | Carrega opções de `options.json` |
| `save_options(data)` | Salva opções em `options.json` |
| `get_run_data(config, exec)` | Carrega dados de execução específica |
| `run_consolidation()` | Executa consolidação de resultados |

### **Novos Métodos (Orquestração)**
| Método | Descrição | Retorno |
|--------|-----------|---------|
| `get_execution_summary()` | Resumo completo das execuções | `dict` |
| `get_all_output_files(type)` | Lista arquivos por tipo | `dict` |
| `find_files_by_pattern(pattern)` | Busca por padrão | `list` |
| `organize_outputs_by_config()` | Organiza por configuração | `bool` |
| `create_output_report()` | Cria relatório Excel | `bool` |
| `cleanup_old_runs(n)` | Remove execuções antigas | `bool` |
| `export_run_to_zip(run_name)` | Exporta para ZIP | `bool` |
| `get_file_info(file_path)` | Informações do arquivo | `dict` |

## 🔍 Exemplos de Uso Avançado

### **Análise de Performance**
```python
# Analisa arquivos de melhor fitness
best_files = controller.find_files_by_pattern("*best*")
for file_path in best_files:
    file_info = controller.get_file_info(file_path)
    print(f"Arquivo: {file_info['name']}")
    print(f"Tamanho: {file_info['size_mb']} MB")
    print(f"Modificado: {file_info['modified']}")
```

### **Backup Automático**
```python
# Exporta as 3 execuções mais recentes
summary = controller.get_execution_summary()
for run_info in summary['run_directories'][:3]:
    run_name = run_info['name']
    controller.export_run_to_zip(run_name)
```

### **Relatório Personalizado**
```python
# Cria relatório com nome personalizado
controller.create_output_report("meu_relatorio_personalizado.xlsx")
```

### **Organização Inteligente**
```python
# Organiza arquivos por configuração em diretório personalizado
controller.organize_outputs_by_config("meus_arquivos_organizados")
```

## 🎯 Casos de Uso

### **1. Análise de Resultados**
- Consolidação automática de dados
- Geração de relatórios detalhados
- Comparação entre execuções
- Rastreamento de performance

### **2. Manutenção de Sistema**
- Limpeza automática de arquivos antigos
- Backup de execuções importantes
- Organização por projetos/configurações
- Gerenciamento de espaço em disco

### **3. Debugging e Troubleshooting**
- Rastreamento de arquivos por padrão
- Análise de tamanhos e datas
- Identificação de problemas
- Histórico de execuções

### **4. Documentação e Relatórios**
- Relatórios automáticos em Excel
- Estatísticas de uso
- Histórico de execuções
- Metadados organizados

## ⚠️ Considerações Importantes

### **1. Compatibilidade**
- ✅ **100% compatível** com código existente
- ✅ **Nenhuma mudança** nas funcionalidades atuais
- ✅ **Interface unificada** para todas as funcionalidades

### **2. Performance**
- 🔍 **Busca eficiente** com `glob` e `pathlib`
- 📊 **Cache inteligente** de diretórios de execução
- 🚀 **Lazy loading** de informações de arquivos

### **3. Segurança**
- 🛡️ **Não modifica** arquivos originais sem confirmação
- 🔒 **Validação** de caminhos e permissões
- 📝 **Logs detalhados** de todas as operações

## 🚀 Execução e Teste

### **Execução Direta**
```bash
# Executa consolidação + demonstração de orquestração
python database_controller.py
```

### **Saída Esperada**
```
🚀 DATABASE CONTROLLER + FILE ORCHESTRATOR
==================================================

1️⃣ EXECUTANDO CONSOLIDAÇÃO...
=== INICIANDO CONSOLIDAÇÃO DE RESULTADOS ===
✅ Consolidação concluída com sucesso!

2️⃣ DEMONSTRANDO ORQUESTRAÇÃO DE ARQUIVOS...
   📁 Total de execuções: 8
   📊 Total de arquivos: 64
   📋 JSON: 16 arquivos
   📋 HTML: 16 arquivos
   📋 PKL: 16 arquivos
   📋 XLSX: 16 arquivos

3️⃣ CRIANDO RELATÓRIO DE SAÍDA...
   ✅ Relatório criado com sucesso!

4️⃣ ORGANIZANDO ARQUIVOS...
   ✅ Arquivos organizados por configuração!

🎯 Processo completo concluído!
```

## 🔧 Personalização

### **Configuração de Diretórios**
```python
# Personaliza diretório de saída
controller = DatabaseController(base_dir="/caminho/personalizado")

# Organiza em diretório específico
controller.organize_outputs_by_config("/meu/diretorio/organizado")
```

### **Filtros Personalizados**
```python
# Busca por padrões específicos
meus_arquivos = controller.find_files_by_pattern("*meu_padrao*")

# Filtra por tipo específico
apenas_json = controller.get_all_output_files('json')
```

## 📞 Suporte e Manutenção

### **Arquivos Principais**
- **Código fonte**: `database_controller.py`
- **Documentação**: Este README
- **Exemplos**: Script principal integrado

### **Próximos Passos**
1. ✅ Execute: `python database_controller.py`
2. ✅ Teste as funcionalidades básicas
3. ✅ Personalize para suas necessidades
4. ✅ Integre com seu workflow existente

### **Contribuições**
- Mantenha a estrutura de design patterns
- Adicione novos métodos seguindo o padrão existente
- Documente todas as novas funcionalidades
- Teste compatibilidade com código existente 