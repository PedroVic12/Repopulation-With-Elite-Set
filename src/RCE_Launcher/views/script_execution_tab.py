# src/RCE_Launcher/views/script_execution_tab.py

import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QProgressBar,
    QGroupBox, QPushButton, QMessageBox
)
from PySide6.QtCore import Slot

class ScriptExecutionTab(QWidget):
    """
    View - Uma aba genérica para executar um script e exibir logs.
    """
    def __init__(self, tab_title: str, is_queue_runner: bool = False):
        super().__init__()
        self.tab_title = tab_title
        self.is_queue_runner = is_queue_runner
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # --- Widgets de Status ---
        self.status_label = QLabel("Aguardando início...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        status_box = QGroupBox("Status")
        sbl = QVBoxLayout(status_box)
        sbl.addWidget(self.status_label)
        sbl.addWidget(self.progress_bar)

        # --- Widget de Log ---
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_box = QGroupBox("Log de Execução")
        lbl = QVBoxLayout(log_box)
        lbl.addWidget(self.log_text)

        layout.addWidget(status_box)
        layout.addWidget(log_box)

        # --- Botões de Controle ---
        ctrl_layout = QHBoxLayout()
        self.start_stop_btn = QPushButton(f"▶️ Iniciar {self.tab_title}")
        # A lógica do clique será conectada pelo Controller
        ctrl_layout.addWidget(self.start_stop_btn)

        if not self.is_queue_runner:
            self.consolidate_btn = QPushButton("📄 Consolidar Resultados")
            # O clique também será conectado pelo Controller
            ctrl_layout.addStretch()
            ctrl_layout.addWidget(self.consolidate_btn)

        layout.addLayout(ctrl_layout)

    @Slot(str)
    def append_log(self, msg: str):
        """Adiciona uma mensagem ao widget de log."""
        self.log_text.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
        self.log_text.ensureCursorVisible()

    @Slot(bool, str)
    def on_execution_finished(self, success: bool, message: str):
        """Atualiza a UI quando a execução termina."""
        self.status_label.setText(f"Finalizado: {message}")
        if success:
            self.progress_bar.setValue(self.progress_bar.maximum())
        
        self.start_stop_btn.setText(f"▶️ Iniciar {self.tab_title}")
        self.start_stop_btn.setEnabled(True)

        if success:
            QMessageBox.information(self, "Concluído", message)
