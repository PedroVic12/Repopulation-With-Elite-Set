"""
Sistema Integrado de Visualização de Decks anaRede com PySide6
Combina funcionalidades de parsing de arquivos .PWF com visualização gráfica
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import json

# PySide6 imports
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QFileDialog, QListWidget, QListWidgetItem, QSplitter,
    QTabWidget, QTextEdit, QMessageBox, QHeaderView, QGroupBox,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize
from PySide6.QtGui import QFont, QColor, QPalette

# Matplotlib
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Pandapower
try:
    import pandapower as pp
    import pandapower.plotting as plotting
    from pandapower.plotting.plotly import simple_plotly
    PANDAPOWER_AVAILABLE = True
except ImportError:
    print("Pandapower não está disponível. Algumas funcionalidades serão limitadas.")
    PANDAPOWER_AVAILABLE = False

# -----------------------------------------------------------------------------
# CLASSES DE DADOS E PARSERS
# -----------------------------------------------------------------------------

@dataclass
class Barra:
    """Classe representando uma barra do sistema"""
    numero: int
    nome: str = ""
    tipo: str = "PQ"  # PQ, PV, REF
    tensao_pu: float = 1.0
    angulo_graus: float = 0.0
    p_ger_mw: float = 0.0
    q_ger_mvar: float = 0.0
    p_carga_mw: float = 0.0
    q_carga_mvar: float = 0.0
    base_kv: float = 138.0
    x: float = 0.0  # Coordenada X para plotagem
    y: float = 0.0  # Coordenada Y para plotagem

@dataclass
class Linha:
    """Classe representando uma linha de transmissão"""
    de_barra: int
    para_barra: int
    nome: str = ""
    r_pu: float = 0.01
    x_pu: float = 0.1
    b_pu: float = 0.0
    taxa_mva: float = 100.0
    comprimento_km: float = 1.0

@dataclass
class Transformador:
    """Classe representando um transformador"""
    barra_alta: int
    barra_baixa: int
    nome: str = ""
    sn_mva: float = 100.0
    vn_hv_kv: float = 138.0
    vn_lv_kv: float = 13.8
    vk_percent: float = 10.0
    vkr_percent: float = 0.6
    pfe_kw: float = 0.0
    i0_percent: float = 0.2

@dataclass
class Gerador:
    """Classe representando um gerador"""
    barra: int
    nome: str = ""
    p_mw: float = 0.0
    q_mvar: float = 0.0
    vn_kv: float = 13.8
    sn_mva: float = 100.0
    min_q_mvar: float = -50.0
    max_q_mvar: float = 50.0

@dataclass
class Carga:
    """Classe representando uma carga"""
    barra: int
    nome: str = ""
    p_mw: float = 0.0
    q_mvar: float = 0.0
    tipo: str = "PQ"  # PQ, Z, I

class DeckAnaRede:
    """Classe principal para representar um deck do anaRede"""
    
    def __init__(self, caminho_arquivo: str = ""):
        self.caminho_arquivo = caminho_arquivo
        self.nome = Path(caminho_arquivo).stem if caminho_arquivo else "Deck Sem Nome"
        self.barras: Dict[int, Barra] = {}
        self.linhas: List[Linha] = []
        self.transformadores: List[Transformador] = []
        self.geradores: List[Gerador] = []
        self.cargas: List[Carga] = []
        self.metadata: Dict = {}
        
    def criar_rede_pandapower(self):
        """Cria uma rede pandapower a partir dos dados do deck"""
        if not PANDAPOWER_AVAILABLE:
            raise ImportError("Pandapower não está disponível")
        
        net = pp.create_empty_network()
        
        # Adiciona barras
        for num_barra, barra in self.barras.items():
            pp.create_bus(
                net, 
                vn_kv=barra.base_kv,
                name=f"Barra {num_barra}",
                index=num_barra
            )
        
        # Adiciona linhas
        for i, linha in enumerate(self.linhas):
            pp.create_line_from_parameters(
                net,
                from_bus=linha.de_barra,
                to_bus=linha.para_barra,
                length_km=linha.comprimento_km,
                r_ohm_per_km=linha.r_pu * linha.de_barra.base_kv**2 / 100,
                x_ohm_per_km=linha.x_pu * linha.de_barra.base_kv**2 / 100,
                c_nf_per_km=linha.b_pu * 1e9 / (2 * np.pi * 60 * linha.de_barra.base_kv**2),
                name=linha.nome or f"Linha {i+1}",
                max_i_ka=linha.taxa_mva / (np.sqrt(3) * linha.de_barra.base_kv)
            )
        
        # Adiciona transformadores
        for trafo in self.transformadores:
            pp.create_transformer_from_parameters(
                net,
                hv_bus=trafo.barra_alta,
                lv_bus=trafo.barra_baixa,
                sn_mva=trafo.sn_mva,
                vn_hv_kv=trafo.vn_hv_kv,
                vn_lv_kv=trafo.vn_lv_kv,
                vkr_percent=trafo.vkr_percent,
                vk_percent=trafo.vk_percent,
                pfe_kw=trafo.pfe_kw,
                i0_percent=trafo.i0_percent,
                name=trafo.nome
            )
        
        # Adiciona geradores
        for gerador in self.geradores:
            pp.create_gen(
                net,
                bus=gerador.barra,
                p_mw=gerador.p_mw,
                vm_pu=gerador.vn_kv / gerador.barra.base_kv,
                name=gerador.nome,
                min_q_mvar=gerador.min_q_mvar,
                max_q_mvar=gerador.max_q_mvar
            )
        
        # Adiciona cargas
        for carga in self.cargas:
            pp.create_load(
                net,
                bus=carga.barra,
                p_mw=carga.p_mw,
                q_mvar=carga.q_mvar,
                name=carga.nome
            )
        
        return net

class ParserPWF:
    """Parser para arquivos .PWF do anaRede"""
    
    @staticmethod
    def parse_arquivo(caminho: str) -> DeckAnaRede:
        """Lê um arquivo .PWF e retorna um objeto DeckAnaRede"""
        deck = DeckAnaRede(caminho)
        
        with open(caminho, 'r', encoding='utf-8', errors='ignore') as f:
            conteudo = f.read()
        
        linhas = conteudo.split('\n')
        
        # Parse simplificado - você pode expandir conforme necessário
        for i, linha in enumerate(linhas):
            linha_limpa = linha.strip()
            
            # Procura por barras no formato do anaRede
            if linha_limpa.startswith("DBAR"):
                # Processa bloco de barras
                ParserPWF._processar_bloco_barras(deck, linhas[i:])
            
            # Procura por linhas
            elif linha_limpa.startswith("DLIN"):
                # Processa bloco de linhas
                ParserPWF._processar_bloco_linhas(deck, linhas[i:])
        
        return deck
    
    @staticmethod
    def _processar_bloco_barras(deck: DeckAnaRede, linhas: List[str]):
        """Processa bloco de definição de barras"""
        for i, linha in enumerate(linhas):
            if linha.strip().startswith("99999"):
                break
            
            partes = linha.split()
            if len(partes) >= 4 and partes[0].isdigit():
                try:
                    num_barra = int(partes[0])
                    tipo = partes[1] if len(partes) > 1 else "PQ"
                    
                    # Tenta extrair tensão
                    tensao = 1.0
                    if len(partes) > 2:
                        if len(partes[2]) == 4 and partes[2].isdigit():
                            tensao = float(partes[2]) / 1000
                    
                    # Tenta extrair potência
                    p_ger = 0.0
                    q_ger = 0.0
                    if len(partes) > 3 and partes[3].replace('.', '').isdigit():
                        q_ger = float(partes[3])
                    
                    barra = Barra(
                        numero=num_barra,
                        tipo=tipo,
                        tensao_pu=tensao,
                        q_ger_mvar=q_ger,
                        p_ger_mw=p_ger
                    )
                    deck.barras[num_barra] = barra
                    
                except ValueError:
                    continue
    
    @staticmethod
    def _processar_bloco_linhas(deck: DeckAnaRede, linhas: List[str]):
        """Processa bloco de definição de linhas"""
        for i, linha in enumerate(linhas):
            if linha.strip().startswith("99999"):
                break
            
            partes = linha.split()
            if len(partes) >= 6 and partes[0].isdigit() and partes[1].isdigit():
                try:
                    de_barra = int(partes[0])
                    para_barra = int(partes[1])
                    
                    r = float(partes[2]) if len(partes) > 2 else 0.01
                    x = float(partes[3]) if len(partes) > 3 else 0.1
                    b = float(partes[4]) if len(partes) > 4 else 0.0
                    
                    linha_obj = Linha(
                        de_barra=de_barra,
                        para_barra=para_barra,
                        r_pu=r,
                        x_pu=x,
                        b_pu=b
                    )
                    deck.linhas.append(linha_obj)
                    
                except ValueError:
                    continue

# -----------------------------------------------------------------------------
# WIDGETS DE VISUALIZAÇÃO
# -----------------------------------------------------------------------------

class MplCanvas(FigureCanvas):
    """Canvas Matplotlib integrado ao PySide6"""
    
    def __init__(self, parent=None, width=10, height=8, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

class WidgetVisualizacaoRede(QWidget):
    """Widget para visualização gráfica da rede"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.deck_atual = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Controles
        controles_layout = QHBoxLayout()
        
        self.combo_tipo_visualizacao = QComboBox()
        self.combo_tipo_visualizacao.addItems([
            "Topologia da Rede",
            "Fluxo de Potência Ativa (P)",
            "Fluxo de Potência Reativa (Q)",
            "Tensão (pu)",
            "Carga/Geração"
        ])
        controles_layout.addWidget(QLabel("Tipo de Visualização:"))
        controles_layout.addWidget(self.combo_tipo_visualizacao)
        
        self.btn_atualizar = QPushButton("Atualizar Visualização")
        self.btn_atualizar.clicked.connect(self.atualizar_visualizacao)
        controles_layout.addWidget(self.btn_atualizar)
        
        controles_layout.addStretch()
        layout.addLayout(controles_layout)
        
        # Canvas Matplotlib
        self.canvas = MplCanvas(self, width=12, height=10)
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
    def carregar_deck(self, deck: DeckAnaRede):
        """Carrega um deck para visualização"""
        self.deck_atual = deck
        self.atualizar_visualizacao()
        
    def atualizar_visualizacao(self):
        """Atualiza a visualização gráfica"""
        if not self.deck_atual:
            return
            
        tipo = self.combo_tipo_visualizacao.currentText()
        self.canvas.axes.clear()
        
        try:
            # Gera posições aleatórias para as barras se não houver coordenadas
            barras = list(self.deck_atual.barras.values())
            n_barras = len(barras)
            
            # Posicionamento circular das barras
            angulos = np.linspace(0, 2 * np.pi, n_barras, endpoint=False)
            raio = 10
            x = raio * np.cos(angulos)
            y = raio * np.sin(angulos)
            
            # Atualiza coordenadas das barras
            for i, barra in enumerate(barras):
                barra.x = x[i]
                barra.y = y[i]
            
            # Plota linhas
            for linha in self.deck_atual.linhas:
                if linha.de_barra in self.deck_atual.barras and linha.para_barra in self.deck_atual.barras:
                    barra_de = self.deck_atual.barras[linha.de_barra]
                    barra_para = self.deck_atual.barras[linha.para_barra]
                    
                    self.canvas.axes.plot(
                        [barra_de.x, barra_para.x],
                        [barra_de.y, barra_para.y],
                        'gray', alpha=0.5, linewidth=2
                    )
            
            # Plota barras com cores baseadas no tipo
            cores = []
            tamanhos = []
            for barra in barras:
                if barra.tipo == "REF":
                    cores.append('red')
                    tamanhos.append(150)
                elif barra.tipo == "PV":
                    cores.append('green')
                    tamanhos.append(100)
                else:  # PQ
                    cores.append('blue')
                    tamanhos.append(80)
                
                # Adiciona label
                self.canvas.axes.text(
                    barra.x + 0.3, barra.y + 0.3,
                    f"{barra.numero}",
                    fontsize=9, ha='center'
                )
            
            # Scatter plot das barras
            self.canvas.axes.scatter(
                [b.x for b in barras],
                [b.y for b in barras],
                s=tamanhos, c=cores, edgecolors='black', zorder=5
            )
            
            # Adiciona legenda
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='red', edgecolor='black', label='Barra de Referência'),
                Patch(facecolor='green', edgecolor='black', label='Barra PV'),
                Patch(facecolor='blue', edgecolor='black', label='Barra PQ'),
            ]
            self.canvas.axes.legend(handles=legend_elements, loc='upper right')
            
            # Configurações do gráfico
            self.canvas.axes.set_title(f"Rede: {self.deck_atual.nome}")
            self.canvas.axes.set_xlabel("Coordenada X")
            self.canvas.axes.set_ylabel("Coordenada Y")
            self.canvas.axes.grid(True, linestyle='--', alpha=0.7)
            self.canvas.axes.set_aspect('equal')
            
            # Ajusta limites
            margin = 2
            x_min = min([b.x for b in barras]) - margin
            x_max = max([b.x for b in barras]) + margin
            y_min = min([b.y for b in barras]) - margin
            y_max = max([b.y for b in barras]) + margin
            self.canvas.axes.set_xlim(x_min, x_max)
            self.canvas.axes.set_ylim(y_min, y_max)
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"Erro ao plotar rede: {e}")

class WidgetTabelaDados(QWidget):
    """Widget para exibição de dados tabulares"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Abas para diferentes tipos de dados
        self.tab_widget = QTabWidget()
        
        # Tabela de barras
        self.tabela_barras = QTableWidget()
        self.tabela_barras.setColumnCount(9)
        self.tabela_barras.setHorizontalHeaderLabels([
            "Número", "Nome", "Tipo", "Tensão (pu)", "Ângulo (°)",
            "P Geração (MW)", "Q Geração (MVAr)", "P Carga (MW)", "Q Carga (MVAr)"
        ])
        self.tabela_barras.horizontalHeader().setStretchLastSection(True)
        
        # Tabela de linhas
        self.tabela_linhas = QTableWidget()
        self.tabela_linhas.setColumnCount(7)
        self.tabela_linhas.setHorizontalHeaderLabels([
            "De Barra", "Para Barra", "Nome", "R (pu)", "X (pu)", "B (pu)", "Taxa (MVA)"
        ])
        
        # Adiciona abas
        self.tab_widget.addTab(self.tabela_barras, "Barras")
        self.tab_widget.addTab(self.tabela_linhas, "Linhas")
        
        layout.addWidget(self.tab_widget)
        
    def carregar_deck(self, deck: DeckAnaRede):
        """Carrega dados do deck nas tabelas"""
        self.carregar_barras(deck)
        self.carregar_linhas(deck)
        
    def carregar_barras(self, deck: DeckAnaRede):
        """Carrega dados das barras na tabela"""
        self.tabela_barras.setRowCount(len(deck.barras))
        
        for i, (num_barra, barra) in enumerate(deck.barras.items()):
            self.tabela_barras.setItem(i, 0, QTableWidgetItem(str(num_barra)))
            self.tabela_barras.setItem(i, 1, QTableWidgetItem(barra.nome))
            self.tabela_barras.setItem(i, 2, QTableWidgetItem(barra.tipo))
            self.tabela_barras.setItem(i, 3, QTableWidgetItem(f"{barra.tensao_pu:.4f}"))
            self.tabela_barras.setItem(i, 4, QTableWidgetItem(f"{barra.angulo_graus:.2f}"))
            self.tabela_barras.setItem(i, 5, QTableWidgetItem(f"{barra.p_ger_mw:.2f}"))
            self.tabela_barras.setItem(i, 6, QTableWidgetItem(f"{barra.q_ger_mvar:.2f}"))
            self.tabela_barras.setItem(i, 7, QTableWidgetItem(f"{barra.p_carga_mw:.2f}"))
            self.tabela_barras.setItem(i, 8, QTableWidgetItem(f"{barra.q_carga_mvar:.2f}"))
        
        self.tabela_barras.resizeColumnsToContents()
        
    def carregar_linhas(self, deck: DeckAnaRede):
        """Carrega dados das linhas na tabela"""
        self.tabela_linhas.setRowCount(len(deck.linhas))
        
        for i, linha in enumerate(deck.linhas):
            self.tabela_linhas.setItem(i, 0, QTableWidgetItem(str(linha.de_barra)))
            self.tabela_linhas.setItem(i, 1, QTableWidgetItem(str(linha.para_barra)))
            self.tabela_linhas.setItem(i, 2, QTableWidgetItem(linha.nome))
            self.tabela_linhas.setItem(i, 3, QTableWidgetItem(f"{linha.r_pu:.6f}"))
            self.tabela_linhas.setItem(i, 4, QTableWidgetItem(f"{linha.x_pu:.6f}"))
            self.tabela_linhas.setItem(i, 5, QTableWidgetItem(f"{linha.b_pu:.6f}"))
            self.tabela_linhas.setItem(i, 6, QTableWidgetItem(f"{linha.taxa_mva:.2f}"))
        
        self.tabela_linhas.resizeColumnsToContents()

# -----------------------------------------------------------------------------
# THREAD PARA CARREGAMENTO DE ARQUIVOS
# -----------------------------------------------------------------------------

class WorkerCarregamento(QThread):
    """Thread para carregamento assíncrono de arquivos .PWF"""
    
    progresso = Signal(int)
    arquivo_carregado = Signal(str, DeckAnaRede)
    finalizado = Signal(list)
    erro = Signal(str)
    
    def __init__(self, diretorio: str):
        super().__init__()
        self.diretorio = diretorio
        self.cancelar = False
        
    def run(self):
        try:
            arquivos = list(Path(self.diretorio).glob("*.PWF"))
            decks = []
            
            for i, arquivo in enumerate(arquivos):
                if self.cancelar:
                    break
                    
                try:
                    deck = ParserPWF.parse_arquivo(str(arquivo))
                    self.arquivo_carregado.emit(str(arquivo), deck)
                    decks.append(deck)
                    
                except Exception as e:
                    self.erro.emit(f"Erro ao processar {arquivo.name}: {str(e)}")
                
                # Emite progresso
                progresso = int((i + 1) / len(arquivos) * 100)
                self.progresso.emit(progresso)
            
            self.finalizado.emit(decks)
            
        except Exception as e:
            self.erro.emit(f"Erro no carregamento: {str(e)}")

# -----------------------------------------------------------------------------
# JANELA PRINCIPAL
# -----------------------------------------------------------------------------

class MainWindow(QMainWindow):
    """Janela principal da aplicação"""
    
    def __init__(self):
        super().__init__()
        self.decks = {}  # nome_arquivo -> DeckAnaRede
        self.deck_selecionado = None
        self.worker_carregamento = None
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        self.setWindowTitle("Visualizador de Decks anaRede")
        self.setGeometry(100, 100, 1600, 900)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Painel esquerdo - lista de arquivos e controles
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Grupo de controles
        grupo_controles = QGroupBox("Controles")
        controles_layout = QVBoxLayout()
        
        # Botão para selecionar diretório
        self.btn_selecionar_diretorio = QPushButton("Selecionar Diretório com .PWF")
        self.btn_selecionar_diretorio.setMinimumHeight(40)
        controles_layout.addWidget(self.btn_selecionar_diretorio)
        
        # Label do diretório atual
        self.label_diretorio = QLabel("Nenhum diretório selecionado")
        self.label_diretorio.setWordWrap(True)
        controles_layout.addWidget(self.label_diretorio)
        
        # Progresso
        self.label_progresso = QLabel("")
        controles_layout.addWidget(self.label_progresso)
        
        # Botão para cancelar carregamento
        self.btn_cancelar = QPushButton("Cancelar Carregamento")
        self.btn_cancelar.setEnabled(False)
        controles_layout.addWidget(self.btn_cancelar)
        
        controles_layout.addStretch()
        grupo_controles.setLayout(controles_layout)
        left_layout.addWidget(grupo_controles)
        
        # Lista de arquivos
        grupo_arquivos = QGroupBox("Arquivos .PWF Carregados")
        arquivos_layout = QVBoxLayout()
        
        self.lista_arquivos = QListWidget()
        self.lista_arquivos.setMinimumWidth(300)
        arquivos_layout.addWidget(self.lista_arquivos)
        
        grupo_arquivos.setLayout(arquivos_layout)
        left_layout.addWidget(grupo_arquivos)
        
        # Adiciona painel esquerdo ao layout principal
        main_layout.addWidget(left_panel)
        
        # Splitter para área direita
        splitter = QSplitter(Qt.Horizontal)
        
        # Widget de visualização
        self.widget_visualizacao = WidgetVisualizacaoRede()
        splitter.addWidget(self.widget_visualizacao)
        
        # Widget de tabelas
        self.widget_tabelas = WidgetTabelaDados()
        splitter.addWidget(self.widget_tabelas)
        
        # Configura proporções do splitter
        splitter.setSizes([800, 400])
        
        main_layout.addWidget(splitter, 1)  # 1 = stretch factor
        
    def setup_connections(self):
        """Configura conexões de sinais e slots"""
        self.btn_selecionar_diretorio.clicked.connect(self.selecionar_diretorio)
        self.btn_cancelar.clicked.connect(self.cancelar_carregamento)
        self.lista_arquivos.itemClicked.connect(self.selecionar_arquivo)
        
    def selecionar_diretorio(self):
        """Seleciona diretório contendo arquivos .PWF"""
        diretorio = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Diretório com Arquivos .PWF",
            str(Path.home()),
            QFileDialog.ShowDirsOnly
        )
        
        if diretorio:
            self.label_diretorio.setText(f"Diretório: {diretorio}")
            self.carregar_arquivos_diretorio(diretorio)
            
    def carregar_arquivos_diretorio(self, diretorio: str):
        """Carrega todos os arquivos .PWF do diretório"""
        # Cancela carregamento anterior se existir
        if self.worker_carregamento and self.worker_carregamento.isRunning():
            self.worker_carregamento.cancelar = True
            self.worker_carregamento.wait()
        
        # Limpa dados anteriores
        self.decks.clear()
        self.lista_arquivos.clear()
        
        # Cria e configura worker
        self.worker_carregamento = WorkerCarregamento(diretorio)
        self.worker_carregamento.progresso.connect(self.atualizar_progresso)
        self.worker_carregamento.arquivo_carregado.connect(self.adicionar_deck)
        self.worker_carregamento.finalizado.connect(self.carregamento_finalizado)
        self.worker_carregamento.erro.connect(self.mostrar_erro)
        
        # Habilita/desabilita controles
        self.btn_selecionar_diretorio.setEnabled(False)
        self.btn_cancelar.setEnabled(True)
        
        # Inicia carregamento
        self.worker_carregamento.start()
        
    def atualizar_progresso(self, valor: int):
        """Atualiza barra de progresso"""
        self.label_progresso.setText(f"Carregando... {valor}%")
        
    def adicionar_deck(self, caminho_arquivo: str, deck: DeckAnaRede):
        """Adiciona um deck carregado à lista"""
        nome_arquivo = Path(caminho_arquivo).name
        self.decks[nome_arquivo] = deck
        
        # Adiciona à lista de arquivos
        item = QListWidgetItem(nome_arquivo)
        self.lista_arquivos.addItem(item)
        
    def carregamento_finalizado(self, decks: List[DeckAnaRede]):
        """Chamado quando o carregamento é finalizado"""
        self.label_progresso.setText(f"Carregamento concluído: {len(decks)} arquivos")
        self.btn_selecionar_diretorio.setEnabled(True)
        self.btn_cancelar.setEnabled(False)
        
        if decks:
            self.lista_arquivos.setCurrentRow(0)
            self.selecionar_arquivo(self.lista_arquivos.item(0))
            
    def cancelar_carregamento(self):
        """Cancela o carregamento em andamento"""
        if self.worker_carregamento and self.worker_carregamento.isRunning():
            self.worker_carregamento.cancelar = True
            self.btn_cancelar.setEnabled(False)
            
    def selecionar_arquivo(self, item):
        """Seleciona um arquivo da lista para visualização"""
        if not item:
            return
            
        nome_arquivo = item.text()
        deck = self.decks.get(nome_arquivo)
        
        if deck:
            self.deck_selecionado = deck
            
            # Atualiza widgets
            self.widget_visualizacao.carregar_deck(deck)
            self.widget_tabelas.carregar_deck(deck)
            
            # Atualiza título da janela
            self.setWindowTitle(f"Visualizador de Decks anaRede - {nome_arquivo}")
            
    def mostrar_erro(self, mensagem: str):
        """Exibe mensagem de erro"""
        QMessageBox.critical(self, "Erro", mensagem)
        
    def closeEvent(self, event):
        """Manipula evento de fechamento da janela"""
        # Cancela carregamento em andamento
        if self.worker_carregamento and self.worker_carregamento.isRunning():
            self.worker_carregamento.cancelar = True
            self.worker_carregamento.wait()
            
        event.accept()

# -----------------------------------------------------------------------------
# FUNÇÃO PRINCIPAL
# -----------------------------------------------------------------------------

def main():
    """Função principal da aplicação"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Estilo moderno
    
    # Configuração de fonte
    font = QFont()
    font.setPointSize(10)
    app.setFont(font)
    
    # Cria e mostra janela principal
    janela = MainWindow()
    janela.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()