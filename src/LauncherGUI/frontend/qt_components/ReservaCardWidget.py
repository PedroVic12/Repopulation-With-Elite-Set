import sys
import os
import subprocess
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, QFrame, 
                               QSpacerItem, QSizePolicy, QToolBar, QDockWidget, QListWidget)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QAction

# --- 1. O COMPONENTE VISUAL (O "MODAL" DA SUA IMAGEM) ---
class ReservaCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        # Estilização do Card (Borda arredondada, sombra leve, fundo branco)
        self.setObjectName("ReservaCard")
        self.setStyleSheet("""
            #ReservaCard {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
            }
            QLabel {
                color: #555555;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
        """)
        
        # Layout Principal do Card
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Texto Informativo
        lbl_texto = QLabel()
        lbl_texto.setAlignment(Qt.AlignCenter)
        lbl_texto.setWordWrap(True)
        # Usando HTML para formatar o negrito e o link
        lbl_texto.setText("""
            Enviamos um resumo de reserva para o seu endereço de e-mail<br>
            <b><span style='text-decoration: underline; color: #333;'>pedrovictor.veras@ons.org.br</span></b>.<br>
            Se você não receber o e-mail, por favor, verifique sua pasta de spam.
        """)
        layout.addWidget(lbl_texto)

        # Layout dos Botões Superiores (Lado a Lado)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        # Estilo CSS para os botões "Outline" (Borda azul)
        style_outline = """
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
            QPushButton:hover {
                background-color: #f0f8ff;
            }
        """

        self.btn_calendario = QPushButton("  ADICIONAR AO CALENDÁRIO")
        # Nota: Se tiver ícones .png, use self.btn_calendario.setIcon(QIcon("caminho.png"))
        self.btn_calendario.setStyleSheet(style_outline)
        self.btn_calendario.setCursor(Qt.PointingHandCursor)
        
        self.btn_alterar = QPushButton("  ALTERAR RESERVA")
        self.btn_alterar.setStyleSheet(style_outline)
        self.btn_alterar.setCursor(Qt.PointingHandCursor)

        btn_layout.addWidget(self.btn_calendario)
        btn_layout.addWidget(self.btn_alterar)
        layout.addLayout(btn_layout)

        # Botão Inferior (Cheio / Azul) - O QUE RODA O SCRIPT
        self.btn_voltar = QPushButton("VOLTAR AO SITE DE RESERVAS")
        self.btn_voltar.setCursor(Qt.PointingHandCursor)
        self.btn_voltar.setStyleSheet("""
            QPushButton {
                background-color: #0088cc;
                border: none;
                border-radius: 4px;
                color: white;
                font-weight: bold;
                padding: 15px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #006699;
            }
        """)
        # Conecta o clique à função de rodar o script
        self.btn_voltar.clicked.connect(self.rodar_script_automacao)
        layout.addWidget(self.btn_voltar)

    def rodar_script_automacao(self):
        """Função que roda o seu script Python usando subprocess"""
        print("Iniciando automação...")
        
        # CAMINHO DO SEU SCRIPT
        # Ajuste para onde está o seu arquivo .py de relatório
        script_path = "seu_script_relatorio.py" 
        python_exe = sys.executable # Usa o mesmo python que está rodando a app

        # Muda o texto do botão para dar feedback
        self.btn_voltar.setText("PROCESSANDO... AGUARDE")
        self.btn_voltar.setEnabled(False)
        self.btn_voltar.setStyleSheet("background-color: #666; color: white; padding: 15px; border-radius: 4px;")
        QApplication.processEvents() # Força a interface a atualizar visualmente

        try:
            # --- AQUI ESTÁ O COMANDO SUBPROCESS ---
            # O parâmetro 'cwd' define a pasta de execução, útil para scripts que geram arquivos locais
            processo = subprocess.run(
                [python_exe, script_path],
                capture_output=True,
                text=True,
                # shell=True # Descomente se precisar abrir console, mas evite se possível
            )

            if processo.returncode == 0:
                print("Sucesso!")
                print(processo.stdout)
                self.btn_voltar.setText("SUCESSO! (CLIQUE P/ VOLTAR)")
                self.btn_voltar.setStyleSheet("background-color: #28a745; color: white; padding: 15px; border-radius: 4px;")
            else:
                print("Erro no script:", processo.stderr)
                self.btn_voltar.setText("ERRO NA EXECUÇÃO")
                self.btn_voltar.setStyleSheet("background-color: #dc3545; color: white; padding: 15px; border-radius: 4px;")

        except Exception as e:
            print(f"Erro ao tentar rodar: {e}")
        
        finally:
            # Reabilita o botão após 3 segundos (apenas visual)
            # Na prática real, você usaria um QTimer
            self.btn_voltar.setEnabled(True)


# --- 2. A TELA PRINCIPAL (TOOLBELT + MENU LATERAL) ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Automação - ToolBelt")
        self.resize(1000, 700)
        self.setStyleSheet("background-color: #f4f4f4;") # Fundo cinza claro igual imagem

        # --- A. APP BAR (TOOLBAR SUPERIOR) ---
        self.toolbar = QToolBar("MyToolBelt")
        self.toolbar.setIconSize(QSize(32, 32))
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: white;
                border-bottom: 1px solid #ccc;
                padding: 10px;
            }
            QToolButton {
                color: #333;
                font-weight: bold;
            }
        """)
        self.addToolBar(self.toolbar)

        # Adicionando ações fictícias imitando a imagem do Excel Ribbon
        act_run = QAction("Run Python", self)
        self.toolbar.addAction(act_run)
        self.toolbar.addSeparator()
        act_template = QAction("Word Template", self)
        self.toolbar.addAction(act_template)
        act_pandas = QAction("Pandas DF", self)
        self.toolbar.addAction(act_pandas)

        # --- B. MENU LATERAL ---
        self.dock = QDockWidget("Navegação", self)
        self.dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.dock.setFeatures(QDockWidget.NoDockWidgetFeatures) # Não deixa fechar/flutuar
        
        self.menu_list = QListWidget()
        self.menu_list.addItems(["Dashboard", "Relatórios", "Configurações", "Ajuda"])
        self.menu_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: #2c3e50;
                color: white;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 15px;
                border-bottom: 1px solid #34495e;
            }
            QListWidget::item:selected {
                background-color: #0088cc;
            }
        """)
        self.dock.setWidget(self.menu_list)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock)

        # --- C. ÁREA CENTRAL (ONDE FICA O SEU MODAL) ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout central para centralizar o Card
        layout_central = QVBoxLayout(central_widget)
        layout_central.setAlignment(Qt.AlignCenter)

        # Adiciona o componente ReservaCard
        self.card = ReservaCard()
        # Define um tamanho fixo máximo para parecer um modal
        self.card.setFixedWidth(600) 
        # self.card.setFixedHeight(400) # Opcional, se quiser altura fixa
        
        layout_central.addWidget(self.card)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Fonte global para ficar bonito
    font = app.font()
    font.setFamily("Segoe UI")
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())