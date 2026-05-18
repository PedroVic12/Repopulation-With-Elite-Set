from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class DashboardWidget(QWidget):
    def __init__(self, side_menu=None):
        super().__init__()
        
        self.layout = QVBoxLayout(self)
        
        title = QLabel("Sistema de Ferramentas RPA - PLC - ONS")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        
        subtitle = QLabel("-")
        subtitle.setAlignment(Qt.AlignCenter)
        
        self.layout.addWidget(title)
        self.layout.addWidget(subtitle)
        self.layout.addStretch()
