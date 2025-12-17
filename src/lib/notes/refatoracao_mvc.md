# Documentação e Plano de Refatoração para Arquitetura MVC

Este documento descreve um plano para refatorar o `main_launcher.py` para uma arquitetura Model-View-Controller (MVC), inspirado nos exemplos de `app_template_desktop.py` e `Power-System-py`. Isso tornará o código mais organizado, escalável e fácil de manter, especialmente ao adicionar novas funcionalidades como a execução de diferentes scripts.

## 1. Análise da Arquitetura de Referência (MVC)

A análise dos seus exemplos (`app_template_desktop.py` e `Power-System-py`) revela uma clara separação de responsabilidades:

-   **Model**:
    -   **O que é**: Representa os dados e a lógica de negócio da aplicação. Não tem conhecimento sobre a interface do usuário.
    -   **Exemplos no seu código**: `PowerSystemModel` (lógica de simulação), `SettingsModel` (gerencia configurações).
    -   **Como funciona**: Executa cálculos, manipula dados e emite **sinais (signals)** quando seu estado muda (ex: `settings_changed`).

-   **View**:
    -   **O que é**: A interface gráfica do usuário (GUI). É responsável apenas pela apresentação dos dados.
    -   **Exemplos no seu código**: `MainWindow` (a janela principal), `SidebarWidget`, `NetworkCanvas` (widgets de exibição).
    -   **Como funciona**: Exibe os dados recebidos do Controller e emite **sinais** quando o usuário interage (ex: `run_simulation_requested`). **Não contém lógica de negócio**.

-   **Controller**:
    -   **O que é**: O intermediário que conecta o Model e a View.
    -   **Exemplos no seu código**: `PowerSystemController` ou a própria classe `MainWindow` em `app_template_desktop.py`.
    -   **Como funciona**: Ouve os sinais da View (ex: clique de botão), chama os métodos apropriados no Model para processar a solicitação e, em seguida, atualiza a View com os novos dados retornados pelo Model.

## 2. Plano de Refatoração para `main_launcher.py`

Vamos aplicar o mesmo padrão ao `main_launcher.py` para organizar melhor o código e facilitar a adição de novos botões e scripts.

### Passo 1: Separar o Model
A lógica de negócio já está parcialmente isolada. Vamos formalizar isso.

-   **`ConfigManager`**: Continuará sendo o nosso "Model de Configuração", responsável por carregar e salvar os arquivos `params.json` e `options.json`.
-   **`ScriptWorker`**: Já é um bom "Model de Execução", mas pode ser gerenciado por um Model maior.
-   **Novo `ExecutionModel` (proposta)**: Uma nova classe que vai gerenciar a fila de execuções (`deque`), o estado atual (`configurations`, `runs_per_config`), e o `ScriptWorker`. Ele emitirá sinais como `execution_started`, `log_updated`, `all_executions_finished`.

### Passo 2: Transformar a View
As classes de UI devem apenas emitir sinais e exibir dados.

-   **`LauncherWindow`**: Se tornará puramente a "View Principal". Ela não terá mais a lógica de abrir abas. Em vez disso, emitirá sinais como `open_config_tab_requested`.
-   **`NavigationMenu`**: Adicionaremos um novo sinal para cada novo botão, como `run_agendamento_requested`.
-   **`ConfigTab`, `ParamsAGTab`**: Permanecem como Views, mas seus sinais (como `execution_requested`) serão conectados ao Controller, não a outras abas.
-   **Novo `ScriptExecutionTab` (proposta)**: Uma aba genérica para rodar *qualquer* script. Ela receberá o nome do script a ser executado e exibirá os logs. Isso evita criar uma aba separada para `run.py`, `run_agendamento.py`, etc.

### Passo 3: Criar o `MainController`
Esta é a nova peça central que orquestrará tudo.

-   **`MainController`**:
    -   Irá instanciar o `LauncherWindow` (View) e os Models (`ConfigManager`, `ExecutionModel`).
    -   Conectará os sinais da View aos slots do Controller.
        -   `nav_menu.config_requested` -> `controller.open_config_tab`
        -   `nav_menu.run_agendamento_requested` -> `controller.open_agendamento_tab`
    -   Conectará os sinais dos Models à View.
        -   `execution_model.log_updated` -> `execution_tab.append_log`
    -   Conterá a lógica que hoje está dentro da `LauncherWindow` (ex: `open_or_focus_tab`).

---

## 4. Integração da Aba "Análise de Contingência"

Esta nova aba será uma aplicação completa dentro do launcher, fundindo a interface do `Power-System-py` com a lógica de seleção de casos do `CLI.py` e os dados das suas funções objetivo.

### Arquitetura da Nova Aba

A nova aba funcionará em dois estágios: **Seleção** e **Análise**.

1.  **Estágio de Seleção (View de Seleção)**:
    -   Ao clicar no novo botão "**🔬 Análise de SEP**" no menu principal, uma nova aba será aberta.
    -   Dentro desta aba, aparecerá uma `AnalysisSelectionWidget`. Esta widget, inspirada no seu `CLI_MENU_UI.py`, usará uma `QListWidget` para listar os casos de análise disponíveis (ex: "Análise de Contingência IEEE 14", "Análise IEEE 30", etc.).
    -   Quando o usuário selecionar um caso e clicar em "Carregar Análise", a `AnalysisSelectionWidget` emitirá um sinal com o identificador do caso escolhido (ex: `case_ieee14_analise`).

2.  **Estágio de Análise (View de Análise)**:
    -   O `MainController` receberá o sinal do seletor.
    -   Ele esconderá a `AnalysisSelectionWidget`.
    -   Ele instanciará a view principal da análise, a `PowerSystemAnalysisView`, que é uma adaptação de `QMainWindow` do seu `SYSTEM_ELECTRICAL_PANDAPOWER.py` para ser um `QWidget`.
    -   **Importação Dinâmica**: O Controller irá importar dinamicamente o módulo Python correspondente ao caso escolhido (ex: `src.utils.functions_fitness.analise_contingencia.analise_contingencia_ieee14`).
    -   **Injeção de Dados**: O Controller passará os DataFrames (`agendamento_df`, `contingencia_df`) e a função objetivo do módulo importado para o `PowerSystemController` (o controller da sub-aplicação).
    -   A `PowerSystemAnalysisView` será então exibida dentro da aba, preenchida com os dados corretos e pronta para uso.

### Plano de Implementação no Código

-   **`main_launcher.py`**:
    1.  **Copiar Classes**: Todas as classes do `SYSTEM_ELECTRICAL_PANDAPOWER.py` (como `PowerSystemModel`, `PowerSystemController`, `NetworkCanvas`, `SidebarWidget`, etc.) serão copiadas para dentro do `main_launcher.py`.
    2.  **Adaptar `MainWindow`**: A classe `MainWindow` do `Power-System-py` será renomeada para `PowerSystemAnalysisView` e será modificada para herdar de `QWidget` em vez de `QMainWindow`, para que possa ser usada como uma aba.
    3.  **Criar `AnalysisSelectionWidget`**: Uma nova classe de `QWidget` será criada para exibir a lista de análises disponíveis e emitir o sinal `analysis_selected(case_id)`.
    4.  **Criar `MainAnalysisTab`**: Uma `QWidget` que atuará como um contêiner. Ela usará um `QStackedLayout` para alternar entre a `AnalysisSelectionWidget` e a `PowerSystemAnalysisView`.
    5.  **Atualizar `MainController`**:
        -   Adicionar um novo slot `open_power_system_analysis_tab()`.
        -   Adicionar um dicionário `ANALYSIS_CASES` que mapeia os `case_id` para os caminhos dos módulos a serem importados.
        -   Adicionar um slot `load_analysis_case(case_id)` que executa a lógica de esconder o seletor, importar o módulo, instanciar e exibir a `PowerSystemAnalysisView`.
    6.  **Atualizar `NavigationMenu`**: Adicionar o novo botão e sinal `power_system_analysis_requested`.

Isso resultará em uma aplicação robusta e modular, onde o "launcher" atua como um contêiner principal para múltiplas "ferramentas" complexas, como a de Análise de Contingência.

## 3. Checklist de Sucesso (em 25 minutos)

-   [x] **Análise Concluída**: O padrão MVC dos projetos de referência foi compreendido.
-   [ ] **Estrutura MVC Implementada**: O novo `main_launcher.py` contém as classes `MainController`, `LauncherWindow` (View) e os Models (`ConfigManager`, `ExecutionModel`).
-   [ ] **Separação de Responsabilidades**:
    -   A `LauncherWindow` e as abas (`*Tab`) não contêm mais lógica de negócio, apenas emitem sinais.
    -   O `MainController` gerencia a criação e exibição das abas e inicia as execuções.
    -   A lógica de execução (fila, worker) está encapsulada no `ExecutionModel`.
-   [x] **Adição de Nova Funcionalidade**:
    -   Um novo botão "Executar Agendamento" foi adicionado ao `NavigationMenu`.
    -   Clicar no novo botão abre uma nova aba (`ScriptExecutionTab`) configurada para rodar `src/run_agendamento.py`.
    -   A execução do script de agendamento funciona e exibe logs na sua própria aba.
-   [x] **Modularidade**: A nova `ScriptExecutionTab` é genérica o suficiente para ser reutilizada para rodar outros scripts no futuro com poucas modificações.
-   [x] **Funcionalidade Preservada**: Todas as funcionalidades originais (Configuração, Parâmetros, Execução do `run.py`) continuam funcionando como antes.
-   [x] **Código Limpo e Documentado**: O novo código está mais legível, e o arquivo `refatoracao_mvc.md` serve como documentação da nova arquitetura.
