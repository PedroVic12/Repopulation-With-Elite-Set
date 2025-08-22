# Documentação do Projeto: RCE Framework Launcher

## 1. Visão Geral

Este projeto consiste em uma aplicação desktop (`Launcher`) para configurar e executar um framework de Algoritmo Genético (AG) chamado `Repopulation-With-Elite-Set` (RCE).

O objetivo da aplicação é permitir que o usuário configure e execute múltiplas baterias de testes (execuções) com diferentes parâmetros para o algoritmo genético, de forma organizada e robusta. Ao final, os resultados de todas as execuções podem ser consolidados em um único arquivo Excel para análise.

A arquitetura foi desenhada para separar as responsabilidades, tornando o sistema mais fácil de manter e estender.

## 2. Arquitetura

O sistema é composto por três componentes principais que trabalham em conjunto:

1.  **`laucher_revised.py` (O Maestro):**
    *   É a interface gráfica (GUI) construída com PySide6.
    *   Responsável por permitir ao usuário configurar os parâmetros base (`params.json`) e as variações de teste (`options.json`).
    *   Orquestra todo o processo: ele gera as combinações de parâmetros e chama o script de execução para cada uma delas, sequencialmente.
    *   Mostra os logs em tempo real e o progresso geral da bateria de testes.

2.  **`src/run_execution.py` (O Operário):**
    *   É um script de linha de comando simples e focado.
    *   Sua única responsabilidade é executar **uma única configuração** do algoritmo genético.
    *   Ele é chamado pelo `laucher_revised.py` repetidas vezes, uma para cada combinação de parâmetros.
    *   Lê a configuração que o Launcher salva no `params.json` e, ao final, salva o resultado individual da sua execução na pasta `src/output`.

3.  **`src/database_controller.py` (O Gerente de Dados):**
    *   É uma classe centralizadora que gerencia toda a leitura e escrita de arquivos do projeto.
    *   Abstrai o acesso aos arquivos `params.json`, `options.json` e aos arquivos de resultado.
    *   Tanto o `Launcher` quanto o `run_execution.py` usam o `DatabaseController` para manipular dados, garantindo consistência e robustez.

### Fluxo de Execução

O fluxo de uma bateria de testes acontece da seguinte forma:

1.  O usuário abre o `laucher_revised.py`.
2.  Na interface, ele define os parâmetros que serão fixos e aqueles que terão múltiplos valores para teste (ex: `MUTACAO` com valores `0.1`, `0.5`, `0.9`).
3.  O usuário clica em "Salvar e Executar".
4.  O **Launcher** calcula todas as combinações possíveis de parâmetros.
5.  Para cada combinação:
    a. O **Launcher** salva a combinação atual no arquivo `src/params.json` (usando o `DatabaseController`).
    b. O **Launcher** chama o script `src/run_execution.py`.
    c. O **`run_execution.py`** lê o `params.json` (via `DatabaseController`), executa o algoritmo e salva seu resultado individual (ex: `config_1_exec_1_results.json`) na pasta `src/output`.
6.  Após todas as execuções terminarem, o usuário pode clicar no botão **"Consolidar Resultados"** no Launcher.
7.  Isso aciona o método `consolidate_results()` do **`DatabaseController`**, que lê todos os JSONs de resultados individuais e gera um único arquivo `resultados_consolidados.xlsx`.

## 3. Componentes Principais e Exemplos de Uso

### `src/database_controller.py`

Esta é a classe mais importante para a organização dos dados.

**Classe `DatabaseController`:**

```python
import json
import pandas as pd
from pathlib import Path

class DatabaseController:
    def __init__(self, base_dir: Path):
        # ... inicialização dos caminhos dos arquivos ...

    def get_params(self) -> dict:
        """Carrega os parâmetros base de params.json."""
        # ... implementação ...

    def save_params(self, data: dict) -> bool:
        """Salva os parâmetros em params.json."""
        # ... implementação ...

    def get_options(self) -> dict:
        """Carrega as opções de variação de options.json."""
        # ... implementação ...

    def save_options(self, data: dict) -> bool:
        """Salva as opções de variação em options.json."""
        # ... implementação ...

    def save_individual_result(self, result_data: dict):
        """Salva o resultado de uma única execução em um JSON individual."""
        # ... implementação ...

    def consolidate_results(self):
        """Lê todos os JSONs de resultado e cria o arquivo Excel."""
        # ... implementação ...
```

**Exemplo de Uso:**

```python
# Exemplo de como o run_execution.py usa o controller
from database_controller import DatabaseController

# 1. Inicializa o controller
db = DatabaseController()

# 2. Carrega os parâmetros para a execução
params_atuais = db.get_params()
print(f"Executando com os seguintes parâmetros: {params_atuais}")

# ... (executa o algoritmo genético) ...

# 3. Cria um dicionário com os resultados
resultado_final = {
    "config_num": 1,
    "exec_num": 1,
    "params": params_atuais,
    "best_fitness": 0.987
}

# 4. Salva o resultado usando o controller
db.save_individual_result(resultado_final)
```

### `laucher_revised.py`

É a aplicação principal com a interface gráfica. Suas classes internas mais importantes são:

*   **`LauncherWindow`**: A janela principal que contém e organiza todas as abas.
*   **`ConfigManager`**: Uma classe que usa o `DatabaseController` para gerenciar a lógica de carregar e salvar as configurações.
*   **`ConfigTab`**: A primeira aba da interface, onde o usuário define quais parâmetros serão fixos ou variáveis e dispara a bateria de testes.
*   **`ParamsAGTab`**: A segunda aba, que mostra uma tabela com todos os parâmetros do `params.json` e permite a edição direta.
*   **`ExecutionTab`**: A terceira aba, onde os logs da execução são exibidos em tempo real e onde se encontra o botão para consolidar os resultados.

### `src/run_execution.py`

Este script foi simplificado para ter apenas uma função principal, `run_single_execution()`, que realiza os seguintes passos:
1.  Inicializa o `DatabaseController`.
2.  Usa `db_controller.get_params()` para ler a configuração que o Launcher preparou.
3.  Executa o `AlgoritimoEvolutivoRCE` com esses parâmetros.
4.  Coleta os dados do resultado (melhor fitness, melhores variáveis, etc.).
5.  Usa `db_controller.save_individual_result()` para salvar o resultado em um arquivo JSON único.

## 4. Guia de Uso

Para realizar uma bateria de testes, siga os passos:

1.  **Inicie o Launcher:** Execute o comando no seu terminal, a partir da raiz do projeto:
    ```bash
    python3 laucher_revised.py
    ```
2.  **Configure a Execução:**
    *   Na aba **"⚙️ Configuração e Execução"**, defina o número de repetições para cada configuração.
    *   Para cada parâmetro listado (Mutação, Crossover, etc.), escolha o modo:
        *   **Fixo:** O valor definido será usado em todas as execuções.
        *   **Variável:** Os 4 campos de input aparecerão. Preencha com os diferentes valores que você quer testar.
3.  **Edite Parâmetros Adicionais (Opcional):**
    *   Na aba **"Parametros AG"**, você pode ver e editar diretamente qualquer um dos parâmetros do arquivo `params.json`.
4.  **Inicie a Bateria de Testes:**
    *   Volte para a primeira aba e clique no botão **"💾 Salvar e Executar"**.
    *   O Launcher irá automaticamente para a aba **"📊 Dashboard e Logs"**, onde você poderá acompanhar o progresso em tempo real.
5.  **Consolide os Resultados:**
    *   Após o término de todas as execuções, clique no botão **"📄 Consolidar Resultados"** na parte inferior da aba de logs.
    *   O sistema irá ler todos os resultados individuais e gerar o arquivo `resultados_consolidados.xlsx` na pasta `src/output`.
6.  **Analise os Dados:**
    *   Abra o arquivo Excel gerado para analisar e comparar o desempenho das diferentes configurações.
