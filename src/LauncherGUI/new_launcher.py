import sys

from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow,  QVBoxLayout, QWidget, QLabel, QTabWidget, QScrollArea, 
)
from PySide6.QtCore import Qt

# --- IMPORTS DO PROJETO ---
from style import STYLESHEET

# --- CONFIGURAÇÃO ---
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "frontend"
RUN_FRAMEWORK_SCRIPT = SRC_DIR / "run.py"
DASHBOARD_SCRIPT = SRC_DIR / "DashboardApp" / "dashboard_RCE_APP.py"

# run.py com --config_num 1 e --exec_num N repetidamente.
TEST_DEBUG = False

# Parâmetros que podem variar via options.json (arrays)
VARYING_KEYS = {"MUTACAO", "CROSSOVER", "NUM_GENERATIONS", "POP_SIZE"}

from frontend.ConfigTab import ConfigTab
from frontend.ExecutionTab import ExecutionTab
from frontend.ParamsAGTab import ParamsAGTab
from backend.script_worker_controller import ConfigManager

class LauncherWindow(QMainWindow):
    """Janela principal da aplicação (UI Original mantida)."""
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("RCE Framework Launcher Desktop V3.1.1 - Otimizado para AG")
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        main_layout = QVBoxLayout(content)
        scroll.setWidget(content)
             
        self.setCentralWidget(scroll)
        
        self.create_header(main_layout)
        self.create_tabs(main_layout)
        self.statusBar().showMessage("Pronto.")

    def create_header(self, layout):
        title = QLabel("Repopulation-With-Elite-Set Framework")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Configuração e Execução em Tempo Real usando PySide6")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

    def create_tabs(self, layout):
        tab_widget = QTabWidget()

        # Recriando todas as abas originais
        self.config_tab = ConfigTab(self.config_manager)
        self.params_ag_tab = ParamsAGTab(self.config_manager)
        self.execution_tab = ExecutionTab(self.config_manager)
        
        
        # Adicionando as abas ao widget de abas 
        tab_widget.addTab(self.config_tab, "⚙️ Configuração")
        tab_widget.addTab(self.params_ag_tab, "⌨ Parametros AG - RCE")
        tab_widget.addTab(self.execution_tab, "▶️ Exibição de Logs e Dashboard")
        
        layout.addWidget(tab_widget)

        # Conectando sinais de gerenciamento de estado com Signal para trasmição de dados entre abas 
        self.config_tab.execution_requested.connect(self.execution_tab.start_executions)
        self.config_tab.execution_requested.connect(lambda: tab_widget.setCurrentWidget(self.execution_tab))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = LauncherWindow()
    window.showMaximized()
    sys.exit(app.exec())

# FIXED_BUG (2025-10-15):
# - Corrigido IndexError em ExecutionTab.run_next_configuration adicionando guarda para total_runs
# - Corrigido fluxo para evitar chamadas concorrentes que geravam current_run_number fora de sincronia
# - Adicionada flag `_finished_called` para bloquear callbacks tardios e evitar re-agendamento após finalização
# - Agendamento de próxima execução feito via QTimer.singleShot somente quando ainda houver runs pendentes e não estivermos finalizando
# - Mantive seus comentários e históricos; este bloco documenta as alterações de correção aplicadas
