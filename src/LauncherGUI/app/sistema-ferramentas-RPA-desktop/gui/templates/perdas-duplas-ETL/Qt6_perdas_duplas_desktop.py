import sys
import pandas as pd
import re
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QWidget, QFileDialog, QTextEdit, 
                               QTableWidget, QTableWidgetItem, QLabel, QTabWidget,
                               QGroupBox, QProgressBar, QMessageBox, QCheckBox,
                               QLineEdit, QFrame, QHeaderView)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QFont, QColor
import fitz  # PyMuPDF

# ===============================================================
# CLASSE: ProcessingThread (MODEL)
# ===============================================================

class ProcessingThread(QThread):
    progress_signal = Signal(int)
    result_signal = Signal(pd.DataFrame)
    error_signal = Signal(str)
    
    def __init__(self, pdf_path, script_type, process_options=None, page_range=None):
        super().__init__()
        self.pdf_path = pdf_path
        self.script_type = script_type
        self.process_options = process_options or {}
        self.page_range = page_range  # Array de páginas específicas
    
    def run(self):
        try:
            # Extrai texto do PDF com intervalo específico
            doc = fitz.open(self.pdf_path)
            full_text = ""
            
            # Se page_range for None, processa todas as páginas
            if self.page_range is None:
                pages_to_process = range(len(doc))
            else:
                pages_to_process = [p for p in self.page_range if p < len(doc)]
            
            total_pages = len(pages_to_process)
            for i, page_num in enumerate(pages_to_process):
                page = doc.load_page(page_num)
                full_text += f"\n--- Página {page_num + 1} ---\n"
                full_text += page.get_text()
                progress = int((i + 1) / total_pages * 50)
                self.progress_signal.emit(progress)
            
            doc.close()
            
            # Executa o script específico
            if self.script_type == "contingencias_duplas":
                result_df = self.process_contingencias_duplas(full_text)
            elif self.script_type == "outro_script":
                result_df = self.process_outro_script(full_text)
            
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
            
            # Identifica Volume
            match_volume = re.match(r'(\d+\.\d+)\s+Volume\s+\d+\s*-\s*(.+)', linha)
            if match_volume:
                volume_atual = f"Volume {match_volume.group(1)}"
                area_geoelerica_atual = match_volume.group(2)
                continue
            
            # Identifica Prazo
            match_prazo = re.match(r'\d+\.\d+\.\d+\s+(Curto\s+Prazo|Médio\s+Prazo)', linha)
            if match_prazo:
                prazo_atual = match_prazo.group(1)
                continue
            
            # Identifica contingências
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
                            
                            # Remove "LT" duplicado se necessário
                            if i > 0 and parte.startswith('LT ') and not partes[i-1].endswith('LT'):
                                # Já está correto
                                pass
                            elif not parte.startswith('LT ') and ' kV ' in parte:
                                parte = 'LT ' + parte
                            
                            # Determina se é Futura baseado no prazo
                            futura = "SIM" if prazo_atual == "Curto Prazo" else "NÃO"
                            
                            dados.append({
                                'Volume': volume_atual,
                                'Área Geoelétrica': area_geoelerica_atual,
                                'Perda Dupla': parte,
                                'Prazo': prazo_atual,
                                'Futura': futura,
                                'Contingência Dupla Mesma Linha': 'SIM'
                            })
                    else:
                        # É uma única contingência
                        if not contingencia_limpa.startswith('LT ') and ' kV ' in contingencia_limpa:
                            contingencia_limpa = 'LT ' + contingencia_limpa
                        
                        futura = "SIM" if prazo_atual == "Curto Prazo" else "NÃO"
                        
                        dados.append({
                            'Volume': volume_atual,
                            'Área Geoelétrica': area_geoelerica_atual,
                            'Perda Dupla': contingencia_limpa,
                            'Prazo': prazo_atual,
                            'Futura': futura,
                            'Contingência Dupla Mesma Linha': 'NÃO'
                        })
                else:
                    # Não é uma "Contingência Dupla", processa normalmente
                    if not contingencia.startswith('LT ') and ' kV ' in contingencia:
                        contingencia = 'LT ' + contingencia
                    
                    futura = "SIM" if prazo_atual == "Curto Prazo" else "NÃO"
                    
                    dados.append({
                        'Volume': volume_atual,
                        'Área Geoelétrica': area_geoelerica_atual,
                        'Perda Dupla': contingencia,
                        'Prazo': prazo_atual,
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
# CLASSE: RPAWidget (IFRAME PARA SEU MAINWINDOW)
# ===============================================================

class RPAWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        self.current_pdf_path = None
        self.current_df = None
        self.selected_pages = []  # Array para páginas selecionadas
        
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
        main_layout.addWidget(self.main_container)
        
        # Layout do container
        container_layout = QHBoxLayout(self.main_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Sidebar esquerda
        self.sidebar = self.create_sidebar()
        container_layout.addWidget(self.sidebar)
        
        # Área principal
        self.main_content = QFrame()
        self.main_content.setObjectName("main_content")
        container_layout.addWidget(self.main_content)
        
        # Layout da área principal
        content_layout = QVBoxLayout(self.main_content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        
        # Título
        title_label = QLabel("Ferramenta RPA - Análise de Perdas Duplas")
        title_label.setObjectName("title_label")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        content_layout.addWidget(title_label)
        
        # Controle de intervalo de páginas
        page_controls_layout = QHBoxLayout()
        
        self.page_input = QLineEdit()
        self.page_input.setPlaceholderText("Ex: 1,3,5-10 (deixe vazio para todas as páginas)")
        self.page_input.setMinimumWidth(300)
        
        self.btn_apply_pages = QPushButton("Aplicar Intervalo")
        self.btn_apply_pages.clicked.connect(self.apply_page_range)
        
        page_controls_layout.addWidget(QLabel("Intervalo de páginas:"))
        page_controls_layout.addWidget(self.page_input)
        page_controls_layout.addWidget(self.btn_apply_pages)
        page_controls_layout.addStretch()
        
        content_layout.addLayout(page_controls_layout)
        
        # Área com abas
        self.tab_widget = QTabWidget()
        content_layout.addWidget(self.tab_widget)
        
        # Aba do PDF
        self.pdf_tab = QWidget()
        pdf_layout = QVBoxLayout(self.pdf_tab)
        self.pdf_text = QTextEdit()
        self.pdf_text.setPlaceholderText("Conteúdo do PDF aparecerá aqui...")
        pdf_layout.addWidget(QLabel("Visualização do PDF:"))
        pdf_layout.addWidget(self.pdf_text)
        self.tab_widget.addTab(self.pdf_tab, "📄 PDF Original")
        
        # Aba de resultados
        self.results_tab = QWidget()
        results_layout = QVBoxLayout(self.results_tab)
        self.results_table = QTableWidget()
        results_layout.addWidget(QLabel("📊 Resultados do Processamento:"))
        results_layout.addWidget(self.results_table)
        self.tab_widget.addTab(self.results_tab, "📊 Resultados")
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        content_layout.addWidget(self.progress_bar)
        
    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(350)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Grupo de upload
        upload_group = QGroupBox("📁 Upload de Arquivos")
        upload_layout = QVBoxLayout(upload_group)
        
        self.btn_load_pdf = QPushButton("📄 Carregar PDF")
        self.btn_load_pdf.setObjectName("btn_load_pdf")
        upload_layout.addWidget(self.btn_load_pdf)
        
        self.btn_load_excel = QPushButton("📊 Carregar Excel")
        self.btn_load_excel.setObjectName("btn_load_excel")
        upload_layout.addWidget(self.btn_load_excel)
        
        self.file_label = QLabel("Nenhum arquivo carregado")
        self.file_label.setObjectName("file_label")
        self.file_label.setWordWrap(True)
        upload_layout.addWidget(self.file_label)
        
        # Status do intervalo
        self.pages_status_label = QLabel("Intervalo: Todas as páginas")
        self.pages_status_label.setWordWrap(True)
        upload_layout.addWidget(self.pages_status_label)
        
        # Opções de processamento
        options_group = QGroupBox("⚙️ Opções de Processamento")
        options_layout = QVBoxLayout(options_group)
        
        self.cb_separar_duplas = QCheckBox("🔀 Separar Contingências Duplas")
        self.cb_separar_duplas.setChecked(True)
        options_layout.addWidget(self.cb_separar_duplas)
        
        self.cb_adicionar_lt = QCheckBox("🏷️ Adicionar 'LT' automaticamente")
        self.cb_adicionar_lt.setChecked(True)
        options_layout.addWidget(self.cb_adicionar_lt)
        
        # Scripts RPA
        scripts_group = QGroupBox("🤖 Scripts RPA")
        scripts_layout = QVBoxLayout(scripts_group)
        
        self.btn_contingencias = QPushButton("⚡ Análise Contingências Duplas")
        self.btn_contingencias.setObjectName("btn_contingencias")
        scripts_layout.addWidget(self.btn_contingencias)
        
        self.btn_script2 = QPushButton("🛠️ Script 2 - Em Desenvolvimento")
        scripts_layout.addWidget(self.btn_script2)
        
        # Exportação
        export_group = QGroupBox("📤 Exportação")
        export_layout = QVBoxLayout(export_group)
        
        self.btn_export_excel = QPushButton("💾 Exportar para Excel")
        self.btn_export_excel.setObjectName("btn_export_excel")
        export_layout.addWidget(self.btn_export_excel)
        
        self.btn_export_word = QPushButton("📝 Exportar para Word")
        export_layout.addWidget(self.btn_export_word)
        
        # Espaço flexível
        layout.addWidget(upload_group)
        layout.addWidget(options_group)
        layout.addWidget(scripts_group)
        layout.addWidget(export_group)
        layout.addStretch()
        
        return sidebar
        
    def setup_connections(self):
        self.btn_load_pdf.clicked.connect(self.load_pdf)
        self.btn_load_excel.clicked.connect(self.load_excel)
        self.btn_contingencias.clicked.connect(lambda: self.run_script("contingencias_duplas"))
        self.btn_export_excel.clicked.connect(self.export_to_excel)
        self.btn_export_word.clicked.connect(self.export_to_word)
    
    def apply_page_range(self):
        """Processa o input de páginas do usuário e converte para array"""
        input_text = self.page_input.text().strip()
        self.selected_pages = []
        
        if not input_text:
            # Se vazio, processa todas as páginas
            self.pages_status_label.setText("Intervalo: Todas as páginas")
            QMessageBox.information(self, "Intervalo Definido", "Processando TODAS as páginas do PDF.")
            return
        
        try:
            # Processa diferentes formatos: "1,3,5-10", "1-5", "1,2,3"
            pages = []
            parts = input_text.split(',')
            
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # É um intervalo
                    start, end = map(int, part.split('-'))
                    # Ajusta para base 0 (PDF é base 0 internamente)
                    pages.extend(range(start-1, end))
                else:
                    # É uma página individual
                    pages.append(int(part) - 1)  # Base 0
            
            self.selected_pages = sorted(set(pages))  # Remove duplicatas e ordena
            
            # Atualiza status
            pages_str = ", ".join([str(p+1) for p in self.selected_pages])
            self.pages_status_label.setText(f"Intervalo: Páginas {pages_str}")
            
            QMessageBox.information(self, "Intervalo Definido", 
                                  f"Processando {len(self.selected_pages)} páginas específicas: {pages_str}")
            
        except ValueError as e:
            QMessageBox.warning(self, "Erro", f"Formato inválido. Use: 1,3,5-10\nErro: {str(e)}")
            self.pages_status_label.setText("Intervalo: Erro no formato")
    
    def load_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar PDF", "", "PDF Files (*.pdf)")
        
        if file_path:
            self.current_pdf_path = file_path
            self.file_label.setText(f"PDF: {file_path.split('/')[-1]}")
            
            try:
                doc = fitz.open(file_path)
                full_text = ""
                for page in doc:
                    full_text += page.get_text()
                doc.close()
                
                self.pdf_text.setPlainText(full_text)
                self.tab_widget.setCurrentIndex(0)
                
                # Limpa seleção anterior de páginas
                self.selected_pages = []
                self.page_input.clear()
                self.pages_status_label.setText("Intervalo: Todas as páginas")
                
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao ler PDF: {str(e)}")
    
    def load_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Excel", "", "Excel Files (*.xlsx *.xls)")
        
        if file_path:
            self.file_label.setText(f"Excel: {file_path.split('/')[-1]}")
    
    def run_script(self, script_type):
        if not self.current_pdf_path:
            QMessageBox.warning(self, "Aviso", "Por favor, carregue um PDF primeiro.")
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
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
        self.thread.start()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def show_results(self, df):
        self.current_df = df
        self.progress_bar.setVisible(False)
        
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
                
                # Colorização para melhor visualização
                if col == 4:  # Coluna Futura
                    if df.iat[row, col] == "SIM":
                        item.setBackground(QColor(144, 238, 144, 100))  # Verde claro
                    else:
                        item.setBackground(QColor(255, 182, 193, 100))  # Vermelho claro
                elif col == 5:  # Coluna Contingência Dupla Mesma Linha
                    if df.iat[row, col] == "SIM":
                        item.setBackground(QColor(173, 216, 230, 100))  # Azul claro
                
                self.results_table.setItem(row, col, item)
        
        self.tab_widget.setCurrentIndex(1)
        QMessageBox.information(self, "Sucesso", f"Processamento concluído! {len(df)} registros encontrados.")
    
    def show_error(self, error_msg):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Erro", f"Erro no processamento:\n{error_msg}")
    
    def export_to_excel(self):
        if self.current_df is not None and not self.current_df.empty:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Salvar Excel", "contingencias_duplas.xlsx", "Excel Files (*.xlsx)")
            
            if file_path:
                try:
                    self.current_df.to_excel(file_path, index=False)
                    QMessageBox.information(self, "Sucesso", f"Arquivo salvo em:\n{file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Erro", f"Erro ao salvar:\n{str(e)}")
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum dado para exportar.")
    
    def export_to_word(self):
        QMessageBox.information(self, "Info", "Funcionalidade em desenvolvimento.")

# ===============================================================
# CLASSE: MainWindow (SEU TEMPLATE PRINCIPAL)
# ===============================================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema Principal - Ferramentas RPA")
        self.setGeometry(100, 100, 1400, 900)
        
        self.setup_ui()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Cabeçalho
        header_label = QLabel("Sistema Principal - Ferramentas RPA")
        header_label.setFont(QFont("Arial", 18, QFont.Bold))
        main_layout.addWidget(header_label)
        
        # Widget de abas
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Adiciona a aba da ferramenta RPA
        self.rpa_widget = RPAWidget()
        self.tab_widget.addTab(self.rpa_widget, "🤖 Perdas Duplas ETL")

# ===============================================================
# EXECUÇÃO (APENAS PARA TESTE - REMOVA NO SEU APP PRINCIPAL)
# ===============================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    
    # Para teste individual
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())