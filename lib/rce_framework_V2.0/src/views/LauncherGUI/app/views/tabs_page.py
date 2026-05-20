# --- Imports do PySide6 ---
from PySide6.QtWidgets import (
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
    QHBoxLayout,
    QTextEdit,
    QProgressBar,
    QGroupBox,
    QSpinBox,
    QLineEdit,
    QComboBox,
    QMessageBox,
    QRadioButton,
    QButtonGroup,
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QStackedLayout,
)
from PySide6.QtCore import (
    Qt,
    QThread,
    Signal,
    Slot,
)
from PySide6.QtGui import (
    QIntValidator,
    QDoubleValidator,
    QFont,
    QTextCursor,
)

from itertools import product


import json
import sys
import time
import subprocess
import os

from .....global_settings import OBJECTIVE_FUNCTIONS, VARYING_KEYS, SRC_DIR, OBJECTIVE_FUNCTIONS_METADATA

from ..models.process_output_reader import ProcessOutputReader

from .widgets.QT_Widgets import AnalysisSelectionWidget

# =====================================================================================
#  VIEW - CAMADA DE APRESENTAÇÃO
# =====================================================================================


# Tabs (Iframes separados)
class ConfigTab(QWidget):
    execution_requested = Signal(int)  # Apenas o índice da função objetivo

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager, self.param_widgets = config_manager, {}
        self.init_ui()
        self.update_summary()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.create_general_settings(layout)
        self.create_objective_function_settings(layout)
        self.create_ag_params(layout)
        self.create_summary(layout)
        self.create_run_button(layout)
        layout.addStretch()

    def create_objective_function_settings(self, layout):
        group = QGroupBox("Função Objetivo")
        oblayout = QVBoxLayout(group)
        self.objective_function_combo = QComboBox()
        self.objective_function_combo.addItems(OBJECTIVE_FUNCTIONS)
        oblayout.addWidget(self.objective_function_combo)
        layout.addWidget(group)

    def create_general_settings(self, layout):
        group = QGroupBox("Configurações Gerais")
        glayout = QVBoxLayout(group)
        self.runs_per_config_spin = QSpinBox()
        self.runs_per_config_spin.setRange(1, 100)
        self.runs_per_config_spin.setValue(
            self.config_manager.get_options().get("repeticoes_por_config", 1)
        )
        self.runs_per_config_spin.valueChanged.connect(self.update_summary)
        glayout.addWidget(QLabel("Execuções por Configuração:"))
        glayout.addWidget(self.runs_per_config_spin)
        layout.addWidget(group)

    def create_ag_params(self, layout):
        group = QGroupBox("Parâmetros do AG (Bateria de Testes)")
        ag_layout = QGridLayout(group)
        params_to_render = {
            "MUTACAO": 0.1,
            "CROSSOVER": 0.8,
            "NUM_GENERATIONS": 100,
            "POP_SIZE": 50,
        }
        for i, (name, val) in enumerate(params_to_render.items()):
            widget = self._create_param_widget(
                name, self.config_manager.get_params().get(name, val)
            )
            ag_layout.addWidget(widget, i // 2, i % 2)
        layout.addWidget(group)

    def create_summary(self, layout):
        group = QGroupBox("Resumo da Execução")
        slay = QHBoxLayout(group)
        self.unique_configs_label = QLabel("Configurações Únicas: 1")
        self.total_runs_label = QLabel()
        slay.addWidget(self.unique_configs_label)
        slay.addWidget(self.total_runs_label)
        layout.addWidget(group)
        self.update_summary()

    def create_run_button(self, layout):
        self.run_button = QPushButton("Salvar e Ir para Execução")
        self.run_button.clicked.connect(self.prepare_and_run)
        layout.addWidget(self.run_button, alignment=Qt.AlignCenter)

    def _create_param_widget(self, name, default_value):
        group = QGroupBox(name)
        layout = QVBoxLayout(group)
        mode_group = QButtonGroup(self)
        fr, vr = QRadioButton("Fixo"), QRadioButton("Variável")
        fr.setChecked(True)
        mode_group.addButton(fr)
        mode_group.addButton(vr)
        mlay = QHBoxLayout()
        mlay.addWidget(fr)
        mlay.addWidget(vr)
        layout.addLayout(mlay)
        is_int = isinstance(default_value, int)
        fixed_input = QLineEdit(str(default_value))
        validator = (
            QIntValidator(1, 100000) if is_int else QDoubleValidator(0.0, 1.0, 5)
        )
        fixed_input.setValidator(validator)
        var_widget = QWidget()
        vlay = QGridLayout(var_widget)
        v_inputs = []
        for i in range(4):
            inp = QLineEdit()
            inp.setPlaceholderText(f"V{i+1}")
            inp.setValidator(validator)
            vlay.addWidget(inp, i // 2, i % 2)
            v_inputs.append(inp)
        var_widget.setVisible(False)
        layout.addWidget(fixed_input)
        layout.addWidget(var_widget)
        fr.toggled.connect(fixed_input.setVisible)
        vr.toggled.connect(var_widget.setVisible)
        self.param_widgets[name] = {
            "mode": mode_group,
            "fixed": fixed_input,
            "variable": v_inputs,
            "is_int": is_int,
        }
        fixed_input.textChanged.connect(self.update_summary)
        for vi in v_inputs:
            vi.textChanged.connect(self.update_summary)
        mode_group.buttonClicked.connect(self.update_summary)
        return group

    def update_summary(self, _=None):
        arrays = self._get_variable_arrays()
        num_combs = len(list(product(*arrays.values()))) if arrays else 1
        total_execs = num_combs * self.runs_per_config_spin.value()
        self.unique_configs_label.setText(f"Configurações Únicas: {num_combs}")
        self.total_runs_label.setText(f"Total de Execuções: {total_execs}")

    def _get_variable_arrays(self):
        arrays = {}
        for name, info in self.param_widgets.items():
            if info["mode"].checkedButton().text() == "Variável":
                values = [
                    (
                        int(vi.text().strip())
                        if info["is_int"]
                        else float(vi.text().strip())
                    )
                    for vi in info["variable"]
                    if vi.text().strip()
                ]
                if values:
                    arrays[name] = list(dict.fromkeys(values))
        return arrays

    def prepare_and_run(self):
        params, var_arrays = (
            self.config_manager.get_params(),
            self._get_variable_arrays(),
        )

        # --- Validação de Dimensão das Variáveis de Decisão ---
        func_key = self.objective_function_combo.currentText()
        metadata = OBJECTIVE_FUNCTIONS_METADATA.get(func_key)
        if metadata:
            expected_dim = metadata["dim"]
            current_vars = params.get("ARRAY_VAR", [])
            if len(current_vars) != expected_dim:
                QMessageBox.critical(
                    self,
                    "Erro de Dimensão",
                    f"A função '{metadata['name']}' espera {expected_dim} variáveis de decisão.\n"
                    f"Atualmente existem {len(current_vars)} no params.json.\n\n"
                    "Por favor, ajuste o array 'ARRAY_VAR' na aba 'Parâmetros AG'.",
                )
                return

        # --- Alerta de Modos Especiais (CLI / Benchmarking) ---
        special_modes = []
        if params.get("CLI_MODE", False):
            special_modes.append("CLI MODE")
        if params.get("BENCHMARKING_MODE", False):
            special_modes.append("BENCHMARKING MODE")

        if special_modes:
            reply = QMessageBox.warning(
                self,
                "Aviso de Modo Especial",
                f"Os seguintes modos estão ATIVADOS: {', '.join(special_modes)}.\n\n"
                "O modo CLI pode fazer o programa travar aguardando input no terminal.\n"
                "Deseja continuar mesmo assim?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        for name, info in self.param_widgets.items():
            if name not in VARYING_KEYS:  # Salva params que não são de variação
                try:
                    params[name] = (
                        int(info["fixed"].text())
                        if info["is_int"]
                        else float(info["fixed"].text())
                    )
                except (ValueError, TypeError):
                    pass  # Ignora se o campo estiver vazio ou for inválido
            elif info["mode"].checkedButton().text() == "Fixo":
                try:
                    params[name] = (
                        int(info["fixed"].text())
                        if info["is_int"]
                        else float(info["fixed"].text())
                    )
                except ValueError:
                    QMessageBox.warning(
                        self, "Erro de Valor", f"Valor inválido para '{name}'."
                    )
                    return

        # Salva os parâmetros base em params.json
        self.config_manager.save_params(params)

        # Salva as variações e repetições em options.json
        opts = {
            "repeticoes_por_config": self.runs_per_config_spin.value(),
            **var_arrays,
        }
        self.config_manager.save_options(opts)

        objective_function_index = self.objective_function_combo.currentIndex()
        self.execution_requested.emit(objective_function_index)


class ParamsAGTab(QWidget):
    EXCLUDED_PARAMS = {"MUTACAO", "CROSSOVER", "NUM_GENERATIONS", "POP_SIZE"}

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.init_ui()
        self.reload()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Parâmetro", "Valor"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        btns = QHBoxLayout()
        self.reload_btn = QPushButton("🔄 Recarregar")
        self.save_btn = QPushButton("💾 Salvar")
        self.reload_btn.clicked.connect(self.reload)
        self.save_btn.clicked.connect(self.save)
        btns.addWidget(self.reload_btn)
        btns.addWidget(self.save_btn)
        layout.addLayout(btns)

    def reload(self):
        self.table.clearContents()
        params = {
            k: v
            for k, v in self.config_manager.get_params().items()
            if k not in self.EXCLUDED_PARAMS
        }
        self.table.setRowCount(len(params))
        for r, (key, value) in enumerate(params.items()):
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, 0, key_item)
            self.table.setItem(
                r,
                1,
                QTableWidgetItem(
                    json.dumps(value) if isinstance(value, (list, dict)) else str(value)
                ),
            )

    def save(self):
        params = self.config_manager.get_params()
        for r in range(self.table.rowCount()):
            key, val_str = (
                self.table.item(r, 0).text(),
                self.table.item(r, 1).text().strip(),
            )
            try:
                if (val_str.startswith("[") and val_str.endswith("]")) or (
                    val_str.startswith("{") and val_str.endswith("}")
                ):
                    value = json.loads(val_str)
                else:
                    value = float(val_str)
                    value = int(value) if value.is_integer() else value
            except (json.JSONDecodeError, ValueError):
                value = val_str
            params[key] = value
        if self.config_manager.save_params(params):
            QMessageBox.information(self, "Sucesso", "Parâmetros salvos.")
        else:
            QMessageBox.critical(self, "Erro", "Falha ao salvar parâmetros.")


class ScriptExecutionTab(QWidget):
    def __init__(self, tab_title, is_queue_runner=False, script_path=None):
        super().__init__()
        self.tab_title = tab_title
        self.is_queue_runner = is_queue_runner
        self.script_path = script_path
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.status_label = QLabel("Aguardando início...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        status_box = QGroupBox("Status")
        sbl = QVBoxLayout(status_box)
        sbl.addWidget(self.status_label)
        sbl.addWidget(self.progress_bar)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_box = QGroupBox("Log de Execução")
        lbl = QVBoxLayout(log_box)
        lbl.addWidget(self.log_text)

        layout.addWidget(status_box)
        layout.addWidget(log_box)

        ctrl_layout = QHBoxLayout()
        self.start_stop_btn = QPushButton(f"▶️ Iniciar {self.tab_title}")
        self.consolidate_btn = QPushButton("📄 Consolidar Resultados")
        self.run_dashboard_btn = QPushButton("📊 Abrir Dashboard")

        ctrl_layout.addWidget(self.start_stop_btn)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.consolidate_btn)
        ctrl_layout.addWidget(self.run_dashboard_btn)

        self.run_dashboard_btn.clicked.connect(self.run_dashboard)

        # Oculta o botão de iniciar para a aba da fila de execução, pois ela começa automaticamente
        if self.is_queue_runner:
            self.start_stop_btn.setVisible(False)

        layout.addLayout(ctrl_layout)

    def run_dashboard(self):
        dashboard_script_path = SRC_DIR / "DashboardApp" / "dashboard_RCE_APP.py"

        if not dashboard_script_path.exists():
            QMessageBox.critical(
                self,
                "Erro",
                f"Script do dashboard não encontrado:\n{dashboard_script_path}",
            )
            return

        PORTA = 8501
        try:
            cmd = [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(dashboard_script_path),
                "--server.port",
                str(PORTA),
            ]
            subprocess.Popen(cmd)
            self.append_log(f"Dashboard iniciado em http://localhost:{PORTA}")
        except Exception as e:
            self.append_log(f"Erro ao iniciar dashboard: {e}")
            QMessageBox.critical(
                self, "Erro no Dashboard", f"Não foi possível iniciar o Streamlit: {e}"
            )

    @Slot(str)
    def append_log(self, msg):
        self.log_text.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
        self.log_text.ensureCursorVisible()

    @Slot(bool, str)
    def on_execution_finished(self, success, message):
        self.status_label.setText(f"Finalizado: {message}")
        if success:
            self.progress_bar.setValue(self.progress_bar.maximum())
        self.start_stop_btn.setText(f"▶️ Iniciar {self.tab_title}")
        self.start_stop_btn.setEnabled(True)
        if success:
            QMessageBox.information(self, "Concluído", message)


class TerminalTab(QWidget):
    """Widget que emula um terminal para rodar scripts interativos."""

    def __init__(self, script_path):
        super().__init__()
        self.process = None
        self.thread = None
        self.reader = None
        self.script_path = script_path
        self._init_ui()
        self._start_process()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Monospace", 10))
        self.input_line = QLineEdit()
        self.input_line.setFont(QFont("Monospace", 10))
        self.input_line.returnPressed.connect(self.send_command)
        layout.addWidget(self.log_text)
        layout.addWidget(self.input_line)

    def _start_process(self):
        python_executable = sys.executable

        cmd = [str(python_executable), str(self.script_path)]

        try:
            # Configura o ambiente para forçar UTF-8 no processo filho,
            # o que ajuda a evitar erros de encoding, especialmente no Windows.
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=SRC_DIR,
                encoding="utf-8",
                errors="replace",
                bufsize=1,  # Line-buffered
                env=env,
            )

            self.thread = QThread()
            self.reader = ProcessOutputReader(self.process)
            self.reader.moveToThread(self.thread)
            self.reader.output_ready.connect(self._on_output)
            self.reader.finished.connect(self._on_process_finished, Qt.QueuedConnection)
            self.thread.started.connect(self.reader.run)
            self.thread.start()
            self.input_line.setFocus()

        except Exception as e:
            self.log_text.append(f"Erro ao iniciar o processo: {e}")
            self.input_line.setEnabled(False)

    @Slot(str)
    def _on_output(self, text):
        self.log_text.moveCursor(QTextCursor.End)
        self.log_text.insertPlainText(text)
        self.log_text.ensureCursorVisible()

    @Slot()
    def _on_process_finished(self):
        self.input_line.setEnabled(False)
        self.input_line.setText("--- PROCESSO FINALIZADO ---")
        if self.thread:
            self.thread.quit()

    @Slot()
    def send_command(self):
        command = self.input_line.text() + "\n"
        if self.process and self.process.poll() is None:
            try:
                self.process.stdin.write(command)
                self.process.stdin.flush()
                self._on_output(command)  # Echo input
            except (IOError, ValueError) as e:
                self._on_process_finished()
        self.input_line.clear()

    def stop_process(self):
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait()


class MainAnalysisTab(QWidget):
    def __init__(self, cases, main_controller):
        super().__init__()
        self.main_controller = main_controller
        self.stack = QStackedLayout(self)
        self.selection_widget = AnalysisSelectionWidget(cases)
        self.selection_widget.analysis_selected.connect(
            self.main_controller.load_analysis_case
        )
        self.stack.addWidget(self.selection_widget)

    def show_analysis_view(self, analysis_widget):
        if self.stack.count() > 1:
            old = self.stack.widget(1)
            self.stack.removeWidget(old)
            old.deleteLater()
        self.stack.addWidget(analysis_widget)
        self.stack.setCurrentWidget(analysis_widget)
