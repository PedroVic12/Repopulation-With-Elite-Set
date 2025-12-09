# styles.py

STYLESHEET = """
QWidget {
    background-color: #1e1e1e; color: #ffffff;
    font-family: "Segoe UI", Arial, sans-serif; font-size: 12px;
}
QMainWindow { background-color: #1e1e1e; }
QPushButton {
    background-color: #007acc; color: white; font-size: 14px; font-weight: bold;
    padding: 12px 20px; border-radius: 6px; border: none; min-width: 120px;
}
QPushButton:hover { background-color: #005a9e; }
QPushButton:pressed { background-color: #004578; }
QPushButton.nav-button {
    background-color: transparent; border: none; color: #ffffff;
    text-align: left; padding: 10px; font-size: 16px;
}
QPushButton.nav-button:hover { background-color: #404040; }
QPushButton.nav-button:checked { background-color: #007acc; }
QGroupBox {
    font-weight: bold; border: 1px solid #404040; border-radius: 8px;
    margin-top: 10px; padding: 20px 10px 10px 10px; font-size: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #00d4ff;
}
QTabWidget::pane { border: 1px solid #404040; background-color: #1e1e1e; }
QTabBar::tab {
    background-color: #2d2d2d; color: white; padding: 8px 16px;
    margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px;
    border: 1px solid #404040; border-bottom: none;
}
QTabBar::tab:selected { background-color: #007acc; border-color: #007acc;}
QTabBar::tab:hover { background-color: #404040; }
QTabBar::close-button { image: url(none); }
QSpinBox, QLineEdit, QComboBox {
    background-color: #2d2d2d; border: 1px solid #404040;
    border-radius: 4px; padding: 5px; color: white;
}
QTextEdit {
    background-color: #2b2b2b; border: 1px solid #404040;
    border-radius: 4px; color: #cccccc;
}
QProgressBar {
    border: 2px solid #404040; border-radius: 5px; text-align: center;
    background-color: #2d2d2d; color: white;
}
QProgressBar::chunk { background-color: #28a745; border-radius: 3px; }
QTableWidget {
    background-color: #2d2d2d; border: 1px solid #404040;
    gridline-color: #404040; alternate-background-color: #3a3a3a;
    selection-background-color: #007acc; font-size: 12px;
}
QHeaderView::section {
    background-color: #3a3a3a; color: #00d4ff; padding: 8px;
    border: 1px solid #404040; font-weight: bold;
}
QListWidget {
    background-color: #2d2d2d; border: 2px solid #404040; border-radius: 8px;
    font-size: 16px; padding: 5px;
}
QListWidget::item { padding: 12px; border-bottom: 1px solid #404040; }
QListWidget::item:hover { background-color: #404040; }
QListWidget::item:selected { background-color: #007acc; color: white; font-weight: bold; }
QSplitter::handle { background-color: #404040; }
QSplitter::handle:hover { background-color: #007acc; }
"""
