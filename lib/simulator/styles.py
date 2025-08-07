
"""
styles.py - Contém as folhas de estilo para os temas da aplicação.
"""

class AppStyles:
    """
    Define os estilos CSS para os modos claro e escuro da aplicação.
    """

    LIGHT_MODE_STYLESHEET = """
        QMainWindow, QWidget { 
            background-color: #f0f2f6; 
        }
        QLabel { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            color: #333; 
        }
        QGroupBox { 
            font-weight: bold; 
            border: 1px solid #d0d0d0; 
            border-radius: 8px; 
            margin-top: 10px; 
            background-color: #ffffff; 
        }
        QGroupBox::title { 
            subcontrol-origin: margin; 
            subcontrol-position: top left; 
            padding: 0 8px; 
            left: 10px; 
            color: #333; 
        }
        QComboBox, QListWidget, QTextEdit, QTableWidget { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            padding: 5px; 
            background-color: #ffffff;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            color: #333;
        }
        QListWidget::item:selected {
            background-color: #d4edda;
            color: #155724;
        }
        QTableWidget::item {
            color: #333;
        }
        QTabWidget::pane { 
            border: 1px solid #cccccc; 
            border-radius: 4px; 
            background-color: white; 
        }
        QTabBar::tab { 
            background: #e1e1e1; 
            border: 1px solid #cccccc; 
            border-bottom-color: #c2c7d5; 
            padding: 8px 16px; 
            margin-right: 2px; 
            border-top-left-radius: 4px; 
            border-top-right-radius: 4px; 
            color: #333;
        }
        QTabBar::tab:selected { 
            background: white; 
            border-bottom-color: white; 
        }
        QSplitter::handle { 
            background: #d0d0d0; 
        }
        QSplitter::handle:horizontal { 
            width: 5px; 
        }
        QSplitter::handle:vertical { 
            height: 5px; 
        }
        QHeaderView::section { 
            background-color: #f0f2f6; 
            padding: 4px; 
            border: 1px solid #d0d0d0; 
            font-weight: bold; 
            color: #333;
        }
        QPushButton { 
            background-color: #007bff; 
            color: white; 
            padding: 8px; 
            border-radius: 5px; 
            font-weight: bold; 
        }
        QPushButton:hover {
            background-color: #0056b3;
        }
        QPushButton:disabled { 
            background-color: #9E9E9E; 
        }
        #ThemeToggle {
            background-color: #6c757d;
        }
        #ThemeToggle:hover {
            background-color: #5a6268;
        }
    """

    DARK_MODE_STYLESHEET = """
        QMainWindow, QWidget { 
            background-color: #212529; 
        }
        QLabel, QGroupBox, QCheckBox { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            color: #f8f9fa; 
        }
        QGroupBox { 
            font-weight: bold; 
            border: 1px solid #495057; 
            border-radius: 8px; 
            margin-top: 10px; 
            background-color: #343a40; 
        }
        QGroupBox::title { 
            subcontrol-origin: margin; 
            subcontrol-position: top left; 
            padding: 0 8px; 
            left: 10px; 
            color: #f8f9fa; 
        }
        QComboBox, QListWidget, QTextEdit, QTableWidget { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            padding: 5px; 
            background-color: #495057;
            border: 1px solid #6c757d;
            border-radius: 4px;
            color: #f8f9fa;
        }
        QListWidget::item:selected {
            background-color: #2a9d8f;
            color: #ffffff;
        }
        QTableWidget::item {
            color: #f8f9fa;
        }
        QListWidget::item {
            background-color: #495057;
        }
        QTabWidget::pane { 
            border: 1px solid #495057; 
            border-radius: 4px; 
            background-color: #343a40; 
        }
        QTabBar::tab { 
            background: #495057; 
            border: 1px solid #6c757d; 
            border-bottom-color: #343a40; 
            padding: 8px 16px; 
            margin-right: 2px; 
            border-top-left-radius: 4px; 
            border-top-right-radius: 4px; 
            color: #f8f9fa;
        }
        QTabBar::tab:selected { 
            background: #343a40; 
            border-bottom-color: #343a40; 
        }
        QSplitter::handle { 
            background: #6c757d; 
        }
        QSplitter::handle:horizontal { 
            width: 5px; 
        }
        QSplitter::handle:vertical { 
            height: 5px; 
        }
        QHeaderView::section { 
            background-color: #343a40; 
            padding: 4px; 
            border: 1px solid #495057; 
            font-weight: bold; 
            color: #f8f9fa;
        }
        QPushButton { 
            background-color: #0d6efd; 
            color: white; 
            padding: 8px; 
            border-radius: 5px; 
            font-weight: bold; 
        }
        QPushButton:hover {
            background-color: #0b5ed7;
        }
        QPushButton:disabled { 
            background-color: #6c757d; 
        }
        #ThemeToggle {
            background-color: #fd7e14;
        }
        #ThemeToggle:hover {
            background-color: #e66a0a;
        }
    """
