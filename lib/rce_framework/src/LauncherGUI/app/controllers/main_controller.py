# --- Imports do PySide6 ---
from PySide6.QtWidgets import (
    QMessageBox,
)
from PySide6.QtCore import (
    Qt,
    QThread,
    QTimer,
    Slot,
    QObject,
)

from ..models.executer_model import ExecutionModel, ScriptWorker
from ..models.config_manager import ConfigManager

from ..views.launcher_window import LauncherWindow
from ..views.tabs_page import *
from ..views.widgets.QT_Widgets import PowerSystemAnalysisView

from ..controllers.power_system_controller import PowerSystemController

from ....global_settings import CUSTOM_SCRIPTS, CLI_SCRIPT_PATH, ANALYSIS_CASES
import traceback

from functools import partial
import shutil

import importlib.util


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
