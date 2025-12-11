import pandas as pd
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QFileDialog, QTextEdit, QTableWidget, QTableWidgetItem, QLabel, QTabWidget, QGroupBox, QProgressBar, QMessageBox, QCheckBox, QLineEdit, QFrame, QHeaderView)
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QColor
import fitz # Importa fitz para lidar com PDFs

# ===============================================================
# CLASSE: Controller (app/controllers/etl_repository.py)
# ===============================================================
import pathlib
import sys

# Adiciona duas pastas acima ao sys.path para importar o controller
current_path = pathlib.Path(__file__).parent
parent_path = (current_path / ".." / "..").resolve()
sys.path.insert(0, str(parent_path))

from app.controllers.etl_repository import ETLController

# ===============================================================
# CLASSE: ProcessingThread (Thread de processamento em segundo plano)
# ===============================================================

class ProcessingThread(QThread):
    progress_signal = Signal(int)
    result_signal = Signal(pd.DataFrame)
    error_signal = Signal(str)
    
    def __init__(self, pdf_path, script_type, process_options=None, page_range=None, etl_controller=None, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.script_type = script_type
        self.process_options = process_options or {}
        self.page_range = page_range  # Array de páginas específicas

        # Usa a instância do controller passada, que já tem as opções da UI
        self.etl_controller = etl_controller # etl_controller agora é passado do UIController

    def setState(self, state):
        self.state = state
        
    
    def run(self):
        try:
            # A extração de texto é agora responsabilidade do ETLController/ETLRepository
            full_text = self.etl_controller.extract_pdf_text(self.pdf_path, self.page_range)
            self.progress_signal.emit(50) # Metade do progresso após extração
            
            # Executa o script específico através do controller
            if self.script_type == "contingencias_duplas":
                result_df = self.etl_controller.process_contingencias_duplas(full_text)

            elif self.script_type == "outro_script":
                result_df = self.etl_controller.process_outro_script(full_text)
            else:
                result_df = pd.DataFrame({"Status": ["Script não reconhecido"]})
            
            self.result_signal.emit(result_df)
            self.progress_signal.emit(100)
            
        except Exception as e:
            self.error_signal.emit(str(e))

# ===============================================================
# CLASSE: PerdasDuplasUIController (Controlador da UI)
# ===============================================================

class PerdasDuplasUIController:
    """Controlador para a lógica da UI e orquestração do ETL para o PerdasDuplasWidget."""

    def __init__(self, widget, etl_controller):
        self.widget = widget
        self.etl_controller = etl_controller

    def apply_page_range(self):
        """Processa o input do usuário para definir o intervalo de páginas a serem processadas."""
        input_text = self.widget.page_input.text().strip()
        self.widget.selected_pages = [] # Limpa as páginas selecionadas anteriores
        
        if not input_text:
            # Se o input estiver vazio, processa todas as páginas
            self.widget.pages_status_label.setText("Intervalo: Todas as páginas")
            QMessageBox.information(self.widget, "Intervalo Definido", "Processando TODAS as páginas do PDF.")
            return
        
        try:
            pages = []
            parts = input_text.split(',') # Divide por vírgulas para múltiplos intervalos/páginas
            
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # Processa intervalos (ex: "5-10")
                    start, end = map(int, part.split('-'))
                    pages.extend(range(start-1, end)) # Adiciona páginas (base 0)
                else:
                    # Processa páginas individuais (ex: "3")
                    pages.append(int(part) - 1) # Adiciona página (base 0)
            
            self.widget.selected_pages = sorted(set(pages)) # Remove duplicatas e ordena
            print(f"DEBUG: Selected Pages (UI Controller): {self.widget.selected_pages}") # DEBUG PRINT
            
            # Atualiza o status na UI
            pages_str = ", ".join([str(p+1) for p in self.widget.selected_pages]) # Converte para base 1 para exibição
            self.widget.pages_status_label.setText(f"Intervalo: Páginas {pages_str}")
            
            QMessageBox.information(self.widget, "Intervalo Definido", 
                                  f"Processando {len(self.widget.selected_pages)} páginas específicas: {pages_str}")
            
        except ValueError as e:
            QMessageBox.warning(self.widget, "Erro", f"Formato inválido. Use: 1,3,5-10\nErro: {str(e)}")
            self.widget.pages_status_label.setText("Intervalo: Erro no formato")

    def load_pdf(self):
        """Abre uma caixa de diálogo para selecionar e carregar um arquivo PDF."""
        file_path, _ = QFileDialog.getOpenFileName(
            self.widget, "Selecionar PDF", "", "PDF Files (*.pdf)")
        
        if file_path:
            self.widget.current_pdf_path = file_path
            
            try:
                doc = fitz.open(file_path)
                total_pages = len(doc)
                doc.close()

                self.widget.file_label.setText(f"PDF: {file_path.split('/')[-1]} ({total_pages} páginas)") # Exibe o nome do arquivo e total de páginas
                
                # A extração do texto completo para visualização ainda pode ser feita aqui, se necessário.
                # Para processamento, usaremos o ETLController.
                full_text_preview = self.etl_controller.extract_pdf_text(file_path) # Usa o controller para extrair para pré-visualização
                
                self.widget.pdf_text.setPlainText(full_text_preview)
                self.widget.tab_widget.setCurrentIndex(0) # Volta para a aba do PDF
                
                # Limpa e reseta o controle de páginas
                self.widget.selected_pages = []
                self.widget.page_input.clear()
                self.widget.pages_status_label.setText("Intervalo: Todas as páginas")
                
            except Exception as e:
                QMessageBox.critical(self.widget, "Erro", f"Erro ao ler PDF: {str(e)}")

    def load_excel(self):
        """Abre uma caixa de diálogo para selecionar e carregar um arquivo Excel (funcionalidade a ser implementada)."""
        file_path, _ = QFileDialog.getOpenFileName(
            self.widget, "Selecionar Excel", "", "Excel Files (*.xlsx *.xls)")
        
        if file_path:
            self.widget.file_label.setText(f"Excel: {file_path.split('/')[-1]}") # Exibe o nome do arquivo

    def run_script(self, script_type):
        """
        Inicia a thread de processamento para executar o script ETL selecionado.

        Args:
            script_type (str): O tipo de script a ser executado.
        """
        if not self.widget.current_pdf_path:
            QMessageBox.warning(self.widget, "Aviso", "Por favor, carregue um PDF primeiro.")
            return
        
        self.widget.progress_bar.setVisible(True) # Mostra a barra de progresso
        self.widget.progress_bar.setValue(0)
        
        # Coleta as opções de processamento dos checkboxes
        process_options = {
            'enable_volume_area_extraction': self.widget.cb_enable_volume_area_extraction.isChecked(),
            'enable_prazo_extraction': self.widget.cb_enable_prazo_extraction.isChecked(),
            'enable_contingency_identification': self.widget.cb_enable_contingency_identification.isChecked(),
            'enable_regex_processing': self.widget.cb_regex_processing.isChecked(),
            'standardize_columns': self.widget.cb_standardize_columns.isChecked(),
            'separar_duplas': self.widget.cb_separar_duplas.isChecked(),
            'adicionar_lt': self.widget.cb_adicionar_lt.isChecked()
        }
        
        # Usa as páginas selecionadas ou None para todas
        page_range = self.widget.selected_pages if self.widget.selected_pages else None
        
        # Cria e inicia a thread de processamento, passando a instância do etl_controller
        self.thread = ProcessingThread(self.widget.current_pdf_path, script_type, process_options, page_range, self.etl_controller, parent=self.widget)
        self.thread.progress_signal.connect(self.update_progress)
        self.thread.result_signal.connect(self.show_results)
        self.thread.error_signal.connect(self.show_error)
        self.thread.start()

    def update_progress(self, value):
        """Atualiza o valor da barra de progresso."""
        self.widget.progress_bar.setValue(value)

    def show_results(self, df):
        """
        Exibe os resultados do processamento em uma QTableWidget.

        Args:
            df (pd.DataFrame): O DataFrame com os resultados a serem exibidos.
        """
        self.widget.current_df = df # Armazena o DataFrame atual
        self.widget.progress_bar.setVisible(False) # Esconde a barra de progresso
        
        # Configura a tabela com os dados do DataFrame
        self.widget.results_table.setRowCount(df.shape[0])
        self.widget.results_table.setColumnCount(df.shape[1])
        self.widget.results_table.setHorizontalHeaderLabels(df.columns.tolist())
        
        # Ajusta a largura das colunas para o conteúdo
        header = self.widget.results_table.horizontalHeader()
        for i in range(df.shape[1]):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        # Preenche a tabela com os dados e aplica colorização condicional
        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                item = QTableWidgetItem(str(df.iat[row, col]))
                
                # Colorização para melhor visualização (colunas 'Futura' e 'Contingência Dupla Mesma Linha')
                if col == 4:  # Coluna 'Futura'
                    if df.iat[row, col] == "SIM":
                        item.setBackground(QColor(144, 238, 144, 100))  # Verde claro
                    else:
                        item.setBackground(QColor(255, 182, 193, 100))  # Vermelho claro
                elif col == 5:  # Coluna 'Contingência Dupla Mesma Linha'
                    if df.iat[row, col] == "SIM":
                        item.setBackground(QColor(173, 216, 230, 100))  # Azul claro
                
                self.widget.results_table.setItem(row, col, item)
        
        self.widget.tab_widget.setCurrentIndex(1) # Muda para a aba de resultados
        QMessageBox.information(self.widget, "Sucesso", f"Processamento concluído! {len(df)} registros encontrados.")

    def show_error(self, error_msg):
        """Exibe uma mensagem de erro em caso de falha no processamento."""
        self.widget.progress_bar.setVisible(False) # Esconde a barra de progresso
        QMessageBox.critical(self.widget, "Erro", f"Erro no processamento:\n{error_msg}")

    def export_to_excel(self):
        """Exporta o DataFrame atual de resultados para um arquivo Excel."""
        if self.widget.current_df is not None and not self.widget.current_df.empty:
            file_path, _ = QFileDialog.getSaveFileName(
                self.widget, "Salvar Excel", "perdas_duplas_ETL.xlsx", "Excel Files (*.xlsx)")
            
            if file_path:
                try:
                    self.widget.current_df.to_excel(file_path, index=False)
                    QMessageBox.information(self.widget, "Sucesso", f"Arquivo salvo em:\n{file_path}")
                except Exception as e:
                    QMessageBox.critical(self.widget, "Erro", f"Erro ao salvar:\n{str(e)}")
        else:
            QMessageBox.warning(self.widget, "Aviso", "Nenhum dado para exportar.")

    def export_to_word(self):
        """Exibe uma mensagem informando que a funcionalidade de exportação para Word está em desenvolvimento."""
        QMessageBox.information(self.widget, "Info", "Funcionalidade em desenvolvimento.")

    def _update_and_log_process_options(self):
        """Coleta o estado atual dos checkboxes, atualiza o controller e imprime no terminal."""
        current_options = {
            'enable_volume_area_extraction': self.widget.cb_enable_volume_area_extraction.isChecked(),
            'enable_prazo_extraction': self.widget.cb_enable_prazo_extraction.isChecked(),
            'enable_contingency_identification': self.widget.cb_enable_contingency_identification.isChecked(),
            'enable_regex_processing': self.widget.cb_regex_processing.isChecked(),
            'standardize_columns': self.widget.cb_standardize_columns.isChecked(),
            'separar_duplas': self.widget.cb_separar_duplas.isChecked(),
            'adicionar_lt': self.widget.cb_adicionar_lt.isChecked()
        }
        self.etl_controller.process_options.update(current_options)
        print("Process Options Atualizadas:", self.etl_controller.process_options)

# ===============================================================
# CLASSE: PerdasDuplasWidget (Iframe da ferramenta de Perdas Duplas)
# ===============================================================

class PerdasDuplasWidget(QWidget):
    """Widget principal para a ferramenta de Análise de Perdas Duplas (Iframe)."""
    def __init__(self, side_menu=None, parent=None):
        """
        Inicializa o PerdasDuplasWidget.

        Args:
            side_menu (QWidget, optional): O widget do menu lateral associado a este Iframe. Defaults to None.
            parent (QWidget, optional): O widget pai. Defaults to None.
        """
        super().__init__(parent)
        
        self.side_menu = side_menu # Armazena referência ao menu lateral
        self.current_pdf_path = None # Caminho do PDF atualmente carregado
        self.current_df = None       # DataFrame com os resultados do processamento
        self.selected_pages = []  # Array para páginas selecionadas para processamento
        
        self.setup_ui()        # Configura a interface do usuário
        # Instancia o ETLController e o PerdasDuplasUIController
        self.etl_controller = ETLController()
        self.ui_controller = PerdasDuplasUIController(self, self.etl_controller)

        self.setup_connections() # Configura as conexões de sinais/slots
    
    def setup_ui(self):
        """Configura os elementos da interface do usuário do widget."""
        # Layout principal do widget
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Container principal para estilos visuais
        self.main_container = QFrame()
        self.main_container.setObjectName("main_container") # Para aplicar estilos CSS
        main_layout.addWidget(self.main_container)
        
        # Layout dentro do container principal
        container_layout = QHBoxLayout(self.main_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Cria e adiciona a barra lateral (sidebar)
        self.sidebar = self.create_sidebar()
        container_layout.addWidget(self.sidebar)
        
        # Área principal de conteúdo
        self.main_content = QFrame()
        self.main_content.setObjectName("main_content") # Para aplicar estilos CSS
        container_layout.addWidget(self.main_content)
        
        # Layout da área principal de conteúdo
        content_layout = QVBoxLayout(self.main_content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        
        # Layout para controle de intervalo de páginas
        page_controls_layout = QHBoxLayout()
        
        # Campo de entrada para as páginas
        self.page_input = QLineEdit()
        self.page_input.setPlaceholderText("Ex: 1,3,5-10 (deixe vazio para todas as páginas)")
        self.page_input.setMinimumWidth(300)
        
        # Botão para aplicar o intervalo de páginas
        self.btn_apply_pages = QPushButton("Aplicar Intervalo")
        # self.btn_apply_pages.clicked.connect(self.apply_page_range) # Conexão será feita no setup_connections
        
        page_controls_layout.addWidget(QLabel("Intervalo de páginas:"))
        page_controls_layout.addWidget(self.page_input)
        page_controls_layout.addWidget(self.btn_apply_pages)
        page_controls_layout.addStretch() # Empurra os widgets para a esquerda
        
        content_layout.addLayout(page_controls_layout)
        
        # Widget de abas para visualização do PDF e resultados
        self.tab_widget = QTabWidget()
        content_layout.addWidget(self.tab_widget)
        
        # Aba para visualização do PDF original
        self.pdf_tab = QWidget()
        pdf_layout = QVBoxLayout(self.pdf_tab)
        self.pdf_text = QTextEdit()
        self.pdf_text.setPlaceholderText("Conteúdo do PDF aparecerá aqui...")
        pdf_layout.addWidget(QLabel("Visualização do PDF:"))
        pdf_layout.addWidget(self.pdf_text)
        self.tab_widget.addTab(self.pdf_tab, "📄 PDF Original")
        
        # Aba para exibir os resultados do processamento
        self.results_tab = QWidget()
        results_layout = QVBoxLayout(self.results_tab)
        self.results_table = QTableWidget()
        results_layout.addWidget(QLabel("📊 Resultados do Processamento:"))
        results_layout.addWidget(self.results_table)
        self.tab_widget.addTab(self.results_tab, "📊 Resultados")
        
        # Barra de progresso para feedback do usuário
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False) # Inicialmente invisível
        content_layout.addWidget(self.progress_bar)
        

    def create_options_group(self):
        """Cria e retorna o widget do grupo de opções de processamento."""

        options_group = QGroupBox("⚙️ Opções de Processamento")
        options_layout = QVBoxLayout(options_group)
        
        # Novos Checkboxes para controle granular
        self.cb_enable_volume_area_extraction = QCheckBox("➕ 1) Extrair Volume e Área")
        self.cb_enable_volume_area_extraction.setChecked(True)
        options_layout.addWidget(self.cb_enable_volume_area_extraction)

        self.cb_enable_prazo_extraction = QCheckBox("⏰ 2) Extrair Prazo")
        self.cb_enable_prazo_extraction.setChecked(True)
        options_layout.addWidget(self.cb_enable_prazo_extraction)

        self.cb_enable_contingency_identification = QCheckBox("🔍 3) Identificar Contingências")
        self.cb_enable_contingency_identification.setChecked(True)
        options_layout.addWidget(self.cb_enable_contingency_identification)

        self.cb_regex_processing = QCheckBox("⚙️ 4) Processar Regex de Contingências")
        self.cb_regex_processing.setChecked(True)
        options_layout.addWidget(self.cb_regex_processing)


        # Checkbox para separar contingências duplas
        self.cb_separar_duplas = QCheckBox("🔀 5) Separar Perdas Duplas")
        self.cb_separar_duplas.setChecked(True)
        options_layout.addWidget(self.cb_separar_duplas)
        
        # Checkbox para adicionar 'LT' automaticamente
        self.cb_adicionar_lt = QCheckBox("🏷️ 6) Adicionar 'LT' automaticamente")
        self.cb_adicionar_lt.setChecked(True)
        options_layout.addWidget(self.cb_adicionar_lt)


        self.cb_standardize_columns = QCheckBox("🔡 7) Padronizar Capitalização")
        self.cb_standardize_columns.setChecked(True)
        options_layout.addWidget(self.cb_standardize_columns)
        
        
        return options_group

    def create_sidebar(self):
        """Cria e retorna o widget da barra lateral (sidebar) com as opções de controle."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar") # Para aplicar estilos CSS
        sidebar.setFixedWidth(350)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Grupo para upload de arquivos
        upload_group = QGroupBox("📁 Upload de Arquivos")
        upload_layout = QVBoxLayout(upload_group)
        
        # Botão para carregar PDF
        self.btn_load_pdf = QPushButton("📄 Carregar PDF")
        self.btn_load_pdf.setObjectName("btn_load_pdf")
        upload_layout.addWidget(self.btn_load_pdf)
        
        # Botão para carregar Excel (funcionalidade futura)
        self.btn_load_excel = QPushButton("📊 Carregar Excel")
        self.btn_load_excel.setObjectName("btn_load_excel")
        upload_layout.addWidget(self.btn_load_excel)
        
        # Label para mostrar o nome do arquivo carregado
        self.file_label = QLabel("Nenhum arquivo carregado")
        self.file_label.setObjectName("file_label")
        self.file_label.setWordWrap(True) # Permite quebra de linha
        upload_layout.addWidget(self.file_label)
        
        # Label para mostrar o status do intervalo de páginas
        self.pages_status_label = QLabel("Intervalo: Todas as páginas")
        self.pages_status_label.setWordWrap(True)
        upload_layout.addWidget(self.pages_status_label)
        
        #! Adiciona o grupo de opções de processamento
        options_group = self.create_options_group()
        upload_layout.addWidget(options_group)
        
        #! Grupo para scripts RPA
        scripts_group = QGroupBox("🤖 Scripts Python para RPA")
        scripts_layout = QVBoxLayout(scripts_group)
        
        # Botão para iniciar a análise de contingências duplas
        self.btn_contingencias = QPushButton("⚡ Análise Nomes Perdas Duplas")
        self.btn_contingencias.setObjectName("btn_contingencias")
        scripts_layout.addWidget(self.btn_contingencias)
        
        # Botão placeholder para outros scripts
        self.btn_script2 = QPushButton("🛠️ Organizador arquivos - Em Desenvolvimento")
        scripts_layout.addWidget(self.btn_script2)
        
        # Grupo para opções de exportação
        export_group = QGroupBox("📤 Exportação")
        export_layout = QVBoxLayout(export_group)
        
        # Botão para exportar resultados para Excel
        self.btn_export_excel = QPushButton("💾 Exportar para Excel")
        self.btn_export_excel.setObjectName("btn_export_excel")
        export_layout.addWidget(self.btn_export_excel)
        
        # Botão placeholder para exportar para Word
        self.btn_export_word = QPushButton("📝 Exportar para Word")
        export_layout.addWidget(self.btn_export_word)
        
        # Adiciona todos os grupos à barra lateral e um stretch para ocupar o espaço restante
        layout.addWidget(upload_group)
        layout.addWidget(options_group)
        layout.addWidget(scripts_group)
        layout.addWidget(export_group)
        layout.addStretch()
        
        return sidebar
        
    def setup_connections(self):
        """Configura as conexões de sinais e slots para os elementos da UI."""
        self.btn_apply_pages.clicked.connect(self.ui_controller.apply_page_range)
        self.btn_load_pdf.clicked.connect(self.ui_controller.load_pdf)
        self.btn_load_excel.clicked.connect(self.ui_controller.load_excel)
        self.btn_contingencias.clicked.connect(lambda: self.ui_controller.run_script("contingencias_duplas"))
        self.btn_export_excel.clicked.connect(self.ui_controller.export_to_excel)
        self.btn_export_word.clicked.connect(self.ui_controller.export_to_word)

        # Conecta os checkboxes para atualizar e logar as opções de processamento
        self.cb_enable_volume_area_extraction.stateChanged.connect(self.ui_controller._update_and_log_process_options)
        self.cb_enable_prazo_extraction.stateChanged.connect(self.ui_controller._update_and_log_process_options)
        self.cb_enable_contingency_identification.stateChanged.connect(self.ui_controller._update_and_log_process_options)
        self.cb_regex_processing.stateChanged.connect(self.ui_controller._update_and_log_process_options)
        self.cb_standardize_columns.stateChanged.connect(self.ui_controller._update_and_log_process_options)
        self.cb_separar_duplas.stateChanged.connect(self.ui_controller._update_and_log_process_options)
        self.cb_adicionar_lt.stateChanged.connect(self.ui_controller._update_and_log_process_options)
