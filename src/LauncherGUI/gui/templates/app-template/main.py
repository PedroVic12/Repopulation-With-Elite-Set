# main_app.py - Aplicação Principal com Tema Dinâmico
import sys
import os
import sqlite3
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QTextEdit, QStackedWidget,
    QFrame, QSizePolicy, QLineEdit, QCheckBox, QScrollArea,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QFont, QIcon, QPalette, QColor
from PySide6.QtCharts import QChart, QChartView, QPieSeries

# Importar estilos e database
from styles import DARK_STYLE, LIGHT_STYLE
from database import DatabaseManager

class TodoWidget(QWidget):
    """Widget de Lista de Tarefas"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.init_ui()
        self.load_todos()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("📝 Gerenciador de Tarefas")
        header.setFont(QFont("Segoe UI", 16, QFont.Bold))
        layout.addWidget(header)
        
        # Formulário de nova tarefa
        form_group = QGroupBox("Nova Tarefa")
        form_layout = QVBoxLayout(form_group)
        
        input_layout = QHBoxLayout()
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Título da tarefa...")
        input_layout.addWidget(self.title_input)
        
        self.add_btn = QPushButton("Adicionar")
        self.add_btn.clicked.connect(self.add_todo)
        input_layout.addWidget(self.add_btn)
        
        form_layout.addLayout(input_layout)
        layout.addWidget(form_group)
        
        # Lista de tarefas
        self.todos_scroll = QScrollArea()
        self.todos_widget = QWidget()
        self.todos_layout = QVBoxLayout(self.todos_widget)
        self.todos_scroll.setWidget(self.todos_widget)
        self.todos_scroll.setWidgetResizable(True)
        layout.addWidget(self.todos_scroll)
    
    def add_todo(self):
        title = self.title_input.text().strip()
        if title:
            self.db_manager.add_todo(title)
            self.title_input.clear()
            self.load_todos()
    
    def load_todos(self):
        # Limpar layout atual
        for i in reversed(range(self.todos_layout.count())):
            widget = self.todos_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Carregar tarefas
        todos = self.db_manager.get_todos(completed=False)
        
        if not todos:
            empty_label = QLabel("🎉 Nenhuma tarefa pendente!")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("padding: 20px; color: #6c7086;")
            self.todos_layout.addWidget(empty_label)
        else:
            for todo in todos:
                todo_widget = self.create_todo_item(todo)
                self.todos_layout.addWidget(todo_widget)
        
        self.todos_layout.addStretch()
    
    def create_todo_item(self, todo):
        widget = QFrame()
        widget.setFrameStyle(QFrame.Box)
        widget.setStyleSheet("""
            QFrame {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 10px;
                margin: 2px;
            }
        """)
        
        layout = QHBoxLayout(widget)
        
        # Checkbox
        checkbox = QCheckBox()
        checkbox.setChecked(False)
        checkbox.toggled.connect(lambda checked, tid=todo['id']: self.toggle_todo(tid, checked))
        layout.addWidget(checkbox)
        
        # Texto da tarefa
        text_layout = QVBoxLayout()
        title_label = QLabel(todo['title'])
        title_label.setStyleSheet("font-weight: bold;")
        text_layout.addWidget(title_label)
        
        if todo.get('description'):
            desc_label = QLabel(todo['description'])
            desc_label.setStyleSheet("color: #a6adc8; font-size: 9pt;")
            text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        # Botão deletar
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(30, 30)
        delete_btn.clicked.connect(lambda _, tid=todo['id']: self.delete_todo(tid))
        layout.addWidget(delete_btn)
        
        return widget
    
    def toggle_todo(self, todo_id, completed):
        self.db_manager.update_todo_status(todo_id, completed)
        QTimer.singleShot(500, self.load_todos)  # Recarregar após delay
    
    def delete_todo(self, todo_id):
        self.db_manager.delete_todo(todo_id)
        self.load_todos()

class DashboardWidget(QWidget):
    """Widget de Dashboard com Estatísticas"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.init_ui()
        self.load_stats()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("📊 Dashboard")
        header.setFont(QFont("Segoe UI", 16, QFont.Bold))
        layout.addWidget(header)
        
        # Grid de estatísticas
        self.stats_grid = QGridLayout()
        layout.addLayout(self.stats_grid)
        
        # Gráficos
        charts_layout = QHBoxLayout()
        
        # Gráfico de categorias
        self.categories_chart = QChartView()
        charts_layout.addWidget(self.categories_chart)
        
        # Gráfico de prioridades
        self.priorities_chart = QChartView()
        charts_layout.addWidget(self.priorities_chart)
        
        layout.addLayout(charts_layout)
    
    def load_stats(self):
        stats = self.db_manager.get_dashboard_stats()
        
        # Limpar grid
        for i in reversed(range(self.stats_grid.count())):
            self.stats_grid.itemAt(i).widget().deleteLater()
        
        # Cards de estatísticas
        cards = [
            ("Total de Tarefas", f"📋 {stats['total']}", "#89b4fa"),
            ("Concluídas", f"✅ {stats['completed']}", "#a6e3a1"),
            ("Pendentes", f"⏳ {stats['pending']}", "#f9e2af"),
            ("Taxa de Conclusão", f"📈 {stats['completion_rate']:.1f}%", "#cba6f7")
        ]
        
        for i, (title, value, color) in enumerate(cards):
            card = self.create_stat_card(title, value, color)
            self.stats_grid.addWidget(card, i // 2, i % 2)
        
        # Atualizar gráficos
        self.update_charts(stats)
    
    def create_stat_card(self, title, value, color):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color}20;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 15px;
            }}
            QLabel {{
                color: {color};
                background: transparent;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(value_label)
        
        return card
    
    def update_charts(self, stats):
        # Gráfico de categorias
        categories_series = QPieSeries()
        for category, count in stats['categories'].items():
            categories_series.append(f"{category} ({count})", count)
        
        categories_chart = QChart()
        categories_chart.addSeries(categories_series)
        categories_chart.setTitle("Tarefas por Categoria")
        categories_chart.setAnimationOptions(QChart.SeriesAnimations)
        self.categories_chart.setChart(categories_chart)
        
        # Gráfico de prioridades
        priorities_series = QPieSeries()
        priority_names = {1: "Baixa", 2: "Média", 3: "Alta"}
        for priority, count in stats['priorities'].items():
            priorities_series.append(f"{priority_names.get(priority, priority)} ({count})", count)
        
        priorities_chart = QChart()
        priorities_chart.addSeries(priorities_series)
        priorities_chart.setTitle("Tarefas por Prioridade")
        priorities_chart.setAnimationOptions(QChart.SeriesAnimations)
        self.priorities_chart.setChart(priorities_chart)

class MainWindow(QMainWindow):
    """Janela Principal com Tema Dinâmico"""
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.db_manager = DatabaseManager()
        self.current_theme = 'dark'
        
        self.setWindowTitle("Sistema Completo - Todo & Dashboard")
        self.setGeometry(100, 100, 1400, 900)
        
        self.init_ui()
        self.apply_theme(self.current_theme)
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top Bar
        self.top_bar = self.create_top_bar()
        main_layout.addWidget(self.top_bar)
        
        # Área principal
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Menu lateral
        self.side_menu = self.create_side_menu()
        content_layout.addWidget(self.side_menu)
        
        # Área de conteúdo
        self.content_stack = QStackedWidget()
        content_layout.addWidget(self.content_stack)
        
        main_layout.addLayout(content_layout)
        
        # Inicializar páginas
        self.init_pages()
    
    def create_top_bar(self):
        top_bar = QFrame()
        top_bar.setObjectName("topbar")
        top_bar.setFixedHeight(60)
        
        layout = QHBoxLayout(top_bar)
        
        # Título
        title_label = QLabel("⚡ Sistema Completo Desktop")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Botão de alternância de tema
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setObjectName("theme_toggle")
        self.theme_btn.setFixedSize(60, 30)
        self.theme_btn.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_btn)
        
        return top_bar
    
    def create_side_menu(self):
        side_menu = QFrame()
        side_menu.setObjectName("sidebar")
        side_menu.setFixedWidth(200)
        
        layout = QVBoxLayout(side_menu)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 10, 0, 10)
        
        # Logo
        header = QLabel("🚀 SISTEMA")
        header.setFont(QFont("Segoe UI", 12, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("padding: 20px; color: #89b4fa;")
        layout.addWidget(header)
        
        # Botões de navegação
        self.nav_buttons = {}
        
        nav_items = [
            ("📊 Dashboard", "dashboard"),
            ("📝 Todo List", "todo"),
            ("⚙️ Configurações", "settings"),
            ("ℹ️ Sobre", "about")
        ]
        
        for text, page_id in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("nav_button")
            btn.setMinimumHeight(45)
            btn.clicked.connect(lambda checked, pid=page_id: self.show_page(pid))
            layout.addWidget(btn)
            self.nav_buttons[page_id] = btn
        
        layout.addStretch()
        
        # Footer
        footer = QLabel("v2.0.0")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #6c7086; padding: 10px;")
        layout.addWidget(footer)
        
        return side_menu
    
    def init_pages(self):
        """Inicializa todas as páginas do sistema"""
        # Dashboard
        self.dashboard_page = DashboardWidget(self.db_manager)
        self.content_stack.addWidget(self.dashboard_page)
        
        # Todo List
        self.todo_page = TodoWidget(self.db_manager)
        self.content_stack.addWidget(self.todo_page)
        
        # Configurações
        self.settings_page = self.create_settings_page()
        self.content_stack.addWidget(self.settings_page)
        
        # Sobre
        self.about_page = self.create_about_page()
        self.content_stack.addWidget(self.about_page)
        
        # Mostrar dashboard inicialmente
        self.show_page('dashboard')
    
    def create_settings_page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("⚙️ Configurações")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Configurações de tema
        theme_group = QGroupBox("Aparência")
        theme_layout = QVBoxLayout(theme_group)
        
        theme_info = QLabel("Use o botão na barra superior para alternar entre tema claro e escuro.")
        theme_layout.addWidget(theme_info)
        
        layout.addWidget(theme_group)
        layout.addStretch()
        
        return widget
    
    def create_about_page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("ℹ️ Sobre o Sistema")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        layout.addWidget(title)
        
        about_text = """
        <h2>Sistema Completo Desktop</h2>
        <p><b>Versão:</b> 2.0.0</p>
        <p><b>Tecnologias:</b> Python, PySide6, SQLite3</p>
        <br>
        <h3>Funcionalidades:</h3>
        <ul>
            <li>✅ Gerenciamento de tarefas (Todo List)</li>
            <li>✅ Dashboard com estatísticas em tempo real</li>
            <li>✅ Tema claro/escuro dinâmico</li>
            <li>✅ Banco de dados SQLite integrado</li>
            <li>✅ Interface moderna e responsiva</li>
        </ul>
        """
        
        content = QTextEdit()
        content.setHtml(about_text)
        content.setReadOnly(True)
        layout.addWidget(content)
        
        return widget
    
    def show_page(self, page_id):
        """Mostra a página especificada"""
        page_index = {
            'dashboard': 0,
            'todo': 1,
            'settings': 2,
            'about': 3
        }
        
        if page_id in page_index:
            self.content_stack.setCurrentIndex(page_index[page_id])
            self.set_active_nav_button(page_id)
    
    def set_active_nav_button(self, active_id):
        """Marca o botão de navegação ativo"""
        for page_id, btn in self.nav_buttons.items():
            if page_id == active_id:
                btn.setObjectName("nav_button_active")
            else:
                btn.setObjectName("nav_button")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
    
    def toggle_theme(self):
        """Alterna entre tema claro e escuro"""
        self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
        self.apply_theme(self.current_theme)
        
        # Atualizar ícone do botão
        self.theme_btn.setText("☀️" if self.current_theme == 'light' else "🌙")
    
    def apply_theme(self, theme):
        """Aplica o tema especificado"""
        if theme == 'dark':
            self.app.setStyleSheet(DARK_STYLE)
        else:
            self.app.setStyleSheet(LIGHT_STYLE)

# ============================================================================
# MAIN - Ponto de Entrada
# ============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = MainWindow(app)
    window.show()
    
    sys.exit(app.exec())