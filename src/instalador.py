
import sys
import subprocess
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QLabel, QTextEdit, QStackedWidget, QHBoxLayout
)
from PySide6.QtCore import QThread, Signal, Qt

STYLESHEET = """
QWidget {
    background-color: #0047ab;
    color: #ecf0f1;
    font-family: Arial, sans-serif;
}
QPushButton {
    background-color: #009E2FFF;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #2980b9;
}
QPushButton:disabled {
    background-color: #566573;
    color: #95a5a6;
}
QTextEdit {
    background-color: #34495e;
    border: 1px solid #2c3e50;
    color: #ecf0f1;
    border-radius: 5px;
}
QLabel {
    background-color: transparent;
}
QLabel#title {
    font-size: 24px;
    font-weight: bold;
}
QLabel#subtitle {
    font-size: 18px;
    font-weight: bold;
}
"""

class InstallThread(QThread):
    """Executa a instalação de dependências em uma thread separada."""
    log_message = Signal(str)
    finished = Signal(bool)

    def __init__(self, requirements_path):
        super().__init__()
        self.requirements_path = requirements_path

    def run(self):
        try:
            self.log_message.emit("Iniciando a instalação de dependências...")
            command = [
                sys.executable, '-m', 'pip', 'install', '-r',
                self.requirements_path, '--break-system-packages'
            ]
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )

            for line in iter(process.stdout.readline, ''):
                self.log_message.emit(line.strip())

            process.wait()
            success = process.returncode == 0
            if success:
                self.log_message.emit("\nInstalação concluída com sucesso!")
            else:
                self.log_message.emit(f"\nErro na instalação (código de saída: {process.returncode}).")
            self.finished.emit(success)

        except Exception as e:
            self.log_message.emit(f"\nOcorreu um erro crítico: {e}")
            self.finished.emit(False)

class InstallerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Instalador do RCE Framework")
        self.setFixedSize(600, 400)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Paths
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.requirements_path = os.path.join(self.base_dir,  'DashboardApp', 'requirements.txt')
        self.launcher_path = os.path.join(self.base_dir, '..', 'laucher_revised.py')

        # Create pages
        self.create_welcome_page()
        self.create_install_page()
        self.create_launch_page()
        self.create_finish_page()

        self.current_page = 0
        self.stacked_widget.setCurrentIndex(self.current_page)

    def create_welcome_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Bem-vindo ao Instalador")
        title.setObjectName("title")
        
        description = QLabel(
            "Este assistente irá instalar as dependências necessárias e "
            "iniciar a aplicação RCE Framework."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)

        next_button = QPushButton("Avançar >")
        next_button.clicked.connect(self.next_page)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()
        layout.addWidget(next_button, alignment=Qt.AlignRight)
        
        self.stacked_widget.addWidget(page)

    def create_install_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel("Instalando Dependências")
        title.setObjectName("subtitle")

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)

        self.next_button_install = QPushButton("Avançar >")
        self.next_button_install.setEnabled(False)
        self.next_button_install.clicked.connect(self.next_page)

        layout.addWidget(title)
        layout.addWidget(self.log_text)
        layout.addWidget(self.next_button_install, alignment=Qt.AlignRight)

        self.stacked_widget.addWidget(page)

    def create_launch_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Pronto para Iniciar")
        title.setObjectName("title")

        description = QLabel(
            "A instalação foi concluída. Clique em 'Iniciar' para abrir o "
            "RCE Framework Launcher."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)

        launch_button = QPushButton("🚀 Iniciar")
        launch_button.clicked.connect(self.launch_application)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()
        layout.addWidget(launch_button, alignment=Qt.AlignCenter)

        self.stacked_widget.addWidget(page)

    def create_finish_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Aplicação Iniciada")
        title.setObjectName("title")

        description = QLabel(
            "O launcher foi iniciado em uma nova janela. "
            "Você pode fechar este instalador."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)

        finish_button = QPushButton("Concluir")
        finish_button.clicked.connect(self.close)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()
        layout.addWidget(finish_button, alignment=Qt.AlignRight)

        self.stacked_widget.addWidget(page)

    def next_page(self):
        self.current_page += 1
        self.stacked_widget.setCurrentIndex(self.current_page)

        if self.current_page == 1: # Página de instalação
            self.start_installation()

    def start_installation(self):
        self.install_thread = InstallThread(self.requirements_path)
        self.install_thread.log_message.connect(self.log_text.append)
        self.install_thread.finished.connect(self.on_installation_finished)
        self.install_thread.start()

    def on_installation_finished(self, success):
        if success:
            self.next_button_install.setEnabled(True)
        else:
            self.log_text.append("\n\nFalha na instalação. Verifique os logs acima.")

    def launch_application(self):
        try:
            subprocess.Popen([sys.executable, self.launcher_path])
            self.next_page()
        except Exception as e:
            error_label = self.stacked_widget.widget(2).findChild(QLabel, "error_label")
            if not error_label:
                error_label = QLabel(f"Erro ao iniciar: {e}")
                error_label.setObjectName("error_label")
                error_label.setStyleSheet("color: red;")
                self.stacked_widget.widget(2).layout().insertWidget(3, error_label)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = InstallerWindow()
    window.show()
    sys.exit(app.exec())
