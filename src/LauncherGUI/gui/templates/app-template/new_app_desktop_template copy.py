#!/usr/bin/env python3
"""
App Template Desktop - Sistema Base Modular
Template reutilizável com arquitetura MVC e navegação por tabs

Autor: Pedro Victor Rodrigues Veras
Versão: 10.0.0
Arquitetura: MVC com componentes modulares
"""

import sys
import webbrowser
from functools import partial
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QTextEdit, QStackedWidget,
    QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QIcon

# ============================================================================
# STYLES - Importação dos estilos
# ============================================================================
APP_STYLES = """
QMainWindow { background-color: #1e1e2e; }
QWidget { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI'; font-size: 10pt; }
QPushButton { background-color: #313244; color: #cdd6f4; border: 2px solid #45475a; border-radius: 6px; padding: 8px 16px; }
QPushButton:hover { background-color: #45475a; border-color: #89b4fa; }
QPushButton:pressed { background-color: #585b70; }
QLabel { color: #cdd6f4; }
QTextEdit { background-color: #181825; color: #cdd6f4; border: 2px solid #45475a; border-radius: 4px; }
QFrame#sidebar { background-color: #181825; border-right: 2px solid #45475a; }
QFrame#topbar { background-color: #181825; border-bottom: 2px solid #45475a; }
QPushButton#nav_button { background-color: transparent; border: none; text-align: left; padding: 12px; }
QPushButton#nav_button:hover { background-color: #313244; border-left: 3px solid #89b4fa; }
QPushButton#nav_button_active { background-color: #313244; border-left: 3px solid #89b4fa; }
QTabWidget::pane { border: 2px solid #45475a; background-color: #1e1e2e; }
QTabBar::tab { background-color: #313244; color: #cdd6f4; border: 2px solid #45475a; padding: 8px 16px; }
QTabBar::tab:selected { background-color: #45475a; color: #89b4fa; }
"""

# ============================================================================
# MODELS - Gerenciamento de Estado
# ============================================================================
class SettingsModel:
    """Model para gerenciar configurações da aplicação"""
    
    def __init__(self):
        self.settings = {
            'theme': 'dark',
            'font_family': 'Segoe UI',
            'font_size': 10,
            'language': 'pt_BR'
        }
    
    def get(self, key):
        return self.settings.get(key)
    
    def set(self, key, value):
        self.settings[key] = value

# ============================================================================
# WIDGETS - Componentes Reutilizáveis
# ============================================================================
class NavigationButton(QPushButton):
    """Botão de navegação customizado"""
    
    def __init__(self, icon, text, parent=None):
        super().__init__(f"{icon}  {text}", parent)
        self.setObjectName("nav_button")
        self.setMinimumHeight(45)
        self.setCursor(Qt.PointingHandCursor)


class TopBar(QFrame):
    """Barra superior com título e links rápidos"""
    
    def __init__(self, title="App Template", parent=None):
        super().__init__(parent)
        self.setObjectName("topbar")
        self.setFixedHeight(60)
        
        layout = QHBoxLayout(self)
        
        # Título
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Links rápidos
        links = {
            "🌐 GitHub": "https://github.com/PedroVic12",
            "📚 Docs": "https://doc.qt.io/qtforpython-6/",
        }
        
        for text, url in links.items():
            btn = QPushButton(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(partial(webbrowser.open, url))
            layout.addWidget(btn)


class SideMenu(QFrame):
    """Menu lateral de navegação"""
    
    dashboard_requested = Signal()
    settings_requested = Signal()
    about_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(240)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 10, 0, 10)
        
        # Logo/Header
        header = QLabel("⚡ APP TEMPLATE")
        header.setFont(QFont("Segoe UI", 12, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("padding: 20px; color: #89b4fa;")
        layout.addWidget(header)
        
        # Botões de navegação
        self.nav_buttons = {}
        
        self.btn_dashboard = NavigationButton("📊", "Dashboard")
        self.btn_dashboard.clicked.connect(self.dashboard_requested.emit)
        layout.addWidget(self.btn_dashboard)
        self.nav_buttons['Dashboard'] = self.btn_dashboard
        
        self.btn_settings = NavigationButton("⚙️", "Configurações")
        self.btn_settings.clicked.connect(self.settings_requested.emit)
        layout.addWidget(self.btn_settings)
        self.nav_buttons['Configurações'] = self.btn_settings
        
        self.btn_about = NavigationButton("ℹ️", "Sobre")
        self.btn_about.clicked.connect(self.about_requested.emit)
        layout.addWidget(self.btn_about)
        self.nav_buttons['Sobre'] = self.btn_about
        
        layout.addStretch()
        
        # Footer
        footer = QLabel("v10.0.0")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #6c7086; padding: 10px;")
        layout.addWidget(footer)
    
    def set_active_button(self, name):
        """Marca botão como ativo"""
        for btn_name, btn in self.nav_buttons.items():
            if btn_name == name:
                btn.setObjectName("nav_button_active")
            else:
                btn.setObjectName("nav_button")
            btn.style().unpolish(btn)
            btn.style().polish(btn)


# ============================================================================
# PAGES - Páginas/Telas do Aplicativo
# ============================================================================
class DashboardWidget(QWidget):
    """Página Dashboard"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        title = QLabel("📊 Dashboard Principal")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        layout.addWidget(title)
        
        content = QTextEdit()
        content.setPlaceholderText("Área principal do dashboard...")
        content.setReadOnly(True)
        layout.addWidget(content)


class SettingsWidget(QWidget):
    """Página de Configurações"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        title = QLabel("⚙️ Configurações")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        layout.addWidget(title)
        
        content = QTextEdit()
        content.setPlaceholderText("Configurações da aplicação...")
        content.setReadOnly(True)
        layout.addWidget(content)


class AboutWidget(QWidget):
    """Página Sobre"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        title = QLabel("ℹ️ Sobre")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        layout.addWidget(title)
        
        about_text = """
        <h2>App Template Desktop</h2>
        <p><b>Versão:</b> 10.0.0</p>
        <p><b>Autor:</b> Pedro Victor Rodrigues Veras</p>
        <p><b>Tecnologias:</b> Python, PySide6, Qt</p>
        <br>
        <p>Template modular para desenvolvimento de aplicações desktop.</p>
        <p>Arquitetura MVC com componentes reutilizáveis.</p>
        """
        
        content = QTextEdit()
        content.setHtml(about_text)
        content.setReadOnly(True)
        layout.addWidget(content)


# ============================================================================
# MAIN WINDOW - Janela Principal
# ============================================================================
class MainWindow(QMainWindow):
    """Janela principal da aplicação"""
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWindowTitle("App Template Desktop")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet(APP_STYLES)
        
        # Estado
        self.open_tabs = {}
        self.settings_model = SettingsModel()
        
        self.init_ui()
        self.open_dashboard_tab()
        self.show()
    
    def init_ui(self):
        """Inicializa interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top Bar
        self.top_bar = TopBar("⚡ App Template Desktop")
        main_layout.addWidget(self.top_bar)
        
        # Área principal
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Menu lateral
        self.side_menu = SideMenu()
        self.side_menu.dashboard_requested.connect(self.open_dashboard_tab)
        self.side_menu.settings_requested.connect(self.open_settings_tab)
        self.side_menu.about_requested.connect(self.open_about_tab)
        content_layout.addWidget(self.side_menu)
        
        # Área de tabs
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        content_layout.addWidget(self.tabs)
        
        main_layout.addLayout(content_layout)
    
    # ========== Gerenciamento de Tabs ==========
    def open_or_focus_tab(self, tab_name, widget_class):
        """Abre ou foca em uma tab existente"""
        if tab_name in self.open_tabs:
            self.tabs.setCurrentWidget(self.open_tabs[tab_name])
        else:
            widget = widget_class()
            index = self.tabs.addTab(widget, tab_name)
            self.tabs.setCurrentIndex(index)
            self.open_tabs[tab_name] = widget
        
        self.side_menu.set_active_button(tab_name)
    
    @Slot(int)
    def on_tab_changed(self, index):
        """Atualiza botão ativo quando tab muda"""
        if index >= 0:
            tab_name = self.tabs.tabText(index)
            self.side_menu.set_active_button(tab_name)
    
    @Slot(int)
    def close_tab(self, index):
        """Fecha uma tab"""
        widget = self.tabs.widget(index)
        if widget:
            tab_name = self.tabs.tabText(index)
            if tab_name in self.open_tabs:
                del self.open_tabs[tab_name]
            widget.deleteLater()
            self.tabs.removeTab(index)
    
    # ========== Navegação ==========
    def open_dashboard_tab(self):
        self.open_or_focus_tab("Dashboard", DashboardWidget)
    
    def open_settings_tab(self):
        self.open_or_focus_tab("Configurações", SettingsWidget)
    
    def open_about_tab(self):
        self.open_or_focus_tab("Sobre", AboutWidget)


# ============================================================================
# MAIN - Ponto de Entrada
# ============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))
    
    window = MainWindow(app)
    
    sys.exit(app.exec())