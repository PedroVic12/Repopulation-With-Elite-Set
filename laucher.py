import sys
import os
import json
import subprocess
import threading
import time
from pathlib import Path
from functools import reduce
import operator

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel,
    QHBoxLayout, QTextEdit, QProgressBar, QTabWidget, QGroupBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QLineEdit, QComboBox, QMessageBox, QRadioButton,
    QButtonGroup, QGridLayout
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QIcon

# --- CONFIGURAÇÃO ---
# pasta raiz do projeto
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"

# arquivos de configuração .json para AG
PARAMS_FILE = SRC_DIR / "params.json"
OPTIONS_FILE = SRC_DIR / "options.json"

# arquivos de execução do framework e dashboard
RUN_FRAMEWORK_SCRIPT = SRC_DIR /"run_framework_backup.py" 
#! Script refatorado da pasta lib
#RUN_FRAMEWORK_SCRIPT = BASE_DIR / "lib" / "rce_framework" / "main.py"
DASHBOARD_SCRIPT = SRC_DIR / "DashboardApp" / "dashboard_RCE_APP.py"

from style import STYLESHEET

class ConfigManager:
    def __init__(self):
        self.params = self.load_json(PARAMS_FILE)
        self.options = self.load_json(OPTIONS_FILE)

    def load_json(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar {file_path}: {e}")
            return {}

    def save_json(self, data, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar {file_path}: {e}")
            return False

class ExecutionThread(QThread):
    log_updated = Signal(str)
    execution_finished = Signal(bool, str)

    def __init__(self, script_path, args=None):
        super().__init__()
        self.script_path = script_path
        self.args = args or []
        self.process = None

    def run(self):
        try:
            cmd = [sys.executable, str(self.script_path)] + self.args
            self.log_updated.emit(f"Executando: {' '.join(cmd)}")
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, cwd=SRC_DIR
            )
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.log_updated.emit(line.strip())
            return_code = self.process.wait()
            success = return_code == 0
            self.execution_finished.emit(success, f"Código de retorno: {return_code}")
        except Exception as e:
            self.log_updated.emit(f"Erro na execução: {e}")
            self.execution_finished.emit(False, str(e))

    def stop(self):
        if self.process:
            self.process.terminate()

class ConfigTab(QWidget):
    execution_requested = Signal()

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.param_widgets = {}
        self.init_ui()
        self.update_summary()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Configurações Gerais
        general_group = QGroupBox("Configurações Gerais")
        general_layout = QVBoxLayout(general_group)
        
        self.runs_per_config_spin = QSpinBox()
        self.runs_per_config_spin.setRange(1, 100)
        self.runs_per_config_spin.setValue(self.config_manager.options.get('repeticoes_por_config', 1))
        self.runs_per_config_spin.valueChanged.connect(self.update_summary)
        general_layout.addWidget(QLabel("Execuções por Configuração:"))
        general_layout.addWidget(self.runs_per_config_spin)
        layout.addWidget(general_group)

        # Parâmetros AG
        ag_group = QGroupBox("Parâmetros do Algoritmo Genético")
        ag_layout = QGridLayout(ag_group)
        
        params_to_render = {
            "MUTACAO": self.config_manager.params.get("MUTACAO"),
            "CROSSOVER": self.config_manager.params.get("CROSSOVER"),
            "NUM_GENERATIONS": self.config_manager.params.get("NUM_GENERATIONS"),
            "POP_SIZE": self.config_manager.params.get("POP_SIZE"),
        }

        row, col = 0, 0
        for name, default_val in params_to_render.items():
            param_widget = self._create_param_widget(name, default_val)
            ag_layout.addWidget(param_widget, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1
        
        layout.addWidget(ag_group)

        # Resumo
        summary_group = QGroupBox("Resumo da Execução")
        summary_layout = QHBoxLayout(summary_group)
        self.unique_configs_label = QLabel("Configurações Únicas: 1")
        self.total_runs_label = QLabel(f"Total de Execuções: {self.runs_per_config_spin.value()}")
        summary_layout.addWidget(self.unique_configs_label)
        summary_layout.addWidget(self.total_runs_label)
        layout.addWidget(summary_group)

        # Botão de Execução
        self.run_button = QPushButton("💾 Salvar e Executar")
        self.run_button.setObjectName("run_button")
        self.run_button.clicked.connect(self.save_and_run)
        layout.addWidget(self.run_button, alignment=Qt.AlignCenter)

        layout.addStretch()

    def _create_param_widget(self, name, default_value):
        widget_group = QGroupBox(name)
        layout = QVBoxLayout(widget_group)
        
        # Mode selection
        mode_group = QButtonGroup(self)
        fixed_radio = QRadioButton("Fixo")
        variable_radio = QRadioButton("Variável")
        fixed_radio.setChecked(True)
        mode_group.addButton(fixed_radio)
        mode_group.addButton(variable_radio)
        
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(fixed_radio)
        mode_layout.addWidget(variable_radio)
        layout.addLayout(mode_layout)

        # Input widgets
        is_int = isinstance(default_value, int)
        if is_int:
            fixed_input = QSpinBox()
            fixed_input.setRange(1, 10000)
            fixed_input.setValue(default_value)
        else:
            fixed_input = QDoubleSpinBox()
            fixed_input.setRange(0.0, 1.0)
            fixed_input.setSingleStep(0.01)
            fixed_input.setValue(default_value)

        variable_inputs_widget = QWidget()
        variable_layout = QHBoxLayout(variable_inputs_widget)
        variable_layout.setContentsMargins(0,0,0,0)
        variable_inputs = []
        for i in range(4):
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"V{i+1}")
            variable_layout.addWidget(input_field)
            variable_inputs.append(input_field)
        variable_inputs_widget.setVisible(False)

        layout.addWidget(fixed_input)
        layout.addWidget(variable_inputs_widget)

        # Toggle logic
        fixed_radio.toggled.connect(lambda checked: fixed_input.setVisible(checked))
        variable_radio.toggled.connect(lambda checked: variable_inputs_widget.setVisible(checked))

        # Store widgets for later access
        self.param_widgets[name] = {
            "mode": mode_group,
            "fixed": fixed_input,
            "variable": variable_inputs
        }

        # Connect signals to update summary
        fixed_input.valueChanged.connect(self.update_summary)
        for var_input in variable_inputs:
            var_input.textChanged.connect(self.update_summary)
        mode_group.buttonClicked.connect(self.update_summary)

        return widget_group

    def update_summary(self):
        num_variations = []
        for name, widgets in self.param_widgets.items():
            is_variable = widgets["mode"].buttons()[1].isChecked()
            if is_variable:
                var_values = [inp.text() for inp in widgets["variable"] if inp.text()]
                if var_values:
                    num_variations.append(len(var_values))
        
        total_combinations = reduce(operator.mul, num_variations, 1) if num_variations else 1
        total_execucoes = total_combinations * self.runs_per_config_spin.value()

        self.unique_configs_label.setText(f"Configurações Únicas: {total_combinations}")
        self.total_runs_label.setText(f"Total de Execuções: {total_execucoes}")

    def save_and_run(self):
        try:
            final_config = self.config_manager.params.copy()
            optional_params = {}

            for name, widgets in self.param_widgets.items():
                is_variable = widgets["mode"].buttons()[1].isChecked()
                is_int = isinstance(widgets["fixed"], QSpinBox)
                
                if is_variable:
                    values = []
                    for field in widgets["variable"]:
                        if field.text():
                            try:
                                values.append(int(field.text()) if is_int else float(field.text()))
                            except ValueError:
                                QMessageBox.warning(self, "Valor Inválido", f"Por favor, insira um número válido para {name}.")
                                return
                    if values:
                        optional_params[name] = values
                    else: # Fallback to fixed if no variable values are provided
                        optional_params[name] = [widgets["fixed"].value()]
                else:
                    optional_params[name] = [widgets["fixed"].value()]

            final_config.update(optional_params)
            final_config['repeticoes_por_config'] = self.runs_per_config_spin.value()
            
            # Ensure correct types
            for k in ["NUM_GENERATIONS", "POP_SIZE"]:
                if k in final_config: final_config[k] = [int(x) for x in final_config[k]]
            for k in ["MUTACAO", "CROSSOVER"]:
                 if k in final_config: final_config[k] = [float(x) for x in final_config[k]]

            if self.config_manager.save_json(final_config, OPTIONS_FILE):
                QMessageBox.information(self, "Sucesso", f"Configuração salva em {OPTIONS_FILE.name}")
                self.execution_requested.emit()
            else:
                QMessageBox.critical(self, "Erro", "Falha ao salvar o arquivo de configuração.")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro inesperado: {e}")


class ExecutionTab(QWidget):
    def __init__(self):
        super().__init__()
        self.execution_thread = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        control_layout = QHBoxLayout()
        
        self.run_dashboard_btn = QPushButton("📊 Abrir Dashboard")
        self.run_dashboard_btn.clicked.connect(self.run_dashboard)
        control_layout.addWidget(self.run_dashboard_btn)
        
        self.stop_btn = QPushButton("⏹️ Parar Execução")
        self.stop_btn.clicked.connect(self.stop_execution)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        layout.addLayout(control_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(QLabel("Log de Execução:"))
        layout.addWidget(self.log_text)

    def start_execution(self):
        if not RUN_FRAMEWORK_SCRIPT.exists():
            QMessageBox.critical(self, "Erro", f"Script não encontrado: {RUN_FRAMEWORK_SCRIPT}")
            return
        
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.log_text.clear()
        
        self.execution_thread = ExecutionThread(RUN_FRAMEWORK_SCRIPT)
        self.execution_thread.log_updated.connect(self.append_log)
        self.execution_thread.execution_finished.connect(self.on_execution_finished)
        self.execution_thread.start()

    def run_dashboard(self):
        if not DASHBOARD_SCRIPT.exists():
            QMessageBox.critical(self, "Erro", f"Dashboard não encontrado: {DASHBOARD_SCRIPT}")
            return
        try:
            subprocess.Popen([
                "streamlit", "run", str(DASHBOARD_SCRIPT),
                "--server.port", "8501"
            ], cwd=BASE_DIR)
            self.append_log("Dashboard iniciado em http://localhost:8501")
        except Exception as e:
            self.append_log(f"Erro ao iniciar dashboard: {e}")

    def stop_execution(self):
        if self.execution_thread and self.execution_thread.isRunning():
            self.execution_thread.stop()
            self.append_log("Execução interrompida pelo usuário.")
        self.on_execution_finished(False, "Interrompido")

    def append_log(self, message):
        self.log_text.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        self.log_text.ensureCursorVisible()

    def on_execution_finished(self, success, message):
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        if success:
            self.append_log("✅ Execução concluída com sucesso!")
            QMessageBox.information(self, "Sucesso", "Framework executado com sucesso!")
        else:
            if "Interrompido" not in message:
                self.append_log(f"❌ Erro na execução: {message}")
                QMessageBox.critical(self, "Erro", f"Erro na execução: {message}")

class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("RCE Framework Launcher - Otimizado")
        self.setMinimumSize(900, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        title = QLabel("Repopulation-With-Elite-Set Framework")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        subtitle = QLabel("Configuração e Execução em Tempo Real usando PySide6")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)
        
        tab_widget = QTabWidget()
        self.config_tab = ConfigTab(self.config_manager)
        self.execution_tab = ExecutionTab()
        
        tab_widget.addTab(self.config_tab, "⚙️ Configuração e Execução")
        tab_widget.addTab(self.execution_tab, "📊 Dashboard e Logs")
        
        main_layout.addWidget(tab_widget)
        self.statusBar().showMessage("Pronto.")

        # Connect signals
        self.config_tab.execution_requested.connect(lambda: tab_widget.setCurrentWidget(self.execution_tab))
        self.config_tab.execution_requested.connect(self.execution_tab.start_execution)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = LauncherWindow()
    window.show()
    sys.exit(app.exec())