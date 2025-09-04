import sys
import os
import webbrowser
import subprocess
import pandas as pd
import pandapower as pp
import pandapower.plotting as plot
import pandapower.networks as pn
import matplotlib.pyplot as plt
import traceback
from matplotlib.lines import Line2D
import matplotlib.colors as mcolors
import numpy as np

# Define o backend Qt para o Matplotlib
os.environ['QT_API'] = 'PySide6'

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QFileDialog,
    QMessageBox, QHeaderView, QGroupBox, QSplitter, QLabel, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# =============================================================================
# ESTILO DA APLICAÇÃO (PALETA DE CORES ONS)
# =============================================================================
STYLESHEET = """
    QMainWindow, QWidget { background-color: #f0f2f5; }
    QGroupBox {
        font-family: 'Inter', sans-serif; font-size: 11pt; font-weight: bold;
        color: #003366; border: 1px solid #c8d2dc; border-radius: 8px;
        margin-top: 1ex; background-color: #ffffff;
    }
    QGroupBox::title {
        subcontrol-origin: margin; subcontrol-position: top center;
        padding: 0 10px; background-color: #f0f2f5; color: #003366;
    }
    QPushButton {
        font-family: 'Inter', sans-serif; font-size: 10pt; font-weight: bold;
        color: white; background-color: #005c99; border: none;
        padding: 10px; border-radius: 5px;
    }
    QPushButton:hover { background-color: #0073b3; }
    QPushButton:pressed { background-color: #004c80; }
    QHeaderView::section {
        background-color: #003366; color: white; padding: 5px;
        border: 1px solid #002244; font-weight: bold;
    }
"""

# =============================================================================
# 1. MODELO (Lógica de Dados e Pandapower)
# =============================================================================
class RedeEletricaModel:
    """
    Encapsula toda a lógica de dados, criação e cálculo das redes elétricas.
    """
    def __init__(self):
        self.net = None
        self.network_name = ""
        self.dataframes = {}
        self.bus_map = {}

    def load_network(self, network_name):
        """ Carrega uma rede padrão do pandapower. """
        self.network_name = network_name
        self.dataframes.clear()
        try:
            if network_name == "IEEE 14": self.net = pn.case14()
            elif network_name == "IEEE 30": self.net = pn.case_ieee30()
            elif network_name == "IEEE 57": self.net = pn.case57()
            elif network_name == "IEEE 118": self.net = pn.case118()
            else:
                return False, f"Caso de rede '{network_name}' desconhecido."
            
            self.net.name = network_name
            return True, f"Rede '{network_name}' carregada com sucesso."
        except Exception as e:
            return False, f"Erro ao carregar a rede '{network_name}': {e}"

    def create_sin45_dataset_file(self, filename='SIN_45_barras_dataset.xlsx'):
        """ Cria um arquivo Excel com os dados do sistema SIN 45 Barras. """
        # Dicionários com todos os dados do SIN 45 Barras
        nomes_barras = {'Barra': list(range(1, 46)),'Nome': ['IVAIPORA.525', 'LONDRINA.525', 'BARRACAO13.8', 'SIDEROPOL230', 'FARROUPIL230','P.FUNDO.13.8', 'P.FUNDO.230', 'XANXERE.230', 'P.BRANCO.230', 'S.OSORIO13.8','S.OSORIO.230', 'AREIA.230', 'S.MATEUS.230', 'CURITIBA.230', 'JOINVILE.230','BLUMENAU.230', 'R.QUEIMAD230', 'F.AREIA.13.8', 'AREIA.525', 'CURITIBA.525','CUR.NORTE525', 'BLUMENAU.525', 'BARRACAO.525', 'GRAVATAI.525', 'V.AIRES.525','PINHEIRO.525', 'S.SANTIA13.8', 'S.SANTIAG525', 'J.LAC.A.13.8', 'J.LACERDA138','J.LAC.B.13.8', 'J.LAC.C.13.8', 'J.LACERDA230', 'SEGREDO.13.8', 'SEGREDO.525','CECI.230', 'GRAVATAI.230', 'ITAUBA.13.8', 'ITAUBA.230', 'V.AIRES.230','APUCARANA230', 'LONDRINA.230', 'MARINGA.230', 'C.MOURAO.230', 'FORQUILHI230']}
        reatores = {'Barra': [1, 20, 21, 23, 24, 25],'Susceptância Shunt B(pu)': [-2.000, -1.500, -1.500, -1.000, -1.500, -1.500]}
        dados_rede = {'De': [1, 1, 1, 2, 3, 4, 4, 4, 5, 5, 6, 7, 7, 8, 8, 9, 10, 11, 11, 12, 12, 13, 14, 14, 15, 16, 16, 17, 18, 19, 19, 19, 19, 20, 20, 23, 24, 25, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 36, 36, 38, 39, 41, 41, 41, 42, 43],'Para': [2, 19, 28, 42, 23, 5, 33, 45, 7, 36, 7, 8, 39, 9, 11, 11, 11, 12, 44, 13, 19, 14, 15, 20, 16, 17, 22, 33, 19, 20, 21, 23, 35, 21, 22, 24, 37, 26, 40, 28, 28, 35, 30, 33, 33, 33, 45, 35, 37, 40, 39, 40, 42, 43, 44, 43, 44],'R(pu)': [0.00035, 0.0018, 0.0014, 0.0, 0.0, 0.0386, 0.0096, 0.0033, 0.02315, 0.00885, 0.0, 0.00815, 0.025, 0.0163, 0.0316, 0.0153, 0.0, 0.0306, 0.0172, 0.0245, 0.0, 0.0088, 0.0091, 0.0, 0.0077, 0.0108, 0.0, 0.009, 0.0, 0.0019, 0.0019, 0.0014, 0.0005, 0.0005, 0.0012, 0.0021, 0.0, 0.0022, 0.0, 0.0014, 0.0, 0.0005, 0.0, 0.0, 0.0, 0.0, 0.0129, 0.0, 0.0006971, 0.0061315, 0.0, 0.0202, 0.0051987, 0.011, 0.0229, 0.0086, 0.0181],'X(pu)': [0.00725, 0.0227, 0.0204, 0.0063, 0.0136, 0.1985, 0.0491, 0.0167, 0.1189, 0.0455, 0.046, 0.04175, 0.1548, 0.0835, 0.1621, 0.0861, 0.0114, 0.1523, 0.088, 0.1256, 0.03, 0.0415, 0.04675, 0.0062, 0.0388, 0.05525, 0.0062, 0.046, 0.0067, 0.028, 0.0274, 0.0195, 0.007, 0.0069, 0.0175, 0.0309, 0.0062, 0.03, 0.0062, 0.0195, 0.0114, 0.007, 0.0871, 0.059, 0.0701, 0.045, 0.0657, 0.0068, 0.0035819, 0.0316242, 0.0236, 0.1129, 0.0268149, 0.1184, 0.1174, 0.0442, 0.0929],'B(pu)': [0.8305, 2.2721, 2.4475, 0.0, 0.0, 0.34, 0.0842, 0.2859, 0.2042, 0.07925, 0.0, 0.072, 0.469, 0.144, 0.2784, 0.1344, 0.0, 0.2702, 0.152, 0.2041, 0.0, 0.5211, 0.07975, 0.0, 0.0675, 0.09315, 0.0, 0.07765, 0.0, 3.3576, 3.2867, 2.3968, 0.8392, 0.8216, 2.097, 3.7183, 0.0, 3.83, 0.0, 2.397, 0.0, 0.8392, 0.0, 0.0, 0.0, 0.0, 0.1128, 0.0, 0.0668, 0.5236, 0.0, 0.2062, 0.1905, 0.2027, 0.2027, 0.2868, 0.1607]}
        carga_leve = {'Barra': list(range(1, 46)),'Tipo de Barra (*)': [0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 2, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],'Potência Ativa (MW)': [0.0, 0.0, 1000.0, 0.0, 0.0, 172.0, 0.0, 0.0, 0.0, 736.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1248.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1060.0, 0.0, 72.0, 0.0, 96.0, 192.8, 0.0, 1060.8, 0.0, 0.0, 0.0, 392.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],'Carga Ativa (MW)': [720.1334, 0.0, 0.0, 141.6, 153.0934, 0.0, 136.8, 100.8, 37.2534, 0.0, 224.8, 223.7067, 104.16, 342.36, 248.3734, 339.4934, 94.24, 0.0, 0.0, 0.0, 294.4, 0.0, 139.656, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 100.832, 0.0, 0.0, 0.0, 0.0, 0.0, 650.4, 489.6, 0.0, 323.2, 314.4, 209.6, 183.2, 147.2, 111.2, 72.08],'Carga Reativa (Mvar)': [0.0, 0.0, 0.0, 54.4, 33.6, 0.0, 14.8, 37.6, 11.76, 0.0, 45.2, 48.56, 23.52, -20.0, 112.8, 72.48, 42.48, 0.0, 0.0, 0.0, 55.68, 0.0, -6.56, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 31.84, 0.0, 0.0, 0.0, 0.0, 0.0, 88.0, -364.0, 0.0, 108.0, -88.8, 10.56, 146.4, 48.16, 42.96, 44.24]}
        
        filepath = os.path.join(os.getcwd(), filename)
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            pd.DataFrame(nomes_barras).to_excel(writer, sheet_name='bus', index=False)
            pd.DataFrame(dados_rede).to_excel(writer, sheet_name='line', index=False)
            pd.DataFrame(carga_leve).to_excel(writer, sheet_name='load_gen', index=False)
            pd.DataFrame(reatores).to_excel(writer, sheet_name='shunt', index=False)
        return filepath

    def load_network_from_excel(self, filepath):
        """ Carrega e constrói uma rede a partir de um arquivo Excel. """
        try:
            xls = pd.ExcelFile(filepath)
            self.dataframes = {sheet_name: xls.parse(sheet_name) for sheet_name in xls.sheet_names}
            self.network_name = "SIN 45 Barras"
            
            success, message = self._create_network_from_dataframes()
            if success: self.net.name = self.network_name
            return success, message
        except Exception as e:
            return False, f"Falha ao processar o arquivo Excel: {e}"

    def _create_network_from_dataframes(self):
        """ Lógica interna para construir a rede a partir dos dataframes carregados. """
        df_load_gen = self.dataframes.get('load_gen')
        
        # VALIDAÇÃO DA BARRA SWING (SLACK)
        slack_buses = df_load_gen[df_load_gen['Tipo de Barra (*)'] == 2]
        if len(slack_buses) != 1:
            return False, f"Erro Crítico de Dados: A rede deve ter EXATAMENTE UMA barra de referência (Slack / Tipo 2). Foram encontradas: {len(slack_buses)}."

        self.net = pp.create_empty_network()
        self.bus_map.clear()
        
        df_bus = self.dataframes.get('bus')
        df_line = self.dataframes.get('line')
        df_shunt = self.dataframes.get('shunt')

        for _, row in df_bus.iterrows():
            bus_id = int(row['Barra'])
            name_str = str(row['Nome'])
            try:
                parts = name_str.replace(',', '.').split('.')
                vn_kv = float(parts[-1]) if len(parts) > 1 and parts[-1].replace('.', '', 1).isdigit() else 230.0
            except (ValueError, IndexError): vn_kv = 230.0
            new_idx = pp.create_bus(self.net, name=name_str, vn_kv=vn_kv)
            self.bus_map[bus_id] = new_idx
        
        self.net.bus['min_vm_pu'], self.net.bus['max_vm_pu'] = 0.95, 1.05

        gen_col = next((c for c in df_load_gen.columns if 'pot' in c.lower()), 'Potência Ativa (MW)')
        for _, row in df_load_gen.iterrows():
            bus_idx = self.bus_map.get(int(row['Barra']))
            if bus_idx is None: continue
            if row['Carga Ativa (MW)'] > 0:
                pp.create_load(self.net, bus=bus_idx, p_mw=row['Carga Ativa (MW)'], q_mvar=row['Carga Reativa (Mvar)'])
            if row['Tipo de Barra (*)'] == 2:
                pp.create_ext_grid(self.net, bus=bus_idx, vm_pu=1.0)
            elif row.get(gen_col, 0) > 0:
                pp.create_gen(self.net, bus=bus_idx, p_mw=row[gen_col], vm_pu=1.0)
        
        shunt_col = next((c for c in df_shunt.columns if 'suscept' in c.lower()), None)
        if shunt_col:
            for _, row in df_shunt.iterrows():
                bus_idx = self.bus_map.get(int(row['Barra']))
                if bus_idx is not None:
                    q_mvar = row[shunt_col] * (self.net.bus.vn_kv.at[bus_idx] ** 2)
                    pp.create_shunt(self.net, bus=bus_idx, q_mvar=q_mvar)

        s_base_mva = 100.0
        for _, row in df_line.iterrows():
            from_bus, to_bus = self.bus_map.get(int(row['De'])), self.bus_map.get(int(row['Para']))
            if from_bus is None or to_bus is None: continue
            
            from_vn_kv, to_vn_kv = self.net.bus.vn_kv.at[from_bus], self.net.bus.vn_kv.at[to_bus]
            if abs(from_vn_kv - to_vn_kv) > 1e-3:
                hv_bus, lv_bus = (from_bus, to_bus) if from_vn_kv > to_vn_kv else (to_bus, from_bus)
                pp.create_transformer_from_parameters(self.net, hv_bus=hv_bus, lv_bus=lv_bus, sn_mva=s_base_mva, vn_hv_kv=max(from_vn_kv, to_vn_kv), vn_lv_kv=min(from_vn_kv, to_vn_kv), vkr_percent=row['R(pu)']*100.0, vk_percent=row['X(pu)']*100.0, pfe_kw=0, i0_percent=0)
            else:
                z_base_ohm = (from_vn_kv ** 2) / s_base_mva
                pp.create_line_from_parameters(self.net, from_bus=from_bus, to_bus=to_bus, length_km=1.0, r_ohm_per_km=row['R(pu)']*z_base_ohm, x_ohm_per_km=row['X(pu)']*z_base_ohm, c_nf_per_km=(row['B(pu)']/(2*np.pi*60*z_base_ohm))*1e9, max_i_ka=10.0)
        
        return True, "Rede SIN 45 criada com sucesso."

    def run_power_flow(self):
        """ Executa o fluxo de potência. """
        if self.net is None: return False, "A rede não foi criada."
        try:
            pp.runpp(self.net, algorithm='nr', init='flat')
            return True, "Fluxo de potência calculado com sucesso!"
        except pp.LoadflowNotConverged:
            return False, "ATENÇÃO: O fluxo de potência não convergiu."
        except Exception as e:
            return False, f"Ocorreu um erro inesperado: {e}"

# =============================================================================
# 2. VIEW (Interface Gráfica com PySide6)
# =============================================================================
class MetricsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.gen_card = self._create_metric_card("Geração Total (MW)", "N/A")
        self.load_card = self._create_metric_card("Carga Total (MW)", "N/A")
        layout.addWidget(self.gen_card)
        layout.addWidget(self.load_card)

    def _create_metric_card(self, title, initial_value):
        card = QGroupBox(title)
        card_layout = QVBoxLayout(card)
        value_label = QLabel(initial_value)
        font = QFont("Segoe UI", 20, QFont.Bold)
        value_label.setFont(font)
        value_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(value_label)
        return card

    def update_metrics(self, total_gen_mw, total_load_mw):
        self.gen_card.findChild(QLabel).setText(f"{total_gen_mw:.2f}")
        self.load_card.findChild(QLabel).setText(f"{total_load_mw:.2f}")

class NetworkCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig, self.ax = plt.subplots(figsize=(16, 12))
        super().__init__(self.fig)
        self.setParent(parent)

    def plot_network(self, net, network_name, bus_map={}):
        self.ax.clear()
        if not (net and len(net.bus) > 0):
            self.ax.text(0.5, 0.5, 'Carregue uma rede para visualizar.', ha='center')
            self.draw()
            return
            
        if not hasattr(net, 'bus_geodata') or net.bus_geodata.empty:
            plot.create_generic_coordinates(net, overwrite=True)

        collections = []
        handles = []
        
        # --- Lógica de Plotagem para SIN 45 ---
        if network_name == "SIN 45 Barras":
            ramo1_pairs = [(1,19),(12,19),(12,13),(13,14),(14,15),(15,16),(16,17),(17,30)]
            ramo2_pairs = [(1,28),(26,28),(25,26),(24,25),(23,24),(3,23)]
            ramo3_pairs = [(4,5),(5,7),(7,8),(8,9)]
            ramos = {
                "Ramo 1 (Verde)": {"pairs": ramo1_pairs, "color": "green"},
                "Ramo 2 (Azul)": {"pairs": ramo2_pairs, "color": "blue"},
                "Ramo 3 (Vermelho)": {"pairs": ramo3_pairs, "color": "red"}
            }
            
            plotted_lines = set()
            for name, data in ramos.items():
                indices = []
                for b1, b2 in data["pairs"]:
                    idx1, idx2 = bus_map.get(b1), bus_map.get(b2)
                    if idx1 is not None and idx2 is not None:
                        line = net.line[((net.line.from_bus == idx1) & (net.line.to_bus == idx2)) | ((net.line.from_bus == idx2) & (net.line.to_bus == idx1))]
                        if not line.empty:
                            indices.append(line.index[0])
                if indices:
                    collections.append(plot.create_line_collection(net, lines=indices, color=data["color"], use_bus_geodata=True))
                    plotted_lines.update(indices)
                    handles.append(plt.Line2D([0], [0], color=data["color"], lw=2, label=name))

            other_lines = list(set(net.line.index) - plotted_lines)
            collections.append(plot.create_line_collection(net, lines=other_lines, color="grey", use_bus_geodata=True))
            handles.append(plt.Line2D([0], [0], color='grey', lw=2, label='Outras Linhas'))

        # --- Lógica de Plotagem para Casos IEEE ---
        else:
            collections.append(plot.create_line_collection(net, color="grey", use_bus_geodata=True))
            handles.append(plt.Line2D([0], [0], color='grey', lw=2, label='Linha'))

        collections.append(plot.create_bus_collection(net, color="blue", size=0.04))
        handles.append(plt.Line2D([0], [0], color='blue', marker='o', lw=0, label='Barra'))

        if len(net.trafo) > 0:
            collections.append(plot.create_trafo_collection(net, color='purple'))
            handles.append(plt.Line2D([0], [0], color='purple', lw=2, label='Transformador'))
        
        # Desenha todas as coleções de uma vez
        plot.draw_collections(collections, ax=self.ax)
        
        self.ax.legend(handles=handles, loc='best')
        self.ax.set_title(f"Diagrama Unifilar - {network_name}")
        self.fig.tight_layout()
        self.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador de Redes Elétricas")
        self.setGeometry(100, 100, 1600, 900)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # --- Painel Esquerdo (Controles e Tabelas) ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        splitter.addWidget(left_panel)

        # --- Painel Direito (Visualização) ---
        right_panel = QGroupBox("Visualização da Rede")
        right_layout = QVBoxLayout(right_panel)
        splitter.addWidget(right_panel)
        
        splitter.setSizes([600, 1000])

        self.metrics_widget = MetricsWidget()
        right_layout.addWidget(self.metrics_widget)

        self.network_canvas = NetworkCanvas(self)
        right_layout.addWidget(self.network_canvas)

        # Grupo de Controles
        controls_group = QGroupBox("Controles da Simulação")
        controls_layout = QVBoxLayout(controls_group)
        
        # Botões para Casos IEEE
        ieee_layout = QHBoxLayout()
        self.btn_case14 = QPushButton("IEEE 14")
        self.btn_case30 = QPushButton("IEEE 30")
        self.btn_case57 = QPushButton("IEEE 57")
        self.btn_case118 = QPushButton("IEEE 118")
        ieee_layout.addWidget(self.btn_case14)
        ieee_layout.addWidget(self.btn_case30)
        ieee_layout.addWidget(self.btn_case57)
        ieee_layout.addWidget(self.btn_case118)
        
        # Botões SIN 45 e Ações
        actions_layout = QHBoxLayout()
        self.btn_generate_sin45 = QPushButton("Gerar e Carregar SIN 45")
        self.btn_run_pf = QPushButton("▶ Executar Fluxo de Potência")
        self.btn_run_pf.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        actions_layout.addWidget(self.btn_generate_sin45)
        actions_layout.addStretch()
        actions_layout.addWidget(self.btn_run_pf)
        
        controls_layout.addLayout(ieee_layout)
        controls_layout.addLayout(actions_layout)
        left_layout.addWidget(controls_group)

        # Abas para tabelas de dados
        self.tabs = QTabWidget()
        self.tables = {}
        left_layout.addWidget(self.tabs)

    def add_table_tab(self, name, df):
        if name not in self.tables:
            table = QTableWidget()
            self.tables[name] = table
            self.tabs.addTab(table, name.replace('_', ' ').capitalize())
        
        table = self.tables[name]
        table.setRowCount(df.shape[0])
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels(df.columns)
        for i, row in enumerate(df.itertuples(index=False)):
            for j, value in enumerate(row):
                table.setItem(i, j, QTableWidgetItem(str(value)))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

# =============================================================================
# 3. CONTROLLER (Conecta a View com o Model)
# =============================================================================
class AppController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.view = MainWindow()
        self.model = RedeEletricaModel()
        self._connect_signals()
        self.view.show()

    def _connect_signals(self):
        # Conecta botões dos casos IEEE
        self.view.btn_case14.clicked.connect(lambda: self.load_ieee_case("IEEE 14"))
        self.view.btn_case30.clicked.connect(lambda: self.load_ieee_case("IEEE 30"))
        self.view.btn_case57.clicked.connect(lambda: self.load_ieee_case("IEEE 57"))
        self.view.btn_case118.clicked.connect(lambda: self.load_ieee_case("IEEE 118"))
        
        # Conecta outros botões
        self.view.btn_generate_sin45.clicked.connect(self.generate_and_load_sin45)
        self.view.btn_run_pf.clicked.connect(self.run_power_flow)

    def run(self):
        sys.exit(self.app.exec())
    
    def load_ieee_case(self, case_name):
        """ Carrega um caso padrão IEEE e atualiza a interface. """
        success, message = self.model.load_network(case_name)
        if success:
            self._update_view_after_load(f"Rede {case_name} carregada.")
        else:
            QMessageBox.critical(self.view, "Erro", message)

    def generate_and_load_sin45(self):
        """ Gera o dataset do SIN 45, carrega e atualiza a interface. """
        try:
            filepath = self.model.create_sin45_dataset_file()
            success, message = self.model.load_network_from_excel(filepath)
            if success:
                self._update_view_after_load(f"Dataset SIN 45 gerado e carregado de:\n{filepath}")
            else:
                 QMessageBox.critical(self.view, "Erro", message)
        except Exception as e:
            QMessageBox.critical(self.view, "Erro", f"Falha ao gerar o dataset SIN 45: {e}")

    def _update_view_after_load(self, status_message):
        """ Função auxiliar para atualizar a UI após carregar uma rede. """
        self.view.tabs.clear()
        self.view.tables.clear()
        
        # Adiciona tabelas de dados da rede (se disponíveis)
        self.view.add_table_tab("bus", self.model.net.bus)
        self.view.add_table_tab("line", self.model.net.line)
        self.view.add_table_tab("load", self.model.net.load)
        self.view.add_table_tab("gen", self.model.net.gen)
        
        self.view.network_canvas.plot_network(self.model.net, self.model.network_name, self.model.bus_map)
        self.view.metrics_widget.update_metrics(0, 0)
        QMessageBox.information(self.view, "Sucesso", status_message)

    def run_power_flow(self):
        """ Executa o fluxo de potência e atualiza os resultados. """
        try:
            success, message = self.model.run_power_flow()
            if success:
                QMessageBox.information(self.view, "Sucesso", message)
                # Adiciona ou atualiza tabelas de resultados
                self.view.add_table_tab("res_bus", self.model.net.res_bus)
                self.view.add_table_tab("res_line", self.model.net.res_line)
                
                total_gen = self.model.net.res_gen.p_mw.sum() + self.model.net.res_ext_grid.p_mw.sum()
                total_load = self.model.net.res_load.p_mw.sum()
                self.view.metrics_widget.update_metrics(total_gen, total_load)
                # Atualiza o diagrama após o fluxo de potência
                self.view.network_canvas.plot_network(self.model.net, self.model.network_name, self.model.bus_map)
            else:
                QMessageBox.warning(self.view, "Falha", message)
        except Exception as e:
            QMessageBox.critical(self.view, "Erro Crítico", f"Ocorreu um erro durante o fluxo de potência: {e}")

# =============================================================================
# 4. PONTO DE ENTRADA DA APLICAÇÃO
# =============================================================================
if __name__ == '__main__':
    controller = AppController()
    controller.run()

