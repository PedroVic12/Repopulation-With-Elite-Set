import sys
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from pathlib import Path

class LoadingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Carregando RCE Framework")
        self.setFixedSize(500, 400)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Container com fundo
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 15px;
                border: 2px solid #1976D2;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignCenter)
        container_layout.setSpacing(20)
        container_layout.setContentsMargins(30, 30, 30, 30)
        
        # Logo
        logo_path = Path(__file__).parent / "src" / "assets" / "IconRCELancher.png"
        if logo_path.exists():
            logo_label = QLabel()
            pixmap = QPixmap(str(logo_path))
            scaled_pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            container_layout.addWidget(logo_label)
        
        # Título
        title = QLabel("RCE Framework")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #1976D2;
        """)
        title.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(title)
        
        # Texto de loading
        self.loading_text = QLabel("Carregando aplicação...")
        self.loading_text.setStyleSheet("""
            font-size: 14px;
            color: #666;
        """)
        self.loading_text.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.loading_text)
        
        # Spinner animado
        self.spinner_label = QLabel("⬤ ⬤ ⬤")
        self.spinner_label.setStyleSheet("""
            font-size: 32px;
            color: #1976D2;
        """)
        self.spinner_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.spinner_label)
        
        # Adiciona container ao layout principal
        layout.addWidget(container)
        
        # Timer para animação do spinner
        self.spinner_timer = QTimer()
        self.spinner_timer.timeout.connect(self.animate_spinner)
        self.spinner_states = ["⬤", "⬤ ⬤", "⬤ ⬤ ⬤", "⬤ ⬤", "⬤"]
        self.spinner_index = 0
        self.spinner_timer.start(300)
        
        # Centralizar na tela
        self.center_on_screen()
    
    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def animate_spinner(self):
        self.spinner_label.setText(self.spinner_states[self.spinner_index])
        self.spinner_index = (self.spinner_index + 1) % len(self.spinner_states)
    
    def closeEvent(self, event):
        """Para o timer quando a janela for fechada"""
        self.spinner_timer.stop()
        super().closeEvent(event)