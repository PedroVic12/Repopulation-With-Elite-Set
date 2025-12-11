# Cores Globais
PRIMARY_COLOR = "#0088cc"
BG_COLOR = "#f4f4f4"
TEXT_COLOR = "#555555"

# Estilo do Card (O container branco)
CARD_STYLE = """
    QFrame {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
    }
    QLabel {
        color: #555555;
        font-family: 'Segoe UI', sans-serif;
        font-size: 14px;
        border: none;
    }
"""

# Estilo dos Botões de Contorno (Calendário/Alterar)
BTN_OUTLINE_STYLE = f"""
    QPushButton {{
        background-color: white;
        border: 2px solid {PRIMARY_COLOR};
        border-radius: 4px;
        color: {PRIMARY_COLOR};
        font-weight: bold;
        padding: 10px;
        font-size: 12px;
        text-transform: uppercase;
        font-family: 'Segoe UI';
    }}
    QPushButton:hover {{
        background-color: #f0f8ff;
    }}
    QPushButton:pressed {{
        background-color: #e1efff;
    }}
"""

# Estilo do Botão de Ação Principal (Rodar Script)
BTN_ACTION_STYLE = f"""
    QPushButton {{
        background-color: {PRIMARY_COLOR};
        border: none;
        border-radius: 4px;
        color: white;
        font-weight: bold;
        padding: 15px;
        font-size: 13px;
        font-family: 'Segoe UI';
    }}
    QPushButton:hover {{
        background-color: #006699;
    }}
    QPushButton:disabled {{
        background-color: #cccccc;
        color: #666666;
    }}
"""

# Estilo do Menu Lateral
SIDEBAR_STYLE = """
    QListWidget {
        border: none;
        background-color: #2c3e50;
        outline: none;
    }
    QListWidget::item {
        color: white;
        padding: 15px;
        border-bottom: 1px solid #34495e;
        font-family: 'Segoe UI';
        font-size: 14px;
    }
    QListWidget::item:selected {
        background-color: #0088cc;
        border-left: 4px solid white;
    }
    QListWidget::item:hover {
        background-color: #34495e;
    }
"""