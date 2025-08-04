# src/launcher/controllers/main_controller.py

import sys
import subprocess
import time
from itertools import product
from functools import reduce
import operator
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, QTimer

from ..models.config_model import ConfigManager
from ..views.main_window import LauncherWindow

# O Controller é o "maestro" da aplicação. Ele não conhece os detalhes
# dos widgets da View, mas sabe como obter os dados dela. Ele também não
# sabe como os dados são salvos, apenas pede ao Model para fazer isso.
# Ele contém toda a lógica de negócio da aplicação.

class ExecutionThread(QThread):
    """
    Executa o script do framework em uma thread separada para não congelar a interface.
    Herda de QThread, a classe do PySide6 para gerenciamento de threads.
    """
    # Sinais são a forma como uma thread se comunica com a thread principal da GUI.
    # Eles podem carregar dados (ex: uma string com a mensagem de log).
    log_updated = Signal(str)
    execution_finished = Signal(bool, str)

    def __init__(self, script_path: Path, args: list, src_dir: Path):
        super().__init__()
        self.script_path = script_path
        self.args = args or []
        self.src_dir = src_dir
        self.process = None

    def run(self):
        """O código dentro deste método é executado na nova thread."""
        try:
            cmd = [sys.executable, str(self.script_path)] + self.args
            self.log_updated.emit(f"Executando: {' '.join(cmd)}")
            
            # subprocess.Popen inicia um novo processo.
            self.process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                universal_newlines=True, 
                cwd=self.src_dir, 
                encoding='utf-8'
            )
            # Itera sobre a saída do processo linha por linha em tempo real.
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.log_updated.emit(line.strip())
            
            return_code = self.process.wait() # Espera o processo terminar.
            self.execution_finished.emit(return_code == 0, f"Código de retorno: {return_code}")
        except Exception as e:
            self.log_updated.emit(f"Erro na execução: {e}")
            self.execution_finished.emit(False, str(e))

    def stop(self):
        """Termina o processo em execução."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.log_updated.emit("Processo de execução terminado pelo usuário.")

class MainController(QObject):
    """
    O controlador principal da aplicação.
    Herda de QObject para poder usar o sistema de sinais/slots do PySide6.
    """
    def __init__(self, model: ConfigManager, view: LauncherWindow, config: dict):
        super().__init__()
        self._model = model
        self._view = view
        self._config = config
        self._execution_thread = None
        self._configurations = []
        self._runs_per_config = 0
        self._current_run_number = 0
        self._total_runs = 0

        self._connect_signals()
        self._populate_initial_data()

    def _connect_signals(self):
        """Conecta os sinais dos widgets da View aos slots (métodos) do Controller."""
        # Aba de Configuração
        config_tab = self._view.config_tab
        config_tab.run_button.clicked.connect(self.prepare_and_run)
        config_tab.runs_per_config_spin.valueChanged.connect(self._update_summary)
        for param in config_tab.param_widgets.values():
            param["mode"].buttonClicked.connect(self._update_summary)
            param["fixed"].textChanged.connect(self._update_summary)
            for var_input in param["variable"]:
                var_input.textChanged.connect(self._update_summary)

        # Aba de Execução
        exec_tab = self._view.execution_tab
        exec_tab.stop_btn.clicked.connect(self.stop_execution)
        exec_tab.run_dashboard_btn.clicked.connect(self._run_dashboard)

    def _populate_initial_data(self):
        """Preenche a View com os dados iniciais do Model."""
        config_tab = self._view.config_tab
        params_to_render = {
            "MUTACAO": self._model.get_param("MUTACAO", 0.1),
            "CROSSOVER": self._model.get_param("CROSSOVER", 0.8),
            "NUM_GENERATIONS": self._model.get_param("NUM_GENERATIONS", 100),
            "POP_SIZE": self._model.get_param("POP_SIZE", 50),
        }
        for name, value in params_to_render.items():
            config_tab.add_param_widget(name, value)
        
        runs = self._model.get_option('repeticoes_por_config', 1)
        config_tab.runs_per_config_spin.setValue(runs)
        self._update_summary() # Atualiza o resumo inicial

    def _update_summary(self):
        """Calcula e atualiza as labels de resumo na View."""
        config_tab = self._view.config_tab
        num_variations = []
        for name, widgets in config_tab.param_widgets.items():
            if widgets["mode"].buttons()[1].isChecked(): # Modo variável
                var_values = [inp.text() for inp in widgets["variable"] if inp.text()]
                if var_values:
                    num_variations.append(len(var_values))
        
        total_combinations = reduce(operator.mul, num_variations, 1) if num_variations else 1
        total_execucoes = total_combinations * config_tab.runs_per_config_spin.value()

        config_tab.unique_configs_label.setText(f"Configurações Únicas: {total_combinations}")
        config_tab.total_runs_label.setText(f"Total de Execuções: {total_execucoes}")

    def prepare_and_run(self):
        """Valida os dados da View, prepara as configurações e inicia a execução."""
        try:
            config_tab = self._view.config_tab
            variable_params, fixed_params = {}, {}
            for name, widgets in config_tab.param_widgets.items():
                is_int = widgets["is_int"]
                if widgets["mode"].buttons()[1].isChecked(): # Variável
                    values = []
                    for field in widgets["variable"]:
                        if field.text():
                            try:
                                values.append(int(field.text()) if is_int else float(field.text()))
                            except ValueError:
                                config_tab.show_message("Valor Inválido", f"Valor inválido para {name}: '{field.text()}'", "warning")
                                return
                    if values: 
                        variable_params[name] = values
                    else: # Se não há valores variáveis, usa o fixo
                        fixed_params[name] = int(widgets["fixed"].text()) if is_int else float(widgets["fixed"].text())
                else: # Fixo
                    try:
                        fixed_params[name] = int(widgets["fixed"].text()) if is_int else float(widgets["fixed"].text())
                    except ValueError:
                        config_tab.show_message("Valor Inválido", f"Valor inválido para {name}: '{widgets['fixed'].text()}'", "warning")
                        return

            keys, values = variable_params.keys(), variable_params.values()
            self._configurations = [dict(zip(keys, v)) for v in product(*values)] if keys else [{}]
            for config in self._configurations:
                config.update(fixed_params)

            self._runs_per_config = config_tab.runs_per_config_spin.value()
            options = self._model.options.copy()
            options['repeticoes_por_config'] = self._runs_per_config
            if not self._model.save_json(options, self._model.options_file):
                config_tab.show_message("Erro", f"Falha ao salvar {self._model.options_file.name}", "critical")
                return

            msg = f"{len(self._configurations)} configs únicas serão executadas {self._runs_per_config} vez(es) cada."
            config_tab.show_message("Pronto para Iniciar", msg)
            self._start_executions()

        except Exception as e:
            self._view.config_tab.show_message("Erro", f"Erro ao preparar execução: {e}", "critical")

    def _start_executions(self):
        """Inicia o processo de execução em lote."""
        exec_tab = self._view.execution_tab
        if not self._config["RUN_FRAMEWORK_SCRIPT"].exists():
            self._view.config_tab.show_message("Erro", f"Script não encontrado: {self._config['RUN_FRAMEWORK_SCRIPT']}", "critical")
            return
        
        self._total_runs = len(self._configurations) * self._runs_per_config
        self._current_run_number = 0
        
        exec_tab.log_text.clear()
        self._log(f"Iniciando bateria de testes com {len(self._configurations)} configs e {self._runs_per_config} repetições.")
        self._log(f"Total de execuções: {self._total_runs}")

        exec_tab.stop_btn.setEnabled(True)
        exec_tab.progress_bar.setVisible(True)
        exec_tab.progress_bar.setRange(0, self._total_runs)
        exec_tab.progress_bar.setValue(0)
        self._view.tab_widget.setCurrentWidget(exec_tab)
        
        self._run_next_configuration()

    def _run_next_configuration(self):
        """Executa a próxima configuração da fila."""
        if self._current_run_number >= self.total_runs:
            self._on_all_executions_finished(True, "Todas as execuções foram concluídas.")
            return

        config_index = self._current_run_number // self._runs_per_config
        repetition = (self._current_run_number % self._runs_per_config) + 1
        current_config = self._configurations[config_index]
        
        config_str = ", ".join([f"{k}: {v}" for k, v in current_config.items()])
        self._view.execution_tab.current_config_label.setText(f"Execução {self._current_run_number + 1}/{self._total_runs} (Rep. {repetition}) | {config_str}")
        self._log("-" * 20)
        self._log(f"Iniciando Config {config_index + 1}, Execução {repetition}: {config_str}")

        # Prepara os parâmetros para esta execução específica
        base_params = self._model.params.copy()
        base_params.update(current_config)
        
        # Salva uma cópia do params.json para cada configuração (para o dashboard)
        config_params_path = self._config["SRC_DIR"] / f"output/params_config{config_index + 1}.json"
        if not self._model.save_json(base_params, config_params_path):
             self._log(f"❌ Erro ao salvar o arquivo de parâmetros de configuração {config_params_path}")

        # Salva o params.json principal para o script de execução ler
        if not self._model.save_json(base_params, self._model.params_file):
             self._log(f"❌ Erro ao salvar o arquivo de parâmetros {self._model.params_file}")
             self._on_all_executions_finished(False, "Erro de arquivo.")
             return

        args = ["--config_num", str(config_index + 1), "--exec_num", str(repetition)]
        self._execution_thread = ExecutionThread(self._config["RUN_FRAMEWORK_SCRIPT"], args, self._config["SRC_DIR"])
        self._execution_thread.log_updated.connect(self._log)
        self._execution_thread.execution_finished.connect(self._on_single_execution_finished)
        self._execution_thread.start()

    def _on_single_execution_finished(self, success: bool, message: str):
        """Slot para o sinal de finalização de uma única execução."""
        self._log(f"Finalizada execução {self._current_run_number + 1}. Sucesso: {success}. {message}")
        if not success:
            self._log(f"❌ Erro na execução, pulando para a próxima.")
        
        self._current_run_number += 1
        self._view.execution_tab.progress_bar.setValue(self._current_run_number)
        
        # Usa um QTimer para evitar recursão e manter a GUI responsiva.
        QTimer.singleShot(100, self._run_next_configuration)

    def _on_all_executions_finished(self, success: bool, message: str):
        """Chamado quando todas as execuções terminam ou são interrompidas."""
        exec_tab = self._view.execution_tab
        exec_tab.stop_btn.setEnabled(False)
        exec_tab.progress_bar.setValue(exec_tab.progress_bar.maximum())
        exec_tab.current_config_label.setText(f"Finalizado. {message}")
        
        final_message = f"✅ {message}" if success else f"❌ {message}"
        self._log(final_message)
        
        msg_level = "info" if success else "critical"
        if "Interrompido" in message: msg_level = "warning"
        self._view.config_tab.show_message("Execução Concluída", final_message, msg_level)

    def stop_execution(self):
        """Interrompe a execução em lote."""
        self._total_runs = 0 # Impede a próxima execução
        if self._execution_thread and self._execution_thread.isRunning():
            self._execution_thread.stop()
        self._on_all_executions_finished(False, "Interrompido pelo usuário.")

    def _run_dashboard(self):
        """Inicia o dashboard do Streamlit."""
        dashboard_script = self._config["DASHBOARD_SCRIPT"]
        if not dashboard_script.exists():
            self._view.config_tab.show_message("Erro", f"Dashboard não encontrado: {dashboard_script}", "critical")
            return
        try:
            # Usa Popen para não bloquear o launcher.
            subprocess.Popen(["streamlit", "run", str(dashboard_script), "--server.port", "8501"], cwd=self._config["BASE_DIR"])
            self._log("Dashboard iniciado em http://localhost:8501")
        except Exception as e:
            self._log(f"Erro ao iniciar dashboard: {e}")

    def _log(self, message: str):
        """Adiciona uma mensagem ao log na View com timestamp."""
        timestamp = time.strftime('%H:%M:%S')
        self._view.execution_tab.append_log(f"[{timestamp}] {message}")
