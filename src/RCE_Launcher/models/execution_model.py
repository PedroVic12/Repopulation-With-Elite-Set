# src/RCE_Launcher/models/execution_model.py

import sys
import subprocess
from pathlib import Path
from collections import deque

from PySide6.QtCore import QObject, Signal, Slot, QThread, QTimer

# Define constants relative to the project structure
BASE_DIR = Path(__file__).parent.parent.parent.parent
SRC_DIR = BASE_DIR / "src"
RUN_FRAMEWORK_SCRIPT = SRC_DIR / "run.py"


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
            # Use the python from the virtual environment if it exists
            python_executable = BASE_DIR / ".venv/bin/python3"
            if not python_executable.exists():
                python_executable = sys.executable # Fallback to current python

            cmd = [str(python_executable)] + [str(p) for p in [self.script_path] + self.args]
            self.log_updated.emit(f"Executando: {' '.join(cmd)}")
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=SRC_DIR,
                encoding='utf-8',
                errors='replace'
            )
            for line in iter(self.process.stdout.readline, ''):
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
    """Model - Gerencia a lógica da fila de execuções de scripts."""
    execution_started = Signal(int)  # total_runs
    execution_progress = Signal(int, str)  # current_run_number, status_text
    log_updated = Signal(str)
    all_executions_finished = Signal(bool, str)

    def __init__(self):
        super().__init__()
        self.thread = None
        self.worker = None
        self._pending_runs = deque()
        self.configurations = []
        self.total_runs = 0
        self.current_run_number = 0

    def start_execution_queue(self, configs, runs_per_config, config_manager):
        if self.thread and self.thread.isRunning():
            self.log_updated.emit("Bateria de testes em execução.")
            return

        self.configurations = configs
        self._pending_runs = deque([(ci, r) for ci in range(len(configs)) for r in range(1, runs_per_config + 1)])
        self.total_runs = len(self._pending_runs)
        self.current_run_number = 0

        self.execution_started.emit(self.total_runs)
        self._run_next_in_queue(config_manager)

    def _run_next_in_queue(self, config_manager):
        if not self._pending_runs:
            self.all_executions_finished.emit(True, "Todas as execuções foram concluídas!")
            return

        cfg_idx, rep = self._pending_runs.popleft()
        current_config = self.configurations[cfg_idx]
        self.current_run_number += 1
        status = f"Executando {self.current_run_number}/{self.total_runs} (Config: {cfg_idx + 1}, Rep: {rep})"
        self.execution_progress.emit(self.current_run_number, status)

        if not config_manager.save_params(current_config):
            self.log_updated.emit("Erro ao salvar parâmetros, abortando.")
            self.all_executions_finished.emit(False, "Erro ao salvar arquivo de parâmetros.")
            return

        args = ["--config_num", str(cfg_idx + 1), "--exec_num", str(rep)]
        self.worker = ScriptWorker(RUN_FRAMEWORK_SCRIPT, args)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)

        self.worker.log_updated.connect(self.log_updated)
        self.worker.error.connect(lambda msg: self.all_executions_finished.emit(False, msg))
        self.worker.finished.connect(lambda code: self._on_single_finished(code, config_manager))
        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def _on_single_finished(self, code, config_manager):
        self.log_updated.emit(f"Execução finalizada com código {code}.")
        self.thread.quit()
        self.thread.wait()
        QTimer.singleShot(100, lambda: self._run_next_in_queue(config_manager))

    def stop_all(self):
        self._pending_runs.clear()
        if self.worker:
            self.worker.stop()
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.all_executions_finished.emit(False, "Execução interrompida pelo usuário.")
