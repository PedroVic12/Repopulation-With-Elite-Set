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
    QScrollArea, QFrame, QGraphicsDropShadowEffect, QSizePolicy, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QObject, Slot
from PySide6.QtGui import QFont, QIcon, QIntValidator, QDoubleValidator, QColor


# --- IMPORTS DO PROJETO ---
from style import STYLESHEET
from src.database_controller import DatabaseController

# --- CONFIGURAÇÃO ---
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"
RUN_FRAMEWORK_SCRIPT = SRC_DIR / "run.py"
DASHBOARD_SCRIPT = SRC_DIR / "DashboardApp" / "dashboard_RCE_APP.py"

# Modo de teste agressivo: quando True, para cada configuração salva o launcher
# sobrescreve options.json apenas com 'repeticoes_por_config' e chama
# run.py com --config_num 1 e --exec_num N repetidamente.
TEST_DEBUG = True


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

# 1. CLASSE WORKER QUE HERDA DE QOBJECT (Substitui a antiga ExecutionThread)
class ScriptWorker(QObject):
    """
    Worker que executa o script em um subprocesso.
    Projetado para ser movido para uma QThread separada.
    """
    # 2. SINAIS PARA CADA ETAPA DO PROCESSO
    execution_started = Signal(str)      # Sinal de início
    progress_update = Signal(str)        # Sinal de meio (para cada linha de log)
    execution_finished = Signal(bool, str) # Sinal de fim

    def __init__(self, script_path, args=None):
        super().__init__()
        self.script_path = script_path
        self.args = args or []
        self.process = None
        self._is_running = True

    @Slot()
    def run_script(self):
        """
        Este é o método principal que é chamado quando a thread inicia.
        Ele executa o subprocesso e emite sinais para a UI.
        """
        try:
            cmd = [sys.executable, str(self.script_path)] + self.args
            self.execution_started.emit(f"Executando comando: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, cwd=SRC_DIR, encoding='utf-8', errors='replace'
            )
                        
            for line in iter(self.process.stdout.readline, ''):
                if not self._is_running:
                    self.progress_update.emit("Processo interrompido pelo usuário.")
                    break
                if line:
                    self.progress_update.emit(line.strip())
                    
            return_code = self.process.wait()
            self.execution_finished.emit(return_code == 0, f"Processo finalizado com código: {return_code}")
            
        except Exception as e:
            self.progress_update.emit(f"Erro crítico na execução: {e}")
            self.execution_finished.emit(False, str(e))

    def stop(self):
        """Permite que a UI principal solicite a parada do processo."""
        self._is_running = False
        if self.process and self.process.poll() is None:
            self.process.terminate()

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
        base_params = self.config_manager.db_controller.get_params()
        variable_arrays = self._get_variable_arrays()

        for name, info in self.param_widgets.items():
            if info["mode"].checkedButton().text() == "Fixo":
                try:
                    val_str = info["fixed"].text()
                    base_params[name] = int(val_str) if info["is_int"] else float(val_str)
                except ValueError:
                    QMessageBox.warning(self, "Erro de Entrada", f"Valor inválido para '{name}'. Por favor, insira um número válido.")
                    return
        
        options_to_save = {'repeticoes_por_config': self.runs_per_config_spin.value(), **variable_arrays}
        
        self.config_manager.db_controller.save_params(base_params)
        self.config_manager.db_controller.save_options(options_to_save)

        keys = list(variable_arrays.keys())
        combinations = [dict(zip(keys, v)) for v in product(*variable_arrays.values())] if keys else [{}]
        configurations = [dict(base_params, **combo) for combo in combinations]

        msg = f"{len(configurations)} Configurações únicas serão executadas {self.runs_per_config_spin.value()} vez(es) cada."
        QMessageBox.information(self, "Pronto para Iniciar", msg)
        
        self.run_button.setEnabled(False)
        self.execution_requested.emit(configurations, self.runs_per_config_spin.value())


class ParamsAGTab(QWidget):
    """Aba para editar todos os parâmetros em tabela (UI Original mantida)."""
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
        self.table.clearContents()
        all_params = self.config_manager.db_controller.get_params()
        params_to_show = {
            k: v for k, v in all_params.items() if k not in self.EXCLUDED_PARAMS
        }
        
        self.table.setRowCount(len(params_to_show))
        for r, (key, value) in enumerate(params_to_show.items()):
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, 0, key_item)
            
            display_value = json.dumps(value) if isinstance(value, (list, dict)) else str(value)
            self.table.setItem(r, 1, QTableWidgetItem(display_value))

    def save(self):
        params_to_save = self.config_manager.db_controller.get_params()

        for r in range(self.table.rowCount()):
            key = self.table.item(r, 0).text()
            value_str = self.table.item(r, 1).text().strip()
            
            try:
                if (value_str.startswith('[') and value_str.endswith(']')) or \
                   (value_str.startswith('{') and value_str.endswith('}')):
                    value = json.loads(value_str)
                else:
                    value = int(value_str)
            except (json.JSONDecodeError, ValueError):
                try:
                    value = float(value_str)
                except ValueError:
                    value = value_str

            params_to_save[key] = value
        
        ind_size = params_to_save.get("ind_size")
        array_var = params_to_save.get("array_var")

        if isinstance(ind_size, int) and isinstance(array_var, list) and len(array_var) != ind_size:
            msg = f"Atenção: O tamanho do 'ARRAY_VAR' ({len(array_var)}) é diferente do 'ind_size' ({ind_size})."
            QMessageBox.warning(self, "Validação de Parâmetros!", msg)

        if self.config_manager.db_controller.save_params(params_to_save):
            QMessageBox.information(self, "Sucesso", "Parâmetros salvos.")
            self.reload() 
        else:
            QMessageBox.critical(self, "Erro", "Falha ao salvar parâmetros.")


class ExecutionTab(QWidget):
    """Aba de execução, logs e ações pós-execução, refatorada com o padrão Worker-Thread."""
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.db_controller = self.config_manager.db_controller
        
        self.thread: QThread | None = None
        self.worker: ScriptWorker | None = None

        self.configurations = []
        self.runs_per_config = 0
        self.total_runs = 0
        self.current_run_number = 0
        self.is_running_batch = False
        
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
        if self.is_running_batch:
            QMessageBox.warning(self, "Aviso", "Uma bateria de testes já está em execução.")
            return

        if not RUN_FRAMEWORK_SCRIPT.exists():
            QMessageBox.critical(self, "Erro", f"Script não encontrado: {RUN_FRAMEWORK_SCRIPT}")
            self.window().config_tab.run_button.setEnabled(True)
            return

        if not configs:
            QMessageBox.warning(self, "Aviso", "Nenhuma configuração definida para executar.")
            self.window().config_tab.run_button.setEnabled(True)
            return

        self.configurations = configs
        self.runs_per_config = runs_per_config
        self.total_runs = len(self.configurations) * self.runs_per_config
        self.current_run_number = 0
        self.is_running_batch = True

        self.log_text.clear()
        self.append_log(f"Iniciando bateria de testes com {self.total_runs} execuções totais.")

        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, self.total_runs)
        self.progress_bar.setValue(0)
        
        self.run_next_configuration()

    def run_next_configuration(self):
        if not self.is_running_batch or self.current_run_number >= self.total_runs:
            self.on_all_executions_finished(True, "Bateria de testes concluída.")
            return

        config_index = self.current_run_number // self.runs_per_config
        repetition = (self.current_run_number % self.runs_per_config) + 1
        current_config = self.configurations[config_index]
        
        self.status_label.setText(f"Executando {self.current_run_number + 1}/{self.total_runs} (Config: {config_index + 1}, Rep: {repetition})")
        
        # Salva os parâmetros para esta configuração
        if not self.db_controller.save_params(current_config):
            self.append_log(f"❌ Erro ao salvar o arquivo de parâmetros. Abortando.")
            self.on_all_executions_finished(False, "Erro de arquivo.")
            return
            
        # Se estivermos em modo de teste agressivo, garantimos que run.py receba
        # sempre config_num=1 e salvamos um options.json mínimo para que
        # run.py trate params.json como a única configuração.
        if TEST_DEBUG:
            try:
                self.db_controller.save_options({'repeticoes_por_config': self.runs_per_config})
                self.append_log("[TEST_DEBUG] Salvo options mínimo com apenas 'repeticoes_por_config'")
            except Exception as e:
                self.append_log(f"[TEST_DEBUG] Falha ao salvar options minimal: {e}")
            args = ["--config_num", "1", "--exec_num", str(repetition)]
        else:
            args = ["--config_num", str(config_index + 1), "--exec_num", str(repetition)]

        self.thread = QThread()
        self.worker = ScriptWorker(RUN_FRAMEWORK_SCRIPT, args)
        self.worker.moveToThread(self.thread)

        self.worker.execution_started.connect(self.on_worker_started)
        self.worker.progress_update.connect(self.append_log)
        self.worker.execution_finished.connect(self.on_worker_finished)
        self.thread.started.connect(self.worker.run_script)
        
        # Conexões para limpeza automática de memória
        self.worker.execution_finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.worker.deleteLater)
        
        self.thread.start()

    @Slot(str)
    def on_worker_started(self, message: str):
        self.append_log(f"--- Início da Execução {self.current_run_number + 1}/{self.total_runs} ---")
        self.append_log(message)

    @Slot(bool, str)
    def on_worker_finished(self, success: bool, message: str):
        if not self.is_running_batch: # Ignora se a execução foi cancelada enquanto rodava
            return

        self.append_log(f"Resultado: {message}")
        self.append_log(f"--- Fim da Execução {self.current_run_number + 1}/{self.total_runs} ---")
        
        self.worker = None
        self.thread = None

        self.current_run_number += 1
        self.progress_bar.setValue(self.current_run_number)
        
        # Usa QTimer para desacoplar a chamada e permitir que o loop de eventos processe
        QTimer.singleShot(10, self.run_next_configuration)

    def stop_execution(self):
        if self.is_running_batch:
            self.append_log("Parando execução...")
            self.is_running_batch = False
            if self.worker:
                self.worker.stop()
            self.on_all_executions_finished(False, "Interrompido pelo usuário.")

    def on_all_executions_finished(self, success: bool, message: str):
        self.is_running_batch = False
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.status_label.setText(f"Finalizado! {message}")
        self.append_log(f"✅ {message}")
        
        self.window().config_tab.run_button.setEnabled(True)

        if success:
            QMessageBox.information(self, "Bateria de Testes Concluída", "Todos os testes foram executados com sucesso!")
        else:
            QMessageBox.warning(self, "Bateria de Testes Interrompida", message)

    def consolidate_results(self):
        self.append_log("\nIniciando consolidação de resultados...")
        try:
            self.db_controller.consolidate_results()
            self.append_log("Consolidação concluída com sucesso!")
            QMessageBox.information(self, "Sucesso", "Resultados consolidados com sucesso!")
        except Exception as e:
            self.append_log(f"Erro durante a consolidação: {e}")
            QMessageBox.critical(self, "Erro", f"Falha ao consolidar resultados: {e}")

    def run_dashboard(self):
        PORTA = 8501
        try:
            subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(DASHBOARD_SCRIPT), "--server.port", str(PORTA)], cwd=BASE_DIR)
            self.append_log(f"\nDashboard em Streamlit iniciado. Acesse: http://localhost:{PORTA}")
        except Exception as e:
            self.append_log(f"Erro ao iniciar dashboard: {e}")

    @Slot(str)
    def append_log(self, message: str):
        self.log_text.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        self.log_text.ensureCursorVisible()

class LauncherWindow(QMainWindow):
    """Janela principal da aplicação."""
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

        self.config_tab = ConfigTab(self.config_manager)
        self.params_ag_tab = ParamsAGTab(self.config_manager)
        self.execution_tab = ExecutionTab(self.config_manager)
        
        tab_widget.addTab(self.config_tab, "⚙️ Configuração")
        tab_widget.addTab(self.params_ag_tab, "⌨ Parametros AG - RCE")
        tab_widget.addTab(self.execution_tab, "▶️ Exibição de Logs e Dashboard")
        
        layout.addWidget(tab_widget)
        self.tab_widget = tab_widget

        # Conexão centralizada para orquestrar a troca de aba e o início da execução
        self.config_tab.execution_requested.connect(self.handle_execution_request)

    @Slot(list, int)
    def handle_execution_request(self, configurations: list, runs_per_config: int):
        """
        Este slot orquestra a transição entre abas e o início da execução.
        """
        self.tab_widget.setCurrentWidget(self.execution_tab)
        self.execution_tab.start_executions(configurations, runs_per_config)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = LauncherWindow()
    window.showMaximized()
    sys.exit(app.exec())