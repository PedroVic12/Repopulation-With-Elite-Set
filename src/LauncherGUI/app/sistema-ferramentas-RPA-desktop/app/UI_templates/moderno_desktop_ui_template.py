# -*- coding: utf-8 -*-
"""
main.py

Template de Aplicação Desktop Moderna com PySide6.
Baseado em 'moderno_desktop_ui_template.py', mas refatorado para
um MVC mais limpo, onde cada item da árvore abre uma aba (IFrame)
modular contendo componentes com "glassmorphism".

Funcionalidades:
- Arquitetura MVC (Model-View-Controller).
- Menu lateral em árvore, expansível e recolhível com animação.
- Painel central com Abas (QTabWidget).
- "IFrames" modulares (QWidget) para o conteúdo de cada aba.
- Componentes reutilizáveis (GlassCard, CarouselWidget) com efeito glassmorphism.
- Estilos QSS para modo Dark e Light.
- Código limpo, POO, em um único arquivo.
"""
from __future__ import annotations
import sys
from typing import List, Optional, Dict, Any

from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal, QObject,
    Property, QSize, QPoint, Slot
)
from PySide6.QtGui import QFont, QColor, QAction, QIcon, QPainter
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QTreeWidget, QTreeWidgetItem, QTabWidget, QTextBrowser,
    QInputDialog, QFrame, QStackedWidget, QSizePolicy, QGridLayout, QToolBar,
    QGraphicsDropShadowEffect, QStyle, QToolButton, QComboBox
)

try:
    # QWebEngineView é o "IFrame" real mais próximo
    from PySide6.QtWebEngineWidgets import QWebEngineView
    WEB_AVAILABLE = True
except ImportError:
    QWebEngineView = None  # type: ignore
    WEB_AVAILABLE = False


# ==============================================================================
# 1. ESTILOS QSS (DARK E LIGHT)
# ==============================================================================
# (Estilos mantidos do 'moderno_desktop_ui_template.py')

DARK_STYLE = """
QWidget {
    background-color: #1a1a1a;
    color: #f0f0f0;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 10pt;
}
QToolBar {
    background-color: #2c2c2c;
    border: none;
    padding: 5px;
}
QToolBar QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 8px;
}
QToolBar QToolButton:hover {
    background-color: #3a3a3a;
}
QToolBar QToolButton:pressed {
    background-color: #4a4a4a;
}
/* Estilo do 'splitter' ou 'handle' */
QSplitter::handle {
    background-color: #2c2c2c;
}
QSplitter::handle:hover {
    background-color: #3a3a3a;
}
/* Menu Lateral */
#Sidebar {
    background-color: #2c2c2c;
    border: none;
}
QTreeWidget {
    background-color: #2c2c2c;
    color: #f0f0f0;
    border: none;
    font-size: 11pt;
    padding-top: 10px;
}
QTreeWidget::item {
    padding: 10px 15px;
    border-radius: 5px;
}
QTreeWidget::item:hover {
    background-color: #3a3a3a;
}
QTreeWidget::item:selected {
    background-color: #0078d4;
    color: white;
}
QHeaderView::section {
    background-color: #2c2c2c;
    border: none;
}
/* Painel de Abas */
QTabWidget::pane {
    border: none;
    background-color: #1a1a1a;
}
QTabBar::tab {
    background-color: #2c2c2c;
    color: #f0f0f0;
    border: none;
    padding: 10px 15px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #0078d4;
    color: white;
}
QTabBar::tab:!selected {
    background-color: #3a3a3a;
}
QTabBar::tab:hover {
    background-color: #4a4a4a;
}
QTabBar::close-button {
    image: url(icons:light/close.png); /* ícone de fechar */
}
QTabBar::close-button:hover {
    background-color: #7a7a7a;
}
/* Componentes Glassmorphism */
#GlassCard {
    background-color: rgba(44, 44, 44, 0.7); /* Cor base escura com transparência */
    border: 1px solid rgba(255, 255, 255, 0.1); /* Borda sutil */
    border-radius: 12px;
}
QLabel#GlassTitle {
    font-size: 16pt;
    font-weight: 600;
    color: white;
    background-color: transparent;
}
QLabel#GlassSubtitle {
    font-size: 10pt;
    color: #d0d0d0;
    background-color: transparent;
}
/* Estilo para as Páginas de IFrame */
#IFramePage {
    background-color: #1a1a1a;
    padding: 20px;
}
QLabel#PageTitle {
    font-size: 20pt;
    font-weight: bold;
    color: white;
    padding-bottom: 10px;
}
"""

LIGHT_STYLE = """
QWidget {
    background-color: #f0f0f0;
    color: #1a1a1a;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 10pt;
}
QToolBar {
    background-color: #ffffff;
    border-bottom: 1px solid #dcdcdc;
    padding: 5px;
}
QToolBar QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 8px;
}
QToolBar QToolButton:hover {
    background-color: #f0f0f0;
}
QToolBar QToolButton:pressed {
    background-color: #e0e0e0;
}
QSplitter::handle {
    background-color: #f0f0f0;
}
QSplitter::handle:hover {
    background-color: #e0e0e0;
}
#Sidebar {
    background-color: #ffffff;
    border: none;
    border-right: 1px solid #dcdcdc;
}
QTreeWidget {
    background-color: #ffffff;
    color: #1a1a1a;
    border: none;
    font-size: 11pt;
    padding-top: 10px;
}
QTreeWidget::item {
    padding: 10px 15px;
    border-radius: 5px;
}
QTreeWidget::item:hover {
    background-color: #f0f0f0;
}
QTreeWidget::item:selected {
    background-color: #0078d4;
    color: white;
}
QHeaderView::section {
    background-color: #ffffff;
    border: none;
}
QTabWidget::pane {
    border: none;
    background-color: #f0f0f0;
}
QTabBar::tab {
    background-color: #ffffff;
    color: #1a1a1a;
    border: 1px solid #dcdcdc;
    border-bottom: none;
    padding: 10px 15px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #0078d4;
    color: white;
    border: 1px solid #0078d4;
    border-bottom: none;
}
QTabBar::tab:!selected {
    background-color: #e0e0e0;
}
QTabBar::tab:hover {
    background-color: #f0f0f0;
}
QTabBar::close-button {
    image: url(icons:dark/close.png);
}
QTabBar::close-button:hover {
    background-color: #c0c0c0;
}
/* Componentes Glassmorphism */
#GlassCard {
    background-color: rgba(255, 255, 255, 0.7); /* Cor base clara com transparência */
    border: 1px solid rgba(0, 0, 0, 0.1); /* Borda sutil */
    border-radius: 12px;
}
QLabel#GlassTitle {
    font-size: 16pt;
    font-weight: 600;
    color: #1a1a1a;
    background-color: transparent;
}
QLabel#GlassSubtitle {
    font-size: 10pt;
    color: #333333;
    background-color: transparent;
}
/* Estilo para as Páginas de IFrame */
#IFramePage {
    background-color: #f0f0f0;
    padding: 20px;
}
QLabel#PageTitle {
    font-size: 20pt;
    font-weight: bold;
    color: #1a1a1a;
    padding-bottom: 10px;
}
"""

# ==============================================================================
# 2. COMPONENTES REUTILIZÁVEIS (POO)
# ==============================================================================

class GlassCard(QFrame):
    """
    Um widget de cartão reutilizável com efeito "glassmorphism".
    Extraído de 'glass_carousel_app.py'.
    """
    def __init__(self, title: str, subtitle: str = "",
                 width: int = 260, height: int = 140, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassCard")
        self.setFixedSize(width, height)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignmentFlag.AlignBottom)

        self.lbl_title = QLabel(title, objectName="GlassTitle")
        self.lbl_subtitle = QLabel(subtitle, objectName="GlassSubtitle")

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_subtitle)

        # Sombra
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)


class CarouselWidget(QFrame):
    """
    Um widget de carrossel simples.
    Extraído de 'glass_carousel_app.py'.
    """
    def __init__(self, autoplay: bool = True, interval_ms: int = 5000, parent=None):
        super().__init__(parent)
        self.pages: List[QWidget] = []

        layout = QStackedWidget(self)
        self.stack = layout
        self.current_index = 0

        if autoplay:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.next)
            self.timer.start(interval_ms)

    def add_page(self, widget: QWidget):
        self.stack.addWidget(widget)
        self.pages.append(widget)

    def next(self):
        count = self.stack.count()
        if count == 0:
            return
        self.current_index = (self.current_index + 1) % count
        self.stack.setCurrentIndex(self.current_index)

    def prev(self):
        count = self.stack.count()
        if count == 0:
            return
        self.current_index = (self.current_index - 1) % count
        self.stack.setCurrentIndex(self.current_index)


# ==============================================================================
# 3. PÁGINAS "IFRAME" MODULARES (Conteúdo das Abas)
# ==============================================================================

class BasePage(QWidget):
    """Página base para todas as abas, define o fundo e o layout."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("IFramePage") # Para aplicar o padding do QSS
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0) # QSS cuida do padding
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)


class DashboardPage(BasePage):
    """Página 'IFrame' de Dashboard, com cards e carrossel."""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout.addWidget(QLabel("Dashboard Principal", objectName="PageTitle"))
        
        # Layout de Cards em Grid
        grid = QGridLayout()
        grid.setSpacing(20)
        
        grid.addWidget(GlassCard("Análises MUST", "15 Abertas"), 0, 0)
        grid.addWidget(GlassCard("Atividades SP", "3 Em Andamento"), 0, 1)
        grid.addWidget(GlassCard("Relatórios", "7 Gerados"), 0, 2)
        grid.addWidget(GlassCard("Contingências", "0 Novas"), 1, 0)
        
        self.layout.addLayout(grid)
        
        # Carrossel
        self.layout.addWidget(QLabel("Atualizações Recentes", objectName="PageTitle"))
        carousel = CarouselWidget(autoplay=True, interval_ms=3000)
        carousel.setMinimumHeight(200)

        # Páginas do Carrossel (podem ser QWidgets customizados)
        page1 = GlassCard("Palkia ETL", "Executado há 5 minutos", width=300, height=180)
        page2 = GlassCard("Deck Builder", "Análise #1234 Aprovada", width=300, height=180)
        page3 = GlassCard("Agendamento", "Otimização Concluída", width=300, height=180)

        carousel.add_page(page1)
        carousel.add_page(page2)
        carousel.add_page(page3)
        
        self.layout.addWidget(carousel)
        self.layout.addStretch()


class AnalisePage(BasePage):
    """Página 'IFrame' de Análise."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout.addWidget(QLabel("Análise de Contingência", objectName="PageTitle"))
        self.layout.addWidget(GlassCard("Deck Builder", "Pronto para simulação", height=180))
        self.layout.addStretch()

class SettingsPage(BasePage):
    """Página 'IFrame' de Configurações."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout.addWidget(QLabel("Configurações", objectName="PageTitle"))
        
        card = QFrame(objectName="GlassCard") # Um card para agrupar
        card_layout = QVBoxLayout(card)
        card_layout.addWidget(QLabel("Tema do Aplicativo", objectName="GlassTitle"))
        
        self.combo = QComboBox()
        self.combo.addItem("Escuro (Dark)", "dark")
        self.combo.addItem("Claro (Light)", "light")
        card_layout.addWidget(self.combo)
        
        self.layout.addWidget(card)
        self.layout.addStretch()
        
        # Conexão interna temporária (o Controller fará a principal)
        # self.combo.currentTextChanged.connect(lambda: print(self.combo.currentData()))


class PlaceholderPage(BasePage):
    """Página 'IFrame' genérica para itens não implementados."""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.layout.addWidget(QLabel(title, objectName="PageTitle"))
        self.layout.addWidget(QLabel("Este módulo está em desenvolvimento."))
        self.layout.addStretch()


# ==============================================================================
# 4. ARQUITETURA MVC
# ==============================================================================

# --- 4.1. MODEL ---
class AppModel(QObject):
    """
    Armazena o estado da aplicação.
    """
    # Sinal emitido quando a lista de abas abertas muda
    pages_changed = Signal()
    # Sinal emitido quando o estado da sidebar muda
    sidebar_state_changed = Signal(bool)
    # Sinal emitido quando o tema muda
    theme_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Lista de dicionários, cada um representando uma aba aberta
        # Ex: {"key": "dashboard", "title": "Dashboard"}
        self._open_pages: List[Dict[str, str]] = []
        self._sidebar_is_expanded = True
        self._current_theme = "dark" # Padrão
    
    # --- Gerenciamento de Abas ---
    
    def get_open_pages(self) -> List[Dict[str, str]]:
        return self._open_pages
    
    def get_page_index(self, key: str) -> int:
        """Retorna o índice da aba com a chave 'key', ou -1 se não existir."""
        for i, page in enumerate(self._open_pages):
            if page["key"] == key:
                return i
        return -1

    def add_page(self, key: str, title: str):
        """Adiciona uma nova aba ao modelo, se ela já não existir."""
        if self.get_page_index(key) != -1:
            # Página já existe
            return
        
        self._open_pages.append({"key": key, "title": title})
        self.pages_changed.emit()

    def remove_page(self, index: int):
        """Remove uma aba do modelo pelo seu índice."""
        if 0 <= index < len(self._open_pages):
            del self._open_pages[index]
            self.pages_changed.emit()

    # --- Gerenciamento da Sidebar ---
    
    @property
    def sidebar_is_expanded(self) -> bool:
        return self._sidebar_is_expanded
    
    def toggle_sidebar(self):
        """Inverte o estado da sidebar."""
        self._sidebar_is_expanded = not self._sidebar_is_expanded
        self.sidebar_state_changed.emit(self._sidebar_is_expanded)
        
    # --- Gerenciamento de Tema ---
    
    @property
    def theme(self) -> str:
        return self._current_theme

    def set_theme(self, theme_name: str):
        """Define o tema (dark/light)."""
        if theme_name in ("dark", "light") and theme_name != self._current_theme:
            self._current_theme = theme_name
            self.theme_changed.emit(theme_name)


# --- 4.2. VIEW (MainWindow) ---
class MainView(QMainWindow):
    """
    A Janela Principal (View). Constrói a UI e emite sinais.
    Não contém lógica de aplicação.
    """
    # Sinais que a View emite para o Controller
    toggle_sidebar_requested = Signal()
    tree_item_activated = Signal(str, str) # key, title
    close_tab_requested = Signal(int)
    theme_change_requested = Signal(str)

    def __init__(self, model: AppModel):
        super().__init__()
        self.setWindowTitle("Sistema de Controle e Gestão - ONS 2025")
        self.resize(1400, 900)
        self.model = model # View pode ler o estado inicial do modelo

        self._setup_ui()
        self._setup_icons() # Carrega ícones
        self._connect_internal_signals() # Conecta sinais da UI

    def _setup_ui(self):
        """Constrói a interface principal."""
        
        # --- Toolbar Superior ---
        self.toolbar = QToolBar("Barra de Ferramentas")
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        
        # Botão de Toggle da Sidebar
        self.sidebar_toggle_btn = QToolButton()
        self.sidebar_toggle_btn.setText("Menu")
        self.toolbar.addWidget(self.sidebar_toggle_btn)
        
        # Espaçador
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer)
        
        # Botão de Tema
        self.theme_toggle_btn = QToolButton()
        self.theme_toggle_btn.setText("Tema")
        self.toolbar.addWidget(self.theme_toggle_btn)

        # --- Layout Principal (Sidebar + Abas) ---
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Sidebar (Container com Animação) ---
        self.sidebar_container = QWidget(objectName="Sidebar")
        self.sidebar_container.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(self.sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Árvore de Navegação
        self.tree_menu = QTreeWidget()
        self.tree_menu.setHeaderHidden(True)
        self._populate_tree() # Preenche a árvore
        sidebar_layout.addWidget(self.tree_menu)
        
        # Animação da Sidebar
        self.sidebar_anim = QPropertyAnimation(self.sidebar_container, b"minimumWidth")
        self.sidebar_anim.setDuration(250)
        self.sidebar_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        main_layout.addWidget(self.sidebar_container)

        # --- Painel de Abas Central ---
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        main_layout.addWidget(self.tabs, 1) # '1' faz expandir

    def _setup_icons(self):
        """Carrega ícones (usando ícones padrão do Qt como fallback)."""
        # (Idealmente, você usaria QIcon.fromTheme ou arquivos de recurso)
        menu_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DockWidgetCloseButton)
        self.sidebar_toggle_btn.setIcon(menu_icon)
        
        theme_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon)
        self.theme_toggle_btn.setIcon(theme_icon)

    def _populate_tree(self):
        """Preenche o menu em árvore."""
        self.tree_menu.clear()

        cat_dash = QTreeWidgetItem(self.tree_menu, ["Dashboards"])
        item_dash = QTreeWidgetItem(cat_dash, ["Dashboard Principal"])
        item_dash.setData(0, Qt.ItemDataRole.UserRole, "dashboard") # key

        cat_analise = QTreeWidgetItem(self.tree_menu, ["Análise"])
        item_deck = QTreeWidgetItem(cat_analise, ["Deck Builder"])
        item_deck.setData(0, Qt.ItemDataRole.UserRole, "analise_deck")
        item_agend = QTreeWidgetItem(cat_analise, ["Agendamento Ótimo"])
        item_agend.setData(0, Qt.ItemDataRole.UserRole, "analise_agend")
        
        cat_ferramentas = QTreeWidgetItem(self.tree_menu, ["Ferramentas"])
        item_palkia = QTreeWidgetItem(cat_ferramentas, ["Palkia ETL"])
        item_palkia.setData(0, Qt.ItemDataRole.UserRole, "tool_palkia")

        cat_sistema = QTreeWidgetItem(self.tree_menu, ["Sistema"])
        item_config = QTreeWidgetItem(cat_sistema, ["Configurações"])
        item_config.setData(0, Qt.ItemDataRole.UserRole, "config")
        
        self.tree_menu.expandAll()

    def _connect_internal_signals(self):
        """Conecta os widgets da UI aos sinais da View."""
        self.sidebar_toggle_btn.clicked.connect(self.toggle_sidebar_requested)
        self.theme_toggle_btn.clicked.connect(
            lambda: self.theme_change_requested.emit(
                "light" if self.model.theme == "dark" else "dark"
            )
        )
        self.tree_menu.itemActivated.connect(self._on_tree_item_activated)
        self.tabs.tabCloseRequested.connect(self.close_tab_requested)

    @Slot(QTreeWidgetItem, int)
    def _on_tree_item_activated(self, item: QTreeWidgetItem, column: int):
        """Slot interno que lê o item e emite o sinal padronizado."""
        key = item.data(0, Qt.ItemDataRole.UserRole) # Pega a 'key'
        title = item.text(0) # Pega o Título
        if key:
            self.tree_item_activated.emit(key, title)

    # --- Slots Públicos (chamados pelo Controller) ---

    @Slot(str)
    def set_theme(self, theme_name: str):
        """Aplica o QSS do tema na aplicação."""
        style = DARK_STYLE if theme_name == "dark" else LIGHT_STYLE
        self.setStyleSheet(style)
        self.theme_toggle_btn.setText(theme_name.title())

    @Slot(bool)
    def update_sidebar_state(self, is_expanded: bool):
        """Inicia a animação para expandir ou recolher a sidebar."""
        self.sidebar_anim.stop()
        start_width = self.sidebar_container.width()
        end_width = 250 if is_expanded else 0
        
        if start_width == end_width: # Já no estado correto
            return
            
        self.sidebar_anim.setStartValue(start_width)
        self.sidebar_anim.setEndValue(end_width)
        
        # Oculta/mostra os filhos para evitar renderização estranha
        if is_expanded:
            self.sidebar_container.show()
            for child in self.sidebar_container.children():
                if isinstance(child, QWidget):
                    child.show()
        else:
            self.sidebar_anim.finished.connect(self._on_sidebar_collapse_finished)
            
        self.sidebar_anim.start()

    @Slot()
    def _on_sidebar_collapse_finished(self):
        """Chamado ao final da animação de recolher."""
        self.sidebar_anim.finished.disconnect(self._on_sidebar_collapse_finished)
        if self.sidebar_container.width() == 0:
            for child in self.sidebar_container.children():
                if isinstance(child, QWidget):
                    child.hide()

    @Slot(list)
    def update_tabs(self, open_pages: List[Dict[str, str]], factory_method):
        """
        Sincroniza o QTabWidget com a lista de abas do modelo.
        O 'factory_method' é fornecido pelo Controller para criar o widget.
        """
        # Mapeia as chaves de abas existentes
        current_tab_keys = [self.tabs.widget(i).property("page_key") for i in range(self.tabs.count())]
        
        # 1. Remove abas que não estão mais no modelo
        for i in reversed(range(self.tabs.count())):
            key = self.tabs.widget(i).property("page_key")
            if not any(p["key"] == key for p in open_pages):
                widget = self.tabs.widget(i)
                self.tabs.removeTab(i)
                widget.deleteLater() # Limpa memória

        # 2. Adiciona abas que estão no modelo mas não na UI
        for page in open_pages:
            key = page["key"]
            if key not in current_tab_keys:
                # Aba precisa ser criada
                widget = factory_method(key) # Controller cria o widget
                if not widget: # Se a fábrica falhar
                    widget = PlaceholderPage(page["title"])
                
                widget.setProperty("page_key", key) # Armazena a chave no widget
                self.tabs.addTab(widget, page["title"])

    @Slot(int)
    def set_active_tab(self, index: int):
        """Define a aba ativa."""
        if 0 <= index < self.tabs.count():
            self.tabs.setCurrentIndex(index)


# --- 4.3. CONTROLLER ---
class AppController(QObject):
    """
    O "Cérebro" da aplicação. Conecta o Model e a View.
    """
    def __init__(self, model: AppModel, view: MainView, parent=None):
        super().__init__(parent)
        self.model = model
        self.view = view
        self.tab_widget_cache: Dict[str, QWidget] = {} # Cache para abas

        self._connect_signals()
        
        # Sincronização inicial
        self.view.set_theme(self.model.theme)
        self.view.update_sidebar_state(self.model.sidebar_is_expanded)
        self.sync_tabs_with_model()

    def _connect_signals(self):
        """Conecta todos os sinais MVC."""
        
        # View -> Controller (Ações do Usuário)
        self.view.toggle_sidebar_requested.connect(self.toggle_sidebar)
        self.view.tree_item_activated.connect(self.open_tab_from_tree)
        self.view.close_tab_requested.connect(self.close_tab)
        self.view.theme_change_requested.connect(self.set_theme)
        
        # Model -> Controller/View (Mudanças de Estado)
        self.model.pages_changed.connect(self.sync_tabs_with_model)
        self.model.sidebar_state_changed.connect(self.view.update_sidebar_state)
        self.model.theme_changed.connect(self.view.set_theme)

    # --- Slots para Sinais da View ---
    
    @Slot()
    def toggle_sidebar(self):
        """Chamado pelo clique no botão da view."""
        self.model.toggle_sidebar() # Atualiza o modelo

    @Slot(str, str)
    def open_tab_from_tree(self, key: str, title: str):
        """Chamado pelo clique na árvore da view."""
        self.model.add_page(key, title) # Atualiza o modelo
        # Foca na aba (seja ela nova ou existente)
        index = self.model.get_page_index(key)
        self.view.set_active_tab(index)

    @Slot(int)
    def close_tab(self, index: int):
        """Chamado pelo botão 'X' da aba na view."""
        self.model.remove_page(index) # Atualiza o modelo

    @Slot(str)
    def set_theme(self, theme_name: str):
        """Chamado pelo botão de tema na view."""
        self.model.set_theme(theme_name) # Atualiza o modelo

    # --- Lógica de Sincronização ---
    
    @Slot()
    def sync_tabs_with_model(self):
        """
        Slot chamado quando o Model.pages_changed é emitido.
        Sincroniza o QTabWidget da View com a lista de abas do Model.
        """
        open_pages = self.model.get_open_pages()
        
        # Passa o método da fábrica para a View
        self.view.update_tabs(open_pages, self.create_widget_for_key)

    def create_widget_for_key(self, key: str) -> QWidget:
        """
        Fábrica de "IFrames" (QWidget).
        Cria (ou busca do cache) o widget de conteúdo para uma aba.
        """
        if key in self.tab_widget_cache:
            # (Nota: Esta implementação simples de cache não recria a aba se fechada)
            # (Uma lógica mais robusta removeria do cache no 'close_tab')
            # Por enquanto, vamos recriar sempre, é mais simples e limpo.
            pass
            
        # Mapeamento de Chaves para Classes de Página
        if key == "dashboard":
            widget = DashboardPage()
        elif key == "analise_deck":
            widget = AnalisePage()
        elif key == "config":
            widget = SettingsPage()
            # Conecta o ComboBox de tema no SettingsPage ao Controller
            if isinstance(widget, SettingsPage):
                widget.combo.currentTextChanged.connect(
                    lambda: self.set_theme(widget.combo.currentData())
                )
                # Sincronza o combo com o modelo
                widget.combo.setCurrentIndex(
                    widget.combo.findData(self.model.theme)
                )
                # Conecta a mudança de tema do modelo de volta ao combo
                self.model.theme_changed.connect(
                    lambda theme: widget.combo.setCurrentIndex(widget.combo.findData(theme))
                )
        else:
            widget = PlaceholderPage(f"Módulo: {key}")

        # self.tab_widget_cache[key] = widget
        return widget


# ==============================================================================
# 5. PONTO DE ENTRADA (MAIN)
# ==============================================================================

def main():
    app = QApplication(sys.argv)
    
    # 1. Criar o Model
    model = AppModel()
    
    # 2. Criar a View
    view = MainView(model)
    
    # 3. Criar o Controller
    controller = AppController(model=model, view=view)
    
    # 4. Exibir a View
    view.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()