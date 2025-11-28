import os

from pathlib import Path
import time

from collections import deque

from PySide6.QtWidgets import (
 QPushButton, QVBoxLayout, QWidget, QLabel,
    QHBoxLayout, QTextEdit, QProgressBar,  QGroupBox, QMessageBox

)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, Slot, QObject
from pathlib import Path

from pathlib import Path
import sys

# Get the Path object for the current file
current_file_path = Path(__file__)

# Get the parent directory (the directory containing this file)
parent_directory = current_file_path.parent.parent

# Add the parent directory to the Python import path
sys.path.append(str(parent_directory))

# Now you can import modules from that parent directory
# For example, if you have 'my_module.py' in the parent directory:
from backend.script_worker_controller import ScriptWorker


#! Update 21/11/25 - Refatoração de classes e uso do app desktop template
#! --- CONFIGURAÇÃO --- (ajustar caminho de cada script da raiz do projeto)
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"
RUN_FRAMEWORK_SCRIPT = SRC_DIR / "run.py"
DASHBOARD_SCRIPT = SRC_DIR / "DashboardApp" / "dashboard_RCE_APP.py"

class ExecutionTab(QWidget):
    """Aba de execução, logs e ações pós-execução."""
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.db_controller = self.config_manager.db_controller
        self.thread = None
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.create_status_panel(layout)
        self.create_progress_bar(layout)
        self.create_log_area(layout)
        self.create_control_buttons(layout)

    def create_status_panel(self, layout):
        group = QGroupBox("Progresso da Bateria de Testes")
        h_layout = QHBoxLayout(group)
        self.status_label = QLabel("Aguardando início...")
        h_layout.addWidget(self.status_label)
        layout.addWidget(group)

    def create_progress_bar(self, layout):
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def create_log_area(self, layout):
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(QLabel("Log de Execução:"))
        layout.addWidget(self.log_text)

    def create_control_buttons(self, layout):
        control_layout = QHBoxLayout()
        self.stop_btn = QPushButton("⏹️ Parar Execução")
        self.stop_btn.clicked.connect(self.stop_execution)
        self.stop_btn.setEnabled(False)
        
        self.consolidate_btn = QPushButton("📄 Consolidar Resultados")
        self.consolidate_btn.clicked.connect(self.consolidate_results)

        self.run_dashboard_btn = QPushButton("📊 Abrir Dashboard")
        self.run_dashboard_btn.clicked.connect(self.run_dashboard)

        control_layout.addWidget(self.stop_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.consolidate_btn)
        control_layout.addWidget(self.run_dashboard_btn)
        layout.addLayout(control_layout)

    @Slot(list, int)
    def start_executions(self, configs, runs_per_config):
        if not RUN_FRAMEWORK_SCRIPT.exists():
            QMessageBox.critical(self, "Erro", f"Script não encontrado: {RUN_FRAMEWORK_SCRIPT}")
            return

        if self.thread and self.thread.isRunning():
            self.append_log("Já existe uma bateria em execução — ignorando nova solicitação.")
            return

        self.configurations = configs
        self.runs_per_config = runs_per_config
        self._pending_runs = deque()
        for cfg_idx in range(len(self.configurations)):
            for rep in range(1, self.runs_per_config + 1):
                self._pending_runs.append((cfg_idx, rep))
        
        self.total_runs = len(self._pending_runs)
        self.current_run_number = 0

        self.log_text.clear()
        self.append_log(f"Iniciando bateria de testes com {self.total_runs} execuções totais.")

        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, self.total_runs)
        self.progress_bar.setValue(0)
        
        self.run_next_configuration()

    def run_next_configuration(self):
        if not self._pending_runs:
            self.on_all_executions_finished(True, "Todas as execuções foram concluídas...")
            return

        config_index, repetition = self._pending_runs.popleft()
        current_config = self.configurations[config_index]
        
        self.status_label.setText(f"\nExecutando {self.current_run_number + 1}/{self.total_runs} (Config: {config_index + 1}, Rep: {repetition})")
        self.append_log("-" * 80)
        self.append_log(f"Iniciando Config {config_index + 1}, Repetição {repetition}")

        if not self.db_controller.save_params(current_config):
             self.append_log(f"❌ Erro ao salvar o arquivo de parâmetros.")
             self.on_all_executions_finished(False, "Erro de arquivo.")
             return

        args = ["--config_num", str(config_index + 1), "--exec_num", str(repetition)]
        
        self.thread = QThread()
        self.worker = ScriptWorker(RUN_FRAMEWORK_SCRIPT, args)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run_script)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.worker.log_updated.connect(self.append_log)
        self.worker.error.connect(self.handle_error)
        self.worker.finished.connect(self.on_single_execution_finished)

        self.thread.start()

    @Slot(int)
    def on_single_execution_finished(self, return_code):
        success = return_code == 0
        self.append_log(f"Finalizada execução. Sucesso: {success}. Código de retorno: {return_code}")
        
        if not success:
            self.append_log(f"❌ Erro na execução, pulando para a próxima.")
        
        self.current_run_number += 1
        self.progress_bar.setValue(self.current_run_number)

        if self._pending_runs:
            QTimer.singleShot(100, self.run_next_configuration)
        else:
            self.on_all_executions_finished(True, "Todas as execuções foram concluídas!!!")

    @Slot(str)
    def handle_error(self, message):
        self.append_log(f"[ERRO FATAL] {message}")
        self.stop_execution()

    def stop_execution(self):
        if self.worker:
            self.worker.stop()
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self._pending_runs.clear()
        self.on_all_executions_finished(False, "Interrompido pelo usuário.")

    def on_all_executions_finished(self, success, message):
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.status_label.setText(f"Finalizado! {message}")
        self.append_log(f"✅ {message}")
        
        self.thread = None
        self.worker = None

        try:
            main_win = self.window()
            if hasattr(main_win, 'config_tab') and hasattr(main_win.config_tab, 'run_button'):
                main_win.config_tab.run_button.setEnabled(True)
        except Exception as e:
            self.append_log(f"Não foi possível reativar o botão de execução: {e}")

        if success:
            QMessageBox.information(self, "Bateria de Testes Concluída!", "Abra o Dashboard para ver os resultados!")

    def consolidate_results(self):
        self.append_log("\nIniciando consolidação de resultados...")
        try:
            self.db_controller.consolidate_results()
            self.append_log("Resultados consolidados com sucesso!")
            QMessageBox.information(self, "Sucesso", "Resultados consolidados com sucesso!")
        except Exception as e:
            self.append_log(f"Erro durante a consolidação: {e}")
            QMessageBox.critical(self, "Erro", f"Falha ao consolidar resultados: {e}")

    def run_dashboard(self):
        PORTA=8501
        try:
            os.system(f"streamlit run {DASHBOARD_SCRIPT} --server.port {PORTA} &")
            self.append_log(f"\nDashboard iniciado em http://localhost:{PORTA}")
        except Exception as e:
            self.append_log(f"Erro ao iniciar dashboard: {e}")

    def append_log(self, message):
        self.log_text.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        self.log_text.ensureCursorVisible()
