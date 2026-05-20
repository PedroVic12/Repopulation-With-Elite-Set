# --- Imports do PySide6 ---

from PySide6.QtCore import (

    Signal,
    Slot,
    QObject,

)


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
