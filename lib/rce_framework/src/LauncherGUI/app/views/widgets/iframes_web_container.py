import sys
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                               QWidget, QFrame, QLabel, QPushButton, QScrollArea, QSplitter)
from PySide6.QtWebEngineWidgets import QWebEngineView

class WebContainerWidget(QFrame):
    """
    Container personalizado com cor opcional, texto no centro e ícone ao lado.
    Oferece opção de carregar no Iframe (clique) ou abrir no navegador (botão).
    """
    url_selected = Signal(str)  # Sinal emitido ao clicar no container

    def __init__(self, title, url, color="#ffffff", icon="🔗", parent=None):
        super().__init__(parent)
        self.url = url
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(80)
        
        # Estilização do Container
        self.setStyleSheet(f"""
            WebContainerWidget {{
                background-color: {color};
                border-radius: 10px;
                border: 1px solid #ccc;
            }}
            WebContainerWidget:hover {{
                border: 2px solid #007bff;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        # Ícone (Lado Esquerdo)
        self.icon_label = QLabel(icon)
        self.icon_label.setStyleSheet("font-size: 24px; border: none; background: transparent;")
        layout.addWidget(self.icon_label)

        # Texto (Centro)
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; border: none; background: transparent; color: #333;")
        layout.addWidget(self.title_label, 1) # Stretch factor 1 para centralizar

        # Botão TextButton para abrir no navegador (Lado Direito)
        self.open_btn = QPushButton("Abrir ↗")
        self.open_btn.setCursor(Qt.PointingHandCursor)
        self.open_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.open_btn.clicked.connect(self._open_external)
        layout.addWidget(self.open_btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.url_selected.emit(self.url)
        super().mousePressEvent(event)

    def _open_external(self):
        QDesktopServices.openUrl(QUrl(self.url))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gerenciador de Links e Iframes")
        self.resize(1200, 800)

        # Widget Central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Splitter para dividir a lista de containers e o iframe
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # --- Área Esquerda: Lista de Containers ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(350)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #f5f5f5; }")

        container_content = QWidget()
        self.container_layout = QVBoxLayout(container_content)
        self.container_layout.setAlignment(Qt.AlignTop)
        self.container_layout.setSpacing(10)
        self.container_layout.setContentsMargins(10, 10, 10, 10)
        
        scroll_area.setWidget(container_content)
        splitter.addWidget(scroll_area)

        # --- Área Direita: Iframe (QWebEngineView) ---
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("about:blank"))
        self.browser.setHtml("<html><body style='display:flex;justify-content:center;align-items:center;font-family:sans-serif;color:#666;background-color:#fff;'><h2>Selecione um link à esquerda para visualizar</h2></body></html>")
        
        splitter.addWidget(self.browser)
        splitter.setStretchFactor(1, 1) # Dá prioridade de espaço ao browser

        # --- Adicionando Dados de Exemplo ---
        self.urls_data = [
            {"title": "Wikipedia", "url": "https://www.wikipedia.org", "color": "#ffffff", "icon": "📚"},
            {"title": "Google", "url": "https://www.google.com", "color": "#e8f0fe", "icon": "🔍"},
            {"title": "Python Docs", "url": "https://docs.python.org", "color": "#fff3cd", "icon": "🐍"},
            {"title": "Qt Framework", "url": "https://www.qt.io", "color": "#d1ecf1", "icon": "⚙️"},
            {"title": "GitHub", "url": "https://github.com", "color": "#f0f0f0", "icon": "🐙"},
        ]

        self.load_containers()

    def load_containers(self):
        for item in self.urls_data:
            widget = WebContainerWidget(
                title=item["title"],
                url=item["url"],
                color=item["color"],
                icon=item["icon"]
            )
            widget.url_selected.connect(self.load_url_in_iframe)
            self.container_layout.addWidget(widget)

    def load_url_in_iframe(self, url):
        self.browser.setUrl(QUrl(url))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
