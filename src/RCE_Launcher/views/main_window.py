# src/RCE_Launcher/views/main_window.py

from PySide6.QtWidgets import (
    QMainWindow, QHBoxLayout, QWidget, QFrame, QVBoxLayout, QPushButton, QTabWidget
)
from PySide6.QtCore import Slot, QPropertyAnimation, QEasingCurve

from .navigation_menu import NavigationMenu

class LauncherWindow(QMainWindow):
    """
    View - A janela principal (e contêiner) da aplicação.
    Não contém lógica de negócio, apenas a estrutura da UI.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RCE Framework Launcher - Arquitetura MVC")
        self.resize(1400, 800)

        # --- Estrutura Principal ---
        central_widget = QWidget()
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setCentralWidget(central_widget)

        # --- Menu Lateral ---
        self.left_menu = QFrame()
        self.left_menu.setFixedWidth(240)
        self.left_menu.setStyleSheet("background-color: #1a1a1a;")
        left_menu_layout = QVBoxLayout(self.left_menu)
        left_menu_layout.setContentsMargins(0, 0, 0, 0)

        self.toggle_button = QPushButton("☰")
        self.toggle_button.setFixedSize(40, 40)
        self.toggle_button.clicked.connect(self.toggle_menu)

        self.nav_menu = NavigationMenu()

        left_menu_layout.addWidget(self.toggle_button)
        left_menu_layout.addWidget(self.nav_menu)
        self.main_layout.addWidget(self.left_menu)

        # --- Área de Abas (Tabs) ---
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.main_layout.addWidget(self.tabs)

    def add_tab(self, widget, name):
        """Adiciona uma nova aba e retorna o índice."""
        return self.tabs.addTab(widget, name)

    def set_current_tab(self, widget):
        """Foca em uma aba já existente."""
        self.tabs.setCurrentWidget(widget)

    def close_tab(self, index):
        """Fecha a aba no índice especificado."""
        self.tabs.removeTab(index)

    @Slot()
    def toggle_menu(self):
        """Animação para mostrar/esconder o menu lateral."""
        width = self.left_menu.width()
        target_width = 0 if width > 0 else 240

        self.animation = QPropertyAnimation(self.left_menu, b"minimumWidth")
        self.animation.setDuration(300)
        self.animation.setStartValue(width)
        self.animation.setEndValue(target_width)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.start()

        self.animation2 = QPropertyAnimation(self.left_menu, b"maximumWidth")
        self.animation2.setDuration(300)
        self.animation2.setStartValue(width)
        self.animation2.setEndValue(target_width)
        self.animation2.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation2.start()
