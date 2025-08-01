# Estilo QSS moderno
STYLESHEET = """
QWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 12px;
}
QMainWindow { background-color: #1e1e1e; }
QLabel#title { font-size: 24px; font-weight: bold; color: #00d4ff; padding: 10px; }
QLabel#subtitle { font-size: 14px; color: #cccccc; padding: 5px; }
QPushButton {
    background-color: #007acc;
    color: white;
    font-size: 14px;
    font-weight: bold;
    padding: 12px 20px;
    border-radius: 6px;
    border: none;
    min-width: 120px;
}
QPushButton:hover { background-color: #005a9e; }
QPushButton:pressed { background-color: #004578; }
QPushButton#run_button { background-color: #28a745; }
QPushButton#run_button:hover { background-color: #218838; }
QGroupBox {
    font-weight: bold;
    border: 2px solid #404040;
    border-radius: 8px;
    margin-top: 10px;
    padding: 20px 10px 10px 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
    color: #00d4ff;
}
QSpinBox, QDoubleSpinBox, QLineEdit {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    border-radius: 4px;
    padding: 5px;
    color: white;
}
QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus { border: 2px solid #007acc; }
QTextEdit {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    border-radius: 4px;
    color: #00ff00;
    font-family: "Consolas", "Monaco", monospace;
    font-size: 11px;
}
QProgressBar {
    border: 2px solid #404040;
    border-radius: 5px;
    text-align: center;
    background-color: #2d2d2d;
}
QProgressBar::chunk { background-color: #28a745; border-radius: 3px; }
QTabWidget::pane { border: 1px solid #404040; background-color: #1e1e1e; }
QTabBar::tab {
    background-color: #2d2d2d;
    color: white;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected { background-color: #007acc; }
QTabBar::tab:hover { background-color: #404040; }
"""