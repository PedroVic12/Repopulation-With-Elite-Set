import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                               QListWidget, QStackedWidget, QDockWidget)
from PySide6.QtCore import Qt
import styles
import frames  # Importa o arquivo onde estão suas páginas

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Automação Integrado")
        self.resize(1100, 700)
        self.setStyleSheet(f"background-color: {styles.BG_COLOR};")

        # Configuração do Layout Principal (Sidebar + Conteúdo)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- 1. MENU LATERAL (SIDEBAR) ---
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(250)
        self.sidebar.setStyleSheet(styles.SIDEBAR_STYLE)
        # Adicionando itens ao menu
        self.sidebar.addItem("Reserva & Ações")
        self.sidebar.addItem("Logs do Sistema")
        self.sidebar.addItem("Configurações")
        
        # Conecta o clique no menu à troca de página
        self.sidebar.currentRowChanged.connect(self.mudar_pagina)
        
        main_layout.addWidget(self.sidebar)

        # --- 2. ÁREA DE CONTEÚDO (STACKED WIDGET) ---
        # O QStackedWidget funciona como um baralho, mostra uma carta por vez
        self.content_area = QStackedWidget()
        
        # Instancia as páginas do arquivo frames.py
        self.page_reserva = frames.ReservaPage()  # Iframe 1
        self.page_status = frames.StatusPage()    # Iframe 2
        
        # Adiciona ao "baralho"
        self.content_area.addWidget(self.page_reserva) # Index 0
        self.content_area.addWidget(self.page_status)  # Index 1
        
        # Página vazia para Configurações (Index 2)
        self.content_area.addWidget(QWidget()) 
        
        main_layout.addWidget(self.content_area)

        # Seleciona o primeiro item ao iniciar
        self.sidebar.setCurrentRow(0)

    def mudar_pagina(self, index):
        # Troca o widget visível baseada no index do menu
        self.content_area.setCurrentIndex(index)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Define fonte padrão para o app todo
    font = app.font()
    font.setFamily("Segoe UI")
    app.setFont(font)

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())