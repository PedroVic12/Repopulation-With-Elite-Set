"""
Launcher Desktop App (PySide6) - Refatorado com DatabaseController e Observer
-----------------------------------------------------------------------------

Este aplicativo desktop organiza a configuração e execução do framework RCE.
Agora utiliza o DatabaseController (com Observer Pattern) para centralizar
todo o acesso a arquivos e notificar sobre mudanças.

Principais mudanças:
- Integração do `DatabaseController` para I/O de arquivos.
- `ConfigManager` e outras classes usam o `DatabaseController`.
- Tratamento robusto de arrays em `params.json` via `JsonEditor`.
- `ExecutionTab` simplificada e com botão de consolidação.
"""
import sys
import os
import json
import subprocess
import threading
import time
import shutil
from pathlib import Path
from functools import reduce
import operator
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
from src.database_controller_revised import DatabaseController
from src.event_system import EventObserver # Importa o Observer

# --- CONFIGURAÇÃO ---
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"

# arquivos de execução do framework e dashboard
RUN_FRAMEWORK_SCRIPT = SRC_DIR /"run_execution.py" 
DASHBOARD_SCRIPT = SRC_DIR / "DashboardApp" / "dashboard_RCE_APP.py"

# Parâmetros que podem variar via options.json (arrays)
VARYING_KEYS = {"MUTACAO", "CROSSOVER", "NUM_GENERATIONS", "POP_SIZE"}

class ConfigManager: 
    """Gerencia a lógica de configuração, usando o DatabaseController para I/O."""
    def __init__(self, db_controller: DatabaseController):
        self.db_controller = db_controller
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

    def __init__(self, config_manager: ConfigManager):
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
        general_layout.addWidget(QLabel("Execuções por Configuração:"), 0, 0)
        general_layout.addWidget(self.runs_per_config_spin, 0, 1)
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
        self.run_button = QPushButton("💾 Salvar Configurações e Iniciar Execuções")
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
        
        # Atualiza os valores fixos em params
        for name, info in self.param_widgets.items():
            if info["mode"].checkedButton().text() == "Fixo":
                try:
                    value = int(info["fixed"].text()) if info["is_int"] else float(info["fixed"].text())
                    base_params[name] = value
                except ValueError:
                    QMessageBox.critical(self, "Erro de Formato", f"Valor inválido para o parâmetro fixo '{name}'.")
                    return

        # Salva os arquivos de configuração
        options_to_save = {'repeticoes_por_config': self.runs_per_config_spin.value(), **variable_arrays}
        self.config_manager.db_controller.save_params(base_params)
        self.config_manager.db_controller.save_options(options_to_save)

        keys = list(variable_arrays.keys())
        combinations = [dict(zip(keys, v)) for v in product(*variable_arrays.values())] if keys else [{}]
        
        configurations = [dict(base_params, **combo) for combo in combinations]

        msg = f"{len(configurations)} configs únicas serão executadas {self.runs_per_config_spin.value()} vez(es) cada."
        QMessageBox.information(self, "Pronto para Iniciar", msg)
        self.execution_requested.emit(configurations, self.runs_per_config_spin.value())

class JsonEditor(QWidget):
    """Editor de JSON genérico para params.json e options.json."""
    def __init__(self, title, db_controller: DatabaseController, file_type: str):
        super().__init__()
        self.title = title
        self.db_controller = db_controller
        self.file_type = file_type # 'params' or 'options'
        self.fields = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        group = QGroupBox(self.title)
        v = QVBoxLayout(group)

        self.info_label = QLabel(f"Arquivo: {self.file_type}.json")
        self.info_label.setStyleSheet("color: #666;")
        v.addWidget(self.info_label)

        self.fields_widget = QWidget()
        self.fields_layout = QGridLayout(self.fields_widget)
        self.fields_layout.setColumnStretch(1, 1)
        v.addWidget(self.fields_widget)

        buttons_layout = QHBoxLayout()
        self.reload_btn = QPushButton("🔄 Recarregar")
        self.save_btn = QPushButton("💾 Salvar")
        self.reload_btn.clicked.connect(self.reload)
        self.save_btn.clicked.connect(self.save)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.reload_btn)
        buttons_layout.addWidget(self.save_btn)
        v.addLayout(buttons_layout)

        layout.addWidget(group)
        self.reload()

    def _get_data(self):
        if self.file_type == 'params':
            return self.db_controller.get_params()
        elif self.file_type == 'options':
            return self.db_controller.get_options()
        return {}

    def _save_data(self, data):
        if self.file_type == 'params':
            return self.db_controller.save_params(data)
        elif self.file_type == 'options':
            return self.db_controller.save_options(data)
        return False

    def detect_elem_type(self, lst):
        if not lst:
            return str # Default to string for empty lists
        types = {type(x) for x in lst}
        if int in types and float in types:
            return float
        if int in types and len(types) == 1:
            return int
        if float in types and len(types) == 1:
            return float
        return str

    def build_fields(self, data: dict):
        while self.fields_layout.count():
            item = self.fields_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.fields.clear()

        row = 0
        for key, value in data.items():
            label = QLabel(str(key))
            label.setMinimumWidth(180)
            self.fields_layout.addWidget(label, row, 0)

            if isinstance(value, list):
                editor = QLineEdit(json.dumps(value)) # Store lists as JSON string
                self.fields_layout.addWidget(editor, row, 1)
                self.fields[key] = {"widget": editor, "is_list": True, "orig_type": list}
            elif isinstance(value, int):
                editor = QLineEdit(str(value))
                editor.setValidator(QIntValidator())
                self.fields_layout.addWidget(editor, row, 1)
                self.fields[key] = {"widget": editor, "is_list": False, "orig_type": int}
            elif isinstance(value, float):
                editor = QLineEdit(str(value))
                editor.setValidator(QDoubleValidator())
                self.fields_layout.addWidget(editor, row, 1)
                self.fields[key] = {"widget": editor, "is_list": False, "orig_type": float}
            else:
                editor = QLineEdit(str(value))
                self.fields_layout.addWidget(editor, row, 1)
                self.fields[key] = {"widget": editor, "is_list": False, "orig_type": str}

            row += 1

    def reload(self):
        data = self._get_data()
        if not isinstance(data, dict):
            QMessageBox.critical(self, "Erro", f"Arquivo inválido: {self.file_type}.json")
            data = {}
        self.build_fields(data)

    def save(self):
        try:
            current_data = self._get_data()
            if not isinstance(current_data, dict):
                current_data = {}

            for key, meta in self.fields.items():
                w: QLineEdit = meta["widget"]
                txt = w.text().strip()
                
                if meta["is_list"]:
                    try:
                        # Tenta carregar a string como JSON (para listas)
                        parsed_list = json.loads(txt)
                        if not isinstance(parsed_list, list):
                            raise ValueError("Conteúdo não é uma lista JSON válida.")
                        current_data[key] = parsed_list
                    except (json.JSONDecodeError, ValueError) as e:
                        QMessageBox.warning(self, "Valor Inválido", f"Erro ao analisar lista para '{key}': {e}. Certifique-se de que é um JSON de lista válido (ex: [1, 2, 3]).")
                        return
                else:
                    orig_type = meta.get("orig_type", str)
                    try:
                        if orig_type is int:
                            current_data[key] = int(txt) if txt else 0
                        elif orig_type is float:
                            current_data[key] = float(txt) if txt else 0.0
                        elif orig_type is bool:
                            current_data[key] = txt.lower() in ('1', 'true', 'yes', 'sim')
                        else:
                            current_data[key] = txt
                    except ValueError:
                        QMessageBox.warning(self, "Valor Inválido", f"Erro ao converter valor para '{key}'. Verifique o formato.")
                        return

            if not self._save_data(current_data):
                QMessageBox.critical(self, "Erro", f"Falha ao salvar {self.file_type}.json")
                return
            QMessageBox.information(self, "Sucesso", f"Arquivo salvo: {self.file_type}.json")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")

class ParamsAGTab(QWidget):
    """Aba para editar todos os parâmetros em tabela (UI Original mantida)."""
    def __init__(self, db_controller: DatabaseController):
        super().__init__()
        self.db_controller = db_controller
        self.json_editor = JsonEditor("Editar Parâmetros (params.json)", self.db_controller, 'params')
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        header = QLabel("Edite os parâmetros base do algoritmo genético (params.json).")
        header.setWordWrap(True)
        layout.addWidget(header)
        layout.addWidget(self.json_editor)

class ExecutionTab(QWidget, EventObserver):
    """Aba de execução, logs e ações pós-execução."""
    def __init__(self, db_controller: DatabaseController):
        super().__init__()
        self.db_controller = db_controller
        self.execution_thread = None
        self.configurations = []
        self.runs_per_config = 0
        self.current_run_number = 0
        self.total_runs = 0
        
        # Subscreve para eventos de consolidação
        self.db_controller.subscribe("consolidation_finished", self)
        
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
        self.append_log("-