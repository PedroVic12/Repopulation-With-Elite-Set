"""
styles.py

Contém as definições de stylesheet (QSS) para os temas da aplicação.
Estilos baseados no template de referência para maior robustez.
"""

DARK_STYLE = """
    /* Global */
    QWidget {
        background-color: #2b2b2b; 
        color: #f0f0f0; 
        font-family: "Segoe UI", sans-serif;
    }
    QMainWindow { 
        background-color: #212121; 
    }

    /* Left Menu */
    #left_menu {
        background-color: #3c3f41;
    }
    PyPushButton {
        color: #c3ccdf;
        background-color: #3c3f41;
        border: none;
        text-align: left;
    }
    PyPushButton:hover {
        background-color: #4f5368;
    }
    PyPushButton:pressed {
        background-color: #282a36;
    }
    
    /* Active Button */
    PyPushButton[is_active="true"] {
        background-color: #4f5368;
        border-right: 5px solid #6272a4;
    }

    /* Top and Bottom Bars */
    #top_bar, #bottom_bar {
        background-color: #21232d; 
        color: #6272a4;
    }

    /* Tab Widget */
    QTabWidget::pane {
        border: none;
    }
    QTabBar::tab {
        background-color: #44475a;
        color: #c3ccdf;
        padding: 10px 20px;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
        border: 1px solid #282a36;
    }
    QTabBar::tab:selected {
        background-color: #6272a4;
        color: #f8f8f2;
    }
    QTabBar::tab:!selected:hover {
        background-color: #4f5368;
    }
    QTabBar::close-button {
        margin-left: 5px;
    }

    /* General Widgets inside tabs */
    QLabel {
        color: #f0f0f0;
    }
    QPushButton {
        background-color: #4f5368;
        border: 1px solid #6272a4;
        padding: 8px;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #6272a4;
    }
    QLineEdit, QTextEdit {
        background-color: #2b2b2b;
        border: 1px solid #4f5368;
        padding: 6px;
        border-radius: 4px;
    }
    QListWidget {
        background-color: #2b2b2b;
        border: 1px solid #4f5368;
    }
    QComboBox, QFontComboBox, QSpinBox {
        background-color: #4f5368;
        border: 1px solid #6272a4;
        padding: 4px;
        border-radius: 4px;
    }
    QComboBox QAbstractItemView, QFontComboBox QAbstractItemView {
        background-color: #4f5368;
        border: 1px solid #6272a4;
        selection-background-color: #6272a4;
    }
"""

LIGHT_STYLE = """
    /* Global */
    QWidget {
        background-color: #f0f0f0; 
        color: #000000; 
        font-family: "Segoe UI", sans-serif;
    }
    QMainWindow { 
        background-color: #e0e0e0; 
    }

    /* Left Menu */
    #left_menu {
        background-color: #e5e5e5;
    }
    PyPushButton {
        color: #333;
        background-color: #e5e5e5;
        border: none;
        text-align: left;
    }
    PyPushButton:hover {
        background-color: #d5d5d5;
    }
    PyPushButton:pressed {
        background-color: #c5c5c5;
    }

    /* Active Button */
    PyPushButton[is_active="true"] {
        background-color: #d5d5d5;
        border-right: 5px solid #0078d4;
    }

    /* Top and Bottom Bars */
    #top_bar, #bottom_bar {
        background-color: #d0d0d0; 
        color: #444;
    }

    /* Tab Widget */
    QTabWidget::pane {
        border: 1px solid #c0c0c0;
    }
    QTabBar::tab {
        background-color: #e0e0e0;
        color: #000000;
        padding: 10px 20px;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
        border: 1px solid #c0c0c0;
        border-bottom: none;
    }
    QTabBar::tab:selected {
        background-color: #ffffff;
        border-bottom: 1px solid #ffffff;
    }
    QTabBar::tab:!selected:hover {
        background-color: #d5d5d5;
    }
    QTabBar::close-button {
        margin-left: 5px;
    }

    /* General Widgets inside tabs */
    QLabel {
        color: #000000;
    }
    QPushButton {
        background-color: #e0e0e0;
        border: 1px solid #c0c0c0;
        padding: 8px;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #d5d5d5;
    }
    QLineEdit, QTextEdit {
        background-color: #ffffff;
        border: 1px solid #c0c0c0;
        padding: 6px;
        border-radius: 4px;
    }
    QListWidget {
        background-color: #ffffff;
        border: 1px solid #c0c0c0;
    }
    QComboBox, QFontComboBox, QSpinBox {
        background-color: #e0e0e0;
        border: 1px solid #c0c0c0;
        padding: 4px;
        border-radius: 4px;
    }
    QComboBox QAbstractItemView, QFontComboBox QAbstractItemView {
        background-color: #ffffff;
        border: 1px solid #c0c0c0;
        selection-background-color: #0078d4;
    }
"""
