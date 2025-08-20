# 📊 Consolidador de Resultados

Este script consolida automaticamente todos os resultados das execuções das pastas `run_*` em um único arquivo Excel.

## 🚀 Como Usar

### Opção 1: Execução Automática (Recomendado)
```bash
chmod +x executar_consolidacao.sh
./executar_consolidacao.sh
```

### Opção 2: Execução Manual
```bash
# 1. Instalar dependências
pip3 install -r requirements.txt

# 2. Executar script
python3 consolidar_resultados.py
```

## 📁 Estrutura Esperada

O script espera encontrar a seguinte estrutura:
```
output/
├── run_2025-08-20_20-42-20/
│   ├── config_1/
│   │   ├── exec_1_results.json
│   │   ├── exec_2_results.json
│   │   └── exec_3_results.json
│   └── config_2/
│       └── exec_1_results.json
├── run_2025-08-20_20-43-06/
│   └── config_1/
│       └── exec_1_results.json
└── ...
```

## 📊 Arquivo de Saída

O script gera um arquivo Excel com:
- **Identificação**: pasta_run, configuracao, execucao, config_num
- **Parâmetros**: todos os parâmetros de cada execução
- **Resultados**: melhores variáveis encontradas

### Exemplo de Colunas:
- `pasta_run`: Nome da pasta de execução
- `configuracao`: Nome da configuração
- `execucao`: Número da execução
- `param_ARRAY_VAR_1`, `param_ARRAY_VAR_2`, etc.
- `param_CROSSOVER`, `param_MUTACAO`, etc.
- `best_var_1`, `best_var_2`, etc.

## 🔧 Dependências

- Python 3.7+
- pandas
- openpyxl
- pathlib2

## 📝 Logs

O script mostra:
- Número de pastas encontradas
- Número de configurações por pasta
- Estatísticas finais
- Caminho do arquivo salvo

## 🐛 Solução de Problemas

### Erro de Dependências
```bash
pip3 install --upgrade pip
pip3 install pandas openpyxl --user
```

### Erro de Permissão
```bash
chmod +x executar_consolidacao.sh
```

### Python não encontrado
```bash
# Ubuntu/Debian
sudo apt-get install python3 python3-pip

# CentOS/RHEL
sudo yum install python3 python3-pip

# Arch/Manjaro
sudo pacman -S python python-pip
```

## 📈 Exemplo de Saída

```
=== CONSOLIDADOR DE RESULTADOS ===
Iniciando consolidação...

Encontradas 4 pastas de execução:
  run_2025-08-20_20-42-20: 2 configurações
  run_2025-08-20_20-43-06: 1 configurações
  run_2025-08-20_20-25-18: 1 configurações
  run_2025-08-20_20-09-25: 1 configurações

Arquivo salvo com sucesso: resultados_consolidados_20250820_204500.xlsx
Total de resultados consolidados: 7

Estatísticas:
  - Pastas de execução: 4
  - Configurações: 5
  - Execuções: 7

✅ Consolidação concluída com sucesso!
📁 Arquivo salvo em: resultados_consolidados_20250820_204500.xlsx
``` 