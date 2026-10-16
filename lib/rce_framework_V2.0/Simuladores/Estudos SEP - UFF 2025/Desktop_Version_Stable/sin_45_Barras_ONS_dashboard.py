# sin45_dashboard.py
# Versão consolidada por ChatGPT para Mestre Pedro Victor
# pip install  pandas numpy matplotlib PySide6 openpyxl sqlalchemy  pandapower plotly PySide6


import os, sys, re, traceback, webbrowser, sqlite3, tempfile, base64
from io import BytesIO
from typing import Dict, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D

# Qt / PySide6 imports (GUI)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QFileDialog,
    QMessageBox, QHeaderView, QGroupBox, QSplitter, QLabel, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

# Try optional imports
try:
    import pandapower as pp
    import pandapower.plotting as plot
    HAS_PANDAPOWER = True
except Exception as e:
    pp = None; plot = None; HAS_PANDAPOWER = False

try:
    import plotly.express as px
    HAS_PLOTLY = True
except:
    HAS_PLOTLY = False

# Try to import QWebEngineView for plotly embedding
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except:
    QWebEngineView = None; HAS_WEBENGINE = False

# UI Styles
AppStyles = """
QWidget { background-color: #2E2E2E; color: #F0F0F0; font-family: "Segoe UI"; }
QGroupBox { font-weight: bold; border: 1px solid #555; border-radius: 5px; margin-top: 10px; padding: 12px; }
QPushButton { padding:8px; color: white; font-weight:bold; border:1px solid #555; border-radius:4px; }
QPushButton#run_button, QPushButton#build_button { background-color: #8A2BE2; }
QPushButton#run_button:hover, QPushButton#build_button:hover { background-color: #9932CC; }
QTabWidget::pane { border-top: 2px solid #555; }
QTabBar::tab { background: #444; border:1px solid #555; padding:8px 12px; color:#F0F0F0; }
QTabBar::tab:selected { background:#8A2BE2; color:white; }
QTableWidget { background-color:#3C3C3C; color:#F0F0F0; gridline-color:#555; }
QHeaderView::section { background-color:#555; color:#F0F0F0; padding:4px; border:1px solid #666; }
"""

# ======================================
# Parser (Anarede / Organon .PWF / .DAT)
# ======================================
class AnaredeParser:
    @staticmethod
    def parse_pwf_to_dataframes(filepath: str) -> Dict[str, pd.DataFrame]:
        """
        Lê um arquivo .PWF/.DAT no formato AnaRede/Organon e retorna dict de DataFrames:
        keys: 'bus', 'line', 'gen', 'load', 'shunt' quando detectados.
        """
        data_blocks = { 'DBAR': [], 'DLIN': [], 'DGER': [], 'DCAR': [], 'DBSH': [], 'DTRA': [] }
        current_block = None
        with open(filepath, 'r', encoding='latin-1', errors='ignore') as f:
            for raw in f:
                line = raw.rstrip('\n').rstrip('\r')
                if not line.strip(): continue
                s = line.strip()
                # comentários e delimitadores
                if s.startswith('(') or s.startswith('!'): continue
                if s.startswith('99999'):
                    current_block = None; continue
                m = re.match(r'^(\w{4})', s)
                if m and m.group(1).upper() in data_blocks:
                    current_block = m.group(1).upper(); continue
                if current_block:
                    data_blocks[current_block].append(s)

        dfs = {}
        # DBAR: barras
        if data_blocks['DBAR']:
            rows=[]
            for ln in data_blocks['DBAR']:
                try:
                    num = int(ln[0:5])
                    name = ln[5:22].strip() if len(ln)>=22 else ln[5:12].strip()
                    vn = float(ln[28:34]) if len(ln)>=34 else 230.0
                    rows.append({'bus_id':num,'name':name,'vn_kv':vn})
                except Exception:
                    continue
            dfs['bus']=pd.DataFrame(rows)

        # DLIN: linhas
        if data_blocks['DLIN']:
            rows=[]
            for ln in data_blocks['DLIN']:
                try:
                    de=int(ln[0:5]); para=int(ln[6:11])
                    r_pu=float(ln[21:29]); x_pu=float(ln[30:38]); b_pu=float(ln[39:47])
                    rows.append({'from_bus':de,'to_bus':para,'R(pu)':r_pu,'X(pu)':x_pu,'B(pu)':b_pu})
                except Exception:
                    continue
            dfs['line']=pd.DataFrame(rows)

        # DGER: geradores
        if data_blocks['DGER']:
            rows=[]
            for ln in data_blocks['DGER']:
                try:
                    bus=int(ln[0:5]); p=float(ln[21:29])
                    rows.append({'bus_id':bus,'p_mw':p})
                except:
                    continue
            dfs['gen']=pd.DataFrame(rows)

        # DCAR: cargas
        if data_blocks['DCAR']:
            rows=[]
            for ln in data_blocks['DCAR']:
                try:
                    bus=int(ln[0:5]); p=float(ln[21:29])
                    q=float(ln[30:38]) if len(ln)>=38 else 0.0
                    rows.append({'bus_id':bus,'p_mw':p,'q_mvar':q})
                except:
                    continue
            dfs['load']=pd.DataFrame(rows)

        # DBSH: shunts
        if data_blocks['DBSH']:
            rows=[]
            for ln in data_blocks['DBSH']:
                try:
                    bus=int(ln[0:5]); b=float(ln[21:29])
                    rows.append({'bus_id':bus,'b_pu':b})
                except:
                    continue
            dfs['shunt']=pd.DataFrame(rows)

        return dfs

# ========================
# Database Manager (SQLite)
# ========================
class DatabaseManager:
    def __init__(self, db_path='sin45_data.db'):
        self.db_path = db_path
        import sqlalchemy
        self.engine = sqlalchemy.create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    def save_dataframe(self, df: pd.DataFrame, table_name: str, if_exists='replace'):
        df.to_sql(table_name, self.engine, index=False, if_exists=if_exists)

    def load_table(self, table_name: str) -> pd.DataFrame:
        import sqlalchemy
        try:
            return pd.read_sql_table(table_name, self.engine)
        except Exception:
            return pd.DataFrame()

    def list_tables(self):
        import sqlalchemy
        with self.engine.connect() as conn:
            res = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            return [r[0] for r in res.fetchall()]

# ======================
# SmartGrid (Model layer)
# ======================
class SmartGrid:
    def __init__(self, sn_mva=100.0):
        self.sn_mva = sn_mva
        self.net = None
        self.dataframes = {}
        self.db = DatabaseManager()
        self._pp = pp  # may be None if not installed

    def load_pwf(self, filepath):
        dfs = AnaredeParser.parse_pwf_to_dataframes(filepath)
        for k,v in dfs.items():
            if k in self.dataframes and isinstance(self.dataframes[k], pd.DataFrame):
                self.dataframes[k] = pd.concat([self.dataframes[k], v], ignore_index=True)
            else:
                self.dataframes[k] = v
            # persist
            if isinstance(self.dataframes[k], pd.DataFrame) and not self.dataframes[k].empty:
                self.db.save_dataframe(self.dataframes[k], k)
        return dfs

    def load_excel(self, filepath):
        xls = pd.ExcelFile(filepath)
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            key = sheet.lower().replace(" ", "_")
            self.dataframes[key] = df
            if not df.empty: self.db.save_dataframe(df, key)
        return self.dataframes

    def create_network_from_dataframes(self):
        if self._pp is None:
            raise RuntimeError("pandapower não disponível. Instale pandapower para construir a rede.")
        net = self._pp.create_empty_network(sn_mva=self.sn_mva)
        bus_map = {}
        df_bus = self.dataframes.get('bus')
        if df_bus is None or df_bus.empty:
            raise ValueError("Dados de barras ausentes.")
        dfb = df_bus.copy()
        if 'bus_id' not in dfb.columns:
            # tenta detectar coluna
            candidates = [c for c in dfb.columns if 'barra' in c.lower() or 'bus' in c.lower()]
            if candidates:
                dfb = dfb.rename(columns={candidates[0]:'bus_id'})
        dfb['vn_kv'] = pd.to_numeric(dfb.get('vn_kv', 230.0), errors='coerce').fillna(230.0)
        dfb['bus_id'] = pd.to_numeric(dfb['bus_id'], errors='coerce').astype(int)

        for _,r in dfb.iterrows():
            idx = self._pp.create_bus(net, name=str(r.get('name', r['bus_id'])), vn_kv=float(r['vn_kv']), in_service=True)
            bus_map[int(r['bus_id'])] = idx

        # gens
        for key in ['gen','dger','ger']:
            df_gen = self.dataframes.get(key)
            if isinstance(df_gen, pd.DataFrame) and not df_gen.empty:
                for _,g in df_gen.iterrows():
                    try:
                        bid = int(g.get('bus_id', g.get('Barra', g.get('barra'))))
                        idx = bus_map.get(bid)
                        if idx is None: continue
                        p = float(g.get('p_mw', g.get('p', 0)))
                        self._pp.create_gen(net, bus=idx, p_mw=p, vm_pu=1.0)
                    except:
                        continue

        # loads
        df_load = self.dataframes.get('load')
        if isinstance(df_load, pd.DataFrame) and not df_load.empty:
            for _,l in df_load.iterrows():
                try:
                    bid = int(l.get('bus_id', l.get('Barra', l.get('barra'))))
                    idx = bus_map.get(bid)
                    if idx is None: continue
                    p = float(l.get('p_mw', l.get('p', 0)))
                    q = float(l.get('q_mvar', l.get('q', 0)))
                    self._pp.create_load(net, bus=idx, p_mw=p, q_mvar=q)
                except:
                    continue

        # lines
        df_line = self.dataframes.get('line')
        if isinstance(df_line, pd.DataFrame) and not df_line.empty:
            for _,ln in df_line.iterrows():
                try:
                    fb = bus_map.get(int(ln.get('from_bus', ln.get('De', ln.get('de')))))
                    tb = bus_map.get(int(ln.get('to_bus', ln.get('Para', ln.get('para')))))
                    if fb is None or tb is None: continue
                    r_ohm = float(ln.get('r_ohm_per_km', 0.0))
                    x_ohm = float(ln.get('x_ohm_per_km', 0.0))
                    self._pp.create_line_from_parameters(net, from_bus=fb, to_bus=tb, length_km=1.0,
                                                        r_ohm_per_km=r_ohm, x_ohm_per_km=x_ohm,
                                                        c_nf_per_km=float(ln.get('c_nf_per_km', 0.0)),
                                                        max_i_ka=float(ln.get('max_i_ka', 1.0)))
                except:
                    continue

        if net.ext_grid.empty and not net.bus.empty:
            self._pp.create_ext_grid(net, bus=net.bus.index[0], vm_pu=1.0)

        self.net = net
        return net

    def run_power_flow(self):
        if self._pp is None:
            raise RuntimeError("pandapower não disponível.")
        if self.net is None:
            raise ValueError("Rede não construída.")
        try:
            self._pp.runpp(self.net, algorithm='nr', max_iteration=30, enforce_q_lims=True, numba=True)
            return getattr(self.net,'converged', False)
        except Exception as e:
            try:
                self._pp.diagnostic(self.net)
            except:
                pass
            raise

# ================
# VIEW Components
# ================
class MetricsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.gen_card = self._create_metric_card("Geração Total (MW)", "N/A")
        self.load_card = self._create_metric_card("Carga Total (MW)", "N/A")
        layout.addWidget(self.gen_card); layout.addWidget(self.load_card)
    def _create_metric_card(self, title, initial):
        card=QGroupBox(title); l=QVBoxLayout(card)
        lbl=QLabel(str(initial)); lbl.setFont(QFont("Segoe UI", 20, QFont.Bold)); lbl.setAlignment(Qt.AlignCenter)
        l.addWidget(lbl); card.setLayout(l); return card
    def update_metrics(self, gen_mw, load_mw):
        self.gen_card.findChild(QLabel).setText(f"{gen_mw:.2f}")
        self.load_card.findChild(QLabel).setText(f"{load_mw:.2f}")

class NetworkCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = plt.figure(figsize=(10,8), tight_layout=True)
        gs = gridspec.GridSpec(3,1, height_ratios=[20,1,1], hspace=0.1)
        self.ax_diagram = fig.add_subplot(gs[0]); self.ax_legend = fig.add_subplot(gs[1]); self.ax_colorbar = fig.add_subplot(gs[2])
        super().__init__(fig); self.setParent(parent)
        self.fig = fig
        self.network_map = {
            'bus': {'size':0.08, 'zorder':10},
            'bus_transfer': {'color':'#1f77b4'},
            'bus_gen': {'color':'#2ca02c'},
            'bus_load': {'color':'#ff7f0e'},
            'bus_gen_load': {'color':'#800080'},
            'line': {'linewidth':1.5,'zorder':1},
            'trafo': {'linewidth':1.5,'color':'purple','zorder':5},
            'ext_grid': {'size':0.10,'zorder':12,'color':'gold'},
            'shunt': {'size':0.12,'color':'cyan','zorder':12},
            'diagram':{'bg_color':'#FFFFFF','title_color':'#000000'},
            'legend':{'text_color':'#000000'},
            'colorbar':{'label_color':'#000000','tick_color':'#000000'}
        }

    def plot_network(self, net, plot_results=False):
        for ax in [self.ax_diagram, self.ax_legend, self.ax_colorbar]: ax.clear()
        self.ax_legend.axis('off'); self.ax_colorbar.axis('off')
        bg_color = self.network_map['diagram']['bg_color']; title_color=self.network_map['diagram']['title_color']
        self.fig.patch.set_facecolor(bg_color); self.ax_diagram.set_facecolor(bg_color)

        if net is None or (hasattr(net,'bus') and net.bus.empty):
            self.ax_diagram.text(0.5,0.5,'Nenhuma rede para exibir.', ha='center', va='center', color='gray')
            self.draw(); return

        try:
            # ensure coords
            if HAS_PANDAPOWER:
                if not hasattr(net,'bus_geodata') or net.bus_geodata.empty:
                    pp.plotting.create_generic_coordinates(net, overwrite=True)

                gen_buses = set(net.gen.bus) if not net.gen.empty else set()
                ext_buses = set(net.ext_grid.bus) if not net.ext_grid.empty else set()
                load_buses = set(net.load.bus) if not net.load.empty else set()
                bus_colors=[]
                for b in net.bus.index:
                    is_gen = b in gen_buses or b in ext_buses
                    is_load = b in load_buses
                    if is_gen and is_load: bus_colors.append(self.network_map['bus_gen_load']['color'])
                    elif is_gen: bus_colors.append(self.network_map['bus_gen']['color'])
                    elif is_load: bus_colors.append(self.network_map['bus_load']['color'])
                    else: bus_colors.append(self.network_map['bus_transfer']['color'])

                collections = {'bus': plot.create_bus_collection(net, buses=net.bus.index, size=self.network_map['bus']['size'], color=bus_colors, zorder=self.network_map['bus']['zorder'])}
                if not net.trafo.empty: collections['trafo']=plot.create_trafo_collection(net, color=self.network_map['trafo']['color'], linewidths=self.network_map['trafo']['linewidth'], zorder=self.network_map['trafo']['zorder'])

                if not net.line.empty:
                    line_vns = net.bus.loc[net.line.from_bus,'vn_kv'].values
                    vn_kv_unique = sorted(pd.unique(line_vns))
                    cmap = plt.get_cmap('viridis', len(vn_kv_unique)+1)
                    colors = {v:cmap(i) for i,v in enumerate(vn_kv_unique)}
                    line_handles=[]
                    for v_kv,color in colors.items():
                        lines_at_v = net.line.index[line_vns==v_kv]
                        if len(lines_at_v)>0:
                            lc = plot.create_line_collection(net, lines=lines_at_v, color=color, use_bus_geodata=True, linewidths=self.network_map['line']['linewidth'], zorder=self.network_map['line']['zorder'])
                            self.ax_diagram.add_collection(lc)
                        line_handles.append(Line2D([0],[0], color=color, lw=2, label=f'{v_kv:.1f} kV'))
                # create other collections
                if not net.load.empty: collections['load'] = plot.create_load_collection(net, size=self.network_map['bus']['size'], zorder=self.network_map['bus']['zorder'])
                if not net.gen.empty: collections['gen'] = plot.create_gen_collection(net, size=self.network_map['bus']['size'], zorder=self.network_map['bus']['zorder'])
                if not net.ext_grid.empty: collections['ext_grid'] = plot.create_ext_grid_collection(net, size=self.network_map['ext_grid']['size'], zorder=self.network_map['ext_grid']['zorder'], color=self.network_map['ext_grid']['color'])
                plot.draw_collections(list(collections.values()), ax=self.ax_diagram)

                # overlay results
                if plot_results and not net.res_line.empty and 'loading_percent' in net.res_line:
                    cmap_res=plt.get_cmap('coolwarm'); max_load = max(100, net.res_line.loading_percent.max()*1.1)
                    from matplotlib import colors as mcolors
                    norm = mcolors.Normalize(vmin=0, vmax=max_load)
                    lc_res = plot.create_line_collection(net, lines=net.res_line.index, cmap=cmap_res, norm=norm, use_bus_geodata=True, linewidths=2.5, zorder=2)
                    lc_res.set_array(net.res_line.loading_percent.values)
                    self.ax_diagram.add_collection(lc_res)
                    sm = plt.cm.ScalarMappable(cmap=cmap_res, norm=norm); sm.set_array([])
                    cbar = self.fig.colorbar(sm, cax=self.ax_colorbar, orientation='horizontal', label='Carregamento (%)')
            else:
                # fallback: desenha nós simples
                coords = {}
                buses = []  # generate from dataframes if available
                self.ax_diagram.text(0.5,0.5,'Pandapower não disponível — visualização simplificada', ha='center', color='gray')

            self.ax_diagram.set_title("Diagrama Unifilar", color=title_color)
            self.ax_diagram.set_xticks([]); self.ax_diagram.set_yticks([])
        except Exception as e:
            self.ax_diagram.text(0.5,0.5,f'Erro ao desenhar a rede:\\n{e}', ha='center', color='red')
            print("Erro desenho:", traceback.format_exc())
        self.draw()

class ResultsPlotsCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig, (self.ax_voltage, self.ax_loading) = plt.subplots(2,1, figsize=(8,6), tight_layout=True)
        super().__init__(self.fig); self.setParent(parent)
        self.clear_plots()

    def plot_results(self, net):
        self.clear_plots()
        try:
            if hasattr(net,'res_bus') and not net.res_bus.empty:
                volt = net.res_bus.vm_pu.sort_values()
                volt.plot(kind='barh', ax=self.ax_voltage)
                self.ax_voltage.set_title('Tensão nas Barras (p.u.)')
                self.ax_voltage.axvline(1.05, color='r', linestyle='--'); self.ax_voltage.axvline(0.95, color='r', linestyle='--')
            if hasattr(net,'res_line') and not net.res_line.empty:
                loading = net.res_line.loading_percent.nlargest(15).sort_values()
                loading.plot(kind='barh', ax=self.ax_loading)
                self.ax_loading.set_title('Top 15 Linhas - Carregamento (%)')
        except Exception:
            print("Erro plots resultados:", traceback.format_exc())
        self.draw()

    def clear_plots(self):
        for ax in [self.ax_voltage, self.ax_loading]:
            ax.clear(); ax.text(0.5,0.5,'Resultados não disponíveis', ha='center', color='gray')
        self.draw()

# ======================
# Controller / Main App
# ======================
class AppController:
    def __init__(self):
        self.model = SmartGrid()
        self.view = MainWindow(self)
        self.bind_ui()
        self.view.show()

    def bind_ui(self):
        v = self.view
        v.btn_load_pwf.clicked.connect(self.on_load_pwf)
        v.btn_import_case.clicked.connect(self.on_import_excel)
        v.btn_build_network.clicked.connect(self.on_build_network)
        v.btn_run_pf.clicked.connect(self.on_run_pf)
        v.btn_export_excel.clicked.connect(self.on_export_excel)
        v.btn_generate_report.clicked.connect(self.on_generate_report)

    def on_load_pwf(self):
        fp, _ = QFileDialog.getOpenFileName(self.view, "Abrir .PWF/.DAT", "", "Decks (*.pwf *.dat);;All files (*)")
        if not fp: return
        try:
            dfs = self.model.load_pwf(fp)
            self.update_tabs_with_dfs()
            QMessageBox.information(self.view, "Sucesso", f"{os.path.basename(fp)} carregado ({len(dfs)} blocos).")
        except Exception as e:
            QMessageBox.critical(self.view, "Erro", str(e))

    def on_import_excel(self):
        fp, _ = QFileDialog.getOpenFileName(self.view, "Abrir Excel", "", "Excel (*.xlsx *.xls)")
        if not fp: return
        try:
            self.model.load_excel(fp)
            self.update_tabs_with_dfs()
            QMessageBox.information(self.view, "Sucesso", f"{os.path.basename(fp)} carregado.")
        except Exception as e:
            QMessageBox.critical(self.view, "Erro", str(e))

    def update_tabs_with_dfs(self):
        self.view.tabs.clear(); self.view.tables.clear()
        for name, df in self.model.dataframes.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                self.view.add_table_tab(name, df)
        self.view.network_canvas.plot_network(self.model.net if self.model.net is not None else None)
        self.view.results_canvas.clear_plots()
        self.view.metrics_widget.update_metrics(0,0)

    def _get_dfs_from_ui(self):
        dfs={}
        for i in range(self.view.tabs.count()):
            title = self.view.tabs.tabText(i)
            key = title.lower().replace(" ","_")
            table = self.view.tables.get(key)
            if table is None: continue
            cols=[table.horizontalHeaderItem(j).text() for j in range(table.columnCount())]
            data=[[table.item(r,c).text() if table.item(r,c) else '' for c in range(table.columnCount())] for r in range(table.rowCount())]
            dfs[key]=pd.DataFrame(data, columns=cols)
        return dfs

    def on_build_network(self):
        try:
            # prefer model.dataframes; but allow editing in UI
            dfs_ui = self._get_dfs_from_ui()
            if dfs_ui: self.model.dataframes = dfs_ui
            net = self.model.create_network_from_dataframes()
            self.view.network_canvas.plot_network(net, plot_results=False)
            QMessageBox.information(self.view, "Sucesso", "Rede construída com sucesso.")
        except Exception as e:
            QMessageBox.critical(self.view, "Erro ao construir rede", str(e))

    def on_run_pf(self):
        try:
            ok = self.model.run_power_flow()
            if ok:
                net = self.model.net
                # show results as tabs
                if hasattr(net,'res_bus') and not net.res_bus.empty: self.view.add_table_tab("res_bus", net.res_bus)
                if hasattr(net,'res_line') and not net.res_line.empty: self.view.add_table_tab("res_line", net.res_line)
                gen = (net.res_gen.p_mw.sum() if hasattr(net,'res_gen') and not net.res_gen.empty else 0) + (net.res_ext_grid.p_mw.sum() if hasattr(net,'res_ext_grid') and not net.res_ext_grid.empty else 0)
                load = net.res_load.p_mw.sum() if hasattr(net,'res_load') and not net.res_load.empty else 0
                self.view.metrics_widget.update_metrics(gen, load)
                self.view.network_canvas.plot_network(net, plot_results=True)
                self.view.results_canvas.plot_results(net)
                QMessageBox.information(self.view, "Sucesso", "Fluxo de potência convergiu.")
            else:
                QMessageBox.warning(self.view, "Fluxo de potência", "Fluxo NÃO convergiu.")
        except Exception as e:
            QMessageBox.critical(self.view, "Erro PF", str(e))

    def on_export_excel(self):
        fp, _ = QFileDialog.getSaveFileName(self.view, "Salvar Excel", "", "Excel (*.xlsx)")
        if not fp: return
        try:
            dfs = self._get_dfs_from_ui() or self.model.dataframes
            with pd.ExcelWriter(fp, engine='openpyxl') as writer:
                for k,df in dfs.items():
                    if isinstance(df,pd.DataFrame): df.to_excel(writer, sheet_name=str(k)[:31], index=False)
                if self.model.net is not None:
                    for rname in ['res_bus','res_line','res_gen','res_load']:
                        if hasattr(self.model.net, rname) and getattr(self.model.net, rname) is not None and not getattr(self.model.net, rname).empty:
                            getattr(self.model.net, rname).to_excel(writer, sheet_name=rname[:31], index=False)
            QMessageBox.information(self.view, "Exportado", f"Salvo em: {fp}")
        except Exception as e:
            QMessageBox.critical(self.view, "Erro export", str(e))

    def on_generate_report(self):
        # gera um relatório HTML simples com imagens embutidas
        try:
            if self.model.net is None:
                QMessageBox.warning(self.view, "Aviso", "Construa a rede e rode o PF antes de gerar relatório.")
                return
            # gerar imagens
            tmp = tempfile.gettempdir()
            diagram_path = os.path.join(tmp, "diagram_tmp.png")
            results_path = os.path.join(tmp, "results_tmp.png")
            # plot diagram
            fig = self.view.network_canvas.fig
            fig.savefig(diagram_path, bbox_inches='tight', facecolor=fig.get_facecolor())
            fig2 = self.view.results_canvas.fig
            fig2.savefig(results_path, bbox_inches='tight', facecolor=fig2.get_facecolor())
            # formar HTML
            with open(diagram_path,'rb') as f: d_b64 = base64.b64encode(f.read()).decode('utf-8')
            with open(results_path,'rb') as f: r_b64 = base64.b64encode(f.read()).decode('utf-8')
            bus_html = self.model.net.res_bus.to_html() if hasattr(self.model.net,'res_bus') else "<p>sem res_bus</p>"
            line_html = self.model.net.res_line.to_html() if hasattr(self.model.net,'res_line') else "<p>sem res_line</p>"
            html = f"""
            <html><head><meta charset='utf-8'><title>Relatório</title></head><body>
            <h1>Relatório de Rede</h1>
            <h2>Diagrama</h2><img src="data:image/png;base64,{d_b64}" style="max-width:100%"/>
            <h2>Resultados</h2><img src="data:image/png;base64,{r_b64}" style="max-width:100%"/>
            <h2>res_bus</h2>{bus_html}
            <h2>res_line</h2>{line_html}
            </body></html>"""
            fpath = os.path.join(tempfile.gettempdir(),"sin45_report.html")
            with open(fpath,'w', encoding='utf-8') as f: f.write(html)
            webbrowser.open(f"file://{fpath}")
            QMessageBox.information(self.view, "Relatório", f"Abrindo relatório: {fpath}")
        except Exception as e:
            QMessageBox.critical(self.view, "Erro relatório", str(e))

# =========================
# MainWindow (PySide6 View)
# =========================
class MainWindow(QMainWindow):
    def __init__(self, controller: AppController=None):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Pandapower Case Manager - Mestre Pedro Victor")
        self.resize(1600,900); self.setStyleSheet(AppStyles)
        main = QWidget(); self.setCentralWidget(main); layout = QHBoxLayout(main)
        splitter = QSplitter(Qt.Horizontal); layout.addWidget(splitter)

        # left controls
        left = QWidget(); left_layout = QVBoxLayout(left)
        tools = QGroupBox("Ferramentas"); tlay=QVBoxLayout(tools)
        self.btn_load_pwf = QPushButton("Carregar .PWF / .DAT"); self.btn_import_case = QPushButton("Importar Excel")
        self.btn_build_network = QPushButton("Construir Rede"); self.btn_build_network.setObjectName("build_button")
        self.btn_run_pf = QPushButton("▶ Executar Fluxo de Potência"); self.btn_run_pf.setObjectName("run_button")
        for b in [self.btn_load_pwf, self.btn_import_case, self.btn_build_network, self.btn_run_pf]: tlay.addWidget(b)
        tools.setLayout(tlay); left_layout.addWidget(tools)

        self.tabs = QTabWidget(); left_layout.addWidget(self.tabs); self.tables = {}
        export_g = QGroupBox("Exportar / Relatório"); eg=QVBoxLayout(export_g)
        self.btn_export_excel = QPushButton("Exportar Rede para .XLSX"); self.btn_generate_report = QPushButton("📈 Gerar Relatório HTML")
        eg.addWidget(self.btn_export_excel); eg.addWidget(self.btn_generate_report); export_g.setLayout(eg)
        left_layout.addWidget(export_g)
        left_layout.addStretch()
        splitter.addWidget(left)

        # right visual
        right = QGroupBox("Visualização e Resultados"); rlay = QVBoxLayout(right)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); rlay.addWidget(scroll)
        content = QWidget(); scroll.setWidget(content); c_l = QVBoxLayout(content)
        self.metrics_widget = MetricsWidget(); c_l.addWidget(self.metrics_widget)
        self.network_canvas = NetworkCanvas(self); self.network_canvas.setMinimumHeight(500); c_l.addWidget(self.network_canvas)
        self.results_canvas = ResultsPlotsCanvas(self); self.results_canvas.setMinimumHeight(300); c_l.addWidget(self.results_canvas)
        if HAS_PLOTLY and HAS_WEBENGINE:
            self.web = QWebEngineView(); self.web.setMinimumHeight(300); c_l.addWidget(self.web)
        splitter.addWidget(right); splitter.setSizes([600,1000])
        self.setCentralWidget(main)

    def add_table_tab(self, name: str, df: pd.DataFrame):
        key = name.lower().replace(" ", "_")
        if key not in self.tables:
            tw = QTableWidget(); self.tables[key] = tw
            self.tabs.addTab(tw, name.capitalize())
        table = self.tables[key]; df = df.copy()
        # convert object columns to string for display
        for c in df.columns:
            if df[c].dtype == object: df[c] = df[c].astype(str)
        table.setColumnCount(len(df.columns)); table.setRowCount(len(df.index))
        table.setHorizontalHeaderLabels(list(df.columns))
        for i, row in enumerate(df.itertuples(index=False)):
            for j, val in enumerate(row):
                table.setItem(i, j, QTableWidgetItem(str(val)))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

# =================
# ENTRYPOINT
# =================
def main():
    app = QApplication(sys.argv)
    controller = AppController()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
