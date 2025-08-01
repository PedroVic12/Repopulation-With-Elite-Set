import sys
import os
import json
import subprocess
import threading
import time
from pathlib import Path
from functools import reduce
import operator
from itertools import product

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel,
    QHBoxLayout, QTextEdit, QProgressBar, QTabWidget, QGroupBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QLineEdit, QComboBox, QMessageBox, QRadioButton,
    QButtonGroup, QGridLayout
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QIntValidator, QDoubleValidator

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
                universal_newlines=True, cwd=SRC_DIR, encoding='utf-8'
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
            self.log_updated.emit("Processo de execução terminado pelo usuário.")

class ConfigTab(QWidget):
    execution_requested = Signal(list, int)

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.param_widgets = {}
        self.init_ui()
        self.update_summary()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.create_general_settings(layout)
        self.create_ag_params(layout)
        self.create_summary(layout)
        self.create_run_button(layout)
        layout.addStretch()

    def create_general_settings(self, layout):
        general_group = QGroupBox("Configurações Gerais")
        general_layout = QVBoxLayout(general_group)
        self.runs_per_config_spin = QSpinBox()
        self.runs_per_config_spin.setRange(1, 100)
        self.runs_per_config_spin.setValue(self.config_manager.options.get('repeticoes_por_config', 1))
        self.runs_per_config_spin.valueChanged.connect(self.update_summary)
        general_layout.addWidget(QLabel("Execuções por Configuração:"))
        general_layout.addWidget(self.runs_per_config_spin)
        layout.addWidget(general_group)

    def create_ag_params(self, layout):
        ag_group = QGroupBox("Parâmetros do Algoritmo Genético")
        ag_layout = QGridLayout(ag_group)
        params_to_render = {
            "MUTACAO": self.config_manager.params.get("MUTACAO", 0.1),
            "CROSSOVER": self.config_manager.params.get("CROSSOVER", 0.8),
            "NUM_GENERATIONS": self.config_manager.params.get("NUM_GENERATIONS", 100),
            "POP_SIZE": self.config_manager.params.get("POP_SIZE", 50),
        }
        row, col = 0, 0
        for name, default_val in params_to_render.items():
            param_widget = self._create_param_widget(name, default_val)
            ag_layout.addWidget(param_widget, row, col)
            col += 1
            if col > 1:
                col, row = 0, row + 1
        layout.addWidget(ag_group)

    def create_summary(self, layout):
        summary_group = QGroupBox("Resumo da Execução")
        summary_layout = QHBoxLayout(summary_group)
        self.unique_configs_label = QLabel("Configurações Únicas: 1")
        self.total_runs_label = QLabel(f"Total de Execuções: {self.runs_per_config_spin.value()}")
        summary_layout.addWidget(self.unique_configs_label)
        summary_layout.addWidget(self.total_runs_label)
        layout.addWidget(summary_group)

    def create_run_button(self, layout):
        self.run_button = QPushButton("💾 Salvar e Executar")
        self.run_button.setObjectName("run_button")
        self.run_button.clicked.connect(self.prepare_and_run)
        layout.addWidget(self.run_button, alignment=Qt.AlignCenter)

    def _create_param_widget(self, name, default_value):
        widget_group = QGroupBox(name)
        layout = QVBoxLayout(widget_group)
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

        is_int = isinstance(default_value, int)
        fixed_input = QLineEdit()
        if is_int:
            fixed_input.setValidator(QIntValidator(1, 100000))
        else:
            fixed_input.setValidator(QDoubleValidator(0.0, 1.0, 5))
        fixed_input.setText(str(default_value))

        variable_inputs_widget = QWidget()
        variable_layout = QHBoxLayout(variable_inputs_widget)
        variable_layout.setContentsMargins(0,0,0,0)
        variable_inputs = []
        for i in range(4):
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"V{i+1}")
            if is_int:
                input_field.setValidator(QIntValidator(1, 100000))
            else:
                input_field.setValidator(QDoubleValidator(0.0, 1.0, 5))
            variable_layout.addWidget(input_field)
            variable_inputs.append(input_field)
        variable_inputs_widget.setVisible(False)

        layout.addWidget(fixed_input)
        layout.addWidget(variable_inputs_widget)

        fixed_radio.toggled.connect(fixed_input.setVisible)
        variable_radio.toggled.connect(variable_inputs_widget.setVisible)

        self.param_widgets[name] = {
            "mode": mode_group, "fixed": fixed_input,
            "variable": variable_inputs, "is_int": is_int
        }

        fixed_input.textChanged.connect(self.update_summary)
        for var_input in variable_inputs:
            var_input.textChanged.connect(self.update_summary)
        mode_group.buttonClicked.connect(self.update_summary)

        return widget_group

    def update_summary(self, _=None):
        num_variations = []
        for name, widgets in self.param_widgets.items():
            if widgets["mode"].buttons()[1].isChecked():
                var_values = [inp.text() for inp in widgets["variable"] if inp.text()]
                if var_values:
                    num_variations.append(len(var_values))
        
        total_combinations = reduce(operator.mul, num_variations, 1) if num_variations else 1
        total_execucoes = total_combinations * self.runs_per_config_spin.value()

        self.unique_configs_label.setText(f"Configurações Únicas: {total_combinations}")
        self.total_runs_label.setText(f"Total de Execuções: {total_execucoes}")

    def prepare_and_run(self):
        try:
            variable_params, fixed_params = {}, {}
            for name, widgets in self.param_widgets.items():
                is_int = widgets["is_int"]
                if widgets["mode"].buttons()[1].isChecked(): # Variável
                    values = []
                    for field in widgets["variable"]:
                        if field.text():
                            try:
                                values.append(int(field.text()) if is_int else float(field.text()))
                            except ValueError:
                                QMessageBox.warning(self, "Valor Inválido", f"Valor inválido para {name}: '{field.text()}'")
                                return
                    if values: variable_params[name] = values
                    else: fixed_params[name] = int(widgets["fixed"].text()) if is_int else float(widgets["fixed"].text())
                else: # Fixo
                    try:
                        fixed_params[name] = int(widgets["fixed"].text()) if is_int else float(widgets["fixed"].text())
                    except ValueError:
                        QMessageBox.warning(self, "Valor Inválido", f"Valor inválido para {name}: '{widgets['fixed'].text()}'")
                        return

            keys, values = variable_params.keys(), variable_params.values()
            configurations = [dict(zip(keys, v)) for v in product(*values)] if keys else [{}]
            for config in configurations:
                config.update(fixed_params)

            runs_per_config = self.runs_per_config_spin.value()
            options = self.config_manager.options.copy()
            options['repeticoes_por_config'] = runs_per_config
            if not self.config_manager.save_json(options, OPTIONS_FILE):
                QMessageBox.critical(self, "Erro", f"Falha ao salvar {OPTIONS_FILE.name}")
                return

            msg = f"{len(configurations)} configs únicas serão executadas {runs_per_config} vez(es) cada."
            QMessageBox.information(self, "Pronto para Iniciar", msg)
            self.execution_requested.emit(configurations, runs_per_config)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao preparar execução: {e}")

class ExecutionTab(QWidget):
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.execution_thread = None
        self.configurations = []
        self.runs_per_config = 0
        self.current_run_number = 0
        self.total_runs = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.create_control_buttons(layout)
        self.create_status_panel(layout)
        self.create_progress_bar(layout)
        self.create_log_area(layout)

    def create_control_buttons(self, layout):
        control_layout = QHBoxLayout()
        self.run_dashboard_btn = QPushButton("📊 Abrir Dashboard")
        self.run_dashboard_btn.clicked.connect(self.run_dashboard)
        control_layout.addWidget(self.run_dashboard_btn)
        self.stop_btn = QPushButton("⏹️ Parar Execução")
        self.stop_btn.clicked.connect(self.stop_execution)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        layout.addLayout(control_layout)

    def create_status_panel(self, layout):
        self.current_config_group = QGroupBox("Configuração da Execução Atual")
        current_config_layout = QVBoxLayout(self.current_config_group)
        self.current_config_label = QLabel("Aguardando início...")
        self.current_config_label.setAlignment(Qt.AlignCenter)
        current_config_layout.addWidget(self.current_config_label)
        layout.addWidget(self.current_config_group)

    def create_progress_bar(self, layout):
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def create_log_area(self, layout):
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(QLabel("Log de Execução:"))
        layout.addWidget(self.log_text)

    def start_executions(self, configurations, runs_per_config):
        if not RUN_FRAMEWORK_SCRIPT.exists():
            QMessageBox.critical(self, "Erro", f"Script não encontrado: {RUN_FRAMEWORK_SCRIPT}")
            return
        
        self.configurations = configurations
        self.runs_per_config = runs_per_config
        self.total_runs = len(self.configurations) * self.runs_per_config
        self.current_run_number = 0
        
        self.log_text.clear()
        self.append_log(f"Iniciando bateria de testes com {len(self.configurations)} configs e {self.runs_per_config} repetições.")
        self.append_log(f"Total de execuções: {self.total_runs}")

        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, self.total_runs)
        self.progress_bar.setValue(0)
        
        self.run_next_configuration()

    def run_next_configuration(self):
        if self.current_run_number >= self.total_runs:
            self.on_all_executions_finished(True, "Todas as execuções foram concluídas.")
            return

        config_index = self.current_run_number // self.runs_per_config
        repetition = (self.current_run_number % self.runs_per_config) + 1
        current_config = self.configurations[config_index]
        
        config_str = ", ".join([f"{k}: {v}" for k, v in current_config.items()])
        self.current_config_label.setText(f"Execução {self.current_run_number + 1}/{self.total_runs} (Rep. {repetition}) | {config_str}")
        self.append_log("-" * 20)
        self.append_log(f"Iniciando Config {config_index + 1}, Execução {repetition}: {config_str}")

        base_params = self.config_manager.load_json(PARAMS_FILE)
        base_params.update(current_config)
        if not self.config_manager.save_json(base_params, PARAMS_FILE):
             self.append_log(f"❌ Erro ao salvar o arquivo de parâmetros {PARAMS_FILE}")
             self.on_all_executions_finished(False, "Erro de arquivo.")
             return

        args = ["--config_num", str(config_index + 1), "--exec_num", str(repetition)]
        self.execution_thread = ExecutionThread(RUN_FRAMEWORK_SCRIPT, args)
        self.execution_thread.log_updated.connect(self.append_log)
        self.execution_thread.execution_finished.connect(self.on_single_execution_finished)
        self.execution_thread.start()

    def on_single_execution_finished(self, success, message):
        self.append_log(f"Finalizada execução {self.current_run_number + 1}. Sucesso: {success}. {message}")
        if not success:
            self.append_log(f"❌ Erro na execução, pulando para a próxima.")
        
        self.current_run_number += 1
        self.progress_bar.setValue(self.current_run_number)
        
        QTimer.singleShot(100, self.run_next_configuration)

    def run_dashboard(self):
        if not DASHBOARD_SCRIPT.exists():
            QMessageBox.critical(self, "Erro", f"Dashboard não encontrado: {DASHBOARD_SCRIPT}")
            return
        try:
            subprocess.Popen(["streamlit", "run", str(DASHBOARD_SCRIPT), "--server.port", "8501"], cwd=BASE_DIR)
            self.append_log("Dashboard iniciado em http://localhost:8501")
        except Exception as e:
            self.append_log(f"Erro ao iniciar dashboard: {e}")

    def stop_execution(self):
        self.current_run_number = self.total_runs # Prevent next run
        if self.execution_thread and self.execution_thread.isRunning():
            self.execution_thread.stop()
        self.on_all_executions_finished(False, "Interrompido pelo usuário.")

    def append_log(self, message):
        self.log_text.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        self.log_text.ensureCursorVisible()

    def on_all_executions_finished(self, success, message):
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.current_config_label.setText(f"Finalizado. {message}")
        if success:
            self.append_log(f"✅ {message}")
            QMessageBox.information(self, "Sucesso", "Bateria de testes concluída com sucesso!")
        else:
            self.append_log(f"❌ {message}")
            if "Interrompido" not in message:
                QMessageBox.critical(self, "Erro", f"A bateria de testes terminou com erro: {message}")

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
        self.config_tab = ConfigTab(self.config_manager)
        self.execution_tab = ExecutionTab(self.config_manager)
        
        tab_widget.addTab(self.config_tab, "⚙️ Configuração e Execução")
        tab_widget.addTab(self.execution_tab, "📊 Dashboard e Logs")
        
        layout.addWidget(tab_widget)

        # Connect signals
        self.config_tab.execution_requested.connect(self.execution_tab.start_executions)
        self.config_tab.execution_requested.connect(lambda: tab_widget.setCurrentWidget(self.execution_tab))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = LauncherWindow()
    window.show()
    sys.exit(app.exec())
