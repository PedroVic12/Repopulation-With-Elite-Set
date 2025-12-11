# ///////////////////////////////////////////////////////////////
#
# BY: Pedro Victor Rodrigues Veras (based on Wanderson M. Pimenta)
# PROJECT MADE WITH: Qt Designer and PySide6
# V: 10.0.0 (Final Architecture)
#
# ///////////////////////////////////////////////////////////////

# IMPORT MODULES
import sys
import os 
import webbrowser
from functools import partial
import pandas as pd
import re
import fitz  # PyMuPDF

# IMPORT QT CORE
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QWidget, QFileDialog, QTextEdit, 
                               QTableWidget, QTableWidgetItem, QLabel, QTabWidget,
                               QGroupBox, QProgressBar, QMessageBox, QCheckBox,
                               QFrame, QStackedWidget, QLineEdit, QListWidget,
                               QListWidgetItem, QAbstractItemView, QSpacerItem, 
                               QSizePolicy, QScrollArea, QSplitter, QToolButton,
                               QMenu, QDialog, QDialogButtonBox, QFormLayout,
                               QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit,
                               QTimeEdit, QDateTimeEdit, QPlainTextEdit, QProgressDialog)
from PySide6.QtCore import QThread, Signal, Qt, QSize, QTimer, QDateTime, QDate, QTime
from PySide6.QtGui import QIcon, QFont, QPixmap, QPainter, QColor, QAction, QDesktopServices

# ===============================================================
# CLASSE: ProcessingThread (Model)
# LOCAL: models/processing_thread.py
# ===============================================================

class ProcessingThread(QThread):
    progress_signal = Signal(int)
    result_signal = Signal(pd.DataFrame)
    error_signal = Signal(str)
    page_count_signal = Signal(int)
    
    def __init__(self, pdf_path, script_type, process_options=None, page_range=None):
        super().__init__()
        self.pdf_path = pdf_path
        self.script_type = script_type
        self.process_options = process_options or {}
        self.page_range = page_range
    
    def run(self):
        try:
            # Extrai texto do PDF com intervalo específico
            doc = fitz.open(self.pdf_path)
            total_pages = len(doc)
            self.page_count_signal.emit(total_pages)
            
            full_text = ""
            
            # Define páginas para processar
            if self.page_range is None or not self.page_range:
                pages_to_process = range(total_pages)
            else:
                # Filtra páginas válidas (base 0)
                pages_to_process = [p for p in self.page_range if 0 <= p < total_pages]
                if not pages_to_process:
                    pages_to_process = range(total_pages)
            
            # Processa páginas selecionadas
            for i, page_num in enumerate(pages_to_process):
                page = doc.load_page(page_num)
                full_text += f"\n--- Página {page_num + 1} ---\n"
                full_text += page.get_text()
                progress = int((i + 1) / len(pages_to_process) * 50)
                self.progress_signal.emit(progress)
            
            doc.close()
            
            # Executa o script específico
            if self.script_type == "contingencias_duplas":
                result_df = self.process_contingencias_duplas(full_text)
            elif self.script_type == "outro_script":
                result_df = self.process_outro_script(full_text)
            else:
                result_df = pd.DataFrame()
            
            self.result_signal.emit(result_df)
            self.progress_signal.emit(100)
            
        except Exception as e:
            self.error_signal.emit(str(e))
    
    def process_contingencias_duplas(self, texto):
        dados = []
        volume_atual = None
        area_geoelerica_atual = None
        prazo_atual = None

        for linha in texto.strip().split('\n'):
            linha = linha.strip()
            if not linha or linha.startswith('--- Página'):
                continue
            
            # Identifica Volume (ex: "2.1 Volume 2 - Interligação Sul e Sudeste/Centro-Oeste")
            match_volume = re.match(r'(\d+\.\d+)\s+Volume\s+\d+\s*-\s*(.+)', linha)
            if match_volume:
                volume_atual = f"Volume {match_volume.group(1)}"
                area_geoelerica_atual = match_volume.group(2)
                continue
            
            # Identifica Prazo (Curto Prazo ou Médio Prazo)
            match_prazo = re.match(r'\d+\.\d+\.\d+\s+(Curto\s+Prazo|Médio\s+Prazo)', linha)
            if match_prazo:
                prazo_atual = match_prazo.group(1)
                continue
            
            # Identifica contingências (linhas que começam com • ou -)
            if linha.startswith('•') or linha.startswith('-'):
                contingencia = linha.replace('•', '').replace('-', '').strip()
                
                # VERIFICAÇÃO DAS CONTINGÊNCIAS DUPLAS
                if 'Contingência Dupla' in contingencia:
                    # Remove o texto "Contingência Dupla" e variações
                    contingencia_limpa = re.sub(r'Contingência Dupla (da|das)?\s*', '', contingencia).strip()
                    
                    # Verifica se tem múltiplas contingências separadas por " e "
                    if ' e ' in contingencia_limpa:
                        # Separa as contingências múltiplas
                        partes = contingencia_limpa.split(' e ')
                        
                        # Processa cada contingência individualmente
                        for i, parte in enumerate(partes):
                            parte = parte.strip()
                            
                            # Remove "LT" duplicado se necessário e padroniza
                            if not parte.startswith('LT ') and ' kV ' in parte:
                                parte = 'LT ' + parte
                            elif parte.startswith('LT ') and ' kV ' in parte:
                                # Já está formatado corretamente
                                pass
                            
                            # Determina se é Futura baseado no prazo
                            futura = "SIM" if prazo_atual and "Curto" in prazo_atual else "NÃO"
                            
                            dados.append({
                                'Volume': volume_atual or "Não identificado",
                                'Área Geoelétrica': area_geoelerica_atual or "Não identificado",
                                'Perda Dupla': parte,
                                'Prazo': prazo_atual or "Não identificado",
                                'Futura': futura,
                                'Contingência Dupla Mesma Linha': 'SIM'
                            })
                    else:
                        # É uma única contingência
                        if not contingencia_limpa.startswith('LT ') and ' kV ' in contingencia_limpa:
                            contingencia_limpa = 'LT ' + contingencia_limpa
                        
                        futura = "SIM" if prazo_atual and "Curto" in prazo_atual else "NÃO"
                        
                        dados.append({
                            'Volume': volume_atual or "Não identificado",
                            'Área Geoelétrica': area_geoelerica_atual or "Não identificado",
                            'Perda Dupla': contingencia_limpa,
                            'Prazo': prazo_atual or "Não identificado",
                            'Futura': futura,
                            'Contingência Dupla Mesma Linha': 'NÃO'
                        })
                else:
                    # Não é uma "Contingência Dupla", processa normalmente
                    if not contingencia.startswith('LT ') and ' kV ' in contingencia:
                        contingencia = 'LT ' + contingencia
                    
                    futura = "SIM" if prazo_atual and "Curto" in prazo_atual else "NÃO"
                    
                    dados.append({
                        'Volume': volume_atual or "Não identificado",
                        'Área Geoelétrica': area_geoelerica_atual or "Não identificado",
                        'Perda Dupla': contingencia,
                        'Prazo': prazo_atual or "Não identificado",
                        'Futura': futura,
                        'Contingência Dupla Mesma Linha': 'NÃO'
                    })

        # Cria DataFrame
        df = pd.DataFrame(dados)
        
        # Reorganiza as colunas
        colunas = ['Volume', 'Área Geoelétrica', 'Perda Dupla', 'Prazo', 'Futura', 'Contingência Dupla Mesma Linha']
        if not df.empty:
            df = df[colunas]
        
        return df

    def process_outro_script(self, texto):
        return pd.DataFrame({"Exemplo": ["Script 2 em desenvolvimento"]})

# ===============================================================
# CLASSE: RPAWidget (iFrame)
# LOCAL: gui/iframes/rpa_widget.py
# ===============================================================

class RPAWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        self.current_pdf_path = None
        self.current_df = None
        self.selected_pages = []
        self.total_pages = 0
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        # Layout principal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Container principal
        self.main_container = QFrame()
        self.main_container.setObjectName("main_container")
        self.main_container.setStyleSheet("""
            #main_container {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2c3e50, stop:1 #34495e);
                border-radius: 10px;
                margin: 5px;
            }
        """)
        main_layout.addWidget(self.main_container)
        
        # Layout do container
        container_layout = QHBoxLayout(self.main_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Sidebar esquerda
        self.sidebar = self.create_sidebar()
        container_layout.addWidget(self.sidebar)
        
        # Separador
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.sidebar)
        
        # Área principal
        self.main_content = QFrame()
        self.main_content.setObjectName("main_content")
        self.main_content.setStyleSheet("""
            #main_content {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ecf0f1, stop:1 #bdc3c7);
                border-radius: 10px;
                margin: 5px;
            }
        """)
        splitter.addWidget(self.main_content)
        splitter.setSizes([300, 700])
        
        container_layout.addWidget(splitter)
        
        # Layout da área principal
        content_layout = QVBoxLayout(self.main_content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        
        # Cabeçalho
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🤖 FERRAMENTA RPA - ANÁLISE DE DOCUMENTOS")
        title_label.setObjectName("title_label")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_font.setWeight(75)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; padding: 10px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Botão de ajuda
        help_btn = QPushButton("❓ Ajuda")
        help_btn.setFixedSize(80, 35)
        help_btn.clicked.connect(self.show_help)
        header_layout.addWidget(help_btn)
        
        content_layout.addLayout(header_layout)
        
        # Controles de página
        page_controls_group = QGroupBox("📄 Controle de Páginas do PDF")
        page_controls_layout = QVBoxLayout(page_controls_group)
        
        page_input_layout = QHBoxLayout()
        self.page_input = QLineEdit()
        self.page_input.setPlaceholderText("Ex: 1,3,5-10 ou deixe vazio para todas as páginas")
        self.page_input.setStyleSheet("QLineEdit { padding: 8px; border: 2px solid #3498db; border-radius: 5px; }")
        
        self.btn_select_pages = QPushButton("🎯 Definir Páginas")
        self.btn_select_pages.setFixedSize(120, 35)
        self.btn_select_pages.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #2471a3);
            }
        """)
        
        page_input_layout.addWidget(QLabel("Intervalo de páginas:"))
        page_input_layout.addWidget(self.page_input)
        page_input_layout.addWidget(self.btn_select_pages)
        page_input_layout.addStretch()
        
        page_controls_layout.addLayout(page_input_layout)
        
        # Lista de páginas selecionadas
        pages_list_layout = QHBoxLayout()
        self.pages_list = QListWidget()
        self.pages_list.setMaximumHeight(80)
        self.pages_list.setSelectionMode(QAbstractItemView.MultiSelection)
        
        self.btn_clear_pages = QPushButton("🗑️ Limpar")
        self.btn_clear_pages.setFixedSize(80, 35)
        self.btn_clear_pages.clicked.connect(self.clear_pages)
        
        pages_list_layout.addWidget(QLabel("Páginas selecionadas:"))
        pages_list_layout.addWidget(self.pages_list)
        pages_list_layout.addWidget(self.btn_clear_pages)
        
        page_controls_layout.addLayout(pages_list_layout)
        content_layout.addWidget(page_controls_group)
        
        # Área com abas
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background: white;
            }
            QTabBar::tab {
                background: #ecf0f1;
                border: 1px solid #bdc3c7;
                padding: 8px 15px;
                margin: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #2980b9;
                color: white;
            }
        """)
        content_layout.addWidget(self.tab_widget)
        
        # Aba do PDF
        self.pdf_tab = QWidget()
        pdf_layout = QVBoxLayout(self.pdf_tab)
        
        pdf_header_layout = QHBoxLayout()
        pdf_header_layout.addWidget(QLabel("📖 Visualização do PDF:"))
        
        self.pdf_info_label = QLabel("Nenhum PDF carregado")
        self.pdf_info_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        pdf_header_layout.addWidget(self.pdf_info_label)
        pdf_header_layout.addStretch()
        
        pdf_layout.addLayout(pdf_header_layout)
        
        self.pdf_text = QTextEdit()
        self.pdf_text.setPlaceholderText("O conteúdo do PDF aparecerá aqui após o carregamento...")
        self.pdf_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
                background: #f8f9fa;
                font-family: 'Courier New';
            }
        """)
        pdf_layout.addWidget(self.pdf_text)
        self.tab_widget.addTab(self.pdf_tab, "📄 PDF Original")
        
        # Aba de resultados
        self.results_tab = QWidget()
        results_layout = QVBoxLayout(self.results_tab)
        
        results_header_layout = QHBoxLayout()
        results_header_layout.addWidget(QLabel("📊 Resultados do Processamento:"))
        
        self.results_info_label = QLabel("Nenhum resultado disponível")
        self.results_info_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        results_header_layout.addWidget(self.results_info_label)
        results_header_layout.addStretch()
        
        results_layout.addLayout(results_header_layout)
        
        self.results_table = QTableWidget()
        self.results_table.setStyleSheet("""
            QTableWidget {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background: white;
                gridline-color: #bdc3c7;
            }
            QHeaderView::section {
                background: #34495e;
                color: white;
                padding: 5px;
                border: 1px solid #2c3e50;
                font-weight: bold;
            }
        """)
        results_layout.addWidget(self.results_table)
        self.tab_widget.addTab(self.results_tab, "📊 Resultados")
        
        # Barra de progresso e status
        status_layout = QHBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                background: #ecf0f1;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #2ecc71);
                border-radius: 3px;
            }
        """)
        status_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Pronto")
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold; padding: 5px;")
        status_layout.addWidget(self.status_label)
        
        content_layout.addLayout(status_layout)
        
    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(300)
        sidebar.setStyleSheet("""
            #sidebar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2c3e50, stop:1 #34495e);
                border-right: 2px solid #1abc9c;
                border-top-left-radius: 10px;
                border-bottom-left-radius: 10px;
            }
            QGroupBox {
                color: white;
                font-weight: bold;
                border: 2px solid #1abc9c;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #1abc9c;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Logo/Header
        header_label = QLabel("🛠️ FERRAMENTAS RPA")
        header_label.setStyleSheet("""
            color: #1abc9c;
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
            background: rgba(255,255,255,0.1);
            border-radius: 5px;
            text-align: center;
        """)
        layout.addWidget(header_label)
        
        # Grupo de upload
        upload_group = QGroupBox("📁 Upload de Arquivos")
        upload_layout = QVBoxLayout(upload_group)
        
        self.btn_load_pdf = QPushButton("📄 Carregar PDF")
        self.btn_load_pdf.setObjectName("btn_load_pdf")
        self.btn_load_pdf.setStyleSheet(self.get_button_style("#e74c3c", "#c0392b"))
        upload_layout.addWidget(self.btn_load_pdf)
        
        self.btn_load_excel = QPushButton("📊 Carregar Excel")
        self.btn_load_excel.setObjectName("btn_load_excel")
        self.btn_load_excel.setStyleSheet(self.get_button_style("#3498db", "#2980b9"))
        upload_layout.addWidget(self.btn_load_excel)
        
        self.file_label = QLabel("Nenhum arquivo carregado")
        self.file_label.setObjectName("file_label")
        self.file_label.setWordWrap(True)
        self.file_label.setStyleSheet("""
            color: #ecf0f1;
            background: rgba(255,255,255,0.1);
            padding: 8px;
            border-radius: 5px;
            font-size: 12px;
        """)
        upload_layout.addWidget(self.file_label)
        
        layout.addWidget(upload_group)
        
        # Opções de processamento
        options_group = QGroupBox("⚙️ Opções de Processamento")
        options_layout = QVBoxLayout(options_group)
        
        self.cb_separar_duplas = QCheckBox("🔀 Separar Contingências Duplas")
        self.cb_separar_duplas.setChecked(True)
        self.cb_separar_duplas.setStyleSheet("color: white;")
        options_layout.addWidget(self.cb_separar_duplas)
        
        self.cb_adicionar_lt = QCheckBox("🏷️ Adicionar 'LT' automaticamente")
        self.cb_adicionar_lt.setChecked(True)
        self.cb_adicionar_lt.setStyleSheet("color: white;")
        options_layout.addWidget(self.cb_adicionar_lt)
        
        layout.addWidget(options_group)
        
        # Scripts RPA
        scripts_group = QGroupBox("🤖 Scripts RPA")
        scripts_layout = QVBoxLayout(scripts_group)
        
        self.btn_contingencias = QPushButton("⚡ Análise Contingências Duplas")
        self.btn_contingencias.setObjectName("btn_contingencias")
        self.btn_contingencias.setStyleSheet(self.get_button_style("#9b59b6", "#8e44ad"))
        scripts_layout.addWidget(self.btn_contingencias)
        
        self.btn_script2 = QPushButton("🛠️ Script 2 - Em Desenvolvimento")
        self.btn_script2.setStyleSheet(self.get_button_style("#95a5a6", "#7f8c8d"))
        scripts_layout.addWidget(self.btn_script2)
        
        layout.addWidget(scripts_group)
        
        # Exportação
        export_group = QGroupBox("📤 Exportação")
        export_layout = QVBoxLayout(export_group)
        
        self.btn_export_excel = QPushButton("💾 Exportar para Excel")
        self.btn_export_excel.setObjectName("btn_export_excel")
        self.btn_export_excel.setStyleSheet(self.get_button_style("#27ae60", "#229954"))
        export_layout.addWidget(self.btn_export_excel)
        
        self.btn_export_word = QPushButton("📝 Exportar para Word")
        self.btn_export_word.setStyleSheet(self.get_button_style("#f39c12", "#e67e22"))
        export_layout.addWidget(self.btn_export_word)
        
        layout.addWidget(export_group)
        
        # Espaço flexível
        layout.addStretch()
        
        # Footer
        footer_label = QLabel("v2.0.0 - Sistema RPA")
        footer_label.setStyleSheet("""
            color: #7f8c8d;
            font-size: 10px;
            text-align: center;
            padding: 5px;
        """)
        layout.addWidget(footer_label)
        
        return sidebar
        
    def get_button_style(self, color1, color2):
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color1}, stop:1 {color2});
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
                min-height: 30px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color2}, stop:1 {color1});
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2c3e50, stop:1 #34495e);
            }}
            QPushButton:disabled {{
                background: #95a5a6;
                color: #7f8c8d;
            }}
        """
        
    def setup_connections(self):
        self.btn_load_pdf.clicked.connect(self.load_pdf)
        self.btn_load_excel.clicked.connect(self.load_excel)
        self.btn_select_pages.clicked.connect(self.select_pages)
        self.btn_contingencias.clicked.connect(lambda: self.run_script("contingencias_duplas"))
        self.btn_export_excel.clicked.connect(self.export_to_excel)
        self.btn_export_word.clicked.connect(self.export_to_word)
        
    def select_pages(self):
        """Processa o input de páginas do usuário"""
        input_text = self.page_input.text().strip()
        self.selected_pages = []
        
        if not input_text:
            # Se vazio, processa todas as páginas
            self.pages_list.clear()
            self.pages_list.addItem("Todas as páginas (1-" + str(self.total_pages) + ")")
            self.status_label.setText("✅ Todas as páginas selecionadas")
            self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            return
        
        try:
            # Processa diferentes formatos: "1,3,5-10", "1-5", "1,2,3"
            pages = []
            parts = input_text.split(',')
            
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # É um intervalo
                    range_parts = part.split('-')
                    if len(range_parts) == 2:
                        start, end = map(int, range_parts)
                        # Ajusta para base 0 e garante que esteja dentro dos limites
                        start = max(1, start)
                        end = min(self.total_pages, end)
                        pages.extend(range(start-1, end))
                else:
                    # É uma página individual
                    page_num = int(part)
                    if 1 <= page_num <= self.total_pages:
                        pages.append(page_num - 1)
            
            self.selected_pages = sorted(set(pages))  # Remove duplicatas e ordena
            
            # Atualiza a lista visual
            self.pages_list.clear()
            if self.selected_pages:
                for page in self.selected_pages:
                    self.pages_list.addItem(f"Página {page + 1}")
                self.status_label.setText(f"✅ {len(self.selected_pages)} páginas selecionadas")
                self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            else:
                self.pages_list.addItem("Todas as páginas (1-" + str(self.total_pages) + ")")
                self.status_label.setText("⚠️ Nenhuma página válida, usando todas")
                self.status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
                
        except ValueError as e:
            QMessageBox.warning(self, "Erro", f"Formato inválido. Use: 1,3,5-10\nErro: {str(e)}")
            self.status_label.setText("❌ Erro no formato das páginas")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
    
    def clear_pages(self):
        """Limpa a seleção de páginas"""
        self.page_input.clear()
        self.pages_list.clear()
        self.selected_pages = []
        self.pages_list.addItem("Todas as páginas (1-" + str(self.total_pages) + ")")
        self.status_label.setText("✅ Seleção de páginas limpa")
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
    
    def load_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar PDF", "", "PDF Files (*.pdf)")
        
        if file_path:
            self.current_pdf_path = file_path
            filename = file_path.split('/')[-1]
            self.file_label.setText(f"📄 {filename}")
            
            try:
                # Mostra progresso de carregamento
                self.progress_bar.setVisible(True)
                self.status_label.setText("📥 Carregando PDF...")
                self.status_label.setStyleSheet("color: #3498db; font-weight: bold;")
                
                doc = fitz.open(file_path)
                self.total_pages = len(doc)
                full_text = f"=== ARQUIVO: {filename} ===\n"
                full_text += f"=== TOTAL DE PÁGINAS: {self.total_pages} ===\n\n"
                
                # Carrega apenas as primeiras páginas para preview
                preview_pages = min(5, self.total_pages)
                for page_num in range(preview_pages):
                    page = doc.load_page(page_num)
                    full_text += f"\n--- Página {page_num + 1} ---\n"
                    full_text += page.get_text()
                    self.progress_bar.setValue(int((page_num + 1) / preview_pages * 100))
                
                doc.close()
                
                self.pdf_text.setPlainText(full_text)
                self.tab_widget.setCurrentIndex(0)
                
                # Atualiza informações
                self.pdf_info_label.setText(f"{self.total_pages} páginas carregadas")
                
                # Limpa seleção anterior de páginas
                self.clear_pages()
                
                self.progress_bar.setVisible(False)
                self.status_label.setText("✅ PDF carregado com sucesso")
                self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                
            except Exception as e:
                self.progress_bar.setVisible(False)
                QMessageBox.critical(self, "Erro", f"Erro ao ler PDF: {str(e)}")
                self.status_label.setText("❌ Erro ao carregar PDF")
                self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
    
    def load_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Excel", "", "Excel Files (*.xlsx *.xls)")
        
        if file_path:
            filename = file_path.split('/')[-1]
            self.file_label.setText(f"📊 {filename}")
            self.status_label.setText("✅ Excel carregado (funcionalidade em desenvolvimento)")
            self.status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
    
    def run_script(self, script_type):
        if not self.current_pdf_path:
            QMessageBox.warning(self, "Aviso", "Por favor, carregue um PDF primeiro.")
            return
        
        self.progress_bar.setVisible(True)
        self.status_label.setText("🔄 Processando PDF...")
        self.status_label.setStyleSheet("color: #3498db; font-weight: bold;")
        
        process_options = {
            'separar_duplas': self.cb_separar_duplas.isChecked(),
            'adicionar_lt': self.cb_adicionar_lt.isChecked()
        }
        
        # Usa páginas selecionadas ou None para todas
        page_range = self.selected_pages if self.selected_pages else None
        
        self.thread = ProcessingThread(self.current_pdf_path, script_type, process_options, page_range)
        self.thread.progress_signal.connect(self.update_progress)
        self.thread.result_signal.connect(self.show_results)
        self.thread.error_signal.connect(self.show_error)
        self.thread.page_count_signal.connect(self.update_page_count)
        self.thread.start()
    
    def update_page_count(self, count):
        self.total_pages = count
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def show_results(self, df):
        self.current_df = df
        self.progress_bar.setVisible(False)
        
        if df.empty:
            self.status_label.setText("⚠️ Nenhum dado encontrado")
            self.status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
            QMessageBox.information(self, "Informação", "Nenhuma contingência foi encontrada no PDF.")
            return
        
        # Preenche tabela com resultados
        self.results_table.setRowCount(df.shape[0])
        self.results_table.setColumnCount(df.shape[1])
        self.results_table.setHorizontalHeaderLabels(df.columns.tolist())
        
        # Ajusta largura das colunas
        header = self.results_table.horizontalHeader()
        for i in range(df.shape[1]):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                item = QTableWidgetItem(str(df.iat[row, col]))
                
                # Colorização baseada no conteúdo
                if col == 4:  # Coluna Futura
                    if df.iat[row, col] == "SIM":
                        item.setBackground(QColor(39, 174, 96, 100))  # Verde
                    else:
                        item.setBackground(QColor(231, 76, 60, 100))  # Vermelho
                elif col == 5:  # Coluna Contingência Dupla Mesma Linha
                    if df.iat[row, col] == "SIM":
                        item.setBackground(QColor(155, 89, 182, 100))  # Roxo
                
                self.results_table.setItem(row, col, item)
        
        self.tab_widget.setCurrentIndex(1)
        self.results_info_label.setText(f"{len(df)} registros processados")
        self.status_label.setText(f"✅ Processamento concluído - {len(df)} registros")
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        
        QMessageBox.information(self, "Sucesso", f"Processamento concluído!\n{len(df)} registros encontrados.")
    
    def show_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.status_label.setText("❌ Erro no processamento")
        self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        QMessageBox.critical(self, "Erro", f"Erro no processamento:\n{error_msg}")
    
    def export_to_excel(self):
        if self.current_df is not None and not self.current_df.empty:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Salvar Excel", "contingencias_duplas.xlsx", "Excel Files (*.xlsx)")
            
            if file_path:
                try:
                    self.current_df.to_excel(file_path, index=False)
                    QMessageBox.information(self, "Sucesso", f"Arquivo salvo em:\n{file_path}")
                    self.status_label.setText("💾 Arquivo Excel exportado")
                    self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                except Exception as e:
                    QMessageBox.critical(self, "Erro", f"Erro ao salvar:\n{str(e)}")
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum dado para exportar.")
    
    def export_to_word(self):
        QMessageBox.information(self, "Info", "Funcionalidade em desenvolvimento.")
        self.status_label.setText("🛠️ Exportação Word em desenvolvimento")
        self.status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
    
    def show_help(self):
        help_text = """
        <h2>🤖 Ajuda - Ferramenta RPA</h2>
        
        <h3>📁 Upload de Arquivos:</h3>
        <ul>
        <li><b>Carregar PDF:</b> Seleciona um arquivo PDF para análise</li>
        <li><b>Carregar Excel:</b> Funcionalidade em desenvolvimento</li>
        </ul>
        
        <h3>📄 Controle de Páginas:</h3>
        <ul>
        <li><b>Formato aceito:</b> 1,3,5-10 (páginas 1, 3 e do 5 ao 10)</li>
        <li><b>Deixe vazio</b> para processar todas as páginas</li>
        </ul>
        
        <h3>⚡ Scripts RPA:</h3>
        <ul>
        <li><b>Análise Contingências Duplas:</b> Extrai dados de contingências duplas do PDF</li>
        <li>Identifica automaticamente volumes, áreas geoelétricas e prazos</li>
        </ul>
        
        <h3>📤 Exportação:</h3>
        <ul>
        <li><b>Exportar para Excel:</b> Salva os resultados em formato Excel</li>
        <li><b>Exportar para Word:</b> Em desenvolvimento</li>
        </ul>
        """
        
        msg = QMessageBox()
        msg.setWindowTitle("Ajuda - Ferramenta RPA")
        msg.setTextFormat(Qt.RichText)
        msg.setText(help_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec()

# ===============================================================
# CLASSE: NavigationMenu (Side Menu)
# LOCAL: gui/side_menus/navigation_menu.py
# ===============================================================

class NavigationMenu(QWidget):
    dashboard_requested = Signal()
    pomodoro_requested = Signal()
    checklist_requested = Signal()
    settings_requested = Signal()
    rpa_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Botão Dashboard
        self.btn_dashboard = QPushButton("📊 Dashboard")
        self.btn_dashboard.clicked.connect(self.dashboard_requested.emit)
        self.style_nav_button(self.btn_dashboard)
        layout.addWidget(self.btn_dashboard)
        
        # Botão Pomodoro
        self.btn_pomodoro = QPushButton("⏱️ Pomodoro")
        self.btn_pomodoro.clicked.connect(self.pomodoro_requested.emit)
        self.style_nav_button(self.btn_pomodoro)
        layout.addWidget(self.btn_pomodoro)
        
        # Botão Checklist
        self.btn_checklist = QPushButton("✅ Checklist")
        self.btn_checklist.clicked.connect(self.checklist_requested.emit)
        self.style_nav_button(self.btn_checklist)
        layout.addWidget(self.btn_checklist)
        
        # Botão RPA (NOVO)
        self.btn_rpa = QPushButton("🤖 Ferramenta RPA")
        self.btn_rpa.clicked.connect(self.rpa_requested.emit)
        self.style_nav_button(self.btn_rpa)
        layout.addWidget(self.btn_rpa)
        
        # Botão Settings
        self.btn_settings = QPushButton("⚙️ Configurações")
        self.btn_settings.clicked.connect(self.settings_requested.emit)
        self.style_nav_button(self.btn_settings)
        layout.addWidget(self.btn_settings)
        
        layout.addStretch()
    
    def style_nav_button(self, button):
        button.setStyleSheet("""
            QPushButton {
                background: #34495e;
                color: #ecf0f1;
                border: none;
                padding: 15px;
                text-align: left;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1abc9c;
                color: #2c3e50;
            }
            QPushButton:pressed {
                background: #16a085;
            }
        """)

# ===============================================================
# CLASSE: DefaultSideMenu (Side Menu)
# LOCAL: gui/side_menus/default_sidemenu.py
# ===============================================================

class DefaultSideMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Menu Principal")
        title.setStyleSheet("color: #1abc9c; font-weight: bold; font-size: 16px;")
        layout.addWidget(title)
        
        info = QLabel("Selecione uma função no menu acima para começar.")
        info.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        layout.addStretch()

# ===============================================================
# CLASSE: RPASideMenu (Side Menu)
# LOCAL: gui/side_menus/rpa_sidemenu.py
# ===============================================================

class RPASideMenu(QWidget):
    process_pdf = Signal()
    export_data = Signal()
    open_settings = Signal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        title = QLabel("Ferramentas RPA")
        title.setStyleSheet("color: #1abc9c; font-weight: bold; font-size: 16px;")
        layout.addWidget(title)
        
        # Ações rápidas
        self.btn_quick_process = QPushButton("⚡ Processar PDF")
        self.btn_quick_process.clicked.connect(self.process_pdf.emit)
        self.btn_quick_process.setStyleSheet("""
            QPushButton {
                background: #9b59b6;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #8e44ad;
            }
        """)
        layout.addWidget(self.btn_quick_process)
        
        self.btn_batch_process = QPushButton("🔄 Processamento em Lote")
        self.btn_batch_process.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        layout.addWidget(self.btn_batch_process)
        
        self.btn_export = QPushButton("📤 Exportar Dados")
        self.btn_export.clicked.connect(self.export_data.emit)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #229954;
            }
        """)
        layout.addWidget(self.btn_export)
        
        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(line)
        
        # Configurações
        self.btn_settings = QPushButton("⚙️ Configurações RPA")
        self.btn_settings.clicked.connect(self.open_settings.emit)
        self.btn_settings.setStyleSheet("""
            QPushButton {
                background: #95a5a6;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #7f8c8d;
            }
        """)
        layout.addWidget(self.btn_settings)
        
        layout.addStretch()
        
        # Status
        status_label = QLabel("Sistema RPA Online")
        status_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 10px;")
        layout.addWidget(status_label)

# ===============================================================
# CLASSE: DashboardWidget (iFrame)
# LOCAL: gui/iframes/dashboard_widget.py
# ===============================================================

class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("📊 Dashboard Principal")
        title.setStyleSheet("color: #2c3e50; font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        # Cards de status
        cards_layout = QHBoxLayout()
        
        # Card 1
        card1 = QFrame()
        card1.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 10px;
                padding: 15px;
            }
        """)
        card1_layout = QVBoxLayout(card1)
        card1_layout.addWidget(QLabel("🤖 Processos RPA"))
        card1_layout.addWidget(QLabel("5 executados"))
        card1_layout.addWidget(QLabel("3 em fila"))
        cards_layout.addWidget(card1)
        
        # Card 2
        card2 = QFrame()
        card2.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2ecc71, stop:1 #27ae60);
                border-radius: 10px;
                padding: 15px;
            }
        """)
        card2_layout = QVBoxLayout(card2)
        card2_layout.addWidget(QLabel("📊 Documentos"))
        card2_layout.addWidget(QLabel("12 processados"))
        card2_layout.addWidget(QLabel("98% sucesso"))
        cards_layout.addWidget(card2)
        
        layout.addLayout(cards_layout)
        layout.addStretch()

# ===============================================================
# CLASSE: UI_MainWindow (Main Window UI)
# LOCAL: gui/windows/main_window/ui_main_window.py
# ===============================================================

class UI_MainWindow(object):
    def setup_ui(self, parent):
        if not parent.objectName():
            parent.setObjectName("MainWindow")
        
        parent.resize(1400, 900)
        parent.setMinimumSize(1200, 700)
        
        # Apply dark theme
        self.apply_dark_theme(parent)
        
        # Central Widget
        self.central_widget = QWidget()
        self.central_widget.setObjectName("central_widget")
        
        # Main Layout
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Left Menu
        self.left_menu = QFrame()
        self.left_menu.setObjectName("left_menu")
        self.left_menu.setMinimumWidth(250)
        self.left_menu.setMaximumWidth(250)
        
        # Left Menu Layout
        self.left_menu_layout = QVBoxLayout(self.left_menu)
        self.left_menu_layout.setContentsMargins(0, 0, 0, 0)
        self.left_menu_layout.setSpacing(0)
        
        # Toggle Button
        self.toggle_button = QPushButton("☰")
        self.toggle_button.setObjectName("toggle_button")
        self.toggle_button.setMaximumHeight(45)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background: #1abc9c;
                color: white;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #16a085;
            }
        """)
        
        # Left Menu Frame
        self.left_menu_frame = QFrame()
        self.left_menu_frame.setObjectName("left_menu_frame")
        
        # Content
        self.content = QFrame()
        self.content.setObjectName("content")
        
        # Content Layout
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Top Bar
        self.top_bar = QFrame()
        self.top_bar.setObjectName("top_bar")
        self.top_bar.setMinimumHeight(50)
        self.top_bar.setMaximumHeight(50)
        
        # Top Bar Layout
        self.top_bar_layout = QHBoxLayout(self.top_bar)
        self.top_bar_layout.setContentsMargins(15, 0, 15, 0)
        
        # Top Left Label
        self.top_label_left = QLabel("Sistema RPA Integrado v2.0")
        self.top_label_left.setStyleSheet("color: #1abc9c; font-weight: bold; font-size: 16px;")
        
        # Top Spacer
        self.top_spacer = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # Top Right Label
        self.top_label_right = QLabel(QDateTime.currentDateTime().toString("dd/MM/yyyy hh:mm"))
        self.top_label_right.setStyleSheet("color: #7f8c8d;")
        
        # Add to Top Bar Layout
        self.top_bar_layout.addWidget(self.top_label_left)
        self.top_bar_layout.addItem(self.top_spacer)
        self.top_bar_layout.addWidget(self.top_label_right)
        
        # Application Pages
        self.tabs = QTabWidget()
        self.tabs.setObjectName("tabs")
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        
        # Add to Content Layout
        self.content_layout.addWidget(self.top_bar)
        self.content_layout.addWidget(self.tabs)
        
        # Add to Left Menu Layout
        self.left_menu_layout.addWidget(self.toggle_button)
        self.left_menu_layout.addWidget(self.left_menu_frame)
        
        # Add to Main Layout
        self.main_layout.addWidget(self.left_menu)
        self.main_layout.addWidget(self.content)
        
        # Set Central Widget
        parent.setCentralWidget(self.central_widget)
        
        # Setup timer for clock update
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self.top_label_right.setText(QDateTime.currentDateTime().toString("dd/MM/yyyy hh:mm")))
        self.timer.start(1000)
    
    def apply_dark_theme(self, parent):
        parent.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2c3e50, stop:1 #34495e);
            }
            #central_widget {
                background: transparent;
            }
            #left_menu {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2c3e50, stop:1 #34495e);
                border-right: 2px solid #1abc9c;
            }
            #content {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ecf0f1, stop:1 #bdc3c7);
            }
            #top_bar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #34495e, stop:1 #2c3e50);
                border-bottom: 2px solid #1abc9c;
            }
            #left_menu_frame {
                background: transparent;
            }
        """)

# ===============================================================
# CLASSE: MainWindow (Controller)
# LOCAL: main.py (principal)
# ===============================================================

class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app 

        # --- DICTIONARIES TO MANAGE DYNAMIC WIDGETS ---
        self.open_tabs = {}
        self.side_menus = {}
        self.tab_to_side_menu_map = {}

        # --- SETUP MAIN WINDOW AND UI ---
        self.ui = UI_MainWindow()
        self.ui.setup_ui(self)

        # --- SETUP DYNAMIC UI MODULES ---
        self.navigation_menu = NavigationMenu()
        self.ui.left_menu_layout.insertWidget(0, self.navigation_menu)

        self.side_menu_stack = QStackedWidget()
        
        # Side menus
        self.default_side_menu = DefaultSideMenu()
        self.rpa_side_menu = RPASideMenu()
        
        self.side_menus['default'] = self.default_side_menu
        self.side_menus['rpa'] = self.rpa_side_menu
        
        self.side_menu_stack.addWidget(self.default_side_menu)
        self.side_menu_stack.addWidget(self.rpa_side_menu)
        
        self.ui.left_menu_layout.insertWidget(1, self.side_menu_stack)

        self._setup_appbar_links()
        
        # --- CONNECT SIGNALS ---
        self.connect_signals()

        # --- OPEN INITIAL TAB ---
        self.open_dashboard_tab()

        # --- SHOW APP ---
        self.showMaximized()

    def _setup_appbar_links(self):
        # Configura links da barra superior (se necessário)
        pass

    def connect_signals(self):
        # Main Navigation
        self.navigation_menu.dashboard_requested.connect(self.open_dashboard_tab)
        self.navigation_menu.pomodoro_requested.connect(self.open_pomodoro_tab)
        self.navigation_menu.checklist_requested.connect(self.open_checklist_tab)
        self.navigation_menu.settings_requested.connect(self.open_settings_tab)
        self.navigation_menu.rpa_requested.connect(self.open_rpa_tab)
        
        # RPA Side Menu signals
        self.rpa_side_menu.process_pdf.connect(self.on_rpa_process_pdf)
        self.rpa_side_menu.export_data.connect(self.on_rpa_export_data)
        self.rpa_side_menu.open_settings.connect(self.on_rpa_settings)
        
        # Other UI
        self.ui.toggle_button.clicked.connect(self.toggle_button)
        self.ui.tabs.currentChanged.connect(self.on_tab_changed)
        self.ui.tabs.tabCloseRequested.connect(self.close_tab)

    def toggle_button(self):
        # Implementar toggle do menu lateral
        current_width = self.ui.left_menu.width()
        if current_width == 250:
            self.ui.left_menu.setMaximumWidth(50)
            self.ui.left_menu.setMinimumWidth(50)
        else:
            self.ui.left_menu.setMaximumWidth(250)
            self.ui.left_menu.setMinimumWidth(250)

    def open_dashboard_tab(self):
        self._open_tab(DashboardWidget, "📊 Dashboard", "default")  # CORREÇÃO: Passar a classe, não a instância

    def open_pomodoro_tab(self):
        # Implementar abas futuras
        pass

    def open_checklist_tab(self):
        # Implementar abas futuras
        pass

    def open_settings_tab(self):
        # Implementar abas futuras
        pass

    def open_rpa_tab(self):
        """Abre a aba da ferramenta RPA"""
        # Verifica se já está aberta
        for tab_index in range(self.ui.tabs.count()):
            tab_widget = self.ui.tabs.widget(tab_index)
            if isinstance(tab_widget, RPAWidget):
                self.ui.tabs.setCurrentIndex(tab_index)
                return

        # Cria nova instância
        rpa_widget = RPAWidget()
        
        # Adiciona à aba
        tab_index = self.ui.tabs.addTab(rpa_widget, "🤖 Ferramenta RPA")
        self.ui.tabs.setCurrentIndex(tab_index)
        
        # Mapeia para o side menu RPA
        self.tab_to_side_menu_map[tab_index] = 'rpa'
        self.open_tabs[tab_index] = rpa_widget
        
        # Atualiza side menu
        self.side_menu_stack.setCurrentWidget(self.rpa_side_menu)

    def on_rpa_process_pdf(self):
        """Processa PDF na aba RPA ativa"""
        current_tab = self.ui.tabs.currentWidget()
        if isinstance(current_tab, RPAWidget):
            current_tab.run_script("contingencias_duplas")

    def on_rpa_export_data(self):
        """Exporta dados da aba RPA ativa"""
        current_tab = self.ui.tabs.currentWidget()
        if isinstance(current_tab, RPAWidget):
            current_tab.export_to_excel()

    def on_rpa_settings(self):
        """Abre configurações da RPA"""
        QMessageBox.information(self, "Configurações RPA", "Configurações da ferramenta RPA")

    def on_tab_changed(self, index):
        """Atualiza side menu quando a aba muda"""
        if index in self.tab_to_side_menu_map:
            menu_name = self.tab_to_side_menu_map[index]
            self.side_menu_stack.setCurrentWidget(self.side_menus[menu_name])
        else:
            self.side_menu_stack.setCurrentWidget(self.default_side_menu)

    def close_tab(self, index):
        """Fecha aba e remove dos mapeamentos"""
        if index in self.tab_to_side_menu_map:
            del self.tab_to_side_menu_map[index]
        if index in self.open_tabs:
            del self.open_tabs[index]
        
        self.ui.tabs.removeTab(index)

    def _open_tab(self, widget_class, title, side_menu_key):
        """Abre uma aba genérica"""
        # Verifica se já está aberta
        for tab_index in range(self.ui.tabs.count()):
            tab_widget = self.ui.tabs.widget(tab_index)
            if isinstance(tab_widget, widget_class):  # CORREÇÃO: Usar isinstance em vez de type()
                self.ui.tabs.setCurrentIndex(tab_index)
                return

        # Cria nova instância
        new_widget = widget_class()  # CORREÇÃO: Agora widget_class é uma classe, podemos instanciar
        
        # Adiciona à aba
        tab_index = self.ui.tabs.addTab(new_widget, title)
        self.ui.tabs.setCurrentIndex(tab_index)
        
        # Mapeia para o side menu
        self.tab_to_side_menu_map[tab_index] = side_menu_key
        self.open_tabs[tab_index] = new_widget
        
        # Atualiza side menu
        self.side_menu_stack.setCurrentWidget(self.side_menus[side_menu_key])

# ===============================================================
# EXECUÇÃO PRINCIPAL
# ===============================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Configuração para alta DPI
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Definir informações da aplicação
    app.setApplicationName("Sistema RPA Integrado")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("PVRV Solutions")
    
    # Criar e mostrar janela principal
    window = MainWindow(app)
    window.setWindowTitle("Sistema RPA Integrado v2.0")
    
    # Ícone da aplicação (opcional)
    # window.setWindowIcon(QIcon("icon.png"))
    
    window.show()
    
    # Executar aplicação
    sys.exit(app.exec())