# =============================================================================
# APLICAÇÃO COMPLETA DE ANÁLISE DE REDES ELÉTRICAS
# Todo o código está contido neste único ficheiro, mas organizado em
# classes distintas para seguir os princípios de POO e separação de
# responsabilidades (Model-View-Controller).
# =============================================================================

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

# =============================================================================
# 1. PARSER (Lógica para Leitura de Ficheiros Específicos)
# =============================================================================
class AnaredeParser:
    """
    Classe estática para processar ficheiros de formatos específicos como ANAREDE.
    """
    @staticmethod
    def parse_pwf_to_dataframes(filepath):
        """
        Processa um ficheiro .PWF do ANAREDE e extrai os dados para DataFrames.
        """
        data_blocks = {
            'DBAR': [], 'DLIN': [], 'DGER': [], 'DCAR': [], 'DBSH': [], 'DTRA': []
        }
        current_block = None

        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith(('(', '99999')):
                        if line.startswith('99999'):
                            current_block = None # Fim de um bloco
                        continue

                    block_match = re.match(r'^(\w{4})', line)
                    if block_match and block_match.group(1).upper() in data_blocks:
                        current_block = block_match.group(1).upper()
                        continue
                    
                    if current_block:
                        data_blocks[current_block].append(line)
        except Exception as e:
            raise IOError(f"Erro ao ler o ficheiro {filepath}: {e}")

        dfs = {}
        bus_vn_kv_map = {}

        if data_blocks['DBAR']:
            bus_data = []
            for line in data_blocks['DBAR']:
                try:
                    num_barra = int(line[0:5])
                    nome_barra = line[10:22].strip()
                    vn_kv = float(line[28:34])
                    bus_data.append({'bus_id': num_barra, 'name': nome_barra, 'vn_kv': vn_kv})
                    bus_vn_kv_map[num_barra] = vn_kv
                except (ValueError, IndexError):
                    continue
            dfs['bus'] = pd.DataFrame(bus_data)

        if data_blocks['DLIN']:
            line_data = []
            sn_mva = 100.0
            for line in data_blocks['DLIN']:
                try:
                    de = int(line[0:5])
                    para = int(line[6:11])
                    r_pu = float(line[21:29])
                    x_pu = float(line[30:38])
                    b_pu = float(line[39:47])
                    vn_kv = bus_vn_kv_map.get(de, 230.0)
                    z_base = (vn_kv**2) / sn_mva if vn_kv > 0 else 0
                    r_ohm = r_pu * z_base
                    x_ohm = x_pu * z_base
                    c_nf = (b_pu / (2 * np.pi * 60 * z_base)) * 1e9 if z_base > 0 else 0
                    line_data.append({'from_bus': de, 'to_bus': para, 'length_km': 1.0, 'r_ohm_per_km': r_ohm, 'x_ohm_per_km': x_ohm, 'c_nf_per_km': c_nf, 'max_i_ka': 1.0})
                except (ValueError, IndexError):
                    continue
            dfs['line'] = pd.DataFrame(line_data)
        
        # Implementações para outros blocos (DTRA, DCAR, DGER) seguiriam uma lógica similar...

        return dfs

# =============================================================================
# 2. MODEL (Lógica de Dados e Pandapower)
# =============================================================================
class PowerSystemModel:
    """
    Gere todos os dados, criação da rede pandapower e cálculos.
    """
    def __init__(self):
        self.net = pp.create_empty_network()
        self.dataframes = {}

    def load_data_from_excel(self, filepath):
        try:
            xls = pd.ExcelFile(filepath)
            self.dataframes = {sheet_name: pd.read_excel(xls, sheet_name) for sheet_name in xls.sheet_names}
            return self.dataframes
        except Exception as e:
            raise ValueError(f"Não foi possível ler o ficheiro Excel: {e}")

    def load_data_from_csvs(self, entry_filepath):
        directory = os.path.dirname(entry_filepath)
        selected_filename = os.path.basename(entry_filepath)
        prefix = ""
        known_suffixes = ['bus.csv', 'line.csv', 'load_gen.csv', 'load.csv', 'gen.csv', 'shunt.csv']
        for suffix in known_suffixes:
            if selected_filename.endswith(suffix):
                prefix = selected_filename[:-len(suffix)]
                break
        expected_files = {'bus': 'bus.csv', 'line': 'line.csv', 'load_gen': 'load_gen.csv', 'shunt': 'shunt.csv'}
        loaded_dfs = {}
        for df_name, suffix in expected_files.items():
            filepath = os.path.join(directory, f"{prefix}{suffix}")
            if os.path.exists(filepath):
                try:
                    loaded_dfs[df_name] = pd.read_csv(filepath)
                except Exception as e:
                    print(f"Aviso: Não foi possível ler {filepath}: {e}")
        if 'bus' not in loaded_dfs:
            raise FileNotFoundError(f"Ficheiro 'bus.csv' não encontrado no directório. Prefix='{prefix}'")
        self.dataframes = loaded_dfs
        return self.dataframes

    def _get_region_from_name(self, name):
        """Identifica a região do Brasil com base em palavras-chave no nome da barra."""
        name_upper = str(name).upper()
        # Mapeamento simples (pode ser expandido)
        sul = ['IVAIPORA', 'LONDRINA', 'BARRACAO', 'SIDEROPOL', 'FARROUPIL', 'P.FUNDO', 'XANXERE', 
               'S.OSORIO', 'AREIA', 'JOINVILE', 'BLUMENAU', 'R.QUEIMAD', 'F.AREIA', 'GRAVATAI', 
               'V.AIRES', 'PINHEIRO', 'S.SANTIAG', 'J.LACERDA', 'SEGREDO', 'ITAUBA', 'FORQUILHI']
        sudeste = [] # Adicionar nomes de SE, CO, N, NE
        
        if any(s in name_upper for s in sul): return 'Sul'
        if any(s in name_upper for s in sudeste): return 'Sudeste'
        return 'N/D'

    def create_network_from_dataframes(self):
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
        
        df_bus['regiao'] = df_bus['name'].apply(self._get_region_from_name)

        df_bus['bus_id'] = pd.to_numeric(df_bus['bus_id'], errors='coerce').dropna().astype(int)
        for _, row in df_bus.iterrows():
            bus_id, vn_kv = int(row['bus_id']), float(row['vn_kv'])
            new_idx = pp.create_bus(self.net, name=row['name'], vn_kv=vn_kv, zone=row['regiao'])
            bus_map[bus_id], bus_vn_map[bus_id] = new_idx, vn_kv
        
        # Atualiza o DataFrame de 'bus' nos dataframes do modelo para refletir novas colunas
        self.dataframes['bus'] = df_bus

        def safe_get_bus_idx(val):
            try: return bus_map.get(int(float(val)))
            except (ValueError, TypeError): return None
        if 'load_gen' in raw_dfs:
            df_lg = raw_dfs['load_gen'].copy()
            df_lg.rename(columns={'Barra': 'bus_id', 'Carga Ativa (MW)': 'p_mw_load', 'Carga Reativa (Mvar)': 'q_mvar_load', 'Potência Ativa (MW)': 'p_mw_gen'}, inplace=True, errors='ignore')
            for _, row in df_lg.iterrows():
                bus_idx = safe_get_bus_idx(row.get('bus_id'))
                if bus_idx is None: continue
                if pd.notna(row.get('p_mw_load', 0)) and row.get('p_mw_load', 0) > 0:
                    pp.create_load(self.net, bus=bus_idx, p_mw=row['p_mw_load'], q_mvar=row.get('q_mvar_load', 0))
                if pd.notna(row.get('p_mw_gen', 0)) and row.get('p_mw_gen', 0) > 0:
                    (pp.create_ext_grid if row.get('Tipo de Barra (*)') == 2 else pp.create_gen)(self.net, bus=bus_idx, p_mw=row.get('p_mw_gen', 0), vm_pu=1.0)
        if 'shunt' in raw_dfs:
            df_shunt = raw_dfs['shunt'].copy()
            df_shunt.rename(columns={'Barra': 'bus_id', 'Susceptância Shunt B(pu)': 'b_pu'}, inplace=True, errors='ignore')
            for _, row in df_shunt.iterrows():
                bus_idx = safe_get_bus_idx(row.get('bus_id'))
                if bus_idx is not None:
                    q_mvar = row.get('b_pu', 0) * self.net.sn_mva
                    pp.create_shunt(self.net, bus=bus_idx, p_mw=0, q_mvar=q_mvar)
        if 'line' in raw_dfs:
            df_line = raw_dfs['line'].copy()
            df_line.rename(columns={'De': 'from_bus', 'Para': 'to_bus'}, inplace=True, errors='ignore')
            for _, row in df_line.iterrows():
                from_bus_id, to_bus_id = row.get('from_bus'), row.get('to_bus')
                from_bus_idx, to_bus_idx = safe_get_bus_idx(from_bus_id), safe_get_bus_idx(to_bus_id)
                if from_bus_idx is None or to_bus_idx is None: continue
                vn_from, vn_to = bus_vn_map.get(int(from_bus_id)), bus_vn_map.get(int(to_bus_id))
                if vn_from is None or vn_to is None: continue
                if abs(vn_from - vn_to) > 1:
                    hv_bus, lv_bus = (from_bus_idx, to_bus_idx) if vn_from > vn_to else (to_bus_idx, from_bus_idx)
                    vn_hv, vn_lv = (vn_from, vn_to) if vn_from > vn_to else (vn_to, vn_from)
                    pp.create_transformer_from_parameters(self.net, hv_bus=hv_bus, lv_bus=lv_bus, sn_mva=self.net.sn_mva, vn_hv_kv=vn_hv, vn_lv_kv=vn_lv, vkr_percent=row.get('R(pu)', 0)*100, vk_percent=row.get('X(pu)', 0)*100, pfe_kw=0, i0_percent=0)
                else:
                    z_base = (vn_from**2) / self.net.sn_mva
                    r_ohm = row.get('R(pu)', 0) * z_base
                    x_ohm = row.get('X(pu)', 0) * z_base
                    c_nf = (row.get('B(pu)', 0) / (2 * np.pi * 60 * z_base)) * 1e9 if z_base > 0 else 0
                    pp.create_line_from_parameters(self.net, from_bus=from_bus_idx, to_bus=to_bus_idx, length_km=1.0, r_ohm_per_km=r_ohm, x_ohm_per_km=x_ohm, c_nf_per_km=c_nf, max_i_ka=1.0)
        return self.net

    def run_power_flow(self):
        if self.net is None or self.net.bus.empty: raise ValueError("A rede não foi criada ou está vazia.")
        try:
            pp.runpp(self.net, max_iteration=30, enforce_q_lims=True, numba=False)
            return (True, "Fluxo de potência executado com sucesso.") if self.net.converged else (False, "O fluxo de potência NÃO CONVERGIU.")
        except Exception as e:
            try: pp.diagnostic(self.net)
            except Exception as diag_e: return False, f"Falha no fluxo de potência: {e}\nDiagnóstico também falhou: {diag_e}"
            return False, f"Falha no fluxo de potência: {e}"

# =============================================================================
# 3. VIEW (Interface Gráfica com PySide6)
# =============================================================================
class MetricsWidget(QWidget):
    """Um widget para exibir as métricas da rede."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.gen_card, self.load_card = self._create_metric_card("Geração Total (MW)", "N/A"), self._create_metric_card("Carga Total (MW)", "N/A")
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
    def __init__(self, parent=None):
        self.fig = plt.figure(figsize=(10, 8))
        gs = gridspec.GridSpec(3, 1, height_ratios=[20, 1.5, 1.5], hspace=0.4)
        self.ax_diagram, self.ax_legend, self.ax_colorbar = self.fig.add_subplot(gs[0]), self.fig.add_subplot(gs[1]), self.fig.add_subplot(gs[2])
        super().__init__(self.fig)
        self.setParent(parent)
        self.fig.patch.set_facecolor('#F0F0F0')
    def plot_network(self, net, plot_results=False):
        for ax in [self.ax_diagram, self.ax_legend, self.ax_colorbar]: ax.clear()
        self.ax_legend.axis('off'); self.ax_colorbar.axis('off')
        if not net or net.bus.empty:
            self.ax_diagram.text(0.5, 0.5, 'Nenhuma rede para exibir.', ha='center', va='center', color='gray')
            self.draw(); return
        try:
            collections = {'bus': [], 'line': [], 'trafo': [], 'load': [], 'gen': [], 'ext_grid': []}
            if not net.bus.empty: collections['bus'].append(plot.create_bus_collection(net, size=0.05, zorder=10))
            if not net.line.empty: collections['line'].append(plot.create_line_collection(net, color="grey", linewidth=1.2, use_bus_geodata=True))
            if not net.trafo.empty: collections['trafo'].append(plot.create_trafo_collection(net, color="purple", linewidth=2, use_bus_geodata=True))
            if not net.load.empty: collections['load'].append(plot.create_load_collection(net, size=0.04, orientation=45, color="red"))
            if not net.gen.empty: collections['gen'].append(plot.create_gen_collection(net, size=0.06, orientation=180, color='green'))
            if not net.ext_grid.empty: collections['ext_grid'].append(plot.create_ext_grid_collection(net, size=0.08, orientation=180, color='orange'))
            for col_list in collections.values(): plot.draw_collections(col_list, ax=self.ax_diagram)
            handles = [plt.Line2D([0], [0], color='grey', lw=2, label='Linha'), plt.Line2D([0],[0], marker='o', color='purple', lw=0, markersize=8, label='Transformador'), plt.Line2D([0],[0], marker='>', color='red', lw=0, markersize=8, label='Carga'), plt.Line2D([0],[0], marker='o', color='green', lw=0, markersize=8, label='Gerador'), plt.Line2D([0],[0], marker='s', color='orange', lw=0, markersize=8, label='Rede Externa')]
            self.ax_legend.legend(handles=handles, title="Componentes", loc='center', ncol=len(handles), frameon=False)
            if plot_results and not net.res_line.empty and 'loading_percent' in net.res_line:
                cmap, norm = plt.get_cmap('coolwarm'), mcolors.Normalize(vmin=0, vmax=100)
                lc_res = plot.create_line_collection(net, lines=net.res_line.index, cmap=cmap, norm=norm, linewidth=2.5, use_bus_geodata=True)
                lc_res.set_array(net.res_line.loading_percent.values); plot.draw_collections([lc_res], ax=self.ax_diagram)
                sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm); sm.set_array([])
                self.fig.colorbar(sm, cax=self.ax_colorbar, label='Carregamento da Linha (%)', orientation='horizontal')
            else: self.ax_colorbar.text(0.5, 0.5, 'Carregamento indisponível', ha='center', va='center', color='gray')
        except Exception as e:
            self.ax_diagram.text(0.5, 0.5, f'Erro ao plotar a rede:\n{e}', ha='center', va='center', color='red')
            print(f"ERRO CRÍTICO ao plotar o diagrama: {traceback.format_exc()}")
        self.ax_diagram.set_title("Diagrama Unifilar da Rede"); self.fig.tight_layout(); self.draw()

class ResultsPlotsCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig, (self.ax_voltage, self.ax_loading) = plt.subplots(2, 1, figsize=(8, 6))
        super().__init__(self.fig)
        self.setParent(parent); self.fig.patch.set_facecolor('#F0F0F0'); self.clear_plots()
    def plot_results(self, net):
        self.clear_plots()
        try:
            if 'res_bus' in net and not net.res_bus.empty:
                bus_voltages = net.res_bus.vm_pu
                # Mostrar 10 mais altas e 10 mais baixas
                top_10 = bus_voltages.nlargest(10)
                bottom_10 = bus_voltages.nsmallest(10)
                voltages_to_plot = pd.concat([top_10, bottom_10]).sort_values()

                colors = ['#d9534f' if v < 0.95 else '#f0ad4e' if v > 1.05 else '#5cb85c' for v in voltages_to_plot]
                voltages_to_plot.plot(kind='barh', ax=self.ax_voltage, color=colors, width=0.8)
                self.ax_voltage.set_title('Tensão nas Barras (Maiores e Menores Valores)'); self.ax_voltage.set_xlabel('Tensão (p.u.)')
                self.ax_voltage.axvline(x=1.05, color='r', linestyle='--', linewidth=1, label='Limite Superior')
                self.ax_voltage.axvline(x=0.95, color='r', linestyle='--', linewidth=1, label='Limite Inferior')
                self.ax_voltage.legend(); self.ax_voltage.grid(True, axis='x', linestyle=':')
            if 'res_line' in net and not net.res_line.empty:
                line_loading = net.res_line.loading_percent.sort_values(ascending=False).head(15).sort_values()
                line_loading.plot(kind='barh', ax=self.ax_loading, color='#5bc0de', width=0.8)
                self.ax_loading.set_title('Top 15 Linhas com Maior Carregamento'); self.ax_loading.set_xlabel('Carregamento (%)')
                self.ax_loading.grid(True, axis='x', linestyle=':')
        except Exception as e: print(f"ERRO ao plotar gráficos de resultados: {traceback.format_exc()}")
        self.fig.tight_layout(); self.draw()
    def clear_plots(self):
        self.ax_voltage.clear(); self.ax_loading.clear()
        self.ax_voltage.text(0.5, 0.5, 'Resultados de Tensão Indisponíveis', ha='center', va='center', color='gray')
        self.ax_loading.text(0.5, 0.5, 'Resultados de Carregamento Indisponíveis', ha='center', va='center', color='gray')
        self.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pandapower Case Manager"); self.setGeometry(100, 100, 1600, 900)
        main_widget = QWidget(); self.setCentralWidget(main_widget); main_layout = QHBoxLayout(main_widget)
        splitter = QSplitter(Qt.Horizontal); main_layout.addWidget(splitter)
        left_panel = QWidget(); left_layout = QVBoxLayout(left_panel); splitter.addWidget(left_panel)
        tools_group = QGroupBox("Ferramentas"); tools_group.setCheckable(True); tools_group.setChecked(True)
        tools_layout = QVBoxLayout(tools_group); left_layout.addWidget(tools_group)
        self.btn_load_pwf, self.btn_import_case, self.btn_build_network, self.btn_run_pf = QPushButton("Carregar .PWF"), QPushButton("Importar Caso (Excel/CSV)"), QPushButton("Montar Rede a partir dos Dados"), QPushButton("▶ Executar Fluxo de Potência")
        for btn in [self.btn_load_pwf, self.btn_import_case, self.btn_build_network, self.btn_run_pf]: tools_layout.addWidget(btn)
        green_style = "QPushButton { background-color: #2E8B57; color: white; font-weight: bold; border-radius: 0px; padding: 8px; } QPushButton:hover { background-color: #3CB371; }"
        purple_style = "QPushButton { background-color: #8A2BE2; color: white; font-weight: bold; border-radius: 0px; padding: 8px; } QPushButton:hover { background-color: #9932CC; }"
        for btn in [self.btn_load_pwf, self.btn_import_case, self.btn_build_network]: btn.setStyleSheet(green_style)
        self.btn_run_pf.setStyleSheet(purple_style)
        self.tabs = QTabWidget(); left_layout.addWidget(self.tabs); self.tables = {}
        export_group = QGroupBox("Exportar"); export_layout = QVBoxLayout(export_group)
        self.btn_export_excel = QPushButton("Exportar Rede para .XLSX"); self.btn_export_excel.setStyleSheet(green_style)
        export_layout.addWidget(self.btn_export_excel); left_layout.addWidget(export_group)
        right_panel = QGroupBox("Visualização da Rede e Resultados"); right_layout_main = QVBoxLayout(right_panel)
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True); right_layout_main.addWidget(scroll_area)
        scroll_content = QWidget(); scroll_area.setWidget(scroll_content)
        right_layout_scroll = QVBoxLayout(scroll_content)
        self.metrics_widget = MetricsWidget(); right_layout_scroll.addWidget(self.metrics_widget)
        self.network_canvas = NetworkCanvas(self); right_layout_scroll.addWidget(self.network_canvas)
        self.results_canvas = ResultsPlotsCanvas(self); right_layout_scroll.addWidget(self.results_canvas)
        report_group = QGroupBox("Relatórios"); report_layout = QHBoxLayout(report_group)
        self.btn_generate_report = QPushButton("📈 Gerar Relatório HTML"); self.btn_generate_report.setStyleSheet(green_style)
        report_layout.addWidget(self.btn_generate_report); right_layout_scroll.addWidget(report_group)
        splitter.addWidget(right_panel); splitter.setSizes([700, 900])

    def add_table_tab(self, name, df):
        if name not in self.tables:
            self.tables[name] = QTableWidget()
            self.tabs.addTab(self.tables[name], name.replace("_", " ").capitalize())
        table = self.tables[name]
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
        filepath, _ = QFileDialog.getOpenFileName(self.view, "Importar Caso", "", "Ficheiros Suportados (*.xlsx *.csv)")
        if filepath: self._exec_task(self._do_import, filepath)
    def _do_import(self, filepath):
        dfs = self.model.load_data_from_excel(filepath) if filepath.lower().endswith('.xlsx') else self.model.load_data_from_csvs(filepath)
        self._update_ui_with_dataframes(dfs)
        QMessageBox.information(self.view, "Sucesso", f"Dados carregados de: {os.path.dirname(filepath)}")
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
            pp.plotting.create_generic_coordinates(self.model.net, overwrite=True)
            if 'bus_geodata' in self.model.net: self.model.net.bus_geodata = self.model.net.bus_geodata.reindex(self.model.net.bus.index)
            self.view.network_canvas.plot_network(self.model.net)
            self.view.results_canvas.clear_plots()
            QMessageBox.information(self.view, "Sucesso", "Rede pandapower montada com sucesso.")
        else: QMessageBox.warning(self.view, "Aviso", "Não foi possível montar a rede.")
    def run_power_flow(self):
        if not self.model.net or self.model.net.bus.empty:
            QMessageBox.warning(self.view, "Aviso", "A rede não foi montada. Clique em 'Montar Rede' primeiro."); return
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
            df = pd.DataFrame(data, columns=headers)
            index_name = df.columns[0]
            df_numeric = df.drop(columns=[index_name], errors='ignore').apply(pd.to_numeric, errors='coerce')
            dfs[name] = pd.concat([df[[index_name]], df_numeric], axis=1) if index_name in df.columns else df.apply(pd.to_numeric, errors='coerce')
        return dfs
    def export_network_to_excel(self):
        if not self.view.tables: QMessageBox.warning(self.view, "Aviso", "Não há dados para exportar."); return
        filepath, _ = QFileDialog.getSaveFileName(self.view, "Exportar Rede para Excel", "", "Ficheiro Excel (*.xlsx)")
        if filepath: self._exec_task(self._do_export, filepath)
    def _do_export(self, filepath):
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for i in range(self.view.tabs.count()):
                sheet_name = self.view.tabs.tabText(i)
                table = self.view.tabs.widget(i)
                headers = [table.horizontalHeaderItem(j).text() for j in range(table.columnCount())]
                data = [[table.item(r,c).text() if table.item(r,c) else '' for c in range(table.columnCount())] for r in range(table.rowCount())]
                pd.DataFrame(data, columns=headers).to_excel(writer, sheet_name=sheet_name, index=False)
        QMessageBox.information(self.view, "Sucesso", f"Rede exportada com sucesso para:\n{filepath}")
    def generate_interactive_report(self):
        if not self.model.net or not hasattr(self.model.net, 'res_bus') or self.model.net.res_bus.empty:
            QMessageBox.warning(self.view, "Aviso", "É necessário executar o fluxo de potência primeiro."); return
        filepath, _ = QFileDialog.getSaveFileName(self.view, "Guardar Relatório HTML", "", "Ficheiro HTML (*.html)")
        if filepath: self._exec_task(self._do_generate_report, filepath)
    def _do_generate_report(self, filepath):
        # Gera os gráficos como imagens em memória
        fig_diagram = self._create_diagram_plot()
        fig_voltage, fig_loading = self._create_results_plots()
        
        diagram_img_b64 = self._fig_to_base64(fig_diagram)
        voltage_img_b64 = self._fig_to_base64(fig_voltage)
        loading_img_b64 = self._fig_to_base64(fig_loading)
        
        # Gera tabelas HTML
        res_bus_html = self.model.net.res_bus.to_html(classes='table table-striped table-hover', justify='center')
        res_line_html = self.model.net.res_line.to_html(classes='table table-striped table-hover', justify='center')

        # Monta o HTML final
        html = self._build_html_report(diagram_img_b64, voltage_img_b64, loading_img_b64, res_bus_html, res_line_html)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
            
        QMessageBox.information(self.view, "Sucesso", f"Relatório gerado!\nA abrir {filepath}...")
        webbrowser.open(f"file://{os.path.realpath(filepath)}")

    def _create_diagram_plot(self):
        # Cria uma figura temporária para o diagrama
        temp_canvas = NetworkCanvas()
        temp_canvas.plot_network(self.model.net, plot_results=True)
        return temp_canvas.fig

    def _create_results_plots(self):
        # Lógica duplicada de ResultsPlotsCanvas para desacoplamento
        fig_v, ax_v = plt.subplots(figsize=(10, 8)); fig_l, ax_l = plt.subplots(figsize=(10, 8))
        net = self.model.net
        # Tensão
        bus_voltages = net.res_bus.vm_pu
        top_10 = bus_voltages.nlargest(10)
        bottom_10 = bus_voltages.nsmallest(10)
        voltages_to_plot = pd.concat([top_10, bottom_10]).sort_values()
        colors = ['#d9534f' if v < 0.95 else '#f0ad4e' if v > 1.05 else '#5cb85c' for v in voltages_to_plot]
        voltages_to_plot.plot(kind='barh', ax=ax_v, color=colors, width=0.8)
        ax_v.set_title('Tensão nas Barras (Maiores e Menores Valores)'); ax_v.set_xlabel('Tensão (p.u.)'); ax_v.grid(True, axis='x')
        # Carregamento
        line_loading = net.res_line.loading_percent.sort_values(ascending=False).head(20).sort_values()
        line_loading.plot(kind='barh', ax=ax_l, color='#5bc0de', width=0.8)
        ax_l.set_title('Top 20 Linhas com Maior Carregamento'); ax_l.set_xlabel('Carregamento (%)'); ax_l.grid(True, axis='x')
        for fig in [fig_v, fig_l]: fig.tight_layout()
        return fig_v, fig_l

    def _fig_to_base64(self, fig):
        buf = BytesIO(); fig.savefig(buf, format='png', bbox_inches='tight'); plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode('utf-8')

    def _build_html_report(self, diagram_img, voltage_img, loading_img, bus_html, line_html):
        return f"""
        <!DOCTYPE html><html lang="pt-br"><head><meta charset="UTF-8"><title>Relatório de Fluxo de Potência</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>body{{padding: 2rem; background-color: #f8f9fa;}} .table{{font-size: 0.85rem;}} h2{{border-bottom: 2px solid #dee2e6; padding-bottom: 10px; margin-top: 2.5rem; color: #495057;}} .img-container{{padding: 1rem; border: 1px solid #dee2e6; border-radius: .25rem; background-color: white; margin-bottom: 2rem;}}</style>
        </head><body><div class="container">
        <h1 class="display-4 text-center mb-4">Relatório de Análise de Rede</h1>
        <h2>Diagrama Unifilar</h2><div class="img-container"><img src="data:image/png;base64,{diagram_img}" class="img-fluid"></div>
        <h2>Resultados Gráficos</h2>
        <div class="row">
            <div class="col-lg-6"><div class="img-container"><img src="data:image/png;base64,{voltage_img}" class="img-fluid"></div></div>
            <div class="col-lg-6"><div class="img-container"><img src="data:image/png;base64,{loading_img}" class="img-fluid"></div></div>
        </div>
        <h2>Resultados das Barras</h2><div class="table-responsive">{bus_html}</div>
        <h2>Resultados das Linhas</h2><div class="table-responsive">{line_html}</div>
        </div></body></html>
        """

# =============================================================================
# 5. SIN 45 SIMULATOR - ONS DATASET FOR POWER FLOW IN PANDAPOWER
# =============================================================================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = AppController()
    sys.exit(app.exec())

