"""
Arquivo principal do launcher unificado do RCE Framework.

Este arquivo implementa uma arquitetura Model-View-Controller (MVC) e integra
a funcionalidade completa de análise de sistemas de potência em um único script,
conforme solicitado.

- Model: Camada de dados e lógica de negócio.
- View: A interface gráfica.
- Controller: O orquestrador que conecta Model e View.
"""

#! Bug Fix 18/12/25 execução única
"""
1) self.thread.quit(): Esta função envia um sinal para a thread indicando que ela deve encerrar seu loop de eventos. É um pedido para que a thread termine suas tarefas pendentes e saia de forma limpa. Ela não interrompe a thread imediatamente.

2) self.thread.wait(): Esta função bloqueia a thread que está chamando o wait() até que a self.thread (a thread de trabalho) tenha realmente terminado sua execução.

No nosso caso, com as mudanças que fizemos para usar Qt.QueuedConnection, o método _on_process_finished (e os outros slots que corrigimos) é executado na thread principal da sua aplicação (a thread da GUI).

Quando a thread principal chama self.thread.wait(), ela está esperando pela thread de trabalho (onde o ProcessOutputReader estava rodando) terminar.
"""

# =====================================================================================
# HEADER DE IMPORTAÇÃO COMPLETO
# =====================================================================================
import sys
import os
import json
import subprocess
import time
import importlib.util
import traceback
from pathlib import Path
from itertools import product
from collections import deque
from functools import partial

from src.LauncherGUI.gui.widgets.py_push_button import PyPushButton
from src.LauncherGUI.gui.iframes.LoadingWidget import LoadingWidget

import shutil

# --- Imports para Análise de SEP ---
import pandas as pd
import pandapower as pp
import pandapower.networks as pn
import pandapower.plotting as plot
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# --- Imports do PySide6 ---
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
    QHBoxLayout,
    QTextEdit,
    QProgressBar,
    QTabWidget,
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
    QFrame,
    QHeaderView,
    QListWidget,
    QListWidgetItem,
    QStackedLayout,
    QSplitter,
    QFileDialog,
)
from PySide6.QtCore import (
    Qt,
    QThread,
    Signal,
    QTimer,
    Slot,
    QObject,
    QPropertyAnimation,
    QEasingCurve,
)
from PySide6.QtGui import (
    QIntValidator,
    QDoubleValidator,
    QFont,
    QColor,
    QTextCursor,
    QIcon,
)

# --- Checagem de dependências opcionais ---
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    import plotly.graph_objects as go
    import plotly.io as pio

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# O import do database_controller permanece, pois é um módulo externo essencial
from src.tools.database_controller import DatabaseController

# =====================================================================================
#  CONFIGURAÇÕES, ESTILOS E CONSTANTES
# =====================================================================================

# --- Estilos (QSS) ---
from style import STYLESHEET


# --- Constantes de Caminhos e Configuração ---
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"
RUN_FRAMEWORK_SCRIPT = SRC_DIR / "run.py"
RUN_AGENDAMENTO_SCRIPT = SRC_DIR / "run_agendamento.py"
RUN_SIMULATOR_SCRIPT = SRC_DIR / "RedeEletrica/SimulatorSIN45/PandaPowerCaseManager.py"
CLI_SCRIPT_PATH = SRC_DIR / "CLI.py"
VARYING_KEYS = {"MUTACAO", "CROSSOVER", "NUM_GENERATIONS", "POP_SIZE"}

# --- Funções Objetivo Disponíveis --- no arquivo __init__.py
OBJECTIVE_FUNCTIONS = [
    "funcao_objetivo_IEEE14",
    "funcao_objetivo_IEEE30",
    "funcao_objetivo_IEEE57",
    "funcao_objetivo_IEEE118",
    "funcao_objetivo_SIN45",
]

ANALYSIS_CASES = {
    "case_ieee14": {
        "name": "Análise de Contingência - IEEE 14",
        "module_path": SRC_DIR
        / "utils/functions_fitness/analise_contingencia/analise_contingencia_ieee14.py",
        "agendamento_df_name": "agendamento_df_ieee14",
        "contingencia_df_name": "contingencia_df_ieee14",
        "network_name": "case14",
    },
    "case_ieee30": {
        "name": "Análise de Contingência - IEEE 30",
        "module_path": SRC_DIR
        / "utils/functions_fitness/analise_contingencia/analise_contingencia_ieee30.py",
        "agendamento_df_name": "agendamento_df_ieee30",
        "contingencia_df_name": "contingencia_df_ieee30",
        "network_name": "case30",
    },
    "case_ieee118": {
        "name": "Análise de Contingência - IEEE 118",
        "module_path": SRC_DIR
        / "utils/functions_fitness/analise_contingencia/analise_contingencia_ieee118.py",
        "agendamento_df_name": "agendamento_df_ieee118",
        "contingencia_df_name": "contingencia_df_ieee118",
        "network_name": "case118",
    },
}

# =====================================================================================
#  DICIONÁRIO DE SCRIPTS CUSTOMIZADOS
# =====================================================================================
# Adicione novas entradas aqui para criar botões de script no menu lateral.
# O 'path' deve ser o caminho completo para o seu script.
CUSTOM_SCRIPTS = {
    "IEEE_CASES": {
        "name": "▶️ Executar Electrical-Power-System",
        "path": SRC_DIR
        / "LauncherGUI/frontend/Electrical-System-pandapower/SYSTEM_ELECTRICAL_PANDAPOWER.py",
    },
    "PandaPowerCaseManager": {
        "name": "▶️ Executar PandaPower Case Manager",
        "path": SRC_DIR / "RedeEletrica/SimulatorSIN45/PandaPowerCaseManager.py",
    },
    "SmartGridSimulator": {
        "name": "▶️ Executar Smart Grid Simulator",
        "path": SRC_DIR / "RedeEletrica/SimulatorSIN45/SmartGridSimulator.py",
    },
    # "outro_script": {
    #     "name": "▶️ Outro Script",
    #     "path": SRC_DIR / "caminho/para/outro_script.py"
    # },
}


# =====================================================================================
#  MODEL - CAMADA DE DADOS E LÓGICA
# =====================================================================================


class ProcessOutputReader(QObject):
    """Worker que lê o output de um processo em uma thread."""

    output_ready = Signal(str)
    finished = Signal()

    def __init__(self, process):
        super().__init__()
        self.process = process

    @Slot()
    def run(self):
        try:
            for line in iter(self.process.stdout.readline, ""):
                if line:
                    self.output_ready.emit(line)
            self.process.stdout.close()
        except Exception as e:
            print(f"Erro ao ler output do processo: {e}")
        finally:
            self.finished.emit()


class ConfigManager:
    """Model - Gerencia o acesso aos arquivos de configuração JSON."""

    def __init__(self):
        self.db_controller = DatabaseController(SRC_DIR)

    def get_params(self):
        return self.db_controller.get_params()

    def get_options(self):
        return self.db_controller.get_options()

    def save_params(self, params):
        return self.db_controller.save_params(params)

    def save_options(self, options):
        return self.db_controller.save_options(options)

    def consolidate_results(self):
        self.db_controller.consolidate_results()


class ScriptWorker(QObject):
    """Model - Worker que executa um script em uma thread separada."""

    log_updated = Signal(str)
    finished = Signal(int)
    error = Signal(str)

    def __init__(self, script_path, args=None):
        super().__init__()
        self.script_path = script_path
        self.args = args or []
        self.process = None

    @Slot()
    def run(self):
        try:
            python_executable = sys.executable

            cmd = [str(python_executable)] + [
                str(p) for p in [self.script_path] + self.args
            ]
            self.log_updated.emit(f"Executando: {' '.join(cmd)}")

            # Configura o ambiente para forçar UTF-8 no processo filho,
            # o que ajuda a evitar erros de encoding, especialmente no Windows.
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=SRC_DIR,
                encoding="utf-8",
                errors="replace",
                env=env,
            )
            for line in iter(self.process.stdout.readline, ""):
                if line:
                    self.log_updated.emit(line.strip())
            self.process.wait()
            self.finished.emit(self.process.returncode)
        except Exception as e:
            self.error.emit(f"Erro fatal na execução do script: {e}")
            print(traceback.format_exc())

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.log_updated.emit("Processo terminado pelo usuário.")


class ExecutionModel(QObject):
    """Model - Gerencia a lógica de execução de um único script."""

    log_updated = Signal(str)
    all_executions_finished = Signal(bool, str)  # Mantido para consistência

    def __init__(self):
        super().__init__()
        self.thread, self.worker = None, None

    @Slot()
    def _nullify_worker_references(self):
        """Slot para limpar as referências ao worker e à thread após a finalização segura."""
        self.worker = None
        self.thread = None

    def start_execution(self, config_manager, objective_function_index):
        """Inicia a execução única do script de bateria de testes."""
        if self.thread and self.thread.isRunning():
            self.log_updated.emit("Bateria de testes já está em execução.")
            return

        # Os parâmetros agora são lidos pelo próprio run.py a partir dos arquivos
        # O launcher apenas os salva antes de chamar aqui.
        args = ["--objective_function_index", str(objective_function_index)]

        self.worker = ScriptWorker(RUN_FRAMEWORK_SCRIPT, args)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)

        # Conexões de ciclo de vida
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._nullify_worker_references)

        # Conexões de feedback
        self.worker.log_updated.connect(self.log_updated)
        self.worker.error.connect(
            lambda msg: self.all_executions_finished.emit(False, msg)
        )
        self.worker.finished.connect(
            lambda code: self.all_executions_finished.emit(
                code == 0, f"Execução da bateria de testes concluída com código {code}."
            )
        )

        self.thread.start()

    def stop_all(self):
        """Para a execução atual do script."""
        if self.worker:
            self.worker.stop()
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        # A mensagem de interrupção agora virá do sinal 'finished' com código diferente de 0
        self.log_updated.emit("Processo de execução interrompido pelo usuário.")


class PowerSystemModel:
    """Model - Lógica de análise de sistemas de potência com Pandapower."""

    def __init__(self, network_name="case14"):
        self.network_name = network_name
        self.net = self.load_network(network_name)

    def load_network(self, network_name):
        self.network_name = network_name
        try:
            if network_name == "case14":
                self.net = pn.case14()
            elif network_name == "case30":
                self.net = pn.case_ieee30()
            elif network_name == "case118":
                self.net = pn.case118()
            else:
                self.net = pn.case14()
            if self.net and (
                "coords" not in self.net.bus_geodata.columns
                or self.net.bus_geodata.empty
            ):
                plot.create_generic_coordinates(self.net)
            if self.net:
                self.net.name = network_name
            return self.net
        except Exception:
            return pp.create_empty_network()

    def run_power_flow(self):
        if not self.net or self.net.bus.empty:
            return False, "Rede vazia. Impossível executar fluxo de potência."
        try:
            pp.runpp(self.net, algorithm="nr", numba=True)
            return True, "Fluxo de potência convergiu."
        except pp.LoadflowNotConverged:
            return False, "Fluxo de Potência Não Convergiu."
        except Exception as e:
            return False, f"Erro inesperado: {e}"

    def apply_contingencies(self, contingencies):
        if self.net and not self.net.line.empty:
            self.net.line["in_service"] = True
            for c_type, line_index in contingencies:
                if c_type == "line" and line_index in self.net.line.index:
                    self.net.line.loc[line_index, "in_service"] = False


class ResultsRepository:
    """Repository - Busca e formata resultados da simulação para a View."""

    def __init__(self, net):
        if net is None or not hasattr(net, "res_bus") or net.res_bus.empty:
            raise ValueError("Rede não simulada ou sem resultados.")
        self.net = net

    def get_kpis(self):
        v_viol = (
            (self.net.res_bus.vm_pu > self.net.bus.max_vm_pu)
            | (self.net.res_bus.vm_pu < self.net.bus.min_vm_pu)
        ).sum()
        l_loads = (
            (self.net.res_line.loading_percent > 100).sum()
            if hasattr(self.net, "res_line")
            else 0
        )
        t_loads = (
            (self.net.res_trafo.loading_percent > 100).sum()
            if hasattr(self.net, "res_trafo")
            else 0
        )
        total_gen = (
            self.net.res_gen.p_mw.sum() if hasattr(self.net, "res_gen") else 0
        ) + (
            self.net.res_ext_grid.p_mw.sum() if hasattr(self.net, "res_ext_grid") else 0
        )
        return {
            "total_load_mw": (
                self.net.res_load.p_mw.sum() if hasattr(self.net, "res_load") else 0
            ),
            "total_gen_mw": total_gen,
            "voltage_violations": int(v_viol),
            "overloads": int(l_loads + t_loads),
        }

    def get_bus_voltage_data(self):
        if hasattr(self.net, "res_bus"):
            return (
                self.net.res_bus[["vm_pu"]]
                .copy()
                .round(4)
                .reset_index()
                .rename(columns={"index": "Barra", "vm_pu": "Tensão (p.u.)"})
            )
        return pd.DataFrame()

    def get_line_loading_data(self):
        if hasattr(self.net, "res_line"):
            return (
                self.net.res_line[["loading_percent"]]
                .copy()
                .round(2)
                .reset_index()
                .rename(columns={"index": "Linha", "loading_percent": "Carreg. (%)"})
            )
        return pd.DataFrame()


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


# Widgets
class AnalysisSelectionWidget(QWidget):
    analysis_selected = Signal(str)

    def __init__(self, cases):
        super().__init__()
        self.cases = cases
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        title = QLabel("Selecione o Caso de Análise de Contingência")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title, alignment=Qt.AlignCenter)
        self.list_widget = QListWidget()
        self.list_widget.setMaximumWidth(500)
        for case_id, case_data in self.cases.items():
            item = QListWidgetItem(case_data["name"])
            item.setData(Qt.UserRole, case_id)
            item.setTextAlignment(Qt.AlignCenter)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget, alignment=Qt.AlignCenter)
        self.load_button = QPushButton("Carregar Análise")
        self.load_button.setStyleSheet("font-size: 16px; padding: 15px 30px;")
        self.load_button.clicked.connect(self.on_load_clicked)
        layout.addWidget(self.load_button, alignment=Qt.AlignCenter)

    def on_load_clicked(self):
        if self.list_widget.currentItem():
            self.analysis_selected.emit(
                self.list_widget.currentItem().data(Qt.UserRole)
            )


class NetworkCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(8, 8), dpi=100, tight_layout=True)
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.net = None
        plt.ioff()

    def plot_network(self, net):
        self.net = net
        self.ax.clear()
        self.fig.set_facecolor("#1e1e1e")
        self.ax.set_facecolor("#1e1e1e")
        if not net or net.bus.empty:
            self.ax.text(0.5, 0.5, "Rede Vazia.", ha="center", color="white")
            self.draw()
            return
        if not hasattr(net, "bus_geodata") or net.bus_geodata.empty:
            plot.create_generic_coordinates(net, respect_switches=True)
        bc = plot.create_bus_collection(
            net, buses=net.bus.index, size=0.05, color="blue", zorder=10
        )
        self.ax.add_collection(bc)
        if not net.line.empty:
            in_service = net.line[net.line.in_service].index
            oos = net.line[~net.line.in_service].index
            if not in_service.empty:
                self.ax.add_collection(
                    plot.create_line_collection(
                        net,
                        lines=in_service,
                        use_bus_geodata=True,
                        color="grey",
                        linewidths=1.5,
                    )
                )
            if not oos.empty:
                self.ax.add_collection(
                    plot.create_line_collection(
                        net,
                        lines=oos,
                        use_bus_geodata=True,
                        color="red",
                        linestyle="--",
                        linewidths=1.5,
                    )
                )
        if not net.trafo.empty:
            self.ax.add_collection(
                plot.create_trafo_collection(
                    net, trafos=net.trafo.index, color="purple"
                )
            )
        self.ax.set_title(f"Diagrama: {net.name}", color="white")
        self.ax.autoscale_view(True, True, True)
        self.draw()


class PlotlyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.is_available = PLOTLY_AVAILABLE
        self.setLayout(QVBoxLayout())
        if self.is_available:
            self.browser = QWebEngineView()
            self.layout().addWidget(self.browser)
        else:
            self.label = QLabel(
                "Plotly indisponível.\nInstale 'PySide6-WebEngine' para ver gráficos interativos."
            )
            self.label.setAlignment(Qt.AlignCenter)
            self.layout().addWidget(self.label)

    def plot_chart(self, fig):
        if self.is_available:
            fig.update_layout(
                paper_bgcolor="#1e1e1e", plot_bgcolor="#2d2d2d", font_color="white"
            )
            self.browser.setHtml(
                pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
            )

    def clear(self):
        if self.is_available:
            self.browser.setHtml("")


class PowerSystemAnalysisView(QWidget):
    run_simulation_requested = Signal()
    contingencies_changed = Signal(list)

    def __init__(self, case_name):
        super().__init__()
        self.case_name = case_name
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        main_layout.addWidget(content_area)
        self.status_label = QLabel(f"Caso Carregado: {self.case_name}")
        content_layout.addWidget(self.status_label)
        self.tabs = QTabWidget()
        content_layout.addWidget(self.tabs)
        self._setup_tabs()

    def _create_sidebar(self):
        sidebar_widget = QWidget()
        sidebar_widget.setMaximumWidth(350)
        layout = QVBoxLayout(sidebar_widget)
        layout.addWidget(
            QLabel(
                f"Análise: {self.case_name}",
                styleSheet="font-weight: bold; font-size: 16px;",
            )
        )
        self.contingency_list = QListWidget()
        self.contingency_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.contingency_list)
        self.run_button = QPushButton("Executar Fluxo de Potência")
        self.run_button.clicked.connect(self.run_simulation_requested.emit)
        layout.addWidget(self.run_button)
        return sidebar_widget

    def _setup_tabs(self):
        self.network_canvas = NetworkCanvas(self)
        self.tabs.addTab(self.network_canvas, "Diagrama da Rede")
        self.voltage_plot = PlotlyWidget()
        self.voltage_table = QTableWidget()
        self.tabs.addTab(
            self._create_tab_layout(self.voltage_plot, self.voltage_table),
            "Tensão nas Barras",
        )
        self.line_loading_plot = PlotlyWidget()
        self.line_loading_table = QTableWidget()
        self.tabs.addTab(
            self._create_tab_layout(self.line_loading_plot, self.line_loading_table),
            "Carregamento de Linhas",
        )

    def _create_tab_layout(self, plot_widget, table_widget):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(plot_widget)
        splitter.addWidget(table_widget)
        splitter.setSizes([400, 200])
        layout.addWidget(splitter)
        return tab

    def _on_item_clicked(self, item):
        contingencies = [
            self.contingency_list.item(i).data(Qt.UserRole)
            for i in range(self.contingency_list.count())
            if self.contingency_list.item(i).checkState() == Qt.Checked
        ]
        self.contingencies_changed.emit(contingencies)

    def update_status(self, text, is_error=False):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(
            "color: #e74c3c;" if is_error else "color: #2ecc71;"
        )

    def update_table(self, table, df):
        table.clearContents()
        if df.empty:
            table.setRowCount(0)
            return
        table.setRowCount(df.shape[0])
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels(df.columns)
        for i, row in enumerate(df.itertuples(index=False)):
            for j, val in enumerate(row):
                table.setItem(i, j, QTableWidgetItem(str(val)))


class NavigationMenu(QWidget):
    """View - Menu de navegação lateral."""

    config_ag_requested = Signal()
    params_ag_requested = Signal()
    run_ag_requested = Signal()
    power_system_analysis_requested = Signal()
    run_sin45_simulator_requested = Signal()
    cli_requested = Signal()
    dynamic_script_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.buttons = {}

        # Botões padrão
        self._add_nav_button("config_ag", "⚙️ Setup", self.config_ag_requested.emit)
        self._add_nav_button(
            "params_ag", "⌨️ Parâmetros AG", self.params_ag_requested.emit
        )
        self._add_nav_button("run_ag", "▶️ Executar RCE AG", self.run_ag_requested.emit)
        # self._add_nav_button("power_system_analysis", "🔬 Análise de SEP", self.power_system_analysis_requested.emit)
        # self._add_nav_button("run_sin45_simulator", "⚡️ Simular SIN 45", self.run_sin45_simulator_requested.emit)
        self._add_nav_button("cli_terminal", "💻 Console", self.cli_requested.emit)

        # Botões dinâmicos de script
        # for script_id, script_info in CUSTOM_SCRIPTS.items():
        #    handler = partial(self.dynamic_script_requested.emit, script_id)
        #    self._add_nav_button(f"script_{script_id}", script_info["name"], handler)

        self.layout.addStretch()

    def _add_nav_button(self, name, text, signal_handler):
        btn = PyPushButton(
            text=text,
            btn_color="#1a1a1a",
            btn_hover="#007acc",
            btn_pressed="#005a9e",
            text_color="#ffffff",
            text_padding=20,
            height=50,
            minimum_width=240,
        )
        btn.clicked.connect(signal_handler)
        self.layout.addWidget(btn)
        self.buttons[name] = btn

    def set_active_button(self, name):
        # Desativa todos os botões que não são de script dinâmico
        for btn_name, btn_widget in self.buttons.items():
            if not btn_name.startswith("script_"):
                btn_widget.set_active(btn_name == name)


# =====================================================================================
#  CONTROLLERS
# =====================================================================================


class PowerSystemController(QObject):
    def __init__(self, view, network_name, contingencia_df):
        super().__init__()
        self.view, self.model = view, PowerSystemModel(network_name)
        self.contingencia_df = contingencia_df
        self.current_contingencies = []
        self._setup_connections()
        self._initial_load()

    def _setup_connections(self):
        self.view.run_simulation_requested.connect(self.run_simulation)
        self.view.contingencies_changed.connect(self.prepare_contingencies)

    def _initial_load(self):
        self.view.update_status("Pronto para simular.")
        self._update_contingency_list()
        self.view.network_canvas.plot_network(self.model.net)
        self.clear_results()

    def _update_contingency_list(self):
        self.view.contingency_list.clear()
        if self.contingencia_df is not None and not self.contingencia_df.empty:
            for idx, row in self.contingencia_df.iterrows():
                line = self.model.net.line[
                    (self.model.net.line.from_bus == row["from"])
                    & (self.model.net.line.to_bus == row["to"])
                ]
                line_index = line.index[0] if not line.empty else -1
                item = QListWidgetItem(f"[L] Ramo {row['from']} ↔ {row['to']}")
                item.setData(Qt.UserRole, ("line", line_index))
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self.view.contingency_list.addItem(item)

    @Slot(list)
    def prepare_contingencies(self, contingencies):
        self.current_contingencies = contingencies
        self.model.apply_contingencies(self.current_contingencies)
        self.clear_results()
        self.view.network_canvas.plot_network(self.model.net)

    @Slot()
    def run_simulation(self):
        try:
            self.model.apply_contingencies(self.current_contingencies)
            success, msg = self.model.run_power_flow()
            self.view.update_status(msg, not success)
            if success:
                self.update_results_display()
            else:
                self.clear_results()
        except Exception as e:
            self.view.update_status(f"Erro crítico: {e}", True)
            print(traceback.format_exc())

    def update_results_display(self):
        try:
            repo = ResultsRepository(self.model.net)
            voltage_df = repo.get_bus_voltage_data()
            line_df = repo.get_line_loading_data()
            self.view.update_table(self.view.voltage_table, voltage_df)
            self.view.update_table(self.view.line_loading_table, line_df)
            if PLOTLY_AVAILABLE:
                fig_v = go.Figure(
                    data=[
                        go.Bar(
                            x=voltage_df["Barra"],
                            y=voltage_df["Tensão (p.u.)"],
                            name="Tensão",
                        )
                    ]
                )
                fig_v.add_hline(y=1.05, line_dash="dash", line_color="red")
                fig_v.add_hline(y=0.95, line_dash="dash", line_color="red")
                fig_v.update_layout(title_text="Tensão (p.u.)")
                self.view.voltage_plot.plot_chart(fig_v)
                fig_l = go.Figure(
                    data=[
                        go.Bar(
                            x=line_df["Linha"],
                            y=line_df["Carreg. (%)"],
                            name="Carregamento",
                        )
                    ]
                )
                fig_l.add_hline(y=100, line_dash="dash", line_color="red")
                fig_l.update_layout(title_text="Carreg. (%)")
                self.view.line_loading_plot.plot_chart(fig_l)
        except Exception as e:
            self.view.update_status(f"Erro ao exibir resultados: {e}", True)
            print(traceback.format_exc())

    def clear_results(self):
        self.view.update_table(self.view.voltage_table, pd.DataFrame())
        self.view.update_table(self.view.line_loading_table, pd.DataFrame())
        self.view.voltage_plot.clear()
        self.view.line_loading_plot.clear()


#! Janela Principal do app desktop
class LauncherWindow(QMainWindow):
    closing = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("RCE Framework Launcher MVC")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setObjectName("central_widget")  # Nome para o QSS
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.left_menu = QFrame()
        self.left_menu.setFixedWidth(240)
        self.left_menu.setStyleSheet("background-color: #1a1a1a;")
        left_menu_layout = QVBoxLayout(self.left_menu)
        left_menu_layout.setContentsMargins(0, 0, 0, 0)
        self.toggle_button = QPushButton("☰")
        self.toggle_button.setFixedSize(40, 40)
        self.toggle_button.clicked.connect(self.toggle_menu)
        self.nav_menu = NavigationMenu()
        left_menu_layout.addWidget(self.toggle_button)
        left_menu_layout.addWidget(self.nav_menu)
        self.main_layout.addWidget(self.left_menu)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.main_layout.addWidget(self.tabs)

    def closeEvent(self, event):
        self.closing.emit()
        super().closeEvent(event)

    def add_tab(self, widget, name):
        return self.tabs.addTab(widget, name)

    def set_current_tab(self, widget):
        self.tabs.setCurrentWidget(widget)

    def close_tab(self, index):
        self.tabs.removeTab(index)

    @Slot()
    def toggle_menu(self):
        width = self.left_menu.width()
        target = 0 if width > 0 else 240
        for prop_name in [b"minimumWidth", b"maximumWidth"]:
            anim = QPropertyAnimation(self.left_menu, prop_name)
            anim.setDuration(300)
            anim.setStartValue(width)
            anim.setEndValue(target)
            anim.setEasingCurve(QEasingCurve.InOutCubic)
            anim.start()


class MainController(QObject):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.view = LauncherWindow()
        self.config_manager = ConfigManager()
        self.execution_model = ExecutionModel()
        self.open_tabs = {}
        self.analysis_controllers = {}
        self.connect_signals()
        self.open_config_tab()

    @Slot()
    def cleanup_on_exit(self):
        self.execution_model.stop_all()
        for widget in self.open_tabs.values():
            if isinstance(widget, TerminalTab):
                widget.stop_process()
            elif isinstance(widget, ScriptExecutionTab):
                if widget.property("thread") and widget.property("thread").isRunning():
                    if widget.property("worker"):
                        widget.property("worker").stop()

    def connect_signals(self):
        nav = self.view.nav_menu
        nav.config_ag_requested.connect(self.open_config_tab)
        nav.params_ag_requested.connect(self.open_params_tab)
        nav.cli_requested.connect(self.open_cli_tab)

        self.view.closing.connect(self.cleanup_on_exit)
        self.view.tabs.tabCloseRequested.connect(self.close_tab)
        self.view.tabs.currentChanged.connect(self.on_tab_changed)

        # Conexões simplificadas do modelo
        model = self.execution_model
        model.log_updated.connect(self.update_log_on_active_tab)
        model.all_executions_finished.connect(self.on_execution_finished)

    @Slot(str)
    def run_dynamic_script(self, script_id):
        if script_id not in CUSTOM_SCRIPTS:
            QMessageBox.warning(
                self.view, "Erro", f"Script com ID '{script_id}' não encontrado."
            )
            return

        script_info = CUSTOM_SCRIPTS[script_id]
        script_path = script_info["path"]

        if not script_path.exists():
            QMessageBox.warning(
                self.view,
                "Erro",
                f"Caminho do script não encontrado para '{script_id}':\\n{script_path}",
            )
            return

        try:
            # 1. Encontrar um terminal disponível
            terminals = [
                "gnome-terminal",
                "konsole",
                "xfce4-terminal",
                "terminator",
                "xterm",
            ]
            terminal_cmd = None
            for t in terminals:
                if shutil.which(t):
                    terminal_cmd = t
                    break

            if not terminal_cmd:
                QMessageBox.critical(
                    self.view,
                    "Erro de Terminal",
                    "Nenhum emulador de terminal compatível (gnome-terminal, konsole, etc.) foi encontrado.",
                )
                return

            # 2. Construir o comando para o terminal executar
            script_command = f'{sys.executable} \\"{script_path}\\"; exec bash'

            # 3. Construir lista de argumentos corretamente para cada terminal
            args_for_terminal = [terminal_cmd]
            if terminal_cmd == "gnome-terminal":
                # Gnome-terminal requer "--" para separar suas opções do comando
                args_for_terminal.extend(["--", "bash", "-c", script_command])
            else:
                # Outros terminais geralmente usam -e
                args_for_terminal.extend(["-e", f'bash -c "{script_command}"'])

            subprocess.Popen(args_for_terminal)

        except Exception as e:
            QMessageBox.critical(
                self.view, "Erro ao abrir terminal", f"Ocorreu um erro: {e}"
            )

    def open_or_focus_tab(self, tab_name, title, widget_class, *args, **kwargs):
        if tab_name in self.open_tabs:
            self.view.set_current_tab(self.open_tabs[tab_name])
            return
        widget = widget_class(*args, **kwargs)
        self.view.add_tab(widget, title)
        self.view.tabs.setCurrentWidget(widget)
        self.open_tabs[tab_name] = widget
        if isinstance(widget, ConfigTab):
            widget.execution_requested.connect(
                self.start_ag_execution
            )  # Conexão atualizada
        elif isinstance(widget, ScriptExecutionTab) and not widget.is_queue_runner:
            widget.start_stop_btn.clicked.connect(
                partial(self.toggle_single_script, widget)
            )
        if hasattr(widget, "consolidate_btn"):
            widget.consolidate_btn.clicked.connect(
                self.config_manager.consolidate_results
            )
        self.view.nav_menu.set_active_button(tab_name)

    @Slot()
    def open_cli_tab(self):
        self.open_or_focus_tab(
            "cli_terminal", "💻 Console", TerminalTab, CLI_SCRIPT_PATH
        )

    @Slot()
    def open_config_tab(self):
        self.open_or_focus_tab(
            "config_ag", "⚙️ Configurar AG", ConfigTab, self.config_manager
        )

    @Slot()
    def open_params_tab(self):
        self.open_or_focus_tab(
            "params_ag", "⌨️ Parâmetros AG", ParamsAGTab, self.config_manager
        )

    @Slot()
    def open_run_ag_tab(self):
        self.open_or_focus_tab(
            "run_ag",
            "▶️ Executar AG",
            ScriptExecutionTab,
            "Bateria de Simulações AG",
            is_queue_runner=True,
        )

    # @Slot()
    # def open_power_system_analysis_tab(self): self.open_or_focus_tab("power_system_analysis", "🔬 Análise de SEP", MainAnalysisTab, ANALYSIS_CASES, self)
    # @Slot()
    # def open_sin45_simulator_tab(self): self.open_or_focus_tab("run_sin45_simulator", "⚡️ Simular SIN 45", ScriptExecutionTab, "Simulador SIN 45", script_path=RUN_SIMULATOR_SCRIPT)

    @Slot(str)
    def load_analysis_case(self, case_id):
        main_tab_widget = self.open_tabs.get("power_system_analysis")
        if not main_tab_widget:
            return
        try:
            case_info = ANALYSIS_CASES[case_id]
            spec = importlib.util.spec_from_file_location(
                case_info["module_path"].name, case_info["module_path"]
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            contingencia_df = getattr(module, case_info["contingencia_df_name"])
            view = PowerSystemAnalysisView(case_info["name"])
            controller = PowerSystemController(
                view, case_info["network_name"], contingencia_df
            )
            self.analysis_controllers[case_id] = controller
            main_tab_widget.show_analysis_view(view)
        except Exception as e:
            QMessageBox.critical(
                self.view,
                "Erro ao Carregar",
                f"Não foi possível carregar o caso '{case_id}':\n{e}\n\nTrace: {traceback.format_exc()}",
            )

    @Slot(int)
    def close_tab(self, index):
        widget = self.view.tabs.widget(index)
        if widget:
            if isinstance(widget, TerminalTab):
                widget.stop_process()
            tab_name = next(
                (name for name, w in self.open_tabs.items() if w == widget), None
            )
            if tab_name:
                if tab_name in self.analysis_controllers:
                    del self.analysis_controllers[tab_name]
                del self.open_tabs[tab_name]
            self.view.close_tab(index)

    @Slot(int)
    def on_tab_changed(self, index):
        if index == -1:
            return
        widget = self.view.tabs.widget(index)
        tab_name = next(
            (name for name, w in self.open_tabs.items() if w == widget), None
        )
        if tab_name:
            self.view.nav_menu.set_active_button(tab_name)

    @Slot(int)
    def start_ag_execution(self, objective_function_index):
        """Inicia a aba de execução e dispara o modelo para uma única execução da bateria de testes."""
        self.open_run_ag_tab()

        tab = self.open_tabs.get("run_ag")
        if isinstance(tab, ScriptExecutionTab):
            tab.log_text.clear()
            tab.status_label.setText("Iniciando bateria de testes...")
            tab.progress_bar.setVisible(
                False
            )  # A barra de progresso não é mais granular
            tab.start_stop_btn.setText("⏹️ Parar Bateria")
            tab.start_stop_btn.setVisible(True)
            tab.start_stop_btn.setEnabled(True)

            try:
                tab.start_stop_btn.clicked.disconnect()
            except RuntimeError:
                pass
            tab.start_stop_btn.clicked.connect(self.execution_model.stop_all)

        # Chama o modelo para iniciar a execução do run.py
        QTimer.singleShot(
            100,
            lambda: self.execution_model.start_execution(
                self.config_manager, objective_function_index
            ),
        )

    @Slot(bool, str)
    def on_execution_finished(self, success, message):
        """Chamado quando a execução da bateria de testes termina."""
        tab = self.open_tabs.get("run_ag")
        if isinstance(tab, ScriptExecutionTab):
            tab.on_execution_finished(success, message)

            # Reseta e esconde o botão de parar
            tab.start_stop_btn.setText("▶️ Iniciar Bateria AG")
            tab.start_stop_btn.setVisible(False)
            try:
                tab.start_stop_btn.clicked.disconnect(self.execution_model.stop_all)
            except RuntimeError:
                pass

    @Slot(str)
    def update_log_on_active_tab(self, message):
        widget = self.view.tabs.currentWidget()
        if isinstance(widget, ScriptExecutionTab):
            widget.append_log(message)

    def toggle_single_script(self, tab: ScriptExecutionTab):
        if tab.property("thread") and tab.property("thread").isRunning():
            if tab.property("worker"):
                tab.property("worker").stop()
        else:
            script_path = tab.script_path
            if not script_path:
                QMessageBox.warning(
                    self.view,
                    "Erro",
                    f"Nenhum script associado a esta aba: {tab.tab_title}",
                )
                return

            worker = ScriptWorker(script_path)
            thread = QThread()
            tab.setProperty("worker", worker)
            tab.setProperty("thread", thread)
            worker.moveToThread(thread)
            worker.log_updated.connect(tab.append_log)
            worker.finished.connect(
                lambda code: self.on_single_script_finished(tab, code),
                Qt.QueuedConnection,
            )
            thread.started.connect(worker.run)
            thread.start()
            tab.start_stop_btn.setText("⏹️ Parar Script")

    def on_single_script_finished(self, tab, code):
        thread = tab.property("thread")
        if thread:
            thread.quit()
        tab.setProperty("thread", None)
        tab.setProperty("worker", None)
        tab.on_execution_finished(code == 0, f"Script concluído com código {code}.")


# =====================================================================================
#  PONTO DE ENTRADA DA APLICAÇÃO
# =====================================================================================
if __name__ == "__main__":

    # Configurações de Loading
    lazyLoading = True
    tempo_minimo_segundos = 3

    app = QApplication(sys.argv)
    plt.ioff()

    # Inicia a tela de loading
    print("Iniciando a tela de loading do sistema...")
    loading_screen = LoadingWidget(tempo_minimo_segundos*1000)
    loading_screen.show()

    # Processa os eventos para a tela aparecer imediatamente
    app.processEvents()

    # Configurações visuais
    icon_path = BASE_DIR / "src/assets/IconRCELancher.png"
    app.setWindowIcon(QIcon(str(icon_path)))
    app.setStyleSheet(STYLESHEET)

    if not PLOTLY_AVAILABLE:
        QMessageBox.warning(None, "Dependência", "PySide6-WebEngine não encontrado.")

    # Marca o início do carregamento
    start_time = time.time()

    # Carrega o controller (Parte pesada)
    controller = MainController(app)

    if lazyLoading:
        # Calcula quanto tempo ainda falta para completar os segundos
        elapsed = time.time() - start_time
        remaining = max(0, tempo_minimo_segundos - elapsed)

        # Em vez de time.sleep, usamos um loop de eventos curto ou QTimer
        # para manter a interface responsiva enquanto espera
        wait_until = time.time() + remaining
        while time.time() < wait_until:
            app.processEvents()
            time.sleep(0.05)  # Pequena pausa para não fritar o processador

    # Finaliza e mostra a principal
    loading_screen.close()
    controller.view.showMaximized()

    sys.exit(app.exec())
