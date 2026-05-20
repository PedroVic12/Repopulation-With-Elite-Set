# RCE Framework — Estrutura MVC PySide6

```
rce_framework/
│
├── app.py                          ← Ponto de entrada (mesmos imports/comentários originais)
├── config.py                       ← Todas as constantes globais (from config import *)
│
├── ui/
│   └── launcher_window.ui          ← Layout XML do Qt Designer (janela principal)
│
├── models/                         ← Dados, lógica de negócio, workers
│   ├── process_output_reader.py    ← QObject que lê stdout de subprocessos
│   ├── config_manager.py           ← Lê/salva params.json e options.json
│   ├── script_worker.py            ← Executa scripts Python em QThread
│   ├── execution_model.py          ← Gerencia ciclo de vida da execução AG
│   ├── power_system_model.py       ← Pandapower: load, run, contingências
│   └── results_repository.py      ← Formata resultados para a View
│
├── views/                          ← Interface gráfica (sem lógica de negócio)
│   ├── launcher_window.py          ← QMainWindow que carrega o .ui
│   ├── navigation_menu.py          ← Menu lateral com PyPushButton
│   └── iframes/                    ← Abas (tabs) do QTabWidget
│       ├── config_tab.py           ← Configuração da bateria de testes AG
│       ├── params_ag_tab.py        ← Editor de parâmetros avançados
│       ├── script_exec_tab.py      ← Log de execução + botões de controle
│       ├── terminal_tab.py         ← Terminal interativo (stdin/stdout)
│       └── analysis_tab.py         ← Análise SEP (NetworkCanvas, Plotly, etc.)
│
├── controllers/                    ← Orquestração Model ↔ View
│   ├── main_controller.py          ← Controller principal (app inteiro)
│   └── power_system_controller.py  ← Controller de análise de potência
│
└── db/                             ← Persistência local (SQLite, cache, etc.)
    └── __init__.py
```

## Como usar o arquivo .ui

### Opção 1 — Carregar em tempo de execução (método usado neste projeto)

```python
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice

loader = QUiLoader()
ui_file = QFile("ui/launcher_window.ui")
ui_file.open(QIODevice.ReadOnly)
self.ui = loader.load(ui_file, self)
ui_file.close()
```

### Opção 2 — Gerar código Python (alternativa)

```bash
pyside6-uic ui/launcher_window.ui -o ui/ui_launcher_window.py
```

Depois importe e use:

```python
from ui.ui_launcher_window import Ui_LauncherWindow
class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_LauncherWindow()
        self.ui.setupUi(self)
```

### Opção 3 — Editar visualmente

```bash
pyside6-designer ui/launcher_window.ui
# ou
designer ui/launcher_window.ui
```

## Fluxo de dados

```
NavigationMenu (sinal) → MainController (slot) → abre Tab (View)
ConfigTab (execution_requested) → MainController → ExecutionModel (ScriptWorker)
ScriptWorker (log_updated) → MainController → ScriptExecutionTab.append_log
```

## Adicionando novos scripts ao menu

Edite `config.py` → `CUSTOM_SCRIPTS`, depois descomente os loops em
`views/navigation_menu.py` e `controllers/main_controller.py`.
