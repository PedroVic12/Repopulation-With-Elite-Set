import sys
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QColor
from pathlib import Path

class LoadingWidget(QWidget):
    def __init__(self, duration_ms = 3000):
        super().__init__()
        self.setWindowTitle("RCE Framework Loader")
        # Aumentando a tela para 1000x600 para um visual mais imersivo
        self.setFixedSize(1000, 600) 
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Container Principal com QSS Premium (Dark Mode/Blue Accent)
        self.container = QWidget()
        self.container.setObjectName("MainContainer")
        self.container.setStyleSheet("""
            #MainContainer {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, 
                                    stop:0 rgba(33, 37, 43, 255), stop:1 rgba(45, 52, 63, 255));
                border-radius: 30px;
                border: 1px solid rgba(25, 118, 210, 80);
            }
            QLabel { color: #E0E0E0; font-family: 'Segoe UI', 'Roboto', sans-serif; }
        """)
        
        # Efeito de Sombra
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(self.container)
        container_layout.setAlignment(Qt.AlignCenter)
        container_layout.setSpacing(20)
        
        # Logo com reflexo simples
        logo_path = Path(__file__).parent / "src" / "assets" / "IconRCELancher.png"
        if logo_path.exists():
            logo_label = QLabel()
            pixmap = QPixmap(str(logo_path))
            logo_label.setPixmap(pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            container_layout.addWidget(logo_label, 0, Qt.AlignCenter)
        
        # Título com Gradiente simulado via QSS
        self.title = QLabel("RCE FRAMEWORK")
        self.title.setStyleSheet("font-size: 42px; font-weight: 900; color: #1976D2; letter-spacing: 5px;")
        container_layout.addWidget(self.title, 0, Qt.AlignCenter)
        
        # Status Text
        self.loading_text = QLabel("INICIALIZANDO O SISTEMA...")
        self.loading_text.setStyleSheet("font-size: 14px; color: #888; font-weight: bold;")
        container_layout.addWidget(self.loading_text, 0, Qt.AlignCenter)
        
        # Barra de Progresso Customizada (Simulada com Label)
        self.bar_bg = QWidget()
        self.bar_bg.setFixedSize(600, 4)
        self.bar_bg.setStyleSheet("background: rgba(255,255,255,0.1); border-radius: 2px;")
        container_layout.addWidget(self.bar_bg, 0, Qt.AlignCenter)
        
        self.bar_fg = QWidget(self.bar_bg)
        self.bar_fg.setFixedHeight(4)
        self.bar_fg.setStyleSheet("background: #1976D2; border-radius: 2px;")
        
        layout.addWidget(self.container)

        # Animação da Barra
        self.anim = QPropertyAnimation(self.bar_fg, b"geometry")
        self.anim.setDuration(duration_ms)
        self.anim.setStartValue(self.bar_bg.rect().adjusted(0,0,-600,0))
        self.anim.setEndValue(self.bar_bg.rect())
        self.anim.setEasingCurve(QEasingCurve.InOutQuart)
        self.anim.start()

        # Timer para fechar
        QTimer.singleShot(duration_ms, self.close)
        self.center_on_screen()

    def center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.center() - self.rect().center())

def show_loading_screen(duration_ms):
    app = QApplication(sys.argv)
    loading_widget = LoadingWidget(duration_ms)
    loading_widget.show()
    app.exec() # Roda até o .close() ser chamado pelo Timer

# Rodando em 5 segundos de duração
# show_loading_screen(5000) 
