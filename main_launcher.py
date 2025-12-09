"""
Arquivo principal do launcher unificado.
Combina a funcionalidade de execução de experimentos com uma interface moderna
inspirada em templates PySide6, apresentando um menu lateral e abas dinâmicas.
"""
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

from src.database_controller import DatabaseController

STYLESHEET = """
QWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 12px;
}
QMainWindow { background-color: #1e1e1e; }
QLabel#title { font-size: 24px; font-weight: bold; color: #00d4ff; padding: 10px; }
QLabel#subtitle { font-size: 14px; color: #cccccc; padding: 5px; }
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
QPushButton.nav-button {
    background-color: transparent;
    border: none;
    color: #ffffff;
    text-align: left;
    padding: 10px;
    font-size: 16px;
}
QPushButton.nav-button:hover { background-color: #404040; }
QPushButton.nav-button:checked { background-color: #007acc; }
QRadioButton { font-size: 14px; color: #ffffff; padding: 2px; }
QRadioButton:checked { font-weight: bold;  }
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
QTabWidget::pane { border-top: 2px solid #007acc; background-color: #1e1e1e; }
QTabBar::tab {
    background-color: #2d2d2d;
    color: white;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-size: 14px;
}
QTabBar::tab:selected { background-color: #007acc; }
QTabBar::tab:hover { background-color: #404040; }
QTabBar::close-button { image: url(close.png); subcontrol-position: right; }
QTabBar::close-button:hover { background-color: #c00000; }
QSpinBox, QDoubleSpinBox, QLineEdit {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    border-radius: 4px;
    padding: 5px;
    color: white;
}
QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus { border: 2px solid #007acc; }
QTextEdit {
    background-color: #2b2b2b;
    border: 1px solid #404040;
    border-radius: 4px;
    color: #00ff7f;
    font-family: "Consolas", "Monaco", monospace;
    font-size: 11px;
}
QProgressBar {
    border: 2px solid #404040;
    border-radius: 5px;
    text-align: center;
    background-color: #2d2d2d;
}
QProgressBar::chunk { background-color: #28a745; border-radius: 3px; }
QScrollBar:vertical { background: #1e1e1e; width: 14px; margin: 0px; }
QScrollBar::handle:vertical { background: #f4c430; min-height: 28px; border-radius: 7px; }
QScrollBar::handle:vertical:hover { background: #d9ad27; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { background: transparent; height: 0px; }
QScrollBar:horizontal { background: #1e1e1e; height: 14px; margin: 0px; }
QScrollBar::handle:horizontal { background: #f4c430; min-width: 28px; border-radius: 7px; }
QScrollBar::handle:horizontal:hover { background: #d9ad27; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { background: transparent; width: 0px; }
QTableWidget {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    gridline-color: #404040;
    alternate-background-color: #3a3a3a;
    selection-background-color: #007acc;
    font-size: 14px;
}
QHeaderView::section {
    background-color: #004578;
    color: white;
    padding: 8px;
    border: 1px solid #404040;
    font-weight: bold;
    font-size: 14px;
}
QTableWidget::item { padding: 10px; border-bottom: 1px solid #404040; }
QTableWidget QLineEdit { padding: 8px; min-height: 20px; }
"""

BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"
RUN_FRAMEWORK_SCRIPT = SRC_DIR / "run.py"
DASHBOARD_SCRIPT = SRC_DIR / "DashboardApp" / "dashboard_RCE_APP.py"
VARYING_KEYS = {"MUTACAO", "CROSSOVER", "NUM_GENERATIONS", "POP_SIZE"}

class ConfigManager:
    def __init__(self):
        self.db_controller = DatabaseController(SRC_DIR)
        self.params = self.db_controller.get_params()
        self.options = self.db_controller.get_options()
        self.clean_options()
    def clean_options(self):
        current, cleaned = self.options, {}
        if 'repeticoes_por_config' in current: cleaned['repeticoes_por_config'] = current['repeticoes_por_config']
        for k in VARYING_KEYS:
            if k in current and isinstance(current[k], list): cleaned[k] = list(dict.fromkeys(current[k]))
        if cleaned != current: self.options, self.db_controller.save_options(self.options)

class ScriptWorker(QObject):
    started, log_updated, finished, error = Signal(), Signal(str), Signal(int), Signal(str)
    def __init__(self, script_path, args):
        super().__init__(); self.script_path, self.args, self.process = script_path, args, None
    @Slot()
    def run_script(self):
        self.started.emit()
        try:
            cmd = [sys.executable, str(self.script_path)] + self.args
            self.log_updated.emit(f"Executando: {' '.join(cmd)}")
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, cwd=SRC_DIR, encoding='utf-8', errors='replace')
            for line in iter(self.process.stdout.readline, ''):
                if line: self.log_updated.emit(line.strip())
            self.finished.emit(self.process.wait())
        except Exception as e: self.error.emit(f"Erro na execução: {e}")
    def stop(self):
        if self.process and self.process.poll() is None: self.process.terminate(), self.log_updated.emit("Processo de execução terminado pelo usuário.")

class ConfigTab(QWidget):
    execution_requested = Signal(list, int)
    def __init__(self, config_manager):
        super().__init__(); self.config_manager, self.param_widgets = config_manager, {}; self.init_ui(); self.update_summary()
    def init_ui(self):
        layout = QVBoxLayout(self); self.create_general_settings(layout); self.create_ag_params(layout); self.create_summary(layout); self.create_run_button(layout); layout.addStretch()
    def create_general_settings(self, layout):
        group, glayout, self.runs_per_config_spin = QGroupBox("Configurações Gerais"), QVBoxLayout(), QSpinBox()
        self.runs_per_config_spin.setRange(1, 100); self.runs_per_config_spin.setValue(self.config_manager.options.get('repeticoes_por_config', 1)); self.runs_per_config_spin.valueChanged.connect(self.update_summary)
        glayout.addWidget(QLabel("Execuções por Configuração:")); glayout.addWidget(self.runs_per_config_spin); group.setLayout(glayout); layout.addWidget(group)
    def create_ag_params(self, layout):
        group, ag_layout = QGroupBox("Parâmetros do Algoritmo Genético"), QGridLayout()
        ag_layout.setHorizontalSpacing(16); ag_layout.setVerticalSpacing(16)
        params_to_render = {"MUTACAO": 0.1, "CROSSOVER": 0.8, "NUM_GENERATIONS": 100, "POP_SIZE": 50}
        row, col = 0, 0
        for name, val in params_to_render.items():
            ag_layout.addWidget(self._create_param_widget(name, self.config_manager.params.get(name, val)), row, col); col += 1
            if col > 1: col, row = 0, row + 1
        group.setLayout(ag_layout); layout.addWidget(group)
    def create_summary(self, layout):
        group, slay = QGroupBox("Resumo da Execução"), QHBoxLayout()
        self.unique_configs_label, self.total_runs_label = QLabel("Configurações Únicas: 1"), QLabel(f"Total de Execuções: {self.runs_per_config_spin.value()}")
        slay.addWidget(self.unique_configs_label); slay.addWidget(self.total_runs_label); group.setLayout(slay); layout.addWidget(group)
    def create_run_button(self, layout):
        self.run_button = QPushButton("Salvar e Executar"); self.run_button.clicked.connect(self.prepare_and_run); layout.addWidget(self.run_button, alignment=Qt.AlignCenter)
    def _create_param_widget(self, name, default_value):
        group, layout, mode_group, fr, vr = QGroupBox(name), QVBoxLayout(), QButtonGroup(self), QRadioButton("Fixo"), QRadioButton("Variável")
        fr.setChecked(True); mode_group.addButton(fr); mode_group.addButton(vr); mlay = QHBoxLayout(); mlay.addWidget(fr); mlay.addWidget(vr); layout.addLayout(mlay)
        is_int = isinstance(default_value, int); fixed_input = QLineEdit(str(default_value)); fixed_input.setValidator(QIntValidator(1, 100000) if is_int else QDoubleValidator(0.0, 1.0, 5))
        var_widget, vlay, v_inputs = QWidget(), QGridLayout(), []
        for i in range(4):
            inp = QLineEdit(); inp.setPlaceholderText(f"V{i+1}"); inp.setValidator(fixed_input.validator()); vlay.addWidget(inp, i//2, i%2); v_inputs.append(inp)
        var_widget.setLayout(vlay); var_widget.setVisible(False); layout.addWidget(fixed_input); layout.addWidget(var_widget); group.setLayout(layout)
        fr.toggled.connect(fixed_input.setVisible); vr.toggled.connect(var_widget.setVisible)
        self.param_widgets[name] = {"mode": mode_group, "fixed": fixed_input, "variable": v_inputs, "is_int": is_int}
        fixed_input.textChanged.connect(self.update_summary); [vi.textChanged.connect(self.update_summary) for vi in v_inputs]; mode_group.buttonClicked.connect(self.update_summary)
        return group
    def update_summary(self, _=None):
        arrays = self._get_variable_arrays(); num_combs = len(list(product(*arrays.values()))) if arrays else 1; total_execs = num_combs * self.runs_per_config_spin.value()
        self.unique_configs_label.setText(f"Configurações Únicas: {num_combs}"); self.total_runs_label.setText(f"Total de Execuções: {total_execs}")
    def _get_variable_arrays(self):
        arrays = {}
        for name, info in self.param_widgets.items():
            if info["mode"].checkedButton().text() == "Variável":
                values = [int(vi.text().strip()) if info["is_int"] else float(vi.text().strip()) for vi in info["variable"] if vi.text().strip()]
                if values: arrays[name] = list(dict.fromkeys(values))
        return arrays
    def prepare_and_run(self):
        params, var_arrays = self.config_manager.db_controller.get_params(), self._get_variable_arrays()
        for name, info in self.param_widgets.items():
            if info["mode"].checkedButton().text() == "Fixo": params[name] = int(info["fixed"].text()) if info["is_int"] else float(info["fixed"].text())
        opts = {'repeticoes_por_config': self.runs_per_config_spin.value(), **var_arrays}
        self.config_manager.db_controller.save_params(params); self.config_manager.db_controller.save_options(opts)
        keys, combos = list(var_arrays.keys()), [dict(zip(keys, v)) for v in product(*var_arrays.values())] if keys else [{}]
        configs = [dict(params, **c) for c in combos]
        QMessageBox.information(self, "Pronto para Iniciar", f"{len(configs)} Configurações únicas serão executadas {self.runs_per_config_spin.value()} vez(es) cada."); self.run_button.setEnabled(False)
        self.execution_requested.emit(configs, self.runs_per_config_spin.value())

class ParamsAGTab(QWidget):
    EXCLUDED_PARAMS = {"MUTACAO", "CROSSOVER", "NUM_GENERATIONS", "POP_SIZE"}
    def __init__(self, config_manager: 'ConfigManager'):
        super().__init__(); self.config_manager = config_manager; self.init_ui(); self.reload()
    def init_ui(self):
        layout = QVBoxLayout(self); self.table = QTableWidget(); self.table.setAlternatingRowColors(True); self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Parâmetro", "Valor"]); self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); layout.addWidget(self.table)
        btns = QHBoxLayout(); self.reload_btn, self.save_btn = QPushButton("🔄 Recarregar"), QPushButton("💾 Salvar")
        self.reload_btn.clicked.connect(self.reload); self.save_btn.clicked.connect(self.save); btns.addWidget(self.reload_btn); btns.addWidget(self.save_btn); layout.addLayout(btns)
    def reload(self):
        self.table.clearContents(); params = {k: v for k, v in self.config_manager.db_controller.get_params().items() if k not in self.EXCLUDED_PARAMS}
        self.table.setRowCount(len(params));
        for r, (key, value) in enumerate(params.items()):
            key_item = QTableWidgetItem(key); key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable); self.table.setItem(r, 0, key_item)
            self.table.setItem(r, 1, QTableWidgetItem(json.dumps(value) if isinstance(value, (list, dict)) else str(value)))
    def save(self):
        params = self.config_manager.db_controller.get_params()
        for r in range(self.table.rowCount()):
            key, val_str = self.table.item(r, 0).text(), self.table.item(r, 1).text().strip()
            try: value = json.loads(val_str) if (val_str.startswith('[') and val_str.endswith(']')) or (val_str.startswith('{') and val_str.endswith('}')) else int(val_str)
            except (json.JSONDecodeError, ValueError):
                try: value = float(val_str)
                except ValueError: value = val_str
            params[key] = value
        if self.config_manager.db_controller.save_params(params): QMessageBox.information(self, "Sucesso", "Parâmetros salvos."), self.reload()
        else: QMessageBox.critical(self, "Erro", "Falha ao salvar parâmetros.")

class ExecutionTab(QWidget):
    def __init__(self, config_manager):
        super().__init__(); self.config_manager, self.db_controller, self.thread, self.worker = config_manager, config_manager.db_controller, None, None; self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout(self); self.create_status_panel(layout); self.create_progress_bar(layout); self.create_log_area(layout); self.create_control_buttons(layout)
    def create_status_panel(self, layout):
        group, h_layout, self.status_label = QGroupBox("Progresso da Bateria de Testes"), QHBoxLayout(), QLabel("Aguardando início...")
        h_layout.addWidget(self.status_label); group.setLayout(h_layout); layout.addWidget(group)
    def create_progress_bar(self, layout): self.progress_bar = QProgressBar(); self.progress_bar.setVisible(False); layout.addWidget(self.progress_bar)
    def create_log_area(self, layout): self.log_text = QTextEdit(); self.log_text.setReadOnly(True); layout.addWidget(QLabel("Log de Execução:")); layout.addWidget(self.log_text)
    def create_control_buttons(self, layout):
        ctrl_layout = QHBoxLayout(); self.stop_btn, self.consolidate_btn, self.run_dashboard_btn = QPushButton("⏹️ Parar"), QPushButton("📄 Consolidar"), QPushButton("📊 Dashboard")
        self.stop_btn.clicked.connect(self.stop_execution); self.stop_btn.setEnabled(False); self.consolidate_btn.clicked.connect(self.consolidate_results); self.run_dashboard_btn.clicked.connect(self.run_dashboard)
        ctrl_layout.addWidget(self.stop_btn); ctrl_layout.addStretch(); ctrl_layout.addWidget(self.consolidate_btn); ctrl_layout.addWidget(self.run_dashboard_btn); layout.addLayout(ctrl_layout)
    @Slot(list, int)
    def start_executions(self, configs, runs_per_config):
        if not RUN_FRAMEWORK_SCRIPT.exists(): QMessageBox.critical(self, "Erro", f"Script não encontrado: {RUN_FRAMEWORK_SCRIPT}"); return
        if self.thread and self.thread.isRunning(): self.append_log("Bateria em execução."); return
        self.configurations, self.runs_per_config, self._pending_runs = configs, runs_per_config, deque([(ci, r) for ci in range(len(configs)) for r in range(1, runs_per_config+1)])
        self.total_runs, self.current_run_number = len(self._pending_runs), 0; self.log_text.clear(); self.append_log(f"Iniciando {self.total_runs} execuções.")
        self.stop_btn.setEnabled(True); self.progress_bar.setVisible(True); self.progress_bar.setRange(0, self.total_runs); self.progress_bar.setValue(0); self.run_next_configuration()
    def run_next_configuration(self):
        if not self._pending_runs: self.on_all_executions_finished(True, "Execuções concluídas."); return
        cfg_idx, rep = self._pending_runs.popleft(); current_config = self.configurations[cfg_idx]
        self.status_label.setText(f"Executando {self.current_run_number + 1}/{self.total_runs} (Config: {cfg_idx + 1}, Rep: {rep})"); self.append_log("-" * 80); self.append_log(f"Iniciando Config {cfg_idx + 1}, Rep {rep}")
        if not self.db_controller.save_params(current_config): self.append_log("Erro ao salvar parâmetros."), self.on_all_executions_finished(False, "Erro de arquivo."); return
        args = ["--config_num", str(cfg_idx + 1), "--exec_num", str(rep)]; self.thread, self.worker = QThread(), ScriptWorker(RUN_FRAMEWORK_SCRIPT, args); self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run_script); self.worker.finished.connect(self.on_single_execution_finished); self.worker.log_updated.connect(self.append_log); self.worker.error.connect(self.handle_error); self.thread.start()
    @Slot(int)
    def on_single_execution_finished(self, code):
        self.append_log(f"Finalizada. Sucesso: {code == 0}."); self.thread.quit(); self.thread.wait()
        if code != 0: self.append_log("Erro na execução, pulando para próxima.")
        self.current_run_number += 1; self.progress_bar.setValue(self.current_run_number)
        if self._pending_runs: QTimer.singleShot(100, self.run_next_configuration)
        else: self.on_all_executions_finished(True, "Todas as execuções foram concluídas!")
    @Slot(str)
    def handle_error(self, msg): self.append_log(f"[ERRO FATAL] {msg}"); self.stop_execution()
    def stop_execution(self):
        if self.worker: self.worker.stop()
        if self.thread and self.thread.isRunning(): self.thread.quit(), self.thread.wait()
        self._pending_runs.clear(); self.on_all_executions_finished(False, "Interrompido.")
    def on_all_executions_finished(self, success, message):
        self.stop_btn.setEnabled(False); self.progress_bar.setValue(self.total_runs); self.status_label.setText(f"Finalizado! {message}"); self.append_log(f"✅ {message}"); self.thread, self.worker = None, None
        try: self.window().pages['config'].run_button.setEnabled(True)
        except Exception as e: self.append_log(f"Erro ao reativar botão: {e}")
        if success: QMessageBox.information(self, "Concluído!", "Resultados no Dashboard!")
    def consolidate_results(self):
        self.append_log("Consolidando...");
        try: self.db_controller.consolidate_results(), self.append_log("Resultados consolidados."), QMessageBox.information(self, "Sucesso", "Resultados consolidados.")
        except Exception as e: self.append_log(f"Erro: {e}"), QMessageBox.critical(self, "Erro", f"Falha: {e}")
    def run_dashboard(self):
        try: os.system(f"streamlit run {DASHBOARD_SCRIPT} --server.port 8501 &"), self.append_log("Dashboard iniciado em http://localhost:8501")
        except Exception as e: self.append_log(f"Erro ao iniciar dashboard: {e}")
    def append_log(self, msg): self.log_text.append(f"[{time.strftime('%H:%M:%S')}] {msg}"); self.log_text.ensureCursorVisible()

class NavigationMenu(QWidget):
    config_requested, params_requested, logs_requested = Signal(), Signal(), Signal()
    def __init__(self):
        super().__init__(); self.layout = QVBoxLayout(self); self.layout.setContentsMargins(0,0,0,0); self.layout.setSpacing(0); self.buttons, self.button_group = {}, QButtonGroup(self); self.button_group.setExclusive(True)
        self._add_nav_button("config", "⚙️ Configuração", self.config_requested); self._add_nav_button("params", "⌨ Parametros AG", self.params_requested); self._add_nav_button("logs", "▶️ Logs e Execução", self.logs_requested); self.layout.addStretch()
    def _add_nav_button(self, name, text, signal):
        btn = QPushButton(text); btn.setCheckable(True); btn.setObjectName(f"nav_btn_{name}"); btn.setProperty("class", "nav-button"); btn.clicked.connect(signal.emit); self.layout.addWidget(btn); self.buttons[name] = btn; self.button_group.addButton(btn)
    def set_active_button(self, tab_name):
        map = {"Configuração": "config", "Parametros AG - RCE": "params", "Exibição de Logs": "logs"}; btn_name = map.get(tab_name)
        if btn_name in self.buttons: self.buttons[btn_name].setChecked(True)

class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.config_manager, self.open_tabs = ConfigManager(), {}; self.init_ui(); self.init_pages(); self.connect_signals(); self.open_config_tab()
    def init_ui(self):
        self.setWindowTitle("RCE Framework Launcher - Edição PVRV"); self.resize(1280, 720)
        central_widget, self.main_layout = QWidget(), QHBoxLayout(None); self.main_layout.setContentsMargins(0,0,0,0); self.main_layout.setSpacing(0); central_widget.setLayout(self.main_layout); self.setCentralWidget(central_widget)
        self.left_menu = QFrame(); self.left_menu.setFixedWidth(240); self.left_menu.setStyleSheet("background-color: #1e1e1e;"); self.left_menu_layout = QVBoxLayout(self.left_menu); self.left_menu_layout.setContentsMargins(0,0,0,0)
        self.toggle_button = QPushButton("☰"); self.toggle_button.setFixedSize(40, 40); self.toggle_button.clicked.connect(self.toggle_menu); self.left_menu_layout.addWidget(self.toggle_button)
        self.nav_menu = NavigationMenu(); self.left_menu_layout.addWidget(self.nav_menu); self.main_layout.addWidget(self.left_menu)
        self.tabs = QTabWidget(); self.tabs.setTabsClosable(True); self.main_layout.addWidget(self.tabs); self.statusBar().showMessage("Pronto.")
    def init_pages(self): self.pages = {"config": ConfigTab(self.config_manager), "params": ParamsAGTab(self.config_manager), "logs": ExecutionTab(self.config_manager)}
    def connect_signals(self):
        self.nav_menu.config_requested.connect(self.open_config_tab); self.nav_menu.params_requested.connect(self.open_params_tab); self.nav_menu.logs_requested.connect(self.open_logs_tab)
        self.pages["config"].execution_requested.connect(self.pages["logs"].start_executions); self.pages["config"].execution_requested.connect(self.open_logs_tab)
        self.tabs.tabCloseRequested.connect(self.close_tab); self.tabs.currentChanged.connect(self.on_tab_changed)
    def open_or_focus_tab(self, name, title, widget):
        if name in self.open_tabs: self.tabs.setCurrentWidget(self.open_tabs[name])
        else: index = self.tabs.addTab(widget, title); self.tabs.setCurrentIndex(index); self.open_tabs[name] = widget
        self.nav_menu.set_active_button(title)
    @Slot()
    def open_config_tab(self): self.open_or_focus_tab("config", "Configuração", self.pages["config"])
    @Slot()
    def open_params_tab(self): self.open_or_focus_tab("params", "Parametros AG - RCE", self.pages["params"])
    @Slot()
    def open_logs_tab(self): self.open_or_focus_tab("logs", "Exibição de Logs", self.pages["logs"])
    @Slot(int)
    def close_tab(self, index):
        widget = self.tabs.widget(index)
        if widget:
            tab_name_to_remove = next((name for name, w in self.open_tabs.items() if w == widget), None)
            if tab_name_to_remove: del self.open_tabs[tab_name_to_remove]
            self.tabs.removeTab(index)
    @Slot(int)
    def on_tab_changed(self, index):
        if index != -1: self.nav_menu.set_active_button(self.tabs.tabText(index))
    @Slot()
    def toggle_menu(self):
        w, target = self.left_menu.width(), 0 if self.left_menu.width() > 0 else 240
        for prop in [b"minimumWidth", b"maximumWidth"]:
            anim = QPropertyAnimation(self.left_menu, prop); anim.setDuration(300); anim.setStartValue(w); anim.setEndValue(target); anim.setEasingCurve(QEasingCurve.InOutCubic); anim.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = LauncherWindow()
    window.show()
    sys.exit(app.exec())
