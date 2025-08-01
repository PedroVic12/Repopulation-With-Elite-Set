import sys
import os
import json
import subprocess
import threading
import time
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, 
    QHBoxLayout, QTextEdit, QProgressBar, QTabWidget, QGroupBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QLineEdit, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PySide6.QtGui import QFont, QIcon

# --- CONFIGURAÇÃO ---
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"
PARAMS_FILE = SRC_DIR / "params.json"
OPTIONS_FILE = SRC_DIR / "options.json"
RUN_FRAMEWORK_SCRIPT = SRC_DIR / "run_framework.py"
DASHBOARD_SCRIPT = SRC_DIR / "DashboardApp" / "dashboard_rce_app_v11.py"

# Estilo QSS moderno
STYLESHEET = """
QWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 12px;
}

QMainWindow {
    background-color: #1e1e1e;
}

QLabel#title {
    font-size: 24px;
    font-weight: bold;
    color: #00d4ff;
    padding: 10px;
}

QLabel#subtitle {
    font-size: 14px;
    color: #cccccc;
    padding: 5px;
}

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

QPushButton:hover {
    background-color: #005a9e;
}

QPushButton:pressed {
    background-color: #004578;
}

QPushButton#success {
    background-color: #28a745;
}

QPushButton#success:hover {
    background-color: #218838;
}

QPushButton#warning {
    background-color: #ffc107;
    color: #212529;
}

QPushButton#warning:hover {
    background-color: #e0a800;
}

QGroupBox {
    font-weight: bold;
    border: 2px solid #404040;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
    color: #00d4ff;
}

QSpinBox, QDoubleSpinBox, QLineEdit {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    border-radius: 4px;
    padding: 5px;
    color: white;
}

QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {
    border: 2px solid #007acc;
}

QTextEdit {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    border-radius: 4px;
    color: #00ff00;
    font-family: "Consolas", "Monaco", monospace;
    font-size: 11px;
}

QProgressBar {
    border: 2px solid #404040;
    border-radius: 5px;
    text-align: center;
    background-color: #2d2d2d;
}

QProgressBar::chunk {
    background-color: #28a745;
    border-radius: 3px;
}

QTabWidget::pane {
    border: 1px solid #404040;
    background-color: #1e1e1e;
}

QTabBar::tab {
    background-color: #2d2d2d;
    color: white;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #007acc;
}

QTabBar::tab:hover {
    background-color: #404040;
}
"""

class ConfigManager:
    """Gerencia as configurações do framework"""
    
    def __init__(self):
        self.params = self.load_json(PARAMS_FILE)
        self.options = self.load_json(OPTIONS_FILE)
    
    def load_json(self, file_path):
        """Carrega arquivo JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar {file_path}: {e}")
            return {}
    
    def save_json(self, data, file_path):
        """Salva arquivo JSON"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar {file_path}: {e}")
            return False
    
    def update_params(self, new_params):
        """Atualiza params.json"""
        self.params.update(new_params)
        return self.save_json(self.params, PARAMS_FILE)
    
    def update_options(self, new_options):
        """Atualiza options.json"""
        self.options.update(new_options)
        return self.save_json(self.options, OPTIONS_FILE)

class ExecutionThread(QThread):
    """Thread para execução do framework em background"""
    
    progress_updated = pyqtSignal(int)
    log_updated = pyqtSignal(str)
    execution_finished = pyqtSignal(bool, str)
    
    def __init__(self, script_path, args=None):
        super().__init__()
        self.script_path = script_path
        self.args = args or []
        self.process = None
    
    def run(self):
        try:
            cmd = [sys.executable, str(self.script_path)] + self.args
            self.log_updated.emit(f"Executando: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=SRC_DIR
            )
            
            # Monitora a saída em tempo real
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.log_updated.emit(line.strip())
            
            return_code = self.process.wait()
            success = return_code == 0
            self.execution_finished.emit(success, f"Código de retorno: {return_code}")
            
        except Exception as e:
            self.log_updated.emit(f"Erro na execução: {e}")
            self.execution_finished.emit(False, str(e))

class ConfigTab(QWidget):
    """Aba de configuração dos parâmetros"""
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Parâmetros do Algoritmo Genético
        ag_group = QGroupBox("Parâmetros do Algoritmo Genético")
        ag_layout = QVBoxLayout()
        
        # Número de Gerações
        self.generations_spin = QSpinBox()
        self.generations_spin.setRange(1, 1000)
        self.generations_spin.setValue(self.config_manager.params.get("NUM_GENERATIONS", 40))
        ag_layout.addWidget(QLabel("Número de Gerações:"))
        ag_layout.addWidget(self.generations_spin)
        
        # Tamanho da População
        self.pop_size_spin = QSpinBox()
        self.pop_size_spin.setRange(1, 1000)
        self.pop_size_spin.setValue(self.config_manager.params.get("POP_SIZE", 5))
        ag_layout.addWidget(QLabel("Tamanho da População:"))
        ag_layout.addWidget(self.pop_size_spin)
        
        # Taxa de Mutação
        self.mutation_spin = QDoubleSpinBox()
        self.mutation_spin.setRange(0.0, 1.0)
        self.mutation_spin.setSingleStep(0.01)
        self.mutation_spin.setValue(self.config_manager.params.get("MUTACAO", 0.25))
        ag_layout.addWidget(QLabel("Taxa de Mutação:"))
        ag_layout.addWidget(self.mutation_spin)
        
        # Taxa de Crossover
        self.crossover_spin = QDoubleSpinBox()
        self.crossover_spin.setRange(0.0, 1.0)
        self.crossover_spin.setSingleStep(0.01)
        self.crossover_spin.setValue(self.config_manager.params.get("CROSSOVER", 0.95))
        ag_layout.addWidget(QLabel("Taxa de Crossover:"))
        ag_layout.addWidget(self.crossover_spin)
        
        ag_group.setLayout(ag_layout)
        layout.addWidget(ag_group)
        
        # Parâmetros RCE
        rce_group = QGroupBox("Parâmetros RCE")
        rce_layout = QVBoxLayout()
        
        # Gerações de Repopulação
        self.rce_generations_spin = QSpinBox()
        self.rce_generations_spin.setRange(1, 1000)
        self.rce_generations_spin.setValue(self.config_manager.params.get("RCE_REPOPULATION_GENERATIONS", 50))
        rce_layout.addWidget(QLabel("Gerações de Repopulação:"))
        rce_layout.addWidget(self.rce_generations_spin)
        
        # Porcentagem
        self.percentage_spin = QDoubleSpinBox()
        self.percentage_spin.setRange(0.0, 1.0)
        self.percentage_spin.setSingleStep(0.01)
        self.percentage_spin.setValue(self.config_manager.params.get("PORCENTAGEM", 0.2))
        rce_layout.addWidget(QLabel("Porcentagem:"))
        rce_layout.addWidget(self.percentage_spin)
        
        rce_group.setLayout(rce_layout)
        layout.addWidget(rce_group)
        
        # Botões de ação
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("💾 Salvar Configurações")
        self.save_button.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_button)
        
        self.reset_button = QPushButton("🔄 Resetar")
        self.reset_button.clicked.connect(self.reset_config)
        button_layout.addWidget(self.reset_button)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def save_config(self):
        """Salva as configurações"""
        new_params = {
            "NUM_GENERATIONS": self.generations_spin.value(),
            "POP_SIZE": self.pop_size_spin.value(),
            "MUTACAO": self.mutation_spin.value(),
            "CROSSOVER": self.crossover_spin.value(),
            "RCE_REPOPULATION_GENERATIONS": self.rce_generations_spin.value(),
            "PORCENTAGEM": self.percentage_spin.value(),
        }
        
        if self.config_manager.update_params(new_params):
            QMessageBox.information(self, "Sucesso", "Configurações salvas com sucesso!")
        else:
            QMessageBox.critical(self, "Erro", "Erro ao salvar configurações!")
    
    def reset_config(self):
        """Reseta as configurações para os valores padrão"""
        self.generations_spin.setValue(40)
        self.pop_size_spin.setValue(5)
        self.mutation_spin.setValue(0.25)
        self.crossover_spin.setValue(0.95)
        self.rce_generations_spin.setValue(50)
        self.percentage_spin.setValue(0.2)

class ExecutionTab(QWidget):
    """Aba de execução do framework"""
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.execution_thread = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Controles de execução
        control_layout = QHBoxLayout()
        
        self.run_framework_btn = QPushButton("🚀 Executar Framework")
        self.run_framework_btn.clicked.connect(self.run_framework)
        control_layout.addWidget(self.run_framework_btn)
        
        self.run_dashboard_btn = QPushButton("📊 Abrir Dashboard")
        self.run_dashboard_btn.clicked.connect(self.run_dashboard)
        control_layout.addWidget(self.run_dashboard_btn)
        
        self.stop_btn = QPushButton("⏹️ Parar Execução")
        self.stop_btn.clicked.connect(self.stop_execution)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        layout.addLayout(control_layout)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Log de execução
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(300)
        layout.addWidget(QLabel("Log de Execução:"))
        layout.addWidget(self.log_text)
        
        self.setLayout(layout)
    
    def run_framework(self):
        """Executa o framework"""
        if not RUN_FRAMEWORK_SCRIPT.exists():
            QMessageBox.critical(self, "Erro", f"Script não encontrado: {RUN_FRAMEWORK_SCRIPT}")
            return
        
        self.run_framework_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminado
        
        self.execution_thread = ExecutionThread(RUN_FRAMEWORK_SCRIPT)
        self.execution_thread.progress_updated.connect(self.progress_bar.setValue)
        self.execution_thread.log_updated.connect(self.append_log)
        self.execution_thread.execution_finished.connect(self.execution_finished)
        self.execution_thread.start()
    
    def run_dashboard(self):
        """Executa o dashboard Streamlit"""
        if not DASHBOARD_SCRIPT.exists():
            QMessageBox.critical(self, "Erro", f"Dashboard não encontrado: {DASHBOARD_SCRIPT}")
            return
        
        try:
            subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", str(DASHBOARD_SCRIPT),
                "--server.port", "8501"
            ], cwd=SRC_DIR)
            self.append_log("Dashboard iniciado em http://localhost:8501")
        except Exception as e:
            self.append_log(f"Erro ao iniciar dashboard: {e}")
    
    def stop_execution(self):
        """Para a execução atual"""
        if self.execution_thread and self.execution_thread.isRunning():
            self.execution_thread.terminate()
            self.execution_thread.wait()
            self.append_log("Execução interrompida pelo usuário")
        
        self.run_framework_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
    
    def append_log(self, message):
        """Adiciona mensagem ao log"""
        self.log_text.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        self.log_text.ensureCursorVisible()
    
    def execution_finished(self, success, message):
        """Chamado quando a execução termina"""
        self.run_framework_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if success:
            self.append_log("✅ Execução concluída com sucesso!")
            QMessageBox.information(self, "Sucesso", "Framework executado com sucesso!")
        else:
            self.append_log(f"❌ Erro na execução: {message}")
            QMessageBox.critical(self, "Erro", f"Erro na execução: {message}")

class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("RCE Framework Launcher - Otimizado")
        self.setMinimumSize(800, 600)
        
        # Widget central com tabs
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(self.central_widget)
        
        # Título
        title = QLabel("Repopulation-With-Elite-Set Framework")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        subtitle = QLabel("Launcher Otimizado com Configuração e Execução em Tempo Real")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)
        
        # Tabs
        self.tab_widget = QTabWidget()
        
        # Tab de configuração
        self.config_tab = ConfigTab(self.config_manager)
        self.tab_widget.addTab(self.config_tab, "⚙️ Configuração")
        
        # Tab de execução
        self.execution_tab = ExecutionTab(self.config_manager)
        self.tab_widget.addTab(self.execution_tab, "🚀 Execução")
        
        main_layout.addWidget(self.tab_widget)
        
        # Status bar
        self.statusBar().showMessage("Pronto para executar")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    
    window = LauncherWindow()
    window.show()
    
    sys.exit(app.exec())
