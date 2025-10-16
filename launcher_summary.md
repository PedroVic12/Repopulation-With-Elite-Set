# Resumo das Correções e Arquitetura do `launcher.py`

Este documento resume os problemas encontrados no `launcher.py`, as soluções aplicadas e a arquitetura de software orientada a objetos utilizada no arquivo refatorado.

---

## 1. O Problema

O launcher apresentava dois bugs principais que causavam um comportamento inesperado na execução dos testes:

1.  **Execuções Duplicadas**: Ao solicitar a execução de, por exemplo, 2 configurações com 2 repetições cada (total de 4 execuções), o sistema executava 8 vezes. Isso ocorria porque o `launcher.py` chamava o `src/run.py` para cada repetição, mas o `src/run.py` ignorava o argumento recebido e executava seu próprio loop interno de repetições.

2.  **Configuração Incorreta**: Todas as execuções rodavam com os parâmetros da **Configuração 1**, mesmo quando o launcher indicava que estava iniciando a "Config 2". Isso era causado por uma flag `TEST_DEBUG = True` no `launcher.py` que forçava o envio do argumento `--config_num 1` em todas as chamadas.

## 2. As Soluções Aplicadas

Para corrigir os problemas e aumentar a confiabilidade, as seguintes alterações foram feitas:

1.  **Correção do Loop Duplicado (em `src/run.py`)**: O script `src/run.py` foi modificado para verificar se o argumento `--exec_num` foi fornecido. Se sim, ele executa **apenas** a repetição específica solicitada, em vez de rodar o loop completo. Isso deu ao `launcher.py` controle total sobre qual repetição executar.

2.  **Correção da Configuração Incorreta (em `launcher.py`)**: A flag `TEST_DEBUG` foi alterada para `False`, garantindo que o `launcher.py` passe o número da configuração correta (`--config_num 1`, `--config_num 2`, etc.) para o `src/run.py`.

3.  **Melhoria no Log de Garantia (em `src/run.py`)**: Foi adicionada uma linha de log no início da execução do `run.py` que imprime a combinação exata de parâmetros sendo utilizada (ex: `[INFO] Executando com a seguinte combinação de parâmetros: {'MUTACAO': 0.8, ...}`). Isso oferece uma confirmação explícita de qual configuração está em teste.

4.  **Refatoração do Gerenciamento de Threads (em `launcher.py`)**: O mecanismo de execução em segundo plano foi completamente reescrito para seguir as melhores práticas da biblioteca PySide6, o que nos leva à nova arquitetura.

## 3. Arquitetura Orientada a Objetos do `launcher.py`

A nova versão do `launcher.py` é um exemplo prático de uma aplicação de desktop robusta que utiliza conceitos avançados de programação para garantir que a interface gráfica nunca trave e que a comunicação entre as partes do sistema seja segura e organizada.

### Componentes Principais

-   **`LauncherWindow(QMainWindow)`**: A classe principal da aplicação, responsável por montar a janela e organizar os componentes visuais, como as abas.
-   **`ConfigTab` e `ParamsAGTab`**: Classes que representam as "views" (visões). Cada uma encapsula uma aba da interface, gerenciando seus próprios widgets e interações do usuário. Elas são responsáveis pela **entrada de dados**.
-   **`ExecutionTab(QWidget)`**: Atua como a **classe controladora** do processo de execução. Ela não executa a tarefa em si, mas gerencia a fila de execuções, atualiza a interface (barra de progresso, logs) e orquestra a criação e destruição das threads.
-   **`ScriptWorker(QObject)`**: É o **"Trabalhador"**. Esta classe contém a lógica que não pode rodar na thread principal (a chamada do `subprocess` que executa `run.py`). Ela é projetada especificamente para ser movida para uma thread separada.
-   **`QThread`**: É o **gerenciador da thread**. Sua única função é fornecer um contexto de execução em segundo plano para o objeto `ScriptWorker`.

### Conceitos de Programação Aplicados

-   **Encapsulamento**: Cada classe tem sua própria responsabilidade e dados. A `ConfigTab` não sabe como a `ExecutionTab` funciona, ela apenas emite um sinal quando o usuário clica em "Executar".

-   **Separação de Responsabilidades (Separation of Concerns)**: Este é um conceito-chave na nova arquitetura.
    -   A **Interface (UI)** é responsável apenas por exibir dados e capturar a entrada do usuário.
    -   O **Controlador (`ExecutionTab`)** gerencia a lógica da aplicação (a fila de testes, o progresso, etc.).
    -   O **Trabalhador (`ScriptWorker`)** executa a tarefa pesada em si.

-   **Padrão de Projeto Worker-Thread**: Esta é a mudança mais importante. Em vez de herdar de `QThread` e colocar a lógica dentro, seguimos o padrão recomendado pelo Qt:
    1.  A lógica pesada fica em um `QObject` (`ScriptWorker`).
    2.  Uma `QThread` vazia é criada.
    3.  O `worker` é movido para a `thread` com `worker.moveToThread(thread)`.
    4.  A `thread` é iniciada, e um sinal (`thread.started`) aciona o início do trabalho no `worker`.
    *   **Vantagem**: Isso garante que a thread da interface gráfica **nunca seja bloqueada**, mantendo o programa sempre responsivo, e permite um gerenciamento de memória mais seguro.

-   **Comunicação Assíncrona com Sinais e Slots**: Este é o mecanismo que permite a comunicação segura entre a thread de trabalho e a thread da interface.
    -   O `ScriptWorker` (na thread de trabalho) **emite sinais** como `log_updated(str)` ou `finished(int)` quando algo acontece.
    -   A `ExecutionTab` (na thread da interface) possui **slots** (métodos como `append_log` ou `on_single_execution_finished`) que são conectados a esses sinais. 
    -   O Qt garante que, mesmo que o sinal seja emitido de outra thread, o slot será executado de forma segura na thread a que ele pertence. Isso evita condições de corrida e corrupção de dados.
    -   O uso de decorators (`@Signal`, `@Slot`) é a sintaxe moderna e mais limpa para declarar esses elementos em PySide6.
