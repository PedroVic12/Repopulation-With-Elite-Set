import sys
import os
import webbrowser
import re
import traceback
import base64
from io import BytesIO
import pandas as pd
import pandapower as pp
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
    QMessageBox, QHeaderView, QGroupBox, QSplitter, QLabel, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas


AppStyles = """
QWidget {
    background-color: #2E2E2E;
    color: #F0F0F0;
    font-family: "Segoe UI";
}
QMainWindow, QGroupBox {
    background-color: #2E2E2E;
}
QGroupBox {
    font-weight: bold;
    border: 1px solid #555;
    border-radius: 5px;
    margin-top: 10px;
    padding: 15px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 10px;
    color: #F0F0F0;
}
QPushButton {
    border-radius: 0px; 
    padding: 8px;
    color: white;
    font-weight: bold;
    border: 1px solid #555;
}
QPushButton#run_button, QPushButton#build_button {
    background-color: #8A2BE2; /* Roxo */
}
QPushButton#run_button:hover, QPushButton#build_button:hover {
    background-color: #9932CC;
}

QPushButton {
    background-color: #2E8B57; /* Verde */
}
QPushButton:hover {
    background-color: #3CB371;
}


QTabWidget::pane {
    border-top: 2px solid #555;
}
QTabBar::tab {
    background: #444;
    border: 1px solid #555;
    padding: 8px 16px;
    color: #F0F0F0;
}
QTabBar::tab:selected {
    background: #8A2BE2; /* Roxo */
    color: white;
}
QTableWidget {
    gridline-color: #555;
    background-color: #3C3C3C;
    color: #F0F0F0;
    alternate-background-color: #454545;
}
QHeaderView::section {
    background-color: #555;
    padding: 4px;
    border: 1px solid #666;
    color: #F0F0F0;
}
"""



"""
=============================================================================
         ! SIMULADOR DE SISTEMAS ELÉTRICOS COM PANDAPOWER E PYSIDE6
=============================================================================

Este arquivo contém a aplicação completa para a simulação de redes elétricas, focado no SIN 45, seguindo uma arquitetura Model-View-Controller (MVC) para uma organização  limpa e manutenível do código.

Arquitetura:
-----------
1. MODEL:
   - Contém a classe `PowerSystemModel`.
   - Responsável por toda a lógica de negócio e manipulação de dados.
   - Interage diretamente com a biblioteca `pandapower` para criar a rede,
     executar o fluxo de potência e processar os dados de entrada.

2. VIEW:
   - Contém as classes `MainWindow`, `NetworkCanvas`, `MetricsWidget`, etc.
   - Responsável por toda a interface gráfica do utilizador (GUI).
   - Não contém lógica de negócio; apenas exibe os dados fornecidos pelo
     Controller e emite sinais quando o utilizador interage.

3. CONTROLLER:
   - Contém a classe `AppController`.
   - Atua como o intermediário entre o Model e a View.
   - Ouve os sinais da View (ex: cliques em botões), chama os métodos
     apropriados no Model para executar as tarefas e, em seguida, atualiza
     a View com os novos dados.

4. PARSER E ESTILOS:
   - A classe `AnaredeParser` é um utilitário para ler formatos de ficheiro
     específicos (.PWF).
   - A variável `AppStyles` contém todo o CSS (QSS) para estilizar a
     aplicação, mantendo o código num único ficheiro.
"""



# =============================================================================
# 1. PARSER (Lógica para Leitura de Ficheiros Específicos)
# =============================================================================
class AnaredeParser:
    @staticmethod
    def parse_pwf_to_dataframes(filepath):
        # Esta função permanece inalterada
        data_blocks = { 'DBAR': [], 'DLIN': [], 'DGER': [], 'DCAR': [], 'DBSH': [], 'DTRA': [] }
        current_block = None
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith(('(', '99999')):
                        if line.startswith('99999'): current_block = None
                        continue
                    block_match = re.match(r'^(\w{4})', line)
                    if block_match and block_match.group(1).upper() in data_blocks:
                        current_block = block_match.group(1).upper()
                        continue
                    if current_block: data_blocks[current_block].append(line)
        except Exception as e:
            raise IOError(f"Erro ao ler o ficheiro {filepath}: {e}")

        dfs, bus_vn_kv_map = {}, {}
        if data_blocks['DBAR']:
            bus_data = []
            for line in data_blocks['DBAR']:
                try:
                    num_barra, nome_barra, vn_kv = int(line[0:5]), line[10:22].strip(), float(line[28:34])
                    bus_data.append({'bus_id': num_barra, 'name': nome_barra, 'vn_kv': vn_kv})
                    bus_vn_kv_map[num_barra] = vn_kv
                except (ValueError, IndexError): continue
            dfs['bus'] = pd.DataFrame(bus_data)
        if data_blocks['DLIN']:
            line_data, sn_mva = [], 100.0
            for line in data_blocks['DLIN']:
                try:
                    de, para, r_pu, x_pu, b_pu = int(line[0:5]), int(line[6:11]), float(line[21:29]), float(line[30:38]), float(line[39:47])
                    vn_kv = bus_vn_kv_map.get(de, 230.0)
                    z_base = (vn_kv**2) / sn_mva if vn_kv > 0 else 0
                    r_ohm, x_ohm = r_pu * z_base, x_pu * z_base
                    c_nf = (b_pu / (2 * np.pi * 60 * z_base)) * 1e9 if z_base > 0 else 0
                    line_data.append({'from_bus': de, 'to_bus': para, 'length_km': 1.0, 'r_ohm_per_km': r_ohm, 'x_ohm_per_km': x_ohm, 'c_nf_per_km': c_nf, 'max_i_ka': 1.0})
                except (ValueError, IndexError): continue
            dfs['line'] = pd.DataFrame(line_data)
        return dfs

# =============================================================================
# 2. MODEL (Lógica de Dados e Pandapower)
# =============================================================================
class PowerSystemModel:
    def __init__(self):
        self.net = pp.create_empty_network()
        self.dataframes = {}

    def load_data_from_excel(self, filepath):
        try:
            xls = pd.ExcelFile(filepath)
            self.dataframes = {sheet_name: pd.read_excel(xls, sheet_name) for sheet_name in xls.sheet_names}
            return self.dataframes
        except Exception as e: raise ValueError(f"Não foi possível ler o ficheiro Excel: {e}")

    def create_network_from_dataframes(self):
        # A lógica permanece a mesma
        raw_dfs = self.dataframes
        if not raw_dfs: raise ValueError("Nenhum dado carregado para criar a rede.")
        self.net = pp.create_empty_network(sn_mva=100)
        bus_map, bus_vn_map = {}, {}
        if 'bus' not in raw_dfs: raise ValueError("Dados de 'bus' em falta.")
        df_bus = raw_dfs['bus'].copy()
        df_bus.rename(columns={'Barra': 'bus_id', 'Nome': 'name'}, inplace=True, errors='ignore')
        if 'vn_kv' not in df_bus.columns:
            def extract_vn(name):
                try:
                    match = re.search(r'[\._ ]([\d\.]+)$', str(name))
                    if match: return float(match.group(1))
                except (ValueError, TypeError): pass
                return 230.0
            df_bus['vn_kv'] = df_bus['name'].apply(extract_vn)
        
        df_bus['bus_id'] = pd.to_numeric(df_bus['bus_id'], errors='coerce').dropna().astype(int)
        for _, row in df_bus.iterrows():
            bus_id, vn_kv = int(row['bus_id']), float(row['vn_kv'])
            new_idx = pp.create_bus(self.net, name=row['name'], vn_kv=vn_kv, in_service=True)
            bus_map[bus_id], bus_vn_map[bus_id] = new_idx, vn_kv
        
        self.dataframes['bus'] = df_bus

        def safe_get_bus_idx(val):
            try: return bus_map.get(int(float(val)))
            except (ValueError, TypeError): return None
        
        self._create_elements(raw_dfs, safe_get_bus_idx, bus_vn_map)

        if self.net.ext_grid.empty:
            slack_bus_idx = self._find_slack_bus(bus_map)
            pp.create_ext_grid(self.net, bus=slack_bus_idx, vm_pu=1.0)
            
        return self.net

    def _find_slack_bus(self, bus_map):
        # A lógica permanece a mesma
        if not self.net.gen.empty:
            return self.net.gen.bus.iloc[0]
        if bus_map:
            min_original_bus_id = min(bus_map.keys())
            return bus_map[min_original_bus_id]
        if not self.net.bus.empty:
            return self.net.bus.index[0]
        raise ValueError("Nenhuma barra disponível para criar uma barra de referência (ext_grid).")


    def _create_elements(self, dfs, bus_map_func, bus_vn_map):
        # A lógica permanece a mesma
        if 'load' in dfs or 'load_gen' in dfs: self._create_loads_from_dfs(dfs, bus_map_func)
        if 'gen' in dfs or 'load_gen' in dfs: self._create_gens_from_dfs(dfs, bus_map_func)
        if 'shunt' in dfs: self._create_shunts_from_dfs(dfs, bus_map_func)
        if 'line' in dfs: self._create_lines_trafos_from_dfs(dfs, bus_map_func, bus_vn_map)

    def _create_loads_from_dfs(self, dfs, bus_map_func):
        df = pd.concat([dfs.get('load', pd.DataFrame()), dfs.get('load_gen', pd.DataFrame())])
        if df.empty: return
        df.rename(columns={'Barra': 'bus_id', 'Carga Ativa (MW)': 'p_mw', 'Carga Reativa (Mvar)': 'q_mvar'}, inplace=True, errors='ignore')
        for _, row in df.iterrows():
            bus_idx = bus_map_func(row.get('bus_id'))
            if bus_idx is not None and pd.notna(row.get('p_mw')) and float(row['p_mw']) > 0:
                pp.create_load(self.net, bus=bus_idx, p_mw=float(row['p_mw']), q_mvar=float(row.get('q_mvar', 0)))

    def _create_gens_from_dfs(self, dfs, bus_map_func):
        df = pd.concat([dfs.get('gen', pd.DataFrame()), dfs.get('load_gen', pd.DataFrame())])
        if df.empty: return
        df.rename(columns={'Barra': 'bus_id', 'Potência Ativa (MW)': 'p_mw'}, inplace=True, errors='ignore')
        for _, row in df.iterrows():
            bus_idx = bus_map_func(row.get('bus_id'))
            if bus_idx is not None and pd.notna(row.get('p_mw')) and float(row['p_mw']) > 0:
                pp.create_gen(self.net, bus=bus_idx, p_mw=float(row['p_mw']), vm_pu=1.0)

    def _create_shunts_from_dfs(self, dfs, bus_map_func):
        if 'shunt' not in dfs or dfs['shunt'].empty: return
        df = dfs['shunt'].copy()
        df.rename(columns={'Barra': 'bus_id', 'Susceptância Shunt B(pu)': 'b_pu'}, inplace=True, errors='ignore')
        for _, row in df.iterrows():
            bus_idx = bus_map_func(row.get('bus_id'))
            if bus_idx is not None and pd.notna(row.get('b_pu')):
                pp.create_shunt(self.net, bus=bus_idx, p_mw=0, q_mvar=float(row['b_pu']) * self.net.sn_mva)
    
    def _create_lines_trafos_from_dfs(self, dfs, bus_map_func, bus_vn_map):
        if 'line' not in dfs or dfs['line'].empty: return
        df = dfs['line'].copy()
        df.rename(columns={'De': 'from_bus', 'Para': 'to_bus'}, inplace=True, errors='ignore')
        for _, row in df.iterrows():
            from_bus_id, to_bus_id = row.get('from_bus'), row.get('to_bus')
            from_bus_idx, to_bus_idx = bus_map_func(from_bus_id), bus_map_func(to_bus_id)
            if from_bus_idx is None or to_bus_idx is None: continue
            
            vn_from, vn_to = bus_vn_map.get(int(from_bus_id)), bus_vn_map.get(int(to_bus_id))
            if vn_from is None or vn_to is None: continue
            
            if abs(vn_from - vn_to) > 1: # É um transformador
                hv_bus, lv_bus = (from_bus_idx, to_bus_idx) if vn_from > vn_to else (to_bus_idx, from_bus_idx)
                vn_hv, vn_lv = (vn_from, vn_to) if vn_from > vn_to else (vn_to, vn_from)
                pp.create_transformer_from_parameters(self.net, hv_bus=hv_bus, lv_bus=lv_bus, 
                                                     sn_mva=row.get('sn_mva', 100.0), vn_hv_kv=vn_hv, vn_lv_kv=vn_lv, 
                                                     vkr_percent=float(row.get('R(pu)', 0.0))*100, 
                                                     vk_percent=float(row.get('X(pu)', 0.1))*100, 
                                                     pfe_kw=0, i0_percent=0)
            else: # É uma linha
                z_base = (vn_from**2) / self.net.sn_mva
                r_ohm = float(row.get('R(pu)', 0)) * z_base
                x_ohm = float(row.get('X(pu)', 0.001)) * z_base
                c_nf = (float(row.get('B(pu)', 0)) / (2 * np.pi * 60 * z_base)) * 1e9 if z_base > 0 else 0
                pp.create_line_from_parameters(self.net, from_bus=from_bus_idx, to_bus=to_bus_idx, length_km=1.0, 
                                               r_ohm_per_km=r_ohm, x_ohm_per_km=x_ohm, c_nf_per_km=c_nf, max_i_ka=1.0)


    def run_power_flow(self):
        if self.net is None or self.net.bus.empty: raise ValueError("A rede não foi criada ou está vazia.")
        try:
            pp.runpp(self.net, algorithm='nr', max_iteration=30, enforce_q_lims=True, numba=True)
            return (True, "Fluxo de potência executado com sucesso.") if self.net.converged else (False, "O fluxo de potência NÃO CONVERGIU.")
        except Exception as e:
            try: pp.diagnostic(self.net)
            except Exception as diag_e: return False, f"Falha no fluxo de potência: {e}\nDiagnóstico também falhou: {diag_e}"
            return False, f"Falha no fluxo de potência: {e}"

# =============================================================================
# 3. VIEW (Interface Gráfica com PySide6)
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
        card, card_layout, value_label = QGroupBox(title), QVBoxLayout(), QLabel(initial_value)
        value_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        value_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(value_label)
        card.setLayout(card_layout)
        return card
    def update_metrics(self, total_gen_mw, total_load_mw):
        self.gen_card.findChild(QLabel).setText(f"{total_gen_mw:.2f}")
        self.load_card.findChild(QLabel).setText(f"{total_load_mw:.2f}")

class NetworkCanvas(FigureCanvas):
    """
    Um Canvas Matplotlib melhorado que combina funcionalidades de desenho detalhadas.
    Mostra tipos de barras, tensões de linha, marcadores de componentes e sobreposições de resultados.
    """
    def __init__(self, parent=None):
        self.fig = plt.figure(figsize=(12, 10), tight_layout=True)
        gs = gridspec.GridSpec(3, 1, height_ratios=[20, 1, 1], hspace=0.1)
        self.ax_diagram = self.fig.add_subplot(gs[0])
        self.ax_legend = self.fig.add_subplot(gs[1])
        self.ax_colorbar = self.fig.add_subplot(gs[2])
        super().__init__(self.fig)
        self.setParent(parent)
        
        # Mapa de estilos centralizado para o diagrama da rede
        self.network_map = {
            'bus':          {'size': 0.08, 'zorder': 10},
            'bus_transfer': {'color': '#1f77b4'},
            'bus_gen':      {'color': '#2ca02c'},
            'bus_load':     {'color': '#ff7f0e'},
            'bus_gen_load': {'color': '#800080'}, # roxo
            'line':         {'linewidth': 1.5, 'zorder': 1},
            'trafo':        {'linewidth': 1.5, 'color': 'purple', 'zorder': 5},
            'load':         {'size': 0.08, 'zorder': 12},
            'gen':          {'size': 0.08, 'zorder': 12},
            'ext_grid':     {'size': 0.10, 'zorder': 12, 'color': 'gold'}, # ATUALIZADO
            'shunt':        {'size': 0.12, 'color': 'cyan', 'zorder': 12},
            'diagram':      {'bg_color': '#FFFFFF', 'title_color': '#000000'},
            'legend':       {'text_color': '#000000'},
            'colorbar':     {'label_color': '#000000', 'tick_color': '#000000'}
        }
        
        # Define a cor de fundo inicial usando o mapa
        self.fig.patch.set_facecolor(self.network_map['diagram']['bg_color'])

    def _create_shunt_collection(self, net, **kwargs):
        return plot.create_bus_collection(net, net.shunt.bus, patch_type='poly3', 
                                         color=self.network_map['shunt']['color'], 
                                         orientation=np.pi, **kwargs)

    def plot_network(self, net, plot_results=False):
        for ax in [self.ax_diagram, self.ax_legend, self.ax_colorbar]: ax.clear()
        self.ax_legend.axis('off'); self.ax_colorbar.axis('off')
        
        # Usa o mapa de estilos para as cores
        bg_color = self.network_map['diagram']['bg_color']
        title_color = self.network_map['diagram']['title_color']
        legend_text_color = self.network_map['legend']['text_color']
        cbar_label_color = self.network_map['colorbar']['label_color']
        cbar_tick_color = self.network_map['colorbar']['tick_color']

        self.fig.patch.set_facecolor(bg_color)
        self.ax_diagram.set_facecolor(bg_color)

        if not net or net.bus.empty:
            self.ax_diagram.text(0.5, 0.5, 'Nenhuma rede para exibir.', ha='center', va='center', color='gray')
            self.draw(); return
        
        try:
            if not hasattr(net, 'bus_geodata') or net.bus_geodata.empty:
                pp.plotting.create_generic_coordinates(net, overwrite=True)

            # --- Determina as Cores das Barras usando o network_map ---
            gen_buses = set(net.gen.bus) | set(net.ext_grid.bus) if not (net.gen.empty and net.ext_grid.empty) else set()
            load_buses = set(net.load.bus) if not net.load.empty else set()
            
            bus_colors = []
            for bus_idx in net.bus.index:
                is_gen = bus_idx in gen_buses
                is_load = bus_idx in load_buses
                if is_gen and is_load: bus_colors.append(self.network_map['bus_gen_load']['color'])
                elif is_gen: bus_colors.append(self.network_map['bus_gen']['color'])
                elif is_load: bus_colors.append(self.network_map['bus_load']['color'])
                else: bus_colors.append(self.network_map['bus_transfer']['color'])
            
            # --- Desenha Coleções Base usando o network_map ---
            collections = {
                'bus': plot.create_bus_collection(net, buses=net.bus.index, 
                                                 size=self.network_map['bus']['size'], 
                                                 color=bus_colors, 
                                                 zorder=self.network_map['bus']['zorder']),
            }
            if not net.trafo.empty:
                 collections['trafo'] = plot.create_trafo_collection(net, 
                                                                    color=self.network_map['trafo']['color'], 
                                                                    linewidths=self.network_map['trafo']['linewidth'], 
                                                                    zorder=self.network_map['trafo']['zorder'])

            # --- Desenha Linhas por Nível de Tensão ---
            line_handles = []
            if not net.line.empty:
                line_vns = net.bus.loc[net.line.from_bus, 'vn_kv'].values
                vn_kv_unique = sorted(pd.unique(line_vns))
                cmap = plt.get_cmap('viridis', len(vn_kv_unique) + 1)
                colors = {v: cmap(i) for i, v in enumerate(vn_kv_unique)}

                for v_kv, color in colors.items():
                    lines_at_v = net.line.index[line_vns == v_kv]
                    if not lines_at_v.empty:
                        lc = plot.create_line_collection(net, lines=lines_at_v, color=color, use_bus_geodata=True, 
                                                        linewidths=self.network_map['line']['linewidth'], 
                                                        zorder=self.network_map['line']['zorder'])
                        self.ax_diagram.add_collection(lc)
                    line_handles.append(Line2D([0], [0], color=color, lw=2, label=f'{v_kv:.1f} kV'))
            
            # --- Desenha Marcadores de Outros Componentes usando o network_map ---
            if not net.load.empty: collections['load'] = plot.create_load_collection(net, size=self.network_map['load']['size'], zorder=self.network_map['load']['zorder'], orientation=np.pi/2)
            if not net.gen.empty: collections['gen'] = plot.create_gen_collection(net, size=self.network_map['gen']['size'], zorder=self.network_map['gen']['zorder'], orientation=-np.pi/2)
            if not net.ext_grid.empty: collections['ext_grid'] = plot.create_ext_grid_collection(net, size=self.network_map['ext_grid']['size'], zorder=self.network_map['ext_grid']['zorder'], color=self.network_map['ext_grid']['color'])
            if not net.shunt.empty: collections['shunt'] = self._create_shunt_collection(net, size=self.network_map['shunt']['size'], zorder=self.network_map['shunt']['zorder'])

            plot.draw_collections(list(collections.values()), ax=self.ax_diagram)

            # --- Sobreposição de Resultados ---
            if plot_results and not net.res_line.empty and 'loading_percent' in net.res_line:
                cmap_res = plt.get_cmap('coolwarm')
                max_load = max(100, net.res_line.loading_percent.max() * 1.1)
                norm = mcolors.Normalize(vmin=0, vmax=max_load)
                lc_res = plot.create_line_collection(net, lines=net.res_line.index, cmap=cmap_res, norm=norm, use_bus_geodata=True, linewidths=2.5, zorder=2)
                lc_res.set_array(net.res_line.loading_percent.values)
                self.ax_diagram.add_collection(lc_res)
                sm = plt.cm.ScalarMappable(cmap=cmap_res, norm=norm); sm.set_array([])
                cbar = self.fig.colorbar(sm, cax=self.ax_colorbar, label='Carregamento da Linha (%)', orientation='horizontal')
                cbar.ax.xaxis.label.set_color(cbar_label_color); cbar.ax.tick_params(axis='x', colors=cbar_tick_color)

            # --- Cria Legenda COMPLETA usando o network_map ---
            bus_handles = [
                Line2D([0], [0], marker='o', color='w', label='Barra', markerfacecolor=self.network_map['bus_transfer']['color'], markersize=8),
                Line2D([0], [0], marker='o', color='w', label='Barra (Geração)', markerfacecolor=self.network_map['bus_gen']['color'], markersize=8),
                Line2D([0], [0], marker='o', color='w', label='Barra (Carga)', markerfacecolor=self.network_map['bus_load']['color'], markersize=8),
                Line2D([0], [0], marker='o', color='w', label='Transformadores', markerfacecolor=self.network_map['bus_gen_load']['color'], markersize=8)
            ]
            
            component_handles = [
                Line2D([0], [0], marker='s', color=self.network_map['ext_grid']['color'], label='Rede Externa', markersize=8, linestyle='None'),
                Line2D([0], [0], marker='v', color=self.network_map['shunt']['color'], label='Reator Shunt', markersize=8, linestyle='None')
            ]
            
            all_handles = bus_handles + line_handles + component_handles
            legend = self.ax_legend.legend(handles=all_handles, loc='center', ncol=len(all_handles), frameon=False, labelcolor=legend_text_color)

            self.ax_diagram.set_title("Diagrama Unifilar da Rede", color=title_color)
            self.ax_diagram.autoscale_view(); self.ax_diagram.set_xticks([]); self.ax_diagram.set_yticks([]); self.ax_diagram.set_aspect('auto')
        
        except Exception as e:
            self.ax_diagram.text(0.5, 0.5, f'Erro ao desenhar a rede:\n{e}', ha='center', va='center', color='red')
            print(f"ERRO CRÍTICO ao desenhar o diagrama: {traceback.format_exc()}")
        self.draw()

class ResultsPlotsCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig, (self.ax_voltage, self.ax_loading) = plt.subplots(2, 1, figsize=(8, 6), tight_layout=True)
        super().__init__(self.fig)
        self.setParent(parent)
        self.fig.patch.set_facecolor('#FFFFFF') 
        self.ax_voltage.set_facecolor('#F0F0F0'); self.ax_loading.set_facecolor('#F0F0F0')
        self.clear_plots()

    def plot_results(self, net):
        self.clear_plots()
        try:
            text_color = '#000000'
            grid_color = '#CCCCCC'

            if 'res_bus' in net and not net.res_bus.empty:
                bus_voltages = net.res_bus.vm_pu
                combined = pd.concat([bus_voltages.nlargest(10), bus_voltages.nsmallest(10)]).drop_duplicates().sort_values()
                colors = ['#d9534f' if v < 0.95 else '#f0ad4e' if v > 1.05 else '#5cb85c' for v in combined]
                combined.plot(kind='barh', ax=self.ax_voltage, color=colors, width=0.8)
                self.ax_voltage.set_title('Tensão nas Barras (Valores Mais Altos e Baixos)', color=text_color)
                self.ax_voltage.set_xlabel('Tensão (p.u.)', color=text_color)
                self.ax_voltage.axvline(x=1.05, color='r', linestyle='--', lw=1); self.ax_voltage.axvline(x=0.95, color='r', linestyle='--', lw=1)
                self.ax_voltage.grid(True, axis='x', linestyle=':', color=grid_color)
                self.ax_voltage.tick_params(axis='both', colors=text_color)
                for spine in self.ax_voltage.spines.values(): spine.set_edgecolor(grid_color)

            if 'res_line' in net and not net.res_line.empty:
                line_loading = net.res_line.loading_percent.nlargest(15).sort_values()
                line_loading.plot(kind='barh', ax=self.ax_loading, color='#5bc0de', width=0.8)
                self.ax_loading.set_title('Top 15 Linhas Mais Carregadas', color=text_color)
                self.ax_loading.set_xlabel('Carregamento (%)', color=text_color)
                self.ax_loading.grid(True, axis='x', linestyle=':', color=grid_color)
                self.ax_loading.tick_params(axis='both', colors=text_color)
                for spine in self.ax_loading.spines.values(): spine.set_edgecolor(grid_color)
                
        except Exception as e: print(f"ERRO ao desenhar gráficos de resultados: {traceback.format_exc()}")
        self.draw()
    
    def clear_plots(self):
        for ax in [self.ax_voltage, self.ax_loading]:
            ax.clear()
            ax.text(0.5, 0.5, 'Resultados não disponíveis', ha='center', va='center', color='gray')
            ax.tick_params(axis='both', colors='#000000') 
            for spine in ax.spines.values(): spine.set_edgecolor('#CCCCCC') 
        self.draw()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pandapower Case Manager"); self.setGeometry(100, 100, 1600, 900)
        self.setStyleSheet(AppStyles)
        main_widget = QWidget(); self.setCentralWidget(main_widget); main_layout = QHBoxLayout(main_widget)
        splitter = QSplitter(Qt.Horizontal); main_layout.addWidget(splitter)
        
        # Painel Esquerdo para Controlos e Tabelas de Dados
        left_panel = QWidget(); left_layout = QVBoxLayout(left_panel); splitter.addWidget(left_panel)
        tools_group = QGroupBox("Ferramentas")
        tools_layout = QVBoxLayout(tools_group); left_layout.addWidget(tools_group)
        self.btn_load_pwf, self.btn_import_case, self.btn_build_network, self.btn_run_pf = QPushButton("Carregar .PWF"), QPushButton("Importar Caso (Excel)"), QPushButton("Construir Rede a partir dos Dados"), QPushButton("▶ Executar Fluxo de Potência")
        self.btn_build_network.setObjectName("build_button")
        self.btn_run_pf.setObjectName("run_button")
        for btn in [self.btn_load_pwf, self.btn_import_case, self.btn_build_network, self.btn_run_pf]: tools_layout.addWidget(btn)
        
        self.tabs = QTabWidget(); left_layout.addWidget(self.tabs); self.tables = {}
        
        export_group = QGroupBox("Exportar"); export_layout = QVBoxLayout(export_group)
        self.btn_export_excel = QPushButton("Exportar Rede para .XLSX"); self.btn_generate_report = QPushButton("📈 Gerar Relatório HTML")
        export_layout.addWidget(self.btn_export_excel); export_layout.addWidget(self.btn_generate_report)
        left_layout.addWidget(export_group)
        
        # Painel Direito para Visualizações
        right_panel = QGroupBox("Visualização da Rede e Resultados"); right_layout_main = QVBoxLayout(right_panel)
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True); right_layout_main.addWidget(scroll_area)
        scroll_content = QWidget(); scroll_area.setWidget(scroll_content)
        right_layout_scroll = QVBoxLayout(scroll_content)
        
        self.metrics_widget = MetricsWidget(); right_layout_scroll.addWidget(self.metrics_widget)
        self.network_canvas = NetworkCanvas(self); self.network_canvas.setMinimumHeight(800)
        right_layout_scroll.addWidget(self.network_canvas)
        self.results_canvas = ResultsPlotsCanvas(self); self.results_canvas.setMinimumHeight(600)
        right_layout_scroll.addWidget(self.results_canvas)
        
        splitter.addWidget(right_panel); splitter.setSizes([700, 900])

    def add_table_tab(self, name, df):
        if name not in self.tables:
            self.tables[name] = QTableWidget()
            self.tabs.addTab(self.tables[name], name.replace("_", " ").capitalize())
        table = self.tables[name]
        df = df.round(4) # Arredonda dados para melhor visualização
        table.setRowCount(df.shape[0]); table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels(df.columns)
        for i, row in enumerate(df.itertuples(index=False)):
            for j, value in enumerate(row):
                table.setItem(i, j, QTableWidgetItem(str(value)))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

# =============================================================================
# 4. CONTROLLER (Conecta a View com o Model)
# =============================================================================
class AppController:
    def __init__(self):
        self.view = MainWindow(); self.model = PowerSystemModel()
        self._connect_signals(); self.view.show()
    def _connect_signals(self):
        self.view.btn_import_case.clicked.connect(self.import_case_files)
        self.view.btn_load_pwf.clicked.connect(self.load_pwf_file)
        self.view.btn_build_network.clicked.connect(self.build_network_from_ui)
        self.view.btn_run_pf.clicked.connect(self.run_power_flow)
        self.view.btn_generate_report.clicked.connect(self.generate_interactive_report)
        self.view.btn_export_excel.clicked.connect(self.export_network_to_excel)
    def _exec_task(self, task, *args):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try: task(*args)
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.critical(self.view, "Erro Inesperado", f"Ocorreu um erro:\n\n{e}\n\nTraceback:\n{tb_str}")
        finally: QApplication.restoreOverrideCursor()
    def import_case_files(self):
        filepath, _ = QFileDialog.getOpenFileName(self.view, "Importar Caso", "", "Ficheiros Suportados (*.xlsx)")
        if filepath: self._exec_task(self._do_import, filepath)
    def _do_import(self, filepath):
        dfs = self.model.load_data_from_excel(filepath)
        self._update_ui_with_dataframes(dfs)
        QMessageBox.information(self.view, "Sucesso", f"Dados carregados de: {os.path.basename(filepath)}")
    def load_pwf_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self.view, "Importar Ficheiro PWF", "", "ANAREDE (*.PWF)")
        if filepath: self._exec_task(self._do_load_pwf, filepath)
    def _do_load_pwf(self, filepath):
        dfs = AnaredeParser.parse_pwf_to_dataframes(filepath)
        self._update_ui_with_dataframes(dfs)
        QMessageBox.information(self.view, "Sucesso", f"Ficheiro {os.path.basename(filepath)} carregado.")
    def _update_ui_with_dataframes(self, dfs):
        self.view.tabs.clear(); self.view.tables.clear()
        for name, df in dfs.items():
            if df is not None and not df.empty: self.view.add_table_tab(name, df)
        self.view.network_canvas.plot_network(None)
        self.view.results_canvas.clear_plots()
        self.view.metrics_widget.update_metrics(0, 0)
    def build_network_from_ui(self):
        self._exec_task(self._do_build_network)
    def _do_build_network(self):
        self.model.dataframes = self._get_dataframes_from_ui_tabs()
        self.model.create_network_from_dataframes()
        if self.model.net and not self.model.net.bus.empty:
            self.view.network_canvas.plot_network(self.model.net)
            self.view.results_canvas.clear_plots()
            QMessageBox.information(self.view, "Sucesso", "Rede pandapower construída com sucesso.")
        else: QMessageBox.warning(self.view, "Aviso", "Não foi possível construir a rede.")
    def run_power_flow(self):
        if not self.model.net or self.model.net.bus.empty:
            QMessageBox.warning(self.view, "Aviso", "A rede não foi construída. Clique em 'Construir Rede' primeiro."); return
        self._exec_task(self._do_run_power_flow)
    def _do_run_power_flow(self):
        success, message = self.model.run_power_flow()
        if success:
            QMessageBox.information(self.view, "Sucesso", message)
            self.view.add_table_tab("res_bus", self.model.net.res_bus)
            self.view.add_table_tab("res_line", self.model.net.res_line)
            if 'res_trafo' in self.model.net and not self.model.net.res_trafo.empty: self.view.add_table_tab("res_trafo", self.model.net.res_trafo)
            gen = (self.model.net.res_gen.p_mw.sum() if not self.model.net.res_gen.empty else 0) + \
                  (self.model.net.res_ext_grid.p_mw.sum() if not self.model.net.res_ext_grid.empty else 0)
            load = self.model.net.res_load.p_mw.sum() if not self.model.net.res_load.empty else 0
            self.view.metrics_widget.update_metrics(gen, load)
            self.view.network_canvas.plot_network(self.model.net, plot_results=True)
            self.view.results_canvas.plot_results(self.model.net)
        else:
            QMessageBox.warning(self.view, "Falha no Fluxo de Potência", message)
            self.view.network_canvas.plot_network(self.model.net, plot_results=False)
            self.view.results_canvas.clear_plots()
    def _get_dataframes_from_ui_tabs(self):
        dfs = {}
        for i in range(self.view.tabs.count()):
            name = self.view.tabs.tabText(i).lower().replace(" ", "_")
            table = self.view.tabs.widget(i)
            headers = [table.horizontalHeaderItem(j).text() for j in range(table.columnCount())]
            data = [[table.item(i,j).text() if table.item(i,j) else '' for j in range(table.columnCount())] for i in range(table.rowCount())]
            dfs[name] = pd.DataFrame(data, columns=headers)
        return dfs
    def export_network_to_excel(self):
        if not self.view.tables: QMessageBox.warning(self.view, "Aviso", "Não há dados para exportar."); return
        filepath, _ = QFileDialog.getSaveFileName(self.view, "Exportar Rede para Excel", "", "Ficheiro Excel (*.xlsx)")
        if filepath: self._exec_task(self._do_export, filepath)
    def _do_export(self, filepath):
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            dataframes = self._get_dataframes_from_ui_tabs()
            for name, df in dataframes.items():
                df.to_excel(writer, sheet_name=name.capitalize(), index=False)
        QMessageBox.information(self.view, "Sucesso", f"Rede exportada com sucesso para:\n{filepath}")

    def generate_interactive_report(self):
        if not self.model.net or not hasattr(self.model.net, 'res_bus') or self.model.net.res_bus.empty:
            QMessageBox.warning(self.view, "Aviso", "É necessário executar o fluxo de potência primeiro."); return
        filepath, _ = QFileDialog.getSaveFileName(self.view, "Guardar Relatório HTML", "", "Ficheiro HTML (*.html)")
        if filepath: self._exec_task(self._do_generate_report, filepath)

    def _do_generate_report(self, filepath):
        # Gerar imagens
        temp_diagram_canvas = NetworkCanvas()
        temp_diagram_canvas.plot_network(self.model.net, plot_results=True)
        diagram_img_b64 = self._fig_to_base64(temp_diagram_canvas.fig)
        
        temp_results_canvas = ResultsPlotsCanvas()
        temp_results_canvas.plot_results(self.model.net)
        results_img_b64 = self._fig_to_base64(temp_results_canvas.fig)

        fig_p, fig_q = self._create_power_flow_plots()
        p_flow_img_b64 = self._fig_to_base64(fig_p)
        q_flow_img_b64 = self._fig_to_base64(fig_q)

        # Gerar tabelas HTML
        res_bus_html = self.model.net.res_bus.to_html(classes='table table-striped table-hover', justify='center')
        res_line_html = self.model.net.res_line.to_html(classes='table table-striped table-hover', justify='center')
        
        # Obter dados da primeira aba carregada para a tabela
        first_sheet_data_html = "<p>Nenhum dado de entrada carregado.</p>"
        first_sheet_title = "Dados de Entrada"
        if self.model.dataframes:
            # Pega o nome e o dataframe da primeira aba
            first_sheet_name = list(self.model.dataframes.keys())[0]
            first_sheet_df = self.model.dataframes[first_sheet_name]
            first_sheet_title = f"Dados de Entrada: Aba '{first_sheet_name.capitalize()}'"
            if not first_sheet_df.empty:
                first_sheet_data_html = first_sheet_df.to_html(classes='table table-striped table-hover', justify='center', index=False)
            else:
                first_sheet_data_html = f"<p>A aba '{first_sheet_name.capitalize()}' está vazia.</p>"

        # Construir o HTML
        html = self._build_html_report(diagram_img_b64, results_img_b64, res_bus_html, res_line_html, first_sheet_data_html, first_sheet_title, p_flow_img_b64, q_flow_img_b64)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
            
        QMessageBox.information(self.view, "Sucesso", f"Relatório gerado!\nA abrir {filepath}...")
        webbrowser.open(f"file://{os.path.realpath(filepath)}")

    def _create_power_flow_plots(self):
        fig_p, ax_p = plt.subplots(figsize=(10, 8))
        fig_q, ax_q = plt.subplots(figsize=(10, 8))
        net = self.model.net
        text_color = '#000000'
        grid_color = '#CCCCCC'

        if 'res_line' in net and not net.res_line.empty:
            # Potência Ativa
            p_flow = net.res_line.p_from_mw
            p_combined = pd.concat([p_flow.nlargest(10), p_flow.nsmallest(10)]).drop_duplicates().sort_values()
            p_combined.plot(kind='barh', ax=ax_p, color=['#5cb85c' if v > 0 else '#d9534f' for v in p_combined], width=0.8)
            ax_p.set_title('Fluxo de Potência Ativa (Valores Mais Significativos)', color=text_color)
            ax_p.set_xlabel('Potência Ativa (MW)', color=text_color)
            ax_p.grid(True, axis='x', linestyle=':', color=grid_color)
            ax_p.tick_params(axis='both', colors=text_color)
            for spine in ax_p.spines.values(): spine.set_edgecolor(grid_color)

            # Potência Reativa
            q_flow = net.res_line.q_from_mvar
            q_combined = pd.concat([q_flow.nlargest(10), q_flow.nsmallest(10)]).drop_duplicates().sort_values()
            q_combined.plot(kind='barh', ax=ax_q, color=['#5bc0de' if v > 0 else '#f0ad4e' for v in q_combined], width=0.8)
            ax_q.set_title('Fluxo de Potência Reativa (Valores Mais Significativos)', color=text_color)
            ax_q.set_xlabel('Potência Reativa (MVAr)', color=text_color)
            ax_q.grid(True, axis='x', linestyle=':', color=grid_color)
            ax_q.tick_params(axis='both', colors=text_color)
            for spine in ax_q.spines.values(): spine.set_edgecolor(grid_color)

        for fig in [fig_p, fig_q]:
            fig.patch.set_facecolor('#FFFFFF')
            fig.tight_layout()
            
        return fig_p, fig_q

    def _fig_to_base64(self, fig):
        buf = BytesIO(); fig.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor()); plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode('utf-8')

    def _build_html_report(self, diagram_img, results_img, bus_html, line_html, first_sheet_data_html, first_sheet_title, p_flow_img, q_flow_img):
        return f"""
        <!DOCTYPE html><html lang="pt-br"><head><meta charset="UTF-8"><title>Relatório de Fluxo de Potência</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>body{{padding: 2rem; background-color: #f8f9fa;}} .table{{font-size: 0.85rem;}} h2{{border-bottom: 2px solid #dee2e6; padding-bottom: 10px; margin-top: 2.5rem; color: #495057;}} .img-container{{padding: 1rem; border: 1px solid #dee2e6; border-radius: .25rem; background-color: white; margin-bottom: 2rem;}} .table-container{{max-height: 600px; overflow-y: auto;}}</style>
        </head><body><div class="container-fluid">
        <h1 class="display-4 text-center mb-4">Relatório de Análise de Rede</h1>
        <h2>Diagrama Unifilar</h2><div class="img-container"><img src="data:image/png;base64,{diagram_img}" class="img-fluid"></div>
        
        <h2>Resultados Gráficos e Dados de Entrada</h2>
        <div class="row">
            <div class="col-lg-6">
                <div class="img-container"><img src="data:image/png;base64,{results_img}" class="img-fluid"></div>
            </div>
            <div class="col-lg-6">
                <div class="table-container border rounded p-2 bg-white">
                    <h4>{first_sheet_title}</h4>
                    {first_sheet_data_html}
                </div>
            </div>
        </div>

        <h2>Resultados das Barras</h2><div class="table-responsive">{bus_html}</div>
        <h2>Resultados das Linhas</h2><div class="table-responsive">{line_html}</div>

        <h2>Fluxo de Potência nas Linhas</h2>
        <div class="row">
            <div class="col-lg-6"><div class="img-container"><img src="data:image/png;base64,{p_flow_img}" class="img-fluid"></div></div>
            <div class="col-lg-6"><div class="img-container"><img src="data:image/png;base64,{q_flow_img}" class="img-fluid"></div></div>
        </div>

        </div></body></html>
        """

# =============================================================================
# 5. MAIN EXECUTION
# ===========================================================================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = AppController()
    sys.exit(app.exec())

