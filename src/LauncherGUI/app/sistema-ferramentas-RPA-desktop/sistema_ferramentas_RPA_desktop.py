import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QWidget, QFileDialog, QTextEdit, 
                               QTableWidget, QTableWidgetItem, QLabel, QTabWidget,
                               QGroupBox, QProgressBar, QMessageBox, QCheckBox,
                               QLineEdit, QFrame, QHeaderView)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QFont, QColor


from gui.iframes.perdas_duplas_widget import PerdasDuplasWidget

# ===============================================================
# CLASSE: MainWindow (SEU TEMPLATE PRINCIPAL)
# ===============================================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema Principal - Ferramentas RPA")
        self.setGeometry(100, 100, 1400, 900)
        
        self.setup_ui()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Cabeçalho
        header_label = QLabel("Sistema Principal - Ferramentas RPA")
        header_label.setFont(QFont("Arial", 20, QFont.Bold))
        main_layout.addWidget(header_label)
        
        # Widget de abas
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Adiciona a aba da ferramenta RPA
        self.rpa_widget = PerdasDuplasWidget()
        self.tab_widget.addTab(self.rpa_widget, "🤖 Perdas Duplas ETL")

# ===============================================================
# EXECUÇÃO (APENAS PARA TESTE - REMOVA NO SEU APP PRINCIPAL)
# ===============================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    
    # Para teste individual
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())