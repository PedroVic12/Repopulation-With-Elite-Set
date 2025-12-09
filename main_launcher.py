"Arquivo principal do launcher unificado."
import sys
import os
import json
import subprocess
import time
from pathlib import Path
from itertools import product
from collections import deque

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel,
    QHBoxLayout, QTextEdit, QProgressBar, QTabWidget, QGroupBox, QSpinBox,
    QLineEdit,  QMessageBox, QRadioButton,
    QButtonGroup, QGridLayout, QTableWidget, QTableWidgetItem, QPlainTextEdit,
    QScrollArea, QFrame, QGraphicsDropShadowEffect, QSizePolicy, QHeaderView, QAbstractItemView,
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, Slot, QObject, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QIcon, QIntValidator, QDoubleValidator, QColor


# --- IMPORTS DO PROJETO ---
# from style import STYLESHEET # Removido para internalizar o estilo
from src.database_controller import DatabaseController

# Estilo QSS moderno e temático (escuro + amarelo)
STYLESHEET = """
/* ========================================
   Base/Tipografia/Janela
   ======================================== */
QWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 12px;
}
QMainWindow { background-color: #1e1e1e; }

/* Títulos */
QLabel#title { font-size: 24px; font-weight: bold; color: #00d4ff; padding: 10px; }
QLabel#subtitle { font-size: 14px; color: #cccccc; padding: 5px; }

/* ========================================
   Botões
   ======================================== */
QPushButton {
    background-color: #007acc;
    color: white;
    font-size: 14px;
    font-weight: bold;
    padding: 12px 20px;
    border-radius: 6px;
    border: none;
    min-width: 120px;
}
QPushButton:hover { background-color: #005a9e; }
QPushButton:pressed { background-color: #004578; }
QPushButton#run_button { background-color: #28a745; }
QPushButton#run_button:hover { background-color: #218838; }
QTabWidget::tab:selected { background-color: #007acc; }

/* ========================================
   RadioButtons
   ======================================== */
QRadioButton { font-size: 24px; color: #ffffff; padding: 2px; }
QRadioButton:checked { font-weight: bold;  }
QRadioButton:hover { background-color: #007acc; }
QRadioButton:checked:hover { background-color: #007acc;  }

/* ========================================
   Containers (GroupBox, Tabs)
   ======================================== */
QGroupBox {
    font-weight: bold;
    border: 2px solid #404040;
    border-radius: 8px;
    margin-top: 10px;
    padding: 20px 10px 10px 10px;
    font-size: 14px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
    color: #00d4ff;
}
QTabWidget::pane { border: 1px solid #404040; background-color: #1e1e1e; }
QTabBar::tab {
    background-color: #2d2d2d;
    color: white;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected { background-color: #007acc; }
QTabBar::tab:hover { background-color: #404040; }

/* ========================================
   Inputs (Spin, LineEdit)
   ======================================== */
QSpinBox, QDoubleSpinBox, QLineEdit {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    border-radius: 4px;
    padding: 5px;
    color: white;
}
QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus { border: 2px solid #007acc; }

/* ========================================
   Áreas de texto (Logs e Editor)
   ======================================== */
/* Logs (QTextEdit) */
QTextEdit {
    background-color: #2b2b2b;
    border: 1px solid #404040;
    border-radius: 4px;
    color: #00ff7f; /* verde mais suave */
    font-family: "Consolas", "Monaco", monospace;
    font-size: 11px;
}

/* Editor de código (QPlainTextEdit) */
QPlainTextEdit {
    background-color: #1e1e1e;
    color: #eaeaea;
    border: 1px solid #3a3a3a;
    selection-background-color: #264f78;
    selection-color: #ffffff;
}

/* ========================================
   Barras de Progresso
   ======================================== */
QProgressBar {
    border: 2px solid #404040;
    border-radius: 5px;
    text-align: center;
    background-color: #2d2d2d;
}
QProgressBar::chunk { background-color: #28a745; border-radius: 3px; }

/* ========================================
   Barras de Rolagem (Scrollbars) - Globais
   Aplicado a todas as barras (QScrollArea, QTextEdit, QPlainTextEdit)
   ======================================== */
QScrollBar:vertical {
    background: #1e1e1e;
    width: 14px; /* largura maior para usabilidade */
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #f4c430; /* amarelo principal */
    min-height: 28px;
    border-radius: 7px;
}
QScrollBar::handle:vertical:hover {
    background: #d9ad27; /* amarelo mais escuro no hover */
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background: transparent;
    height: 0px; /* oculta botões */
}

QScrollBar:horizontal {
    background: #1e1e1e;
    height: 14px; /* altura maior para usabilidade */
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: #f4c430; /* amarelo principal */
    min-width: 28px;
    border-radius: 7px;
}
QScrollBar::handle:horizontal:hover {
    background: #d9ad27; /* amarelo mais escuro no hover */
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    background: transparent;
    width: 0px; /* oculta botões */
}

/* ========================================
   Tabela (QTableWidget)
   ======================================== */
QTableWidget {
    background-color: #2d2d2d; /* Mesmo cinza dos inputs */
    border: 1px solid #404040;
    gridline-color: #404040; /* Cor da grade */
    alternate-background-color: #3a3a3a; /* Cor para linhas alternadas */
    selection-background-color: #007acc; /* Azul de seleção */
    font-size: 14px; /* Aumenta a fonte para toda a tabela */
}

QHeaderView::section {
    background-color: #004578; /* Azul escuro */
    color: white;
    padding: 8px;
    border: 1px solid #404040;
    font-weight: bold;
    font-size: 14px; /* Alinha com o novo tamanho da fonte */
}

QTableWidget::item {
    padding: 10px; /* Aumenta o espaçamento, tornando as células e o editor maiores */
    border-bottom: 1px solid #404040;
}

/* Editor de item da tabela */
QTableWidget QLineEdit {
    padding: 8px;
    min-height: 20px; /* Garante uma altura mínima para o editor */
}
"""

# --- CONFIGURAÇÃO ---
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"
RUN_FRAMEWORK_SCRIPT = SRC_DIR / "run.py"
DASHBOARD_SCRIPT = SRC_DIR / "DashboardApp" / "dashboard_RCE_APP.py"

# Modo de teste agressivo: quando True, para cada configuração salva o launcher
# sobrescreve options.json apenas com 'repeticoes_por_config' e chama
# run.py com --config_num 1 e --exec_num N repetidamente.
TEST_DEBUG = False

# Parâmetros que podem variar via options.json (arrays)
VARYING_KEYS = {"MUTACAO", "CROSSOVER", "NUM_GENERATIONS", "POP_SIZE"}

class ConfigManager:
    """Gerencia a lógica de configuração, usando o DatabaseController para I/O."""
    def __init__(self):
        self.db_controller = DatabaseController(SRC_DIR)
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

class ScriptWorker(QObject):
    """Worker object that runs the script in a subprocess."""
    started = Signal()
    log_updated = Signal(str)
    finished = Signal(int)
    error = Signal(str)

    def __init__(self, script_path, args):
        super().__init__()
        self.script_path = script_path
        self.args = args
        self.process = None

    @Slot()
    def run_script(self):
        self.started.emit()
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
            self.finished.emit(return_code)

        except Exception as e:
            self.error.emit(f"Erro na execução: {e}")

    def stop(self):
        if self.process and self.process.poll() is None:
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
        self.run_button = QPushButton("Salvar e Executar")
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

        # Fetch current base params and variable arrays
        base_params = self.config_manager.db_controller.get_params()
        variable_arrays = self._get_variable_arrays()

        # Escolhe valores fixos para os parâmetros não variáveis
        for name, info in self.param_widgets.items():
            if info["mode"].checkedButton().text() == "Fixo":
                base_params[name] = int(info["fixed"].text()) if info["is_int"] else float(info["fixed"].text())
        options_to_save = {'repeticoes_por_config': self.runs_per_config_spin.value(), **variable_arrays}

        # Save and connect the json configurations file
        self.config_manager.db_controller.save_params(base_params)
        self.config_manager.db_controller.save_options(options_to_save)

        # Generate all combinations
        keys = list(variable_arrays.keys())
        combinations = [dict(zip(keys, v)) for v in product(*variable_arrays.values())] if keys else [{}]
        configurations = [dict(base_params, **combo) for combo in combinations]

        msg = f"{len(configurations)} Configurações únicas serão executadas {self.runs_per_config_spin.value()} vez(es) cada."
        QMessageBox.information(self, "Pronto para Iniciar", msg)
        # Desabilita o botão para evitar múltiplos cliques que emitiriam o sinal novamente
        try:
            self.run_button.setEnabled(False)
        except Exception:
            pass
        self.execution_requested.emit(configurations, self.runs_per_config_spin.value())

class ParamsAGTab(QWidget):
    """Aba para editar todos os parâmetros em tabela (UI Original mantida)."""
    # Parâmetros gerenciados pela outra aba não são mostrados aqui
    EXCLUDED_PARAMS = {"MUTACAO", "CROSSOVER", "NUM_GENERATIONS", "POP_SIZE"}

    def __init__(self, config_manager: 'ConfigManager'):
        super().__init__()
        self.config_manager = config_manager
        self.init_ui()
        self.reload()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
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
        """Recarrega os parâmetros do `params.json`, excluindo os gerenciados em outra aba."""
        self.table.clearContents()

        all_params = self.config_manager.db_controller.get_params()
        params_to_show = {
            k: v for k, v in all_params.items() if k not in self.EXCLUDED_PARAMS
        }


        print("Parametros editáveis para o AG", params_to_show)

        self.table.setRowCount(len(params_to_show))
        for r, (key, value) in enumerate(params_to_show.items()):
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, 0, key_item)

            # Converte listas e dicionários para uma string JSON para exibição
            if isinstance(value, (list, dict)):
                display_value = json.dumps(value)
            else:
                display_value = str(value)
            self.table.setItem(r, 1, QTableWidgetItem(display_value))

    def save(self):
        """Salva os parâmetros da tabela, preservando os que não são mostrados."""
        # Carrega o estado atual do arquivo para não sobrescrever parâmetros ocultos
        params_to_save = self.config_manager.db_controller.get_params()

        # Atualiza com os valores da tabela
        for r in range(self.table.rowCount()):
            key = self.table.item(r, 0).text()
            value_str = self.table.item(r, 1).text().strip()

            # Tenta converter para o tipo de dado correto
            # 1. JSON (listas/dicionários)
            if (value_str.startswith('[') and value_str.endswith(']')) or \
               (value_str.startswith('{') and value_str.endswith('}')):
                try:
                    value = json.loads(value_str)
                except json.JSONDecodeError:
                    value = value_str # Mantém como string se o JSON for inválido
            else:
                # 2. Números (int, depois float)
                try:
                    value = int(value_str)
                except ValueError:
                    try:
                        value = float(value_str)
                    except ValueError:
                        value = value_str # Se tudo falhar, é uma string

            params_to_save[key] = value

        # --- Validação: ind_size vs array_var (código do usuário mantido) ---
        ind_size = params_to_save.get("ind_size")
        array_var = params_to_save.get("array_var")

        if isinstance(ind_size, int) and isinstance(array_var, list):
            if len(array_var) != ind_size:
                msg = f"Atenção: O tamanho do 'ARRAY_VAR' ({len(array_var)}) é diferente do 'ind_size' ({ind_size}).\n\n Corrija o tamanho das variáveis de decisão e do tamanho do individuo da sua população."
                QMessageBox.warning(self, "Validação de Parâmetros!", msg)
        # --- Fim da Validação ---

        if self.config_manager.db_controller.save_params(params_to_save):
            QMessageBox.information(self, "Sucesso", "Parâmetros salvos.")
            # Recarrega a tabela para mostrar os valores formatados corretamente
            self.reload()
        else:
            QMessageBox.critical(self, "Erro", "Falha ao salvar parâmetros.")

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