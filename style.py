"""Estilos QSS globais do app (PySide6)

Este arquivo define o tema e os estilos dos componentes do app.
Seções marcadas com comentários ajudam a localizar rapidamente estilos
por componente.
"""

# Estilo QSS moderno e temático (escuro + amarelo)
STYLESHEET = """
/* ========================================
   Base/Tipografia/Janela
   ======================================== */
/* Aplica os estilos base APENAS ao widget central e seus filhos,
   para não interferir com a moldura/título da janela principal. */
QWidget#central_widget {
    background-color: #1e1e1e;
    color: #ffffff;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 12px;
}

/* Títulos */
QLabel#title { font-size: 24px; font-weight: bold; color: #00d4ff; padding: 10px; }
QLabel#subtitle { font-size: 14px; color: #cccccc; padding: 5px; }

/* ========================================
   Botões
   ======================================== */
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
QTabWidget::tab:selected { background-color: #007acc; }

/* ========================================
   RadioButtons
   ======================================== */
QRadioButton { font-size: 24px; color: #ffffff; padding: 2px; }
QRadioButton:checked { font-weight: bold;  }
QRadioButton:hover { background-color: #007acc; }
QRadioButton:checked:hover { background-color: #007acc;  }

/* ========================================
   Containers (GroupBox, Tabs)
   ======================================== */
QGroupBox {
    font-weight: bold;
    border: 2px solid #404040;
    border-radius: 8px;
    margin-top: 10px;
    padding: 20px 10px 10px 10px;
    font-size: 14px;
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
}
QTabBar::tab:selected { background-color: #007acc; }
QTabBar::tab:hover { background-color: #404040; }

/* ========================================
   Inputs (Spin, LineEdit)
   ======================================== */
QSpinBox, QDoubleSpinBox, QLineEdit {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    border-radius: 4px;
    padding: 5px;
    color: white;
}
QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus { border: 2px solid #007acc; }

/* ========================================
   Áreas de texto (Logs e Editor)
   ======================================== */
/* Logs (QTextEdit) */
QTextEdit {
    background-color: #2b2b2b;
    border: 1px solid #404040;
    border-radius: 4px;
    color: #00ff7f; /* verde mais suave */
    font-family: "Consolas", "Monaco", monospace;
    font-size: 11px;
}

/* Editor de código (QPlainTextEdit) */
QPlainTextEdit {
    background-color: #1e1e1e;
    color: #eaeaea;
    border: 1px solid #3a3a3a;
    selection-background-color: #264f78;
    selection-color: #ffffff;
}

/* ========================================
   Barras de Progresso
   ======================================== */
QProgressBar {
    border: 2px solid #404040;
    border-radius: 5px;
    text-align: center;
    background-color: #2d2d2d;
}
QProgressBar::chunk { background-color: #28a745; border-radius: 3px; }

/* ========================================
   Barras de Rolagem (Scrollbars) - Globais
   Aplicado a todas as barras (QScrollArea, QTextEdit, QPlainTextEdit)
   ======================================== */
QScrollBar:vertical {
    background: #1e1e1e;
    width: 14px; /* largura maior para usabilidade */
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #f4c430; /* amarelo principal */
    min-height: 28px;
    border-radius: 7px;
}
QScrollBar::handle:vertical:hover {
    background: #d9ad27; /* amarelo mais escuro no hover */
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background: transparent;
    height: 0px; /* oculta botões */
}

QScrollBar:horizontal {
    background: #1e1e1e;
    height: 14px; /* altura maior para usabilidade */
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: #f4c430; /* amarelo principal */
    min-width: 28px;
    border-radius: 7px;
}
QScrollBar::handle:horizontal:hover {
    background: #d9ad27; /* amarelo mais escuro no hover */
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    background: transparent;
    width: 0px; /* oculta botões */
}

/* ========================================
   Tabela (QTableWidget)
   ======================================== */
QTableWidget {
    background-color: #2d2d2d; /* Mesmo cinza dos inputs */
    border: 1px solid #404040;
    gridline-color: #404040; /* Cor da grade */
    alternate-background-color: #3a3a3a; /* Cor para linhas alternadas */
    selection-background-color: #007acc; /* Azul de seleção */
    font-size: 14px; /* Aumenta a fonte para toda a tabela */
}

QHeaderView::section {
    background-color: #004578; /* Azul escuro */
    color: white;
    padding: 8px;
    border: 1px solid #404040;
    font-weight: bold;
    font-size: 14px; /* Alinha com o novo tamanho da fonte */
}

QTableWidget::item {
    padding: 10px; /* Aumenta o espaçamento, tornando as células e o editor maiores */
    border-bottom: 1px solid #404040;
}

/* Editor de item da tabela */
QTableWidget QLineEdit {
    padding: 8px;
    min-height: 20px; /* Garante uma altura mínima para o editor */
}
"""