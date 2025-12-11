# styles.py - Estilos atualizados com tema claro/escuro
APP_STYLES = """
/* ========================================
   ESTILOS GLOBAIS - TEMA ESCURO
======================================== */
QMainWindow {
    background-color: #1e1e2e;
}

QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
}

/* ========================================
   GROUPBOX
======================================== */
QGroupBox {
    border: 2px solid #45475a;
    border-radius: 8px;
    margin-top: 12px;
    padding: 15px;
    font-weight: bold;
    color: #89b4fa;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #89b4fa;
}

/* ========================================
   BOTÕES
======================================== */
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 2px solid #45475a;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    min-height: 30px;
}

QPushButton:hover {
    background-color: #45475a;
    border-color: #89b4fa;
}

QPushButton:pressed {
    background-color: #585b70;
}

QPushButton:disabled {
    background-color: #1e1e2e;
    color: #6c7086;
    border-color: #313244;
}

/* ========================================
   LABELS
======================================== */
QLabel {
    color: #cdd6f4;
    background: transparent;
}

/* ========================================
   LINE EDIT
======================================== */
QLineEdit {
    background-color: #313244;
    color: #cdd6f4;
    border: 2px solid #45475a;
    border-radius: 4px;
    padding: 6px;
}

QLineEdit:focus {
    border-color: #89b4fa;
}

/* ========================================
   TEXT EDIT
======================================== */
QTextEdit {
    background-color: #181825;
    color: #cdd6f4;
    border: 2px solid #45475a;
    border-radius: 4px;
    padding: 8px;
    selection-background-color: #585b70;
}

/* ========================================
   TABLE VIEW / WIDGET
======================================== */
QTableView, QTableWidget {
    background-color: #181825;
    alternate-background-color: #1e1e2e;
    color: #cdd6f4;
    gridline-color: #313244;
    border: 2px solid #45475a;
    border-radius: 4px;
}

QTableView::item:selected, QTableWidget::item:selected {
    background-color: #585b70;
    color: #cdd6f4;
}

QHeaderView::section {
    background-color: #313244;
    color: #89b4fa;
    padding: 8px;
    border: 1px solid #45475a;
    font-weight: bold;
}

/* ========================================
   TABS
======================================== */
QTabWidget::pane {
    border: 2px solid #45475a;
    border-radius: 4px;
    background-color: #1e1e2e;
}

QTabBar::tab {
    background-color: #313244;
    color: #cdd6f4;
    border: 2px solid #45475a;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 16px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #45475a;
    color: #89b4fa;
    border-color: #89b4fa;
}

QTabBar::tab:hover {
    background-color: #585b70;
}

/* ========================================
   CHECKBOX
======================================== */
QCheckBox {
    color: #cdd6f4;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #45475a;
    border-radius: 4px;
    background-color: #313244;
}

QCheckBox::indicator:checked {
    background-color: #89b4fa;
    border-color: #89b4fa;
}

QCheckBox::indicator:hover {
    border-color: #89b4fa;
}

/* ========================================
   SCROLLBAR
======================================== */
QScrollBar:vertical {
    background-color: #1e1e2e;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #585b70;
}

/* ========================================
   FRAMES
======================================== */
QFrame#sidebar {
    background-color: #181825;
    border-right: 2px solid #45475a;
}

QFrame#topbar {
    background-color: #181825;
    border-bottom: 2px solid #45475a;
}

QPushButton#nav_button {
    background-color: transparent;
    border: none;
    text-align: left;
    padding: 12px;
}

QPushButton#nav_button:hover {
    background-color: #313244;
    border-left: 3px solid #89b4fa;
}

QPushButton#nav_button_active {
    background-color: #313244;
    border-left: 3px solid #89b4fa;
}

QPushButton#theme_toggle {
    background-color: transparent;
    border: 2px solid #45475a;
    border-radius: 20px;
    padding: 8px;
    min-width: 60px;
}

QPushButton#theme_toggle:hover {
    background-color: #45475a;
}
"""

LIGHT_STYLE = """
/* ========================================
   ESTILOS GLOBAIS - TEMA CLARO
======================================== */
QMainWindow {
    background-color: #eff1f5;
}

QWidget {
    background-color: #eff1f5;
    color: #4c4f69;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
}

/* ========================================
   GROUPBOX
======================================== */
QGroupBox {
    border: 2px solid #9ca0b0;
    border-radius: 8px;
    margin-top: 12px;
    padding: 15px;
    font-weight: bold;
    color: #1e66f5;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #1e66f5;
}

/* ========================================
   BOTÕES
======================================== */
QPushButton {
    background-color: #ccd0da;
    color: #4c4f69;
    border: 2px solid #9ca0b0;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    min-height: 30px;
}

QPushButton:hover {
    background-color: #bcc0cc;
    border-color: #1e66f5;
}

QPushButton:pressed {
    background-color: #acb0be;
}

QPushButton:disabled {
    background-color: #e6e9ef;
    color: #8c8fa1;
    border-color: #ccd0da;
}

/* ========================================
   LABELS
======================================== */
QLabel {
    color: #4c4f69;
    background: transparent;
}

/* ========================================
   LINE EDIT
======================================== */
QLineEdit {
    background-color: #e6e9ef;
    color: #4c4f69;
    border: 2px solid #9ca0b0;
    border-radius: 4px;
    padding: 6px;
}

QLineEdit:focus {
    border-color: #1e66f5;
}

/* ========================================
   TEXT EDIT
======================================== */
QTextEdit {
    background-color: #dce0e8;
    color: #4c4f69;
    border: 2px solid #9ca0b0;
    border-radius: 4px;
    padding: 8px;
    selection-background-color: #acb0be;
}

/* ========================================
   TABLE VIEW / WIDGET
======================================== */
QTableView, QTableWidget {
    background-color: #dce0e8;
    alternate-background-color: #e6e9ef;
    color: #4c4f69;
    gridline-color: #ccd0da;
    border: 2px solid #9ca0b0;
    border-radius: 4px;
}

QTableView::item:selected, QTableWidget::item:selected {
    background-color: #acb0be;
    color: #4c4f69;
}

QHeaderView::section {
    background-color: #ccd0da;
    color: #1e66f5;
    padding: 8px;
    border: 1px solid #9ca0b0;
    font-weight: bold;
}

/* ========================================
   TABS
======================================== */
QTabWidget::pane {
    border: 2px solid #9ca0b0;
    border-radius: 4px;
    background-color: #eff1f5;
}

QTabBar::tab {
    background-color: #ccd0da;
    color: #4c4f69;
    border: 2px solid #9ca0b0;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 16px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #acb0be;
    color: #1e66f5;
    border-color: #1e66f5;
}

QTabBar::tab:hover {
    background-color: #bcc0cc;
}

/* ========================================
   CHECKBOX
======================================== */
QCheckBox {
    color: #4c4f69;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #9ca0b0;
    border-radius: 4px;
    background-color: #e6e9ef;
}

QCheckBox::indicator:checked {
    background-color: #1e66f5;
    border-color: #1e66f5;
}

QCheckBox::indicator:hover {
    border-color: #1e66f5;
}

/* ========================================
   SCROLLBAR
======================================== */
QScrollBar:vertical {
    background-color: #eff1f5;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #9ca0b0;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #8c8fa1;
}

/* ========================================
   FRAMES
======================================== */
QFrame#sidebar {
    background-color: #dce0e8;
    border-right: 2px solid #9ca0b0;
}

QFrame#topbar {
    background-color: #dce0e8;
    border-bottom: 2px solid #9ca0b0;
}

QPushButton#nav_button {
    background-color: transparent;
    border: none;
    text-align: left;
    padding: 12px;
    color: #4c4f69;
}

QPushButton#nav_button:hover {
    background-color: #ccd0da;
    border-left: 3px solid #1e66f5;
}

QPushButton#nav_button_active {
    background-color: #ccd0da;
    border-left: 3px solid #1e66f5;
}

QPushButton#theme_toggle {
    background-color: transparent;
    border: 2px solid #9ca0b0;
    border-radius: 20px;
    padding: 8px;
    min-width: 60px;
}

QPushButton#theme_toggle:hover {
    background-color: #ccd0da;
}
"""

DARK_STYLE = APP_STYLES