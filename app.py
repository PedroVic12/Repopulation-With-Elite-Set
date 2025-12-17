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
from PySide6.QtCore import Qt, QThread, Signal, QTimer, Slot, QObject
from PySide6.QtGui import QFont, QIcon, QIntValidator, QDoubleValidator, QColor


#! FIXED_BUG (2025-10-15):
# - Corrigido IndexError em ExecutionTab.run_next_configuration adicionando guarda para total_runs
# - Corrigido fluxo para evitar chamadas concorrentes que geravam current_run_number fora de sincronia
# - Agendamento de próxima execução feito via QTimer.singleShot somente quando ainda houver runs pendentes e não estivermos finalizando
# - Mantive seus comentários e históricos; este bloco documenta as alterações de correção aplicadas


# --- IMPORTS DO PROJETO ---
from style import STYLESHEET
from src.database_controller import DatabaseController
from src.config import BASE_DIR, SRC_DIR, RUN_FRAMEWORK_SCRIPT, DASHBOARD_SCRIPT, VARYING_KEYS, TEST_DEBUG


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

