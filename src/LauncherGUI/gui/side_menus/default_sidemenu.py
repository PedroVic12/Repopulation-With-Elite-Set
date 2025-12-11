from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class DefaultSideMenu(QWidget):
    def __init__(self):
        super().__init__()
        
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)
        
        self.label = QLabel("Menu de Contexto")
        self.label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.layout.addWidget(self.label)
