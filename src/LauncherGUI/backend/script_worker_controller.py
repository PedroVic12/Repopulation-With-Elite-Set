import sys

import subprocess
from pathlib import Path



from PySide6.QtCore import Signal,  Slot, QObject


# --- IMPORTS DO PROJETO ---
from database_controller import DatabaseController

# --- CONFIGURAÇÃO ---
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"
RUN_FRAMEWORK_SCRIPT = SRC_DIR / "run.py"
DASHBOARD_SCRIPT = SRC_DIR / "DashboardApp" / "dashboard_RCE_APP.py"

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
