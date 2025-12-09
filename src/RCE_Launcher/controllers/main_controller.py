# src/RCE_Launcher/controllers/main_controller.py

import sys
import importlib.util
import traceback
from functools import partial
from pathlib import Path

from PySide6.QtCore import QObject, Slot, QTimer
from PySide6.QtWidgets import QMessageBox

from ..models.config_manager import ConfigManager
from ..models.execution_model import ExecutionModel, ScriptWorker
from ..views.main_window import LauncherWindow
from ..views.config_tabs import ConfigTab, ParamsAGTab
from ..views.script_execution_tab import ScriptExecutionTab
from ..views.power_analysis_tab import MainAnalysisTab, PowerSystemAnalysisView
from .power_system_controller import PowerSystemController


# --- Constantes ---
BASE_DIR = Path(__file__).parent.parent.parent.parent
SRC_DIR = BASE_DIR / "src"
RUN_FRAMEWORK_SCRIPT = SRC_DIR / "run.py"
RUN_AGENDAMENTO_SCRIPT = SRC_DIR / "run_agendamento.py"

ANALYSIS_CASES = {
    "case_ieee14": {
        "name": "Análise de Contingência - IEEE 14",
        "module_path": SRC_DIR / "utils/functions_fitness/analise_contingencia/analise_contingencia_ieee14.py",
        "agendamento_df_name": "agendamento_df_ieee14",
        "contingencia_df_name": "contingencia_df_ieee14",
        "network_name": "case14"
    },
    "case_ieee30": {
        "name": "Análise de Contingência - IEEE 30",
        "module_path": SRC_DIR / "utils/functions_fitness/analise_contingencia/analise_contingencia_ieee30.py",
        "agendamento_df_name": "agendamento_df_ieee30",
        "contingencia_df_name": "contingencia_df_ieee30",
        "network_name": "case30"
    },
    "case_ieee118": {
        "name": "Análise de Contingência - IEEE 118",
        "module_path": SRC_DIR / "utils/functions_fitness/analise_contingencia/analise_contingencia_ieee118.py",
        "agendamento_df_name": "agendamento_df_ieee118",
        "contingencia_df_name": "contingencia_df_ieee118",
        "network_name": "case118"
    }
}


class MainController(QObject):
    """
    Controller Principal - Orquestra toda a aplicação, conectando
    os Models (lógica) com as Views (UI).
    """
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.view = LauncherWindow()
        self.config_manager = ConfigManager()
        self.execution_model = ExecutionModel()
        
        self.open_tabs = {}  # Rastreia as abas abertas: {"tab_name": widget}
        self.analysis_controllers = {}  # Rastreia os sub-controllers de análise

        self.connect_signals()
        self.open_config_tab() # Abre a primeira aba ao iniciar

    def show(self):
        """Exibe a janela principal."""
        self.view.show()

    def connect_signals(self):
        """Conecta todos os sinais e slots da aplicação."""
        # --- Navegação Principal ---
        nav = self.view.nav_menu
        nav.config_ag_requested.connect(self.open_config_tab)
        nav.params_ag_requested.connect(self.open_params_tab)
        nav.run_ag_requested.connect(self.open_run_ag_tab)
        nav.run_agendamento_requested.connect(self.open_run_agendamento_tab)
        nav.power_system_analysis_requested.connect(self.open_power_system_analysis_tab)

        # --- Gerenciamento de Abas ---
        self.view.tabs.tabCloseRequested.connect(self.close_tab)
        self.view.tabs.currentChanged.connect(self.on_tab_changed)

        # --- Modelo de Execução (para a bateria de testes) ---
        model = self.execution_model
        model.log_updated.connect(self.update_log_on_active_tab)
        model.all_executions_finished.connect(self.on_queue_finished)
        model.execution_started.connect(self.on_queue_started)
        model.execution_progress.connect(self.on_queue_progress)

    def open_or_focus_tab(self, tab_name, title, widget_class, *args):
        """
        Abre uma nova aba ou foca em uma já existente.
        Este método também conecta os sinais específicos da aba.
        """
        if tab_name in self.open_tabs:
            self.view.set_current_tab(self.open_tabs[tab_name])
            return

        # Cria a view da aba
        widget = widget_class(*args)
        self.view.add_tab(widget, title)
        self.view.tabs.setCurrentWidget(widget)
        self.open_tabs[tab_name] = widget

        # Conecta os sinais específicos da aba recém-criada
        if isinstance(widget, ConfigTab):
            widget.execution_requested.connect(self.start_ag_execution_queue)
        elif isinstance(widget, ScriptExecutionTab):
            widget.start_stop_btn.clicked.connect(partial(self.toggle_single_script, widget))
            if hasattr(widget, 'consolidate_btn'):
                widget.consolidate_btn.clicked.connect(self.config_manager.consolidate_results)
        elif isinstance(widget, MainAnalysisTab):
            # Passa a si mesmo (o controller) como uma fábrica para o widget de seleção
            widget.selection_widget.analysis_selected.connect(self.load_analysis_case)

        self.view.nav_menu.set_active_button(tab_name)

    # --- Slots para Abrir Abas ---
    @Slot()
    def open_config_tab(self):
        self.open_or_focus_tab("config_ag", "⚙️ Configurar AG", ConfigTab, self.config_manager)

    @Slot()
    def open_params_tab(self):
        self.open_or_focus_tab("params_ag", "⌨️ Parâmetros AG", ParamsAGTab, self.config_manager)

    @Slot()
    def open_run_ag_tab(self):
        self.open_or_focus_tab("run_ag", "▶️ Executar AG", ScriptExecutionTab, "Bateria AG", RUN_FRAMEWORK_SCRIPT, is_queue_runner=True)

    @Slot()
    def open_run_agendamento_tab(self):
        self.open_or_focus_tab("run_agendamento", "📅 Executar Agendamento", ScriptExecutionTab, "Agendamento", RUN_AGENDAMENTO_SCRIPT)

    @Slot()
    def open_power_system_analysis_tab(self):
        self.open_or_focus_tab("power_system_analysis", "🔬 Análise de SEP", MainAnalysisTab, ANALYSIS_CASES, self)

    @Slot(str)
    def load_analysis_case(self, case_id):
        """Carrega dinamicamente o módulo do caso de análise e cria a sua UI."""
        main_tab_widget = self.open_tabs.get("power_system_analysis")
        if not main_tab_widget:
            return

        try:
            case_info = ANALYSIS_CASES[case_id]
            
            # Importação dinâmica do módulo
            spec = importlib.util.spec_from_file_location(case_info["module_path"].name, case_info["module_path"])
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Extração dos dados do módulo carregado
            agendamento_df = getattr(module, case_info["agendamento_df_name"])
            contingencia_df = getattr(module, case_info["contingencia_df_name"])

            # Cria a view e o controller para este caso
            view = PowerSystemAnalysisView(case_info["name"])
            # O item_class é necessário porque a view não pode importar o QListWidgetItem
            view.contingency_list.item_class = type(self.view.findChild(QListWidgetItem) or QListWidgetItem)

            controller = PowerSystemController(view, case_info['network_name'], agendamento_df, contingencia_df)
            self.analysis_controllers[case_id] = controller  # Guarda a referência

            main_tab_widget.show_analysis_view(view)

        except Exception as e:
            QMessageBox.critical(self.view, "Erro ao Carregar Análise", f"Não foi possível carregar o caso '{case_id}':\n{e}\n\nTrace: {traceback.format_exc()}")

    # --- Slots para Gerenciamento de Abas e Execuções ---
    @Slot(int)
    def close_tab(self, index):
        widget = self.view.tabs.widget(index)
        if widget:
            tab_name = next((name for name, w in self.open_tabs.items() if w == widget), None)
            if tab_name:
                if tab_name in self.analysis_controllers:
                    del self.analysis_controllers[tab_name]
                del self.open_tabs[tab_name]
            self.view.close_tab(index)

    @Slot(int)
    def on_tab_changed(self, index):
        if index == -1: return
        widget = self.view.tabs.widget(index)
        tab_name = next((name for name, w in self.open_tabs.items() if w == widget), None)
        if tab_name:
            self.view.nav_menu.set_active_button(tab_name)

    @Slot(list, int)
    def start_ag_execution_queue(self, configs, runs_per_config):
        self.open_run_ag_tab()
        QTimer.singleShot(100, lambda: self.execution_model.start_execution_queue(configs, runs_per_config, self.config_manager))

    # --- Slots que recebem sinais do ExecutionModel ---
    @Slot(int)
    def on_queue_started(self, total_runs):
        tab = self.open_tabs.get("run_ag")
        if tab and isinstance(tab, ScriptExecutionTab):
            tab.progress_bar.setRange(0, total_runs)
            tab.progress_bar.setValue(0)
            tab.progress_bar.setVisible(True)
            tab.start_stop_btn.setText("⏹️ Parar Bateria")
            tab.start_stop_btn.setEnabled(True)
            tab.start_stop_btn.clicked.disconnect()
            tab.start_stop_btn.clicked.connect(self.execution_model.stop_all)


    @Slot(int, str)
    def on_queue_progress(self, current_run, status_text):
        tab = self.open_tabs.get("run_ag")
        if tab and isinstance(tab, ScriptExecutionTab):
            tab.progress_bar.setValue(current_run)
            tab.status_label.setText(status_text)

    @Slot(bool, str)
    def on_queue_finished(self, success, message):
        tab = self.open_tabs.get("run_ag")
        if tab and isinstance(tab, ScriptExecutionTab):
            tab.on_execution_finished(success, message)
            # Reconecta o botão para a função original
            tab.start_stop_btn.clicked.disconnect()
            tab.start_stop_btn.clicked.connect(partial(self.toggle_single_script, tab))


    @Slot(str)
    def update_log_on_active_tab(self, message):
        current_widget = self.view.tabs.currentWidget()
        if isinstance(current_widget, ScriptExecutionTab):
            current_widget.append_log(message)

    # --- Lógica para Scripts Individuais ---
    def toggle_single_script(self, tab_widget: ScriptExecutionTab):
        if tab_widget.thread and tab_widget.thread.isRunning():
            if tab_widget.worker:
                tab_widget.worker.stop()
        else:
            tab_widget.log_text.clear()
            tab_widget.worker = ScriptWorker(tab_widget.script_path)
            tab_widget.thread = QThread()
            tab_widget.worker.moveToThread(tab_widget.thread)
            tab_widget.worker.log_updated.connect(tab_widget.append_log)
            tab_widget.worker.finished.connect(lambda code: self.on_single_script_finished(tab_widget, code))
            tab_widget.thread.started.connect(tab_widget.worker.run)
            tab_widget.thread.start()
            tab_widget.start_stop_btn.setText("⏹️ Parar Script")

    def on_single_script_finished(self, tab_widget: ScriptExecutionTab, code: int):
        tab_widget.thread.quit()
        tab_widget.thread.wait()
        tab_widget.thread, tab_widget.worker = None, None
        tab_widget.on_execution_finished(code == 0, f"Script concluído com código {code}.")
