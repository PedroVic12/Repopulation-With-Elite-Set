# Guia de Refatoração: De MVC para MVVM

Este guia descreve como refatorar a aplicação `main_launcher.py` de sua estrutura atual (um único arquivo com padrão MVC) para uma arquitetura MVVM (Model-View-ViewModel) mais robusta, modular e escalável, inspirada na estrutura do seu `app_template_desktop.py`.

## 1. O Que é MVVM e Por Que Usar?

- **Model**: Representa os dados e a lógica de negócio. Não tem conhecimento da interface. No seu código, são classes como `ConfigManager`, `ExecutionModel`, `PowerSystemModel`.
- **View**: A interface do usuário (UI). No seu código, são as classes de widgets como `LauncherWindow`, `ConfigTab`, `NavigationMenu`. A View deve ser "burra", apenas exibindo dados e encaminhando ações do usuário para o ViewModel.
- **ViewModel**: É a ponte entre o Model e a View. Ele prepara os dados do Model para serem exibidos na View e executa ações com base na entrada do usuário (comandos). No PySide, o ViewModel é tipicamente um `QObject` que usa o sistema de Sinais e Slots para se comunicar com a View sem conhecê-la diretamente.

**Vantagens:**
- **Organização:** Cada parte tem sua responsabilidade bem definida.
- **Testabilidade:** Você pode testar o ViewModel e o Model sem precisar de uma interface gráfica.
- **Manutenção:** É muito mais fácil encontrar e corrigir bugs ou adicionar novas funcionalidades.

## 2. Estrutura de Pastas Proposta

Baseado no seu `main_launcher.py` e nos imports do `app_template_desktop.py`, sugiro a seguinte estrutura de pastas dentro de `/src`:

```
src/
├── core/
│   ├── __init__.py
│   ├── settings_manager.py  # Mover ConfigManager e lógica de JSON para cá
│   └── workers.py           # Mover ScriptWorker, ProcessOutputReader, ExecutionModel
│
├── models/
│   ├── __init__.py
│   └── power_system_model.py # Mover PowerSystemModel, ResultsRepository
│
├── viewmodels/
│   ├── __init__.py
│   └── main_viewmodel.py    # O novo "cérebro" da aplicação (substitui o MainController)
│
└── views/
    ├── __init__.py
    ├── main_window.py       # A classe LauncherWindow, a janela principal
    │
    ├── components/
    │   ├── __init__.py
    │   ├── navigation_menu.py
    │   ├── terminal_tab.py
    │   └── plotly_widget.py
    │
    └── tabs/
        ├── __init__.py
        ├── config_tab.py
        ├── params_ag_tab.py
        ├── script_execution_tab.py
        └── power_analysis/
            ├── __init__.py
            ├── analysis_view.py       # PowerSystemAnalysisView
            ├── network_canvas.py
            └── selection_widget.py
```
O `main_launcher.py` atual seria substituído por um novo `main.py` na raiz do projeto, muito mais simples.

## 3. Guia de Refatoração Passo a Passo

### Passo 1: Mover as Classes de Modelo (Model)

O "Model" é a parte que lida com os dados e a lógica de negócio pura.

1.  **Crie o arquivo `src/core/settings_manager.py`:**
    - Mova a classe `ConfigManager` para este arquivo.
2.  **Crie o arquivo `src/core/workers.py`:**
    - Mova as classes `ProcessOutputReader`, `ScriptWorker` e `ExecutionModel` para este arquivo.
3.  **Crie o arquivo `src/models/power_system_model.py`:**
    - Mova as classes `PowerSystemModel` e `ResultsRepository` para este arquivo.

### Passo 2: Mover as Classes de Visualização (View)

A "View" é tudo que o usuário vê. Cada widget deve estar em seu próprio arquivo.

1.  **Crie a pasta `src/views/` e as subpastas `components/`, `tabs/` e `tabs/power_analysis/`.**
2.  **`src/views/main_window.py`:**
    - Mova a classe `LauncherWindow` para cá.
3.  **`src/views/components/`:**
    - Mova `NavigationMenu` para `navigation_menu.py`.
    - Mova `TerminalTab` para `terminal_tab.py`.
4.  **`src/views/tabs/`:**
    - Mova `ConfigTab` para `config_tab.py`.
    - Mova `ParamsAGTab` para `params_ag_tab.py`.
    - Mova `ScriptExecutionTab` para `script_execution_tab.py`.
    - Mova `MainAnalysisTab` para `analysis_selection_tab.py`
5.  **`src/views/tabs/power_analysis/`:**
    - Mova `PowerSystemAnalysisView` para `analysis_view.py`.
    - Mova `NetworkCanvas` para `network_canvas.py`.
    - Mova `AnalysisSelectionWidget` para `selection_widget.py`.

### Passo 3: Criar o ViewModel (A Mudança Principal)

O `MainController` atual será substituído por um `MainViewModel`. O ViewModel não deve conhecer a View diretamente (ex: nada de `self.view.tabs.addTab`). Ele apenas gerencia o estado e emite sinais.

**Crie o arquivo `src/viewmodels/main_viewmodel.py`:**

```python
# src/viewmodels/main_viewmodel.py
from PySide6.QtCore import QObject, Signal, Slot
from ..core.settings_manager import ConfigManager
from ..core.workers import ExecutionModel
# ... outros imports de models

class MainViewModel(QObject):
    # Sinal que a View vai ouvir para adicionar uma nova aba
    add_tab_requested = Signal(object, str) # Emite o widget e o nome da aba

    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.execution_model = ExecutionModel()
        self.open_tabs = {} # O ViewModel agora controla o estado das abas abertas

    @Slot()
    def open_config_tab(self):
        # O ViewModel cria a instância do widget da aba, mas não a adiciona à UI
        from ..views.tabs.config_tab import ConfigTab
        
        tab_name = "config_ag"
        if tab_name in self.open_tabs:
            # Lógica para focar na aba existente (pode ser outro sinal)
            return

        # Cria o widget e o armazena
        config_tab_widget = ConfigTab(self.config_manager)
        self.open_tabs[tab_name] = config_tab_widget
        
        # Emite um sinal com o widget pronto para a View adicionar
        self.add_tab_requested.emit(config_tab_widget, "⚙️ Configurar AG")
        
        # Conecta os sinais da nova aba
        config_tab_widget.execution_requested.connect(self.start_ag_execution)

    @Slot(list, int, int)
    def start_ag_execution(self, configs, runs_per_config, objective_function_index):
        # Lógica para iniciar a execução...
        # ...
        pass
    
    # Outros métodos para abrir outras abas seguem o mesmo padrão
```

### Passo 4: Adaptar a View e Criar o Ponto de Entrada

A View (`LauncherWindow`) agora se torna mais "burra". Ela ouve os sinais do ViewModel e atualiza a si mesma.

**Altere `src/views/main_window.py`:**

```python
# src/views/main_window.py
from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Slot

class LauncherWindow(QMainWindow):
    def __init__(self, viewmodel):
        super().__init__()
        self.viewmodel = viewmodel # Recebe o ViewModel
        # ... setup da UI ...

        # Conecta os sinais da UI (botões) aos slots do ViewModel
        self.nav_menu.config_ag_requested.connect(self.viewmodel.open_config_tab)
        
        # Conecta os slots da UI aos sinais do ViewModel
        self.viewmodel.add_tab_requested.connect(self.add_tab)

    @Slot(object, str)
    def add_tab(self, widget, name):
        # A View apenas executa a ordem de adicionar a aba
        index = self.tabs.addTab(widget, name)
        self.tabs.setCurrentIndex(index)
```

**Crie um novo `main.py` na raiz do projeto:**

```python
# main.py (novo)
import sys
from PySide6.QtWidgets import QApplication
from src.viewmodels.main_viewmodel import MainViewModel
from src.views.main_window import LauncherWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # ... carrega stylesheet, ícone, etc. ...
    
    # 1. Cria o ViewModel
    viewmodel = MainViewModel()
    
    # 2. Cria a View e passa o ViewModel para ela
    window = LauncherWindow(viewmodel)
    
    # 3. Exibe a janela
    window.showMaximized()
    
    sys.exit(app.exec())

```

Seguindo estes passos, seu `main_launcher.py` monolítico será transformado em uma aplicação bem estruturada, fácil de dar manutenção e muito mais profissional, assim como seu `app_template_desktop.py`.