# ARQUIVO: gui/iframes/reserva_widget.py
import sys
import subprocess
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QSizePolicy)
from PySide6.QtCore import Qt

class ReservaWidget(QWidget):
    def __init__(self, side_menu=None):
        # NOTA: Recebemos 'side_menu' porque sua função open_or_focus_tab tenta passar esse argumento
        super().__init__()
        self.side_menu = side_menu 
        self.setup_ui()

    def setup_ui(self):
        # Layout principal da aba (Centraliza o Card na tela)
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- ESTILOS LOCAIS (Para garantir que funcione isolado) ---
        style_card = """
            QFrame#ReservaCard {
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
        style_btn_outline = """
            QPushButton {
                background-color: white;
                border: 2px solid #0088cc;
                border-radius: 4px;
                color: #0088cc;
                font-weight: bold;
                padding: 10px;
                font-size: 12px;
                text-transform: uppercase;
            }
            QPushButton:hover { background-color: #f0f8ff; }
        """
        style_btn_action = """
            QPushButton {
                background-color: #0088cc;
                border: none;
                border-radius: 4px;
                color: white;
                font-weight: bold;
                padding: 15px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #006699; }
            QPushButton:disabled { background-color: #cccccc; color: #666; }
        """

        # --- CRIAÇÃO DO CARD ---
        self.card = QFrame()
        self.card.setObjectName("ReservaCard")
        self.card.setFixedWidth(600)
        self.card.setStyleSheet(style_card)

        # Layout interno do card
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(20)

        # Texto HTML
        lbl_info = QLabel()
        lbl_info.setAlignment(Qt.AlignCenter)
        lbl_info.setWordWrap(True)
        lbl_info.setText("""
            Enviamos um resumo de reserva para o seu endereço de e-mail<br>
            <b><span style='text-decoration: underline; color: #333;'>pedrovictor.veras@ons.org.br</span></b>.<br>
            Se você não receber o e-mail, por favor, verifique sua pasta de spam.
        """)
        card_layout.addWidget(lbl_info)

        # Botões Superiores (Calendário / Alterar)
        btn_layout = QHBoxLayout()
        self.btn_calendar = QPushButton("📅  ADICIONAR AO CALENDÁRIO")
        self.btn_edit = QPushButton("✏️  ALTERAR RESERVA")
        self.btn_calendar.setStyleSheet(style_btn_outline)
        self.btn_edit.setStyleSheet(style_btn_outline)
        self.btn_calendar.setCursor(Qt.PointingHandCursor)
        self.btn_edit.setCursor(Qt.PointingHandCursor)
        
        btn_layout.addWidget(self.btn_calendar)
        btn_layout.addWidget(self.btn_edit)
        card_layout.addLayout(btn_layout)

        # Botão Principal (Automação)
        self.btn_run = QPushButton("VOLTAR AO SITE DE RESERVAS")
        self.btn_run.setCursor(Qt.PointingHandCursor)
        self.btn_run.setStyleSheet(style_btn_action)
        self.btn_run.clicked.connect(self.rodar_script)
        card_layout.addWidget(self.btn_run)

        # Adiciona o card ao layout principal
        main_layout.addWidget(self.card)

    def rodar_script(self):
        # CAMINHO DO SEU SCRIPT PYTHON DE AUTOMAÇÃO
        script_path = "seu_script_relatorio.py"  # <--- AJUSTE O CAMINHO AQUI

        self.btn_run.setText("PROCESSANDO... AGUARDE")
        self.btn_run.setEnabled(False)
        self.btn_run.repaint() # Força atualização visual

        try:
            # sys.executable garante que use o mesmo Python que está rodando o app
            processo = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True
            )

            if processo.returncode == 0:
                print("Sucesso:", processo.stdout)
                self.btn_run.setText("SUCESSO! (CLIQUE P/ REPETIR)")
                # Opcional: Mostrar popup de sucesso aqui
            else:
                print("Erro:", processo.stderr)
                self.btn_run.setText("ERRO NA EXECUÇÃO")
        
        except Exception as e:
            print(f"Erro ao tentar rodar: {e}")
            self.btn_run.setText("ERRO DE SISTEMA")
        
        finally:
            self.btn_run.setEnabled(True)