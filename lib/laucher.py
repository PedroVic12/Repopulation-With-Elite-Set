
import sys
import os
import json
import subprocess
import time
import shutil
from pathlib import Path
from itertools import product

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel,
    QHBoxLayout, QTextEdit, QProgressBar, QTabWidget, QGroupBox, QSpinBox,
    QLineEdit,  QMessageBox, QRadioButton,
    QButtonGroup, QGridLayout, QTableWidget, QTableWidgetItem, QPlainTextEdit,
    QScrollArea, QFrame, QGraphicsDropShadowEffect, QSizePolicy, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QIntValidator, QDoubleValidator, QColor

# --- IMPORTS DO PROJETO ---
from style import STYLESHEET
from database_controller import DatabaseController

# --- CONFIGURAÇÃO ---
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"
RUN_FRAMEWORK_SCRIPT = SRC_DIR / "run_execution.py"
DASHBOARD_SCRIPT = SRC_DIR / "DashboardApp" / "dashboard_RCE_APP.py"

# Parâmetros que podem variar via options.json (arrays)
VARYING_KEYS = {"MUTACAO", "CROSSOVER", "NUM_GENERATIONS", "POP_SIZE"}

class ConfigManager:
    """Gerencia a lógica de configuração, usando o DatabaseController para I/O."""
    def __init__(self):
        self.db_controller = DatabaseController(BASE_DIR)
        self.params = self.db_controller.get_params()
        self.options = self.db_controller.get_options()
        self.clean_options()

    def clean_options(self):
        """Mantém apenas arrays para chaves permitidas e deduplica valores."""
        current = self.options
        cleaned = {}
        if 'repeticoes_por_config' in current:
            cleaned['repeticoes_por_config'] = current['repeticoes_por_config']
        for k in VARYING_KEYS:
            if k in current and isinstance(current[k], list):
                cleaned[k] = list(dict.fromkeys(current[k]))
        
        if cleaned != current:
            self.options = cleaned
            self.db_controller.save_options(self.options)

class ExecutionThread(QThread):
    """Executa o framework em subprocesso dentro de uma QThread."""
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
                universal_newlines=True, cwd=SRC_DIR, encoding='utf-8', errors='replace'
            )
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.log_updated.emit(line.strip())
            return_code = self.process.wait()
            self.execution_finished.emit(return_code == 0, f"Código de retorno: {return_code}")
        except Exception as e:
            self.log_updated.emit(f"Erro na execução: {e}")
            self.execution_finished.emit(False, str(e))

    def stop(self):
        if self.process:
            self.process.terminate()
            self.log_updated.emit("Processo de execução terminado pelo usuário.")

class ConfigTab(QWidget):
    """Aba de Configuração e Execução rápida (UI Original mantida)."""
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
        ag_layout.setHorizontalSpacing(16)
        ag_layout.setVerticalSpacing(16)
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
        self.run_button.clicked.connect(self.prepare_and_run)
        layout.addWidget(self.run_button, alignment=Qt.AlignCenter)

    def _create_param_widget(self, name, default_value):
        # Mantendo a UI original com 4 campos de input para variáveis
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
        fixed_input = QLineEdit(str(default_value))
        validator = QIntValidator(1, 100000) if is_int else QDoubleValidator(0.0, 1.0, 5)
        fixed_input.setValidator(validator)

        variable_inputs_widget = QWidget()
        variable_layout = QGridLayout(variable_inputs_widget)
        variable_inputs = []
        for i in range(4):
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"V{i+1}")
            input_field.setValidator(validator)
            variable_layout.addWidget(input_field, i // 2, i % 2)
            variable_inputs.append(input_field)
        variable_inputs_widget.setVisible(False)

        layout.addWidget(fixed_input)
        layout.addWidget(variable_inputs_widget)

        fixed_radio.toggled.connect(fixed_input.setVisible)
        variable_radio.toggled.connect(variable_inputs_widget.setVisible)

        self.param_widgets[name] = {
            "mode": mode_group, "fixed": fixed_input, "variable": variable_inputs, "is_int": is_int
        }

        fixed_input.textChanged.connect(self.update_summary)
        for var_input in variable_inputs:
            var_input.textChanged.connect(self.update_summary)
        mode_group.buttonClicked.connect(self.update_summary)

        return widget_group

    def update_summary(self, _=None):
        variable_arrays = self._get_variable_arrays()
        num_combinations = len(list(product(*variable_arrays.values()))) if variable_arrays else 1
        total_execucoes = num_combinations * self.runs_per_config_spin.value()
        self.unique_configs_label.setText(f"Configurações Únicas: {num_combinations}")
        self.total_runs_label.setText(f"Total de Execuções: {total_execucoes}")

    def _get_variable_arrays(self):
        arrays = {}
        for name, info in self.param_widgets.items():
            if info["mode"].checkedButton().text() == "Variável":
                values = []
                for var_input in info["variable"]:
                    txt = var_input.text().strip()
                    if txt:
                        try:
                            value = int(txt) if info["is_int"] else float(txt)
                            values.append(value)
                        except ValueError:
                            pass # Ignora valores mal formatados
                if values:
                    arrays[name] = list(dict.fromkeys(values))
        return arrays

    def prepare_and_run(self):
        base_params = self.config_manager.db_controller.get_params()
        variable_arrays = self._get_variable_arrays()

        for name, info in self.param_widgets.items():
            if info["mode"].checkedButton().text() == "Fixo":
                base_params[name] = int(info["fixed"].text()) if info["is_int"] else float(info["fixed"].text())

        options_to_save = {'repeticoes_por_config': self.runs_per_config_spin.value(), **variable_arrays}
        self.config_manager.db_controller.save_params(base_params)
        self.config_manager.db_controller.save_options(options_to_save)

        keys = list(variable_arrays.keys())
        combinations = [dict(zip(keys, v)) for v in product(*variable_arrays.values())] if keys else [{}]
        
        configurations = [dict(base_params, **combo) for combo in combinations]

        msg = f"{len(configurations)} configs únicas serão executadas {self.runs_per_config_spin.value()} vez(es) cada."
        QMessageBox.information(self, "Pronto para Iniciar", msg)
        self.execution_requested.emit(configurations, self.runs_per_config_spin.value())

class ParamsAGTab(QWidget):
    """Aba para editar todos os parâmetros em tabela (UI Original mantida)."""
    def __init__(self, config_manager: 'ConfigManager'):
        super().__init__()
        self.config_manager = config_manager
        self.init_ui()
        self.reload()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Parâmetro", "Valor"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        buttons_layout = QHBoxLayout()
        self.reload_btn = QPushButton("🔄 Recarregar")
        self.save_btn = QPushButton("💾 Salvar")
        self.reload_btn.clicked.connect(self.reload)
        self.save_btn.clicked.connect(self.save)
        buttons_layout.addWidget(self.reload_btn)
        buttons_layout.addWidget(self.save_btn)
        layout.addLayout(buttons_layout)

    def reload(self):
        params = self.config_manager.db_controller.get_params()
        self.table.setRowCount(len(params))
        for r, (key, value) in enumerate(params.items()):
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, 0, key_item)
            self.table.setItem(r, 1, QTableWidgetItem(str(value)))

    def save(self):
        params = {}
        for r in range(self.table.rowCount()):
            key = self.table.item(r, 0).text()
            value_str = self.table.item(r, 1).text()
            try:
                # Tenta converter para int, float, ou mantém como string
                if '.' in value_str:
                    params[key] = float(value_str)
                else:
                    params[key] = int(value_str)
            except (ValueError, TypeError):
                # Lida com listas e outras strings
                if value_str.startswith('[') and value_str.endswith(']'):
                    try:
                        params[key] = json.loads(value_str)
                    except json.JSONDecodeError:
                        params[key] = value_str # Mantém como string se não for JSON válido
                else:
                    params[key] = value_str
        
        if self.config_manager.db_controller.save_params(params):
            QMessageBox.information(self, "Sucesso", "Parâmetros salvos.")
        else:
            QMessageBox.critical(self, "Erro", "Falha ao salvar parâmetros.")

class ExecutionTab(QWidget):
    """Aba de execução, logs e ações pós-execução."""
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.db_controller = self.config_manager.db_controller
        self.execution_thread = None
        self.configurations = []
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

    def start_executions(self, configs, runs_per_config):
        if not RUN_FRAMEWORK_SCRIPT.exists():
            QMessageBox.critical(self, "Erro", f"Script não encontrado: {RUN_FRAMEWORK_SCRIPT}")
            return

        self.configurations = configs
        self.runs_per_config = runs_per_config
        self.total_runs = len(self.configurations) * self.runs_per_config
        self.current_run_number = 0

        self.log_text.clear()
        self.append_log(f"Iniciando bateria de testes com {self.total_runs} execuções totais.")

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
        
        self.status_label.setText(f"Executando {self.current_run_number + 1}/{self.total_runs} (Config {config_index + 1}, Rep {repetition})")
        self.append_log("-" * 80)
        self.append_log(f"Iniciando Config {config_index + 1}, Repetição {repetition}")

        if not self.db_controller.save_params(current_config):
             self.append_log(f"❌ Erro ao salvar o arquivo de parâmetros.")
             self.on_all_executions_finished(False, "Erro de arquivo.")
             return

        args = ["--config_num", str(config_index + 1), "--exec_num", str(repetition)]
        self.execution_thread = ExecutionThread(RUN_FRAMEWORK_SCRIPT, args)
        self.execution_thread.log_updated.connect(self.append_log)
        self.execution_thread.execution_finished.connect(self.on_single_execution_finished)
        self.execution_thread.start()

    def on_single_execution_finished(self, success, message):
        self.append_log(f"Finalizada execução. Sucesso: {success}. {message}")
        if not success:
            self.append_log(f"❌ Erro na execução, pulando para a próxima.")
        
        self.current_run_number += 1
        self.progress_bar.setValue(self.current_run_number)
        QTimer.singleShot(100, self.run_next_configuration)

    def stop_execution(self):
        self.current_run_number = self.total_runs
        if self.execution_thread and self.execution_thread.isRunning():
            self.execution_thread.stop()
        self.on_all_executions_finished(False, "Interrompido pelo usuário.")

    def on_all_executions_finished(self, success, message):
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.status_label.setText(f"Finalizado. {message}")
        self.append_log(f"✅ {message}")
        QMessageBox.information(self, "Bateria de Testes Concluída", message)

    def consolidate_results(self):
        self.append_log("Iniciando consolidação manual de resultados...")
        try:
            
            self.db_controller.consolidar_script_button()

            #! Alteração na arquitetura do projeto com MVC  + Observer + Controller
            #self.db_controller.consolidate_results()
            self.append_log("Consolidação com Desgin Pattern DatabaseController!")
            self.append_log("Verifique o terminal para ver quantos arquivos foram resultados da simulação!")
            QMessageBox.information(self, "Sucesso", "Resultados consolidados com sucesso!")
        except Exception as e:
            self.append_log(f"Erro durante a consolidação: {e}")
            QMessageBox.critical(self, "Erro", f"Falha ao consolidar resultados: {e}")

    def run_dashboard(self):
        try:
            subprocess.Popen(["streamlit", "run", str(DASHBOARD_SCRIPT), "--server.port", "8501"], cwd=BASE_DIR)
            self.append_log("\nDashboard iniciado em http://localhost:8501")
        except Exception as e:
            self.append_log(f"Erro ao iniciar dashboard: {e}")

    def append_log(self, message):
        self.log_text.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        self.log_text.ensureCursorVisible()

class LauncherWindow(QMainWindow):
    """Janela principal da aplicação (UI Original mantida)."""
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("RCE Framework Launcher Desktop - Otimizado para AG")
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
        
        tab_widget.addTab(self.config_tab, "⚙️ Configuração e Execução")
        tab_widget.addTab(self.params_ag_tab, "Parametros AG")
        tab_widget.addTab(self.execution_tab, "📊 Dashboard e Logs")
        
        layout.addWidget(tab_widget)

        # Conectando sinais
        self.config_tab.execution_requested.connect(self.execution_tab.start_executions)
        self.config_tab.execution_requested.connect(lambda: tab_widget.setCurrentWidget(self.execution_tab))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = LauncherWindow()
    window.showMaximized()
    sys.exit(app.exec())
