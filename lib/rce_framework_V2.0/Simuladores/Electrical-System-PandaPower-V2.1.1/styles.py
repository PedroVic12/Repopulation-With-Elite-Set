class AppStyles:
    """
    This class holds the QSS stylesheets for the application.
    It provides a dark mode and a light mode theme.
    """

    DARK_MODE_STYLESHEET = """
        /* ========================================
           Base/Window/Typography
           ======================================== */
        QWidget {
            background-color: #1e1e1e;
            color: #f0f0f0;
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 12px;
        }
        QMainWindow { background-color: #1e1e1e; }

        /* Titles */
        QLabel#title { font-size: 24px; font-weight: bold; color: #00d4ff; padding: 10px; }
        QLabel#subtitle { font-size: 14px; color: #cccccc; padding: 5px; }

        /* ========================================
           Buttons
           ======================================== */
        QPushButton {
            background-color: #007acc;
            color: white;
            font-size: 12px;
            font-weight: bold;
            padding: 10px 18px;
            border-radius: 6px;
            border: none;
            min-width: 100px;
        }
        QPushButton:hover { background-color: #008ae6; }
        QPushButton:pressed { background-color: #005a9e; }
        QPushButton:disabled { background-color: #555; color: #999; }
        
        QPushButton#run_button { background-color: #28a745; }
        QPushButton#run_button:hover { background-color: #2dbc4e; }
        QPushButton#run_button:pressed { background-color: #218838; }

        /* ========================================
           Containers (GroupBox, Tabs)
           ======================================== */
        QGroupBox {
            font-weight: bold;
            border: 1px solid #404040;
            border-radius: 8px;
            margin-top: 10px;
            padding: 20px 10px 10px 10px;
            font-size: 12px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #00d4ff;
        }
        QTabWidget::pane { border: 1px solid #404040; background-color: #1e1e1e; }
        QTabBar::tab {
            background-color: #2d2d2d;
            color: white;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            border: 1px solid #404040;
            border-bottom: none;
        }
        QTabBar::tab:selected { background-color: #007acc; border-color: #007acc;}
        QTabBar::tab:hover { background-color: #404040; }

        /* ========================================
           Metric Cards
           ======================================== */
        QGroupBox#metricCard { /* Default state for cards without specific status */
            background-color: #2d2d2d;
            border: 1px solid #404040;
            padding: 10px;
        }
        QGroupBox#metricCard::title {
            color: #cccccc;
            font-size: 11px;
        }
        QLabel#metricValue {
            font-size: 26px;
            font-weight: bold;
            color: #f0f0f0;
            padding-top: 5px;
        }

        /* Specific static card colors */
        QGroupBox#genCard { background-color: #1d402b; border-color: #2a9d8f; }
        QGroupBox#loadCard { background-color: #6f4e00; border-color: #ffb703; }

        /* Conditional colors for violations/overloads */
        QGroupBox#voltageCard[status="alert"], QGroupBox#overloadCard[status="alert"] {
            background-color: #582125;
            border-color: #d90429;
        }
        QGroupBox#voltageCard[status="ok"], QGroupBox#overloadCard[status="ok"] {
            background-color: #2d2d2d;
            border: 1px solid #404040;
        }


        /* ========================================
           Inputs (ComboBox, LineEdit, ListWidget)
           ======================================== */
        QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
            background-color: #2d2d2d;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 5px;
            color: white;
        }
        QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus { border: 2px solid #007acc; }
        QComboBox::drop-down { border: none; }
        
        QListWidget {
            background-color: #2d2d2d;
            border: 1px solid #404040;
            border-radius: 4px;
        }
        QListWidget::item { padding: 8px; border-bottom: 1px solid #404040; }
        QListWidget::item:selected { background-color: #007acc; }
        QListWidget::item:hover { background-color: #404040; }

        /* ========================================
           Text Areas (Logs, Description)
           ======================================== */
        QTextEdit {
            background-color: #2b2b2b;
            border: 1px solid #404040;
            border-radius: 4px;
            color: #cccccc;
        }

        /* ========================================
           Scrollbars
           ======================================== */
        QScrollBar:vertical {
            background: #1e1e1e;
            width: 14px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: #555;
            min-height: 28px;
            border-radius: 7px;
        }
        QScrollBar::handle:vertical:hover { background: #666; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

        QScrollBar:horizontal {
            background: #1e1e1e;
            height: 14px;
            margin: 0px;
        }
        QScrollBar::handle:horizontal {
            background: #555;
            min-width: 28px;
            border-radius: 7px;
        }
        QScrollBar::handle:horizontal:hover { background: #666; }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }

        /* ========================================
           Table
           ======================================== */
        QTableWidget {
            background-color: #2d2d2d;
            border: 1px solid #404040;
            gridline-color: #404040;
            alternate-background-color: #3a3a3a;
            selection-background-color: #007acc;
        }
        QHeaderView::section {
            background-color: #3a3a3a;
            color: #00d4ff;
            padding: 8px;
            border: 1px solid #404040;
            font-weight: bold;
        }
        QTableWidget::item { padding: 8px; }

        /* ========================================
           Splitter
           ======================================== */
        QSplitter::handle { background-color: #404040; }
        QSplitter::handle:hover { background-color: #007acc; }
        QSplitter::handle:pressed { background-color: #005a9e; }
    """

    LIGHT_MODE_STYLESHEET = """
        /* ========================================
           Base/Window/Typography
           ======================================== */
        QWidget {
            background-color: #f0f0f0;
            color: #000000;
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 12px;
        }
        QMainWindow { background-color: #f0f0f0; }

        /* Titles */
        QLabel#title { font-size: 24px; font-weight: bold; color: #005a9e; padding: 10px; }
        QLabel#subtitle { font-size: 14px; color: #555555; padding: 5px; }

        /* ========================================
           Buttons
           ======================================== */
        QPushButton {
            background-color: #0078d7;
            color: white;
            font-size: 12px;
            font-weight: bold;
            padding: 10px 18px;
            border-radius: 6px;
            border: 1px solid #0078d7;
            min-width: 100px;
        }
        QPushButton:hover { background-color: #106ebe; border: 1px solid #106ebe; }
        QPushButton:pressed { background-color: #005a9e; border: 1px solid #005a9e; }
        QPushButton:disabled { background-color: #e0e0e0; color: #999; border: 1px solid #cccccc; }
        
        QPushButton#run_button { background-color: #107c10; border-color: #107c10;}
        QPushButton#run_button:hover { background-color: #0f6a0f; border-color: #0f6a0f;}
        QPushButton#run_button:pressed { background-color: #0e5a0e; border-color: #0e5a0e;}

        /* ========================================
           Containers (GroupBox, Tabs)
           ======================================== */
        QGroupBox {
            font-weight: bold;
            border: 1px solid #cccccc;
            border-radius: 8px;
            margin-top: 10px;
            padding: 20px 10px 10px 10px;
            font-size: 12px;
            background-color: #ffffff;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #005a9e;
        }
        QTabWidget::pane { border: 1px solid #cccccc; background-color: #ffffff; }
        QTabBar::tab {
            background-color: #e0e0e0;
            color: #333;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            border: 1px solid #cccccc;
            border-bottom: none;
        }
        QTabBar::tab:selected { background-color: #0078d7; color: white; border-color: #0078d7;}
        QTabBar::tab:hover { background-color: #cce3f9; }
        
        /* ========================================
           Metric Cards
           ======================================== */
        QGroupBox#metricCard {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            padding: 10px;
        }
        QGroupBox#metricCard::title {
            color: #555555;
            font-size: 11px;
        }
        QLabel#metricValue {
            font-size: 26px;
            font-weight: bold;
            color: #333333;
            padding-top: 5px;
        }

        /* Specific static card colors */
        QGroupBox#genCard { background-color: #d4edda; border-color: #c3e6cb; }
        QGroupBox#genCard QLabel { color: #155724; }
        QGroupBox#loadCard { background-color: #fff3cd; border-color: #ffeeba; }
        QGroupBox#loadCard QLabel { color: #856404; }

        /* Conditional colors for violations/overloads */
        QGroupBox#voltageCard[status="alert"], QGroupBox#overloadCard[status="alert"] {
            background-color: #f8d7da;
            border-color: #f5c6cb;
        }
        QGroupBox#voltageCard[status="alert"] QLabel, QGroupBox#overloadCard[status="alert"] QLabel {
             color: #721c24;
        }
        QGroupBox#voltageCard[status="ok"], QGroupBox#overloadCard[status="ok"] {
            background-color: #ffffff;
            border: 1px solid #cccccc;
        }
        QGroupBox#voltageCard[status="ok"] QLabel, QGroupBox#overloadCard[status="ok"] QLabel {
            color: #333333;
        }


        /* ========================================
           Inputs (ComboBox, LineEdit, ListWidget)
           ======================================== */
        QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 5px;
            color: #000000;
        }
        QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus { border: 2px solid #0078d7; }
        QComboBox::drop-down { border: none; }
        
        QListWidget {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 4px;
        }
        QListWidget::item { padding: 8px; border-bottom: 1px solid #e0e0e0; }
        QListWidget::item:selected { background-color: #0078d7; color: white; }
        QListWidget::item:hover { background-color: #e6f2fa; }

        /* ========================================
           Text Areas (Logs, Description)
           ======================================== */
        QTextEdit {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 4px;
            color: #333333;
        }

        /* ========================================
           Scrollbars
           ======================================== */
        QScrollBar:vertical {
            background: #f0f0f0;
            width: 14px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: #cccccc;
            min-height: 28px;
            border-radius: 7px;
        }
        QScrollBar::handle:vertical:hover { background: #bbbbbb; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

        QScrollBar:horizontal {
            background: #f0f0f0;
            height: 14px;
            margin: 0px;
        }
        QScrollBar::handle:horizontal {
            background: #cccccc;
            min-width: 28px;
            border-radius: 7px;
        }
        QScrollBar::handle:horizontal:hover { background: #bbbbbb; }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }

        /* ========================================
           Table
           ======================================== */
        QTableWidget {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            gridline-color: #e0e0e0;
            alternate-background-color: #f7f7f7;
            selection-background-color: #0078d7;
        }
        QHeaderView::section {
            background-color: #e0e0e0;
            color: #005a9e;
            padding: 8px;
            border: 1px solid #cccccc;
            font-weight: bold;
        }
        QTableWidget::item { padding: 8px; }

        /* ========================================
           Splitter
           ======================================== */
        QSplitter::handle { background-color: #cccccc; }
        QSplitter::handle:hover { background-color: #0078d7; }
        QSplitter::handle:pressed { background-color: #005a9e; }
    """


