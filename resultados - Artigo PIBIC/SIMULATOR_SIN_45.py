import sys
import os

# --- CORREÇÃO IMPORTANTE ---
# Adicione esta linha ANTES de importar matplotlib ou PySide6.
# Ela informa ao Matplotlib para usar o PySide6 como seu backend Qt.
os.environ['QT_API'] = 'PySide6'

import pandas as pd
import pandapower as pp
import pandapower.plotting as plot
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QFileDialog,
    QMessageBox, QHeaderView, QGroupBox, QSplitter, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# =============================================================================
# 1. MODELO (Lógica de Dados e Pandapower)
# =============================================================================
class PowerSystemModel:
    """
    Gerencia todos os dados, criação da rede pandapower e cálculos.
    """
    def __init__(self):
        self.net = None
        self.dataframes = {}

    def create_sin45_dataset_file(self, filename='SIN_45_barras_dataset.xlsx'):
        """
        Cria um arquivo Excel com os dados do sistema SIN 45 Barras.
        Retorna o caminho completo do arquivo criado.
        """
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

    def load_data_from_excel(self, filepath):
        """Carrega dados de um arquivo Excel em um dicionário de DataFrames."""
        try:
            xls = pd.ExcelFile(filepath)
            self.dataframes = {sheet_name: pd.read_excel(xls, sheet_name) for sheet_name in xls.sheet_names}
            return self.dataframes
        except Exception as e:
            raise ValueError(f"Não foi possível ler o arquivo Excel: {e}")

    def create_network_from_dataframes(self):
        """Cria uma rede pandapower a partir dos DataFrames carregados."""
        if not self.dataframes:
            raise ValueError("Nenhum dado carregado para criar a rede.")

        self.net = pp.create_empty_network()
        
        df_bus = self.dataframes.get('bus')
        df_load_gen = self.dataframes.get('load_gen')
        if df_bus is None or df_load_gen is None:
            raise ValueError("Abas 'bus' e 'load_gen' são necessárias.")

        for col in ['Barra', 'Tipo de Barra (*)', 'Potência Ativa (MW)', 'Carga Ativa (MW)', 'Carga Reativa (Mvar)']:
            if col in df_load_gen.columns:
                df_load_gen[col] = pd.to_numeric(df_load_gen[col], errors='coerce').fillna(0)
        
        df_bus['Barra'] = pd.to_numeric(df_bus['Barra'], errors='coerce').fillna(0)

        bus_map = {}
        for _, row in df_bus.iterrows():
            bus_id = int(row['Barra'])
            try:
                name_str = str(row['Nome'])
                parts = name_str.replace(',', '.').split('.')
                if len(parts) > 1 and parts[-1].isdigit():
                    vn_kv = float(parts[-1])
                else:
                    numeric_part = ''.join(filter(lambda x: x.isdigit() or x == '.', name_str))
                    vn_kv = float(numeric_part[-4:]) if '.' in numeric_part else float(numeric_part)
            except (ValueError, IndexError):
                vn_kv = 230.0

            new_idx = pp.create_bus(self.net, name=row['Nome'], vn_kv=vn_kv)
            bus_map[bus_id] = new_idx

        for _, row in df_load_gen.iterrows():
            if row['Carga Ativa (MW)'] > 0:
                bus_idx = bus_map.get(int(row['Barra']))
                if bus_idx is not None:
                    pp.create_load(self.net, bus=bus_idx, p_mw=row['Carga Ativa (MW)'], q_mvar=row['Carga Reativa (Mvar)'])

        for _, row in df_load_gen.iterrows():
            bus_idx = bus_map.get(int(row['Barra']))
            if bus_idx is None: continue
            
            is_slack = row['Tipo de Barra (*)'] == 2
            is_gen = row['Potência Ativa (MW)'] > 0

            if is_gen:
                if is_slack:
                    pp.create_ext_grid(self.net, bus=bus_idx, vm_pu=1.0, name="Slack Bus")
                else:
                    pp.create_gen(self.net, bus=bus_idx, p_mw=row['Potência Ativa (MW)'], vm_pu=1.0)

        df_line = self.dataframes.get('line')
        if df_line is not None:
            for col in ['De', 'Para', 'R(pu)', 'X(pu)', 'B(pu)']:
                 if col in df_line.columns:
                    df_line[col] = pd.to_numeric(df_line[col], errors='coerce').fillna(0)

            s_base_mva = 100.0
            for _, row in df_line.iterrows():
                from_bus = bus_map.get(int(row['De']))
                to_bus = bus_map.get(int(row['Para']))
                if from_bus is None or to_bus is None: continue
                
                vn_kv = self.net.bus.vn_kv.at[from_bus]
                z_base_ohm = (vn_kv ** 2) / s_base_mva
                
                r_ohm = row['R(pu)'] * z_base_ohm
                x_ohm = row['X(pu)'] * z_base_ohm
                
                y_base_siemens = 1 / z_base_ohm
                b_siemens = row['B(pu)'] * y_base_siemens
                c_nf = (b_siemens / (2 * 3.14159 * 60)) * 1e9 if b_siemens > 0 else 0
                
                length_km = 1.0 # Comprimento arbitrário pois os parâmetros já estão totais
                
                from_vn_kv = self.net.bus.vn_kv.at[from_bus]
                to_vn_kv = self.net.bus.vn_kv.at[to_bus]

                # Se as tensões das barras forem diferentes, é um transformador
                if abs(from_vn_kv - to_vn_kv) > 1e-3: # Usar uma tolerância para comparação de float
                    hv_bus, lv_bus = (from_bus, to_bus) if from_vn_kv > to_vn_kv else (to_bus, from_bus)
                    
                    pp.create_transformer_from_parameters(
                        self.net,
                        hv_bus=hv_bus,
                        lv_bus=lv_bus,
                        sn_mva=s_base_mva,
                        vn_hv_kv=max(from_vn_kv, to_vn_kv),
                        vn_lv_kv=min(from_vn_kv, to_vn_kv),
                        vkr_percent=row['R(pu)'] * 100.0,
                        vk_percent=row['X(pu)'] * 100.0,
                        pfe_kw=0,      # Sem dados para perdas no ferro
                        i0_percent=0,  # Sem dados para corrente de excitação
                        name=f"Trafo {row['De']}-{row['Para']}"
                    )
                else: # Caso contrário, é uma linha de transmissão
                    pp.create_line_from_parameters(self.net, from_bus=from_bus, to_bus=to_bus, length_km=length_km,
                                                   r_ohm_per_km=r_ohm/length_km, x_ohm_per_km=x_ohm/length_km,
                                                   c_nf_per_km=c_nf/length_km, max_i_ka=0.5,
                                                   name=f"Linha {row['De']}-{row['Para']}")

        return self.net

    def run_power_flow(self):
        if self.net is None:
            raise ValueError("A rede não foi criada.")
        try:
            pp.runpp(self.net)
            return True, "Fluxo de potência executado com sucesso."
        except Exception as e:
            return False, f"Falha no fluxo de potência: {e}"

# =============================================================================
# 2. VIEW (Interface Gráfica com PySide6)
# =============================================================================
class MetricsWidget(QWidget):
    """Um widget para exibir as métricas da rede em cards."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)

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
        card.setStyleSheet("""
            QGroupBox {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
            }
        """)
        return card

    def update_metrics(self, total_gen_mw, total_load_mw):
        gen_label = self.gen_card.findChild(QLabel)
        load_label = self.load_card.findChild(QLabel)
        gen_label.setText(f"{total_gen_mw:.2f}")
        load_label.setText(f"{total_load_mw:.2f}")

class NetworkCanvas(FigureCanvas):
    """Widget para exibir o gráfico da rede Matplotlib."""
    def __init__(self, parent=None):
        self.fig, self.ax = plt.subplots(figsize=(16, 12))
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax.set_title("Diagrama Unifilar da Rede")
        self.fig.tight_layout()

    def plot_network(self, net):
        """Plota a rede pandapower usando collections para mais detalhes."""
        self.ax.clear()
        if net and len(net.bus) > 0:
            try:
                # --- MELHORIA: Lógica de cores e tamanhos ---
                collections = []
                
                # Mapeamento de cores por tensão
                voltage_levels = sorted(net.bus.vn_kv.unique())
                cmap = plt.get_cmap('viridis', len(voltage_levels))
                norm = mcolors.BoundaryNorm(boundaries=np.append(voltage_levels, voltage_levels[-1]+1)-0.5, ncolors=len(voltage_levels))

                # Coleção de Barras com cores baseadas na tensão
                bc = plot.create_bus_collection(net, size=0.07, zorder=10, 
                                                cmap=cmap, norm=norm)
                collections.append(bc)

                # Outras coleções com tamanhos ajustados
                collections.append(plot.create_line_collection(net, color="grey", linewidth=2.0))
                if len(net.load) > 0:
                    collections.append(plot.create_load_collection(net, size=0.15, orientation=45, color="red"))
                if len(net.gen) > 0:
                    collections.append(plot.create_gen_collection(net, size=0.15, color='green'))
                if len(net.ext_grid) > 0:
                    collections.append(plot.create_ext_grid_collection(net, size=0.15, color='orange'))
                if len(net.trafo) > 0:
                    collections.append(plot.create_trafo_collection(net, size=0.15, color='purple'))
                    
                plot.draw_collections(collections, ax=self.ax)

                # --- MELHORIA: Adicionar números das barras ---
                if 'bus_geodata' in net and not net.bus_geodata.empty:
                    for i, bus in net.bus_geodata.iterrows():
                        self.ax.text(bus.x, bus.y + 0.05, f'{i}',
                                     fontdict={'size': 8, 'color': 'black', 'weight': 'bold'},
                                     bbox=dict(boxstyle='round,pad=0.2', fc='yellow', alpha=0.7),
                                     zorder=20, ha='center', va='bottom')

                # --- MELHORIA: Legenda customizada ---
                handles = [
                    plt.Line2D([0], [0], color='grey', lw=2, label='Linhas'),
                    plt.Line2D([0], [0], marker='>', color='red', lw=0, markersize=8, label='Cargas'),
                    plt.Line2D([0], [0], marker='o', color='green', lw=0, markersize=8, label='Geradores'),
                    plt.Line2D([0], [0], marker='s', color='orange', lw=0, markersize=8, label='Grid Externo'),
                    plt.Line2D([0], [0], marker='o', color='purple', lw=0, markersize=8, label='Transformadores')
                ]
                # Adicionar handles para cada nível de tensão
                for level in voltage_levels:
                    color = cmap(norm([level])[0])
                    handles.append(plt.Line2D([0], [0], marker='o', color=color, lw=0, markersize=8, label=f'Barra {level} kV'))
                
                self.ax.legend(handles=handles, loc='best')

            except Exception as e:
                self.ax.text(0.5, 0.5, f'Erro ao plotar a rede:\n{e}', ha='center', va='center', fontsize=10, color='red')
        
        self.ax.set_title("Diagrama Unifilar da Rede")
        self.ax.set_xlabel("")
        self.ax.set_ylabel("")
        self.ax.grid(False)
        self.fig.tight_layout()
        self.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard de Análise de Redes Elétricas")
        self.setGeometry(100, 100, 1400, 800)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        splitter.addWidget(left_panel)

        right_panel = QGroupBox("Visualização da Rede")
        right_layout = QVBoxLayout(right_panel)
        splitter.addWidget(right_panel)
        
        splitter.setSizes([600, 800])

        self.metrics_widget = MetricsWidget()
        right_layout.addWidget(self.metrics_widget)

        self.network_canvas = NetworkCanvas(self)
        right_layout.addWidget(self.network_canvas)

        controls_group = QGroupBox("Controles")
        controls_layout = QHBoxLayout(controls_group)
        self.btn_generate_sin45 = QPushButton("Gerar e Carregar SIN 45")
        self.btn_import = QPushButton("Importar XLSX")
        self.btn_export = QPushButton("Exportar XLSX")
        self.btn_run_pf = QPushButton("▶ Executar Fluxo de Potência")
        self.btn_run_pf.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        controls_layout.addWidget(self.btn_generate_sin45)
        controls_layout.addWidget(self.btn_import)
        controls_layout.addWidget(self.btn_export)
        controls_layout.addStretch()
        controls_layout.addWidget(self.btn_run_pf)
        left_layout.addWidget(controls_group)

        self.tabs = QTabWidget()
        self.tables = {}
        left_layout.addWidget(self.tabs)

    def add_table_tab(self, name, df):
        if name not in self.tables:
            table = QTableWidget()
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.tables[name] = table
            self.tabs.addTab(table, name.capitalize())
        
        table = self.tables[name]
        table.clear()
        table.setRowCount(df.shape[0])
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels(df.columns)

        for i, row in enumerate(df.itertuples(index=False)):
            for j, value in enumerate(row):
                table.setItem(i, j, QTableWidgetItem(str(value)))
        
        table.resizeColumnsToContents()
    
    def get_dataframes_from_tables(self):
        dfs = {}
        for name, table in self.tables.items():
            if name.startswith('res_'):
                continue
            headers = [table.horizontalHeaderItem(j).text() for j in range(table.columnCount())]
            data = []
            for i in range(table.rowCount()):
                row_data = [table.item(i, j).text() if table.item(i, j) else '' for j in range(table.columnCount())]
                if any(cell.strip() for cell in row_data):
                    data.append(row_data)
            dfs[name] = pd.DataFrame(data, columns=headers)
        return dfs

# =============================================================================
# 3. CONTROLLER (Conecta a View com o Model)
# =============================================================================
class AppController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.view = MainWindow()
        self.model = PowerSystemModel()
        self._connect_signals()
        self.view.show()

    def _connect_signals(self):
        self.view.btn_generate_sin45.clicked.connect(self.generate_and_load_sin45)
        self.view.btn_import.clicked.connect(self.import_from_excel)
        self.view.btn_export.clicked.connect(self.export_to_excel)
        self.view.btn_run_pf.clicked.connect(self.run_power_flow)

    def run(self):
        sys.exit(self.app.exec())

    def generate_and_load_sin45(self):
        try:
            filepath = self.model.create_sin45_dataset_file()
            self._load_data_and_update_view(filepath)
            QMessageBox.information(self.view, "Sucesso", f"Dataset SIN 45 gerado e carregado de:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self.view, "Erro", f"Falha ao gerar o dataset SIN 45: {e}")

    def import_from_excel(self):
        filepath, _ = QFileDialog.getOpenFileName(self.view, "Importar Rede", "", "Arquivos Excel (*.xlsx)")
        if filepath:
            self._load_data_and_update_view(filepath)

    def _load_data_and_update_view(self, filepath):
        try:
            dfs = self.model.load_data_from_excel(filepath)
            self.view.tabs.clear()
            self.view.tables.clear()
            for name, df in dfs.items():
                self.view.add_table_tab(name, df)
            self.view.network_canvas.plot_network(None)
            self.view.metrics_widget.update_metrics(0, 0) # Reseta os cards
        except Exception as e:
            QMessageBox.critical(self.view, "Erro de Importação", str(e))

    def export_to_excel(self):
        filepath, _ = QFileDialog.getSaveFileName(self.view, "Exportar Rede", "", "Arquivos Excel (*.xlsx)")
        if filepath:
            try:
                dfs = self.view.get_dataframes_from_tables()
                with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                    for name, df in dfs.items():
                        df.to_excel(writer, sheet_name=name, index=False)
                QMessageBox.information(self.view, "Sucesso", f"Dados exportados com sucesso para:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self.view, "Erro de Exportação", str(e))

    def run_power_flow(self):
        try:
            self.model.dataframes = self.view.get_dataframes_from_tables()
            net = self.model.create_network_from_dataframes()
            success, message = self.model.run_power_flow()
            
            if success:
                # Gerar coordenadas ANTES de plotar
                pp.plotting.create_generic_coordinates(self.model.net)
                
                QMessageBox.information(self.view, "Fluxo de Potência", message)
                # Atualizar tabelas de resultados
                self.view.add_table_tab("res_bus", self.model.net.res_bus)
                self.view.add_table_tab("res_line", self.model.net.res_line)
                
                # Calcular e atualizar as métricas
                total_gen = self.model.net.res_gen.p_mw.sum() + self.model.net.res_ext_grid.p_mw.sum()
                total_load = self.model.net.res_load.p_mw.sum()
                self.view.metrics_widget.update_metrics(total_gen, total_load)

                # Plotar a rede
                self.view.network_canvas.plot_network(self.model.net)
            else:
                QMessageBox.warning(self.view, "Fluxo de Potência", message)
                self.view.network_canvas.plot_network(None)
                self.view.metrics_widget.update_metrics(0, 0)

        except Exception as e:
            QMessageBox.critical(self.view, "Erro", f"Ocorreu um erro: {e}")
            self.view.network_canvas.plot_network(None)
            self.view.metrics_widget.update_metrics(0, 0)

# =============================================================================
# 4. PONTO DE ENTRADA DA APLICAÇÃO
# =============================================================================
if __name__ == '__main__':
    controller = AppController()
    controller.run()
