
# --- Imports do PySide6 ---

from PySide6.QtCore import (
    QThread,
    Signal,
    Slot,
    QObject
)


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
