import sys
import os
import webbrowser
import re
import traceback
import base64
from io import BytesIO
import pandas as pd
import pandapower as pp
import pandapower.networks as pn
import pandapower.plotting as plot
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.gridspec as gridspec
import numpy as np
from matplotlib.lines import Line2D

# Define o backend Qt para o Matplotlib
os.environ['QT_API'] = 'PySide6'

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QFileDialog,
    QMessageBox, QHeaderView, QGroupBox, QSplitter, QLabel, QScrollArea, QTextEdit, QTabWidget, QProgressBar, QListWidget, QListWidgetItem, QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

# =============================================================================
# ESTILO DA APLICAÇÃO (TEMA FUTURISTA ESCURO)
# =============================================================================
STYLESHEET_DARK = """
    QMainWindow, QWidget {
        background-color: #1e1f22;
        color: #e0e0e0;
        font-family: 'Segoe UI', sans-serif;
    }
    QGroupBox {
        font-size: 11pt;
        font-weight: bold;
        color: #58cfff; /* Azul Neon */
        border: 1px solid #3a3f44;
        border-radius: 8px;
        margin-top: 1ex;
        background-color: #2b2d30;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top center;
        padding: 0 10px;
        background-color: #1e1f22;
    }
    QLabel {
        font-size: 10pt;
        color: #c0c0c0;
    }
    QPushButton {
        font-size: 10pt;
        font-weight: bold;
        color: #ffffff;
        background-color: #007acc;
        border: 1px solid #005c99;
        padding: 10px;
        border-radius: 5px;
    }
    QPushButton:hover {
        background-color: #0099ff;
    }
    QPushButton:pressed {
        background-color: #005c99;
    }
    QHeaderView::section {
        background-color: #3a3f44;
        color: #58cfff;
        padding: 5px;
        border: 1px solid #2b2d30;
        font-weight: bold;
    }
    QTableWidget, QListWidget, QTextEdit {
        background-color: #2b2d30;
        border: 1px solid #3a3f44;
        gridline-color: #3a3f44;
        color: #e0e0e0;
    }
    QTabWidget::pane { border: 1px solid #3a3f44; }
    QTabBar::tab {
        background: #2b2d30; color: #c0c0c0; padding: 8px 15px;
        border-top-left-radius: 5px; border-top-right-radius: 5px;
        margin-right: 2px; border: 1px solid #3a3f44; border-bottom: none;
    }
    QTabBar::tab:selected {
        background: #3a3f44; color: #58cfff; font-weight: bold;
    }
    #StatusBanner[status="success"] { background-color: #1a4f31; color: #a6f6c3; border: 1px solid #2a7e4b; }
    #StatusBanner[status="warning"] { background-color: #4d442a; color: #ffeb99; border: 1px solid #8c732e; }
    #StatusBanner[status="error"] { background-color: #5c2b2f; color: #f8d7da; border: 1px solid #a3464d; }
    #StatusBanner[status="idle"] { background-color: #3a3f44; color: #c0c0c0; border: 1px solid #4a4f54; }
    #StatusBanner { padding: 8px; font-weight: bold; border-radius: 5px; }
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
        self.bus_map = {}

    def _ensure_geodata(self):
        """ Garante que a rede tenha coordenadas geográficas para plotagem. """
        if self.net and (not hasattr(self.net, "bus_geodata") or self.net.bus_geodata.empty):
            plot.create_generic_coordinates(self.net, overwrite=True)

    def load_network(self, network_name):
        """ Carrega uma rede padrão do pandapower. """
        self.network_name = network_name
        try:
            if network_name == "IEEE 14": self.net = pn.case14()
            elif network_name == "IEEE 30": self.net = pn.case_ieee30()
            elif network_name == "IEEE 57": self.net = pn.case57()
            elif network_name == "IEEE 118": self.net = pn.case118()
            else:
                return False, f"Caso de rede '{network_name}' desconhecido."
            
            self.net.name = network_name
            self._ensure_geodata()
            return True, f"Rede '{network_name}' carregada com sucesso."
        except Exception as e:
            return False, f"Erro ao carregar a rede '{network_name}': {e}"

    def create_sin45_dataset_file(self, filename='SIN_45_barras_dataset.xlsx'):
        """ Cria um arquivo Excel com os dados do sistema SIN 45 Barras. """
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
            dataframes = {sheet_name: xls.parse(sheet_name) for sheet_name in xls.sheet_names}
            self.network_name = "SIN 45 Barras"
            
            success, message = self._create_network_from_dataframes(dataframes)
            if success: 
                self.net.name = self.network_name
                self._ensure_geodata()
            return success, message
        except Exception as e:
            return False, f"Falha ao processar o arquivo Excel: {e}"

    def _create_network_from_dataframes(self, dataframes):
        """ Lógica interna para construir a rede a partir dos dataframes carregados. """
        df_load_gen = dataframes.get('load_gen')
        
        # VALIDAÇÃO DA BARRA SWING (SLACK)
        slack_buses = df_load_gen[df_load_gen['Tipo de Barra (*)'] == 2]
        if len(slack_buses) != 1:
            return False, f"Erro Crítico de Dados: A rede deve ter EXATAMENTE UMA barra de referência (Slack / Tipo 2). Foram encontradas: {len(slack_buses)}."

        self.net = pp.create_empty_network()
        self.bus_map.clear()
        
        df_bus = dataframes.get('bus')
        df_line = dataframes.get('line')
        df_shunt = dataframes.get('shunt')

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
    
    def apply_contingencies(self, contingencies):
        """Aplica uma lista de contingências à rede."""
        if not self.net: return
        # Reseta o estado para garantir que apenas as contingências atuais sejam aplicadas
        self.net.line['in_service'] = True
        if not self.net.trafo.empty: self.net.trafo['in_service'] = True
        
        for c_type, c_id in contingencies:
            if c_type == 'line' and c_id in self.net.line.index:
                self.net.line.loc[c_id, 'in_service'] = False
            elif c_type == 'trafo' and c_id in self.net.trafo.index:
                self.net.trafo.loc[c_id, 'in_service'] = False


    def run_power_flow(self):
        """ Executa o fluxo de potência. """
        if self.net is None: return False, "A rede não foi criada.", 'error'
        try:
            pp.runpp(self.net, algorithm='nr', init='flat')
            return True, "Fluxo de potência convergiu com sucesso!", 'success'
        except pp.LoadflowNotConverged:
            return False, "ATENÇÃO: O fluxo de potência não convergiu.", 'warning'
        except Exception as e:
            return False, f"Erro inesperado no cálculo: {e}", 'error'
            
    def get_kpis(self):
        """Calcula e retorna os principais indicadores de desempenho (KPIs)."""
        if not hasattr(self.net, 'res_bus') or self.net.res_bus.empty:
            return { "total_load_mw": 0, "total_gen_mw": 0, "voltage_violations": 0, "overloads": 0 }

        # Violações de Tensão
        voltage_violations = ((self.net.res_bus.vm_pu > self.net.bus.max_vm_pu) | 
                              (self.net.res_bus.vm_pu < self.net.bus.min_vm_pu)).sum()
        
        # Sobrecargas de Ramos (Linhas e Transformadores)
        line_overloads = (self.net.res_line.loading_percent > 100).sum()
        trafo_overloads = 0
        if hasattr(self.net, 'res_trafo') and not self.net.res_trafo.empty:
            trafo_overloads = (self.net.res_trafo.loading_percent > 100).sum()

        return {
            "total_load_mw": self.net.res_load.p_mw.sum(),
            "total_gen_mw": self.net.res_gen.p_mw.sum() + self.net.res_ext_grid.p_mw.sum(),
            "voltage_violations": int(voltage_violations),
            "overloads": int(line_overloads + trafo_overloads)
        }


# =============================================================================
# 2. VIEW (Interface Gráfica com PySide6)
# =============================================================================
class MetricsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.cards = {
            "gen": self._create_metric_card("Geração Total (MW)", "N/A"),
            "load": self._create_metric_card("Carga Total (MW)", "N/A"),
            "voltage": self._create_metric_card("Violações de Tensão", "N/A"),
            "overload": self._create_metric_card("Sobrecargas (Ramos)", "N/A")
        }
        for card in self.cards.values():
            layout.addWidget(card)

    def _create_metric_card(self, title, initial_value):
        card = QGroupBox(title)
        card_layout = QVBoxLayout(card)
        value_label = QLabel(initial_value)
        font = QFont("Segoe UI", 20, QFont.Bold)
        value_label.setFont(font)
        value_label.setAlignment(Qt.AlignCenter)
        card.setStyleSheet("QGroupBox { padding: 15px; }")
        card_layout.addWidget(value_label)
        return card

    def update_metrics(self, kpis):
        self.cards["gen"].findChild(QLabel).setText(f"{kpis['total_gen_mw']:.2f}")
        self.cards["load"].findChild(QLabel).setText(f"{kpis['total_load_mw']:.2f}")
        self.cards["voltage"].findChild(QLabel).setText(f"{kpis['voltage_violations']}")
        self.cards["overload"].findChild(QLabel).setText(f"{kpis['overloads']}")

class NetworkCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig, self.ax = plt.subplots(figsize=(16, 12))
        super().__init__(self.fig)
        self.setParent(parent)
        self.net = None
        self.bus_map = {}
        self.rotation_angle = 0
        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, event):
        """ Captura eventos de teclado para rotacionar o diagrama. """
        if self.net is None:
            return

        if event.key() == Qt.Key_Right:
            self.rotation_angle += 15
        elif event.key() == Qt.Key_Left:
            self.rotation_angle -= 15
        else:
            super().keyPressEvent(event)
            return
        
        self.rotation_angle %= 360
        self.plot_network(self.net, self.net.name, self.bus_map)


    def plot_network(self, net, network_name, bus_map={}, plot_results=False):
        self.net = net
        self.bus_map = bus_map 
        self.ax.clear()
        
        is_ieee_case = "ieee" in network_name.lower()
        
        bg_color = '#ffffff'
        text_color = '#000000'
        line_color_ieee = '#cccccc'
        self.fig.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)

        if not (net and len(net.bus) > 0):
            self.ax.text(0.5, 0.5, 'Carregue uma rede para visualizar.', ha='center', color=text_color)
            self.draw()
            return
            
        if not hasattr(net, "bus_geodata") or net.bus_geodata.empty:
            plot.create_generic_coordinates(net, overwrite=True)
        
        collections = []
        handles = []
        
        if network_name == "SIN 45 Barras":
            ramo1_pairs = [(1,19),(12,19),(12,13),(13,14),(14,15),(15,16),(16,17),(17,30)]
            ramo2_pairs = [(1,28),(26,28),(25,26),(24,25),(23,24),(3,23)]
            ramo3_pairs = [(4,5),(5,7),(7,8),(8,9)]
            ramos = {
                "Troncal Sul-Sudeste": {"pairs": ramo1_pairs, "color": "#2ca02c"},
                "Troncal Sudoeste": {"pairs": ramo2_pairs, "color": "#1f77b4"},
                "Interligação Norte": {"pairs": ramo3_pairs, "color": "#d62728"}
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
                    collections.append(plot.create_line_collection(net, lines=indices, color=data["color"], linewidths=2.0))
                    plotted_lines.update(indices)
                    handles.append(Line2D([0], [0], color=data["color"], lw=2, label=name))

            other_lines = list(set(net.line.index) - plotted_lines)
            collections.append(plot.create_line_collection(net, lines=other_lines, color="#606060"))
            handles.append(Line2D([0], [0], color='#606060', lw=2, label='Outras Linhas'))
        else: # Casos IEEE
            vn_kvs = sorted(net.bus.vn_kv.unique())
            cmap = plt.get_cmap('plasma', len(vn_kvs))
            for i, vn in enumerate(vn_kvs):
                lines = net.line.index[net.bus.vn_kv.loc[net.line.from_bus].values == vn]
                if len(lines) > 0:
                    color = cmap(i / (len(vn_kvs)-1)) if len(vn_kvs) > 1 else cmap(0.5)
                    collections.append(plot.create_line_collection(net, lines=lines, color=color, linewidths=1.2))
                    handles.append(Line2D([0], [0], color=color, lw=2, label=f'Linha {vn} kV'))

        bus_collections, bus_handles = self.create_bus_collections(net, is_ieee_case)
        collections.extend(bus_collections)
        handles.extend(bus_handles)
        
        if not net.trafo.empty:
            collections.append(plot.create_trafo_collection(net, color='#9467bd'))
            handles.append(Line2D([0], [0], color='#9467bd', lw=2, label='Transformador'))

        oos_lines = net.line.index[~net.line.in_service]
        if not oos_lines.empty:
            collections.append(plot.create_line_collection(net, lines=oos_lines, color="#ff7f0e", linestyle="--", linewidths=2.5))
            handles.append(Line2D([0], [0], color='#ff7f0e', linestyle='--', lw=2, label='Fora de Serviço'))

        if plot_results and 'res_line' in net and not net.res_line.empty:
            cmap = plt.get_cmap('coolwarm')
            norm = plt.Normalize(vmin=0, vmax=100)
            lc = plot.create_line_collection(net, lines=net.res_line.index, cmap=cmap, norm=norm, linewidths=3.0, use_bus_geodata=True)
            lc.set_array(net.res_line.loading_percent.values)
            collections.append(lc)
            
            sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
            sm.set_array([])
            cbar = self.fig.colorbar(sm, ax=self.ax, orientation="vertical", shrink=0.7, pad=0.01)
            cbar.set_label('Carregamento da Linha (%)', color=text_color)
            plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color=text_color)

        plot.draw_collections(collections, ax=self.ax)
        
        legend = self.ax.legend(handles=handles, loc='upper left', bbox_to_anchor=(1.01, 1))
        plt.setp(legend.get_texts(), color=text_color)
        legend.get_frame().set_facecolor('#f0f0f0')
        legend.get_frame().set_edgecolor('#cccccc')

        self.ax.set_title(f"Diagrama Unifilar - {network_name}", color=text_color, weight='bold')
        self.fig.tight_layout()
        self.draw()

    def create_bus_collections(self, net, is_ieee_case=False):
        collections, handles = [], []
        size_factor = 0.5 if is_ieee_case else 1.0
        slack_size, gen_size, other_size = 0.05*size_factor, 0.04*size_factor, 0.03*size_factor

        slack_buses = net.ext_grid.bus
        gen_buses = set(net.gen.bus) - set(slack_buses)
        
        if not slack_buses.empty:
            collections.append(plot.create_bus_collection(net, buses=slack_buses, color='#d62728', size=slack_size, zorder=11))
            handles.append(Line2D([0], [0], color='#d62728', marker='o', lw=0, label='Barra Slack (Swing)'))
        if gen_buses:
            collections.append(plot.create_bus_collection(net, buses=list(gen_buses), color='#ff7f0e', size=gen_size, zorder=10))
            handles.append(Line2D([0], [0], color='#ff7f0e', marker='o', lw=0, label='Barra de Geração (PV)'))

        other_buses = set(net.bus.index) - set(slack_buses) - gen_buses
        collections.append(plot.create_bus_collection(net, buses=list(other_buses), color='#1f77b4', size=other_size, zorder=9))
        handles.append(Line2D([0], [0], color='#1f77b4', marker='o', lw=0, label='Barra (Carga/Passagem)'))
        
        return collections, handles


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador de Redes Elétricas")
        self.setGeometry(100, 100, 1800, 1000)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Banner de Status
        self.status_banner = QLabel("Bem-vindo! Selecione uma rede para começar.")
        self.status_banner.setObjectName("StatusBanner")
        self.status_banner.setAlignment(Qt.AlignCenter)
        self.update_status_banner("Bem-vindo! Selecione uma rede para começar.", 'idle')
        main_layout.addWidget(self.status_banner)
        
        # Splitter principal
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)

        # --- Painel Esquerdo (Controles e Tabelas) ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setLayout(left_layout)
        main_splitter.addWidget(left_panel)

        # --- Painel Direito (Visualização e Descrição) ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_panel.setLayout(right_layout)
        main_splitter.addWidget(right_panel)
        
        main_splitter.setSizes([700, 1100])
        
        # --- Conteúdo do Painel Direito ---
        right_splitter = QSplitter(Qt.Vertical)
        right_layout.addWidget(right_splitter)

        self.network_view_group = QGroupBox("Visualização da Rede (Use as setas ← → para rotacionar)")
        network_view_layout = QVBoxLayout(self.network_view_group)
        self.metrics_widget = MetricsWidget()
        network_view_layout.addWidget(self.metrics_widget)
        self.network_canvas = NetworkCanvas(self)
        network_view_layout.addWidget(self.network_canvas)
        right_splitter.addWidget(self.network_view_group)

        self.description_group = QGroupBox("Descrição da Rede")
        description_layout = QVBoxLayout(self.description_group)
        self.network_description_text = QTextEdit()
        self.network_description_text.setReadOnly(True)
        description_layout.addWidget(self.network_description_text)
        right_splitter.addWidget(self.description_group)
        right_splitter.setSizes([700, 300])
        
        
        # --- Layout do Painel Esquerdo ---
        
        # Grupo de Controles da Rede
        network_controls_group = QGroupBox("1. Seleção e Carga da Rede")
        network_controls_layout = QVBoxLayout(network_controls_group)
        
        ieee_layout = QHBoxLayout()
        self.btn_case14 = QPushButton("IEEE 14")
        self.btn_case30 = QPushButton("IEEE 30")
        self.btn_case57 = QPushButton("IEEE 57")
        self.btn_case118 = QPushButton("IEEE 118")
        ieee_layout.addWidget(self.btn_case14)
        ieee_layout.addWidget(self.btn_case30)
        ieee_layout.addWidget(self.btn_case57)
        ieee_layout.addWidget(self.btn_case118)
        
        sin_layout = QHBoxLayout()
        self.btn_generate_sin45 = QPushButton("Gerar Dataset SIN 45")
        self.btn_load_excel = QPushButton("Carregar de Excel...")
        self.btn_export_excel = QPushButton("Exportar para Excel...")
        sin_layout.addWidget(self.btn_generate_sin45)
        sin_layout.addWidget(self.btn_load_excel)
        sin_layout.addWidget(self.btn_export_excel)
        
        network_controls_layout.addLayout(ieee_layout)
        network_controls_layout.addLayout(sin_layout)
        left_layout.addWidget(network_controls_group)

        # Grupo de Contingência
        contingency_group = QGroupBox("2. Análise de Contingência")
        contingency_layout = QVBoxLayout(contingency_group)
        self.element_list = QListWidget()
        self.element_list.setSelectionMode(QListWidget.MultiSelection)
        contingency_layout.addWidget(self.element_list)
        left_layout.addWidget(contingency_group)
        
        # Botão de Execução
        self.btn_run_pf = QPushButton("▶ Executar Fluxo de Potência")
        self.btn_run_pf.setStyleSheet("background-color: #2ca02c; color: white; font-weight: bold; padding: 12px;")
        left_layout.addWidget(self.btn_run_pf)

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
        
    def update_element_list(self, net):
        """Atualiza a lista de elementos para análise de contingência."""
        self.element_list.clear()
        if not net: return
        
        if not net.line.empty:
            for idx, row in net.line.iterrows():
                item = QListWidgetItem(f"[L] Linha {idx}: Barra {row.from_bus} ↔ {row.to_bus}")
                item.setData(Qt.UserRole, ('line', idx))
                self.element_list.addItem(item)
        if not net.trafo.empty:
            for idx, row in net.trafo.iterrows():
                item = QListWidgetItem(f"[T] Trafo {idx}: Barra {row.hv_bus} ↔ {row.lv_bus}")
                item.setData(Qt.UserRole, ('trafo', idx))
                self.element_list.addItem(item)


    def update_status_banner(self, message, status_type):
        """Atualiza o texto e a cor do banner de status."""
        self.status_banner.setText(message)
        self.status_banner.setProperty("status", status_type)
        self.status_banner.style().polish(self.status_banner)

    def update_network_description(self, net):
        if not net:
            self.network_description_text.setHtml("<h3>Nenhuma rede carregada.</h3>")
            return

        description = f"""
        <style>
            body {{ color: #e0e0e0; font-family: 'Segoe UI'; }}
            h3 {{ color: #58cfff; }}
            h4 {{ color: #c0c0c0; border-bottom: 1px solid #3a3f44; padding-bottom: 5px;}}
            ul {{ list-style-type: none; padding-left: 0; }}
            li {{ margin-bottom: 3px; }}
            b {{ color: #ffffff; }}
        </style>
        <h3>Detalhes da Rede: {net.name.upper()}</h3>
        <p>Esta seção fornece uma visão geral dos componentes da rede.</p>
        """
        def create_html_list(title, count, items):
            s = f"<h4>{title} ({count}):</h4>"
            if not items: return s + "<p>Nenhum componente definido.</p>"
            s += "<ul>" + "".join([f"<li>{item}</li>" for item in items[:10]]) + "</ul>" # Limita a 10 itens
            if count > 10: s += f"<p><i>... e mais {count-10} outros.</i></p>"
            return s

        bus_items = [f"<b>Barra {idx}:</b> Tensão Nominal = {bus.vn_kv} kV" for idx, bus in net.bus.iterrows()]
        line_items = [f"<b>Linha {idx}:</b> De {row.from_bus} para {row.to_bus}" for idx, row in net.line.iterrows()]
        trafo_items = [f"<b>Trafo {idx}:</b> HV {row.hv_bus} ↔ LV {row.lv_bus}" for idx, row in net.trafo.iterrows()]
        load_items = [f"<b>Carga {idx}</b> @ Barra {row.bus}: P={row.p_mw:.2f} MW, Q={row.q_mvar:.2f} MVAr" for idx, row in net.load.iterrows()]
        gen_items = [f"<b>Gerador {idx}</b> @ Barra {row.bus}: P={row.p_mw:.2f} MW" for idx, row in net.gen.iterrows()]
        ext_grid_items = [f"<b>Grid Externo {idx}</b> @ Barra {row.bus}" for idx, row in net.ext_grid.iterrows()]

        description += create_html_list("Barras", len(net.bus), bus_items)
        description += create_html_list("Linhas", len(net.line), line_items)
        if not net.trafo.empty: description += create_html_list("Transformadores", len(net.trafo), trafo_items)
        description += create_html_list("Cargas", len(net.load), load_items)
        description += create_html_list("Geradores", len(net.gen), gen_items)
        description += create_html_list("Grid Externo", len(net.ext_grid), ext_grid_items)
        self.network_description_text.setHtml(description)


# =============================================================================
# 3. CONTROLLER (Conecta a View com o Model)
# =============================================================================
class AppController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyleSheet(STYLESHEET_DARK)
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
        self.view.btn_generate_sin45.clicked.connect(self.generate_sin45_file)
        self.view.btn_load_excel.clicked.connect(self.load_from_excel)
        self.view.btn_export_excel.clicked.connect(self.export_to_excel)
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
            
    def generate_sin45_file(self):
        """Apenas gera o arquivo Excel do SIN 45."""
        try:
            filepath = self.model.create_sin45_dataset_file()
            QMessageBox.information(self.view, "Sucesso", f"Arquivo 'SIN_45_barras_dataset.xlsx' gerado com sucesso no diretório:\n{os.getcwd()}")
        except Exception as e:
            QMessageBox.critical(self.view, "Erro", f"Falha ao gerar o arquivo: {e}")

    def load_from_excel(self):
        """Abre um diálogo para o usuário selecionar um arquivo Excel."""
        filepath, _ = QFileDialog.getOpenFileName(self.view, "Carregar Rede de Excel", "", "Excel Files (*.xlsx)")
        if not filepath: return
        
        success, message = self.model.load_network_from_excel(filepath)
        if success:
            self._update_view_after_load(f"Rede carregada de:\n{os.path.basename(filepath)}")
        else:
            QMessageBox.critical(self.view, "Erro de Carregamento", message)


    def _update_view_after_load(self, status_message):
        """ Função auxiliar para atualizar a UI após carregar uma rede. """
        net = self.model.net
        self.view.tabs.clear()
        self.view.tables.clear()
        
        # Adiciona tabelas de dados da rede
        self.view.add_table_tab("bus", net.bus)
        self.view.add_table_tab("line", net.line)
        self.view.add_table_tab("load", net.load)
        self.view.add_table_tab("gen", net.gen)
        if not net.trafo.empty: self.view.add_table_tab("trafo", net.trafo)
        if not net.shunt.empty: self.view.add_table_tab("shunt", net.shunt)
        
        self.view.update_element_list(net)
        self.view.network_canvas.plot_network(net, self.model.network_name, self.model.bus_map)
        self.view.metrics_widget.update_metrics(self.model.get_kpis())
        self.view.update_status_banner("Rede carregada. Pronto para simular.", 'idle')
        self.view.update_network_description(net)

    def export_to_excel(self):
        """Exporta os dados da rede atualmente carregada para um arquivo Excel."""
        if self.model.net is None:
            QMessageBox.warning(self.view, "Aviso", "Nenhuma rede carregada para exportar.")
            return

        path, _ = QFileDialog.getSaveFileName(self.view, "Exportar Rede para Excel", f"{self.model.network_name.replace(' ', '_')}.xlsx", "Excel Files (*.xlsx)")
        if not path: return

        try:
            with pd.ExcelWriter(path) as writer:
                self.model.net.bus.to_excel(writer, sheet_name='bus')
                self.model.net.line.to_excel(writer, sheet_name='line')
                self.model.net.load.to_excel(writer, sheet_name='load')
                self.model.net.gen.to_excel(writer, sheet_name='gen')
                if not self.model.net.trafo.empty:
                    self.model.net.trafo.to_excel(writer, sheet_name='trafo')
                if not self.model.net.shunt.empty:
                    self.model.net.shunt.to_excel(writer, sheet_name='shunt')
                if hasattr(self.model.net, 'res_bus') and not self.model.net.res_bus.empty:
                     self.model.net.res_bus.to_excel(writer, sheet_name='res_bus')
                     self.model.net.res_line.to_excel(writer, sheet_name='res_line')
            
            QMessageBox.information(self.view, "Sucesso", f"Rede exportada para:\n{path}")
        except Exception as e:
            QMessageBox.critical(self.view, "Erro de Exportação", f"Não foi possível exportar o arquivo: {e}")

    def run_power_flow(self):
        """ Executa o fluxo de potência e atualiza os resultados. """
        if self.model.net is None:
            self.view.update_status_banner("Nenhuma rede carregada para simular.", 'error')
            return

        # Obtém contingências selecionadas na UI
        contingencies = []
        for i in range(self.view.element_list.count()):
            item = self.view.element_list.item(i)
            if item.isSelected():
                 contingencies.append(item.data(Qt.UserRole))

        self.model.apply_contingencies(contingencies)

        try:
            success, message, status_type = self.model.run_power_flow()
            
            self.view.update_status_banner(message, status_type)

            if success:
                # Adiciona ou atualiza tabelas de resultados
                self.view.add_table_tab("Resultados Barras", self.model.net.res_bus.round(4))
                self.view.add_table_tab("Resultados Linhas", self.model.net.res_line.round(4))
                
                kpis = self.model.get_kpis()
                self.view.metrics_widget.update_metrics(kpis)

            # Atualiza o diagrama para refletir o estado da rede (com ou sem convergência)
            self.view.network_canvas.plot_network(self.model.net, self.model.network_name, self.model.bus_map, plot_results=success)

        except Exception as e:
            error_msg = f"Erro Crítico: {e}"
            self.view.update_status_banner(error_msg, 'error')
            QMessageBox.critical(self.view, "Erro Inesperado", error_msg)

# =============================================================================
# 4. PONTO DE ENTRADA DA APLICAÇÃO - PVRV
# =============================================================================
if __name__ == '__main__':
    controller = AppController()
    controller.run()

