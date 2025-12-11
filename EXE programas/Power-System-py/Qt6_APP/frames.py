import sys
import subprocess
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QPlainTextEdit)
from PySide6.QtCore import Qt
import styles  # Importando nosso arquivo de estilos

# --- IFRAME 1: PÁGINA DE RESERVA (COM A AUTOMAÇÃO) ---
class ReservaPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Layout principal da página (centraliza o card)
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        # O CARD (Quadro Branco)
        self.card = QFrame()
        self.card.setFixedWidth(600)
        self.card.setStyleSheet(styles.CARD_STYLE) # Usa o estilo do arquivo styles.py
        
        # Layout dentro do card
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

        # Botões Superiores
        btn_layout = QHBoxLayout()
        self.btn_calendar = QPushButton("📅  ADICIONAR AO CALENDÁRIO")
        self.btn_edit = QPushButton("✏️  ALTERAR RESERVA")
        
        # Aplicando estilo Outline
        self.btn_calendar.setStyleSheet(styles.BTN_OUTLINE_STYLE)
        self.btn_edit.setStyleSheet(styles.BTN_OUTLINE_STYLE)
        
        btn_layout.addWidget(self.btn_calendar)
        btn_layout.addWidget(self.btn_edit)
        card_layout.addLayout(btn_layout)

        # Botão de Ação (Automação)
        self.btn_run = QPushButton("VOLTAR AO SITE DE RESERVAS (RODAR SCRIPT)")
        self.btn_run.setCursor(Qt.PointingHandCursor)
        self.btn_run.setStyleSheet(styles.BTN_ACTION_STYLE)
        self.btn_run.clicked.connect(self.rodar_automacao)
        card_layout.addWidget(self.btn_run)

        # Adiciona o card ao layout da página
        main_layout.addWidget(self.card)

    def rodar_automacao(self):
        # Lógica do Subprocess
        script_path = "seu_script.py" # <--- NOME DO SEU SCRIPT AQUI
        
        self.btn_run.setText("PROCESSANDO...")
        self.btn_run.setEnabled(False)
        
        try:
            # Roda o script usando o mesmo python do ambiente
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                self.btn_run.setText("SUCESSO! (CLIQUE PARA REPETIR)")
                print("Output:", result.stdout)
            else:
                self.btn_run.setText("ERRO NA EXECUÇÃO")
                print("Erro:", result.stderr)
                
        except Exception as e:
            self.btn_run.setText(f"ERRO DE SISTEMA: {e}")
        finally:
            self.btn_run.setEnabled(True)
            # Retorna texto original após 3s (simulação)
            # Na prática real usaria QTimer


# --- IFRAME 2: PÁGINA DE LOGS/STATUS (EXEMPLO) ---
class StatusPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        lbl = QLabel("Logs de Execução")
        lbl.setStyleSheet("font-size: 24px; color: #333; font-weight: bold;")
        layout.addWidget(lbl)
        
        # Um Card menor para logs
        log_card = QFrame()
        log_card.setStyleSheet(styles.CARD_STYLE)
        log_layout = QVBoxLayout(log_card)
        
        self.txt_log = QPlainTextEdit()
        self.txt_log.setPlaceholderText("Os logs do sistema aparecerão aqui...")
        self.txt_log.setStyleSheet("border: none; background: transparent;")
        
        log_layout.addWidget(self.txt_log)
        layout.addWidget(log_card)