# main.py
# SIN45 Manager - All-in-one (MVC single-file)
# Saves a requirements.txt automatically on first run.
#
# Recommended (conda):
#   conda create -n sin45 python=3.10 -y
#   conda activate sin45
#   conda install -c conda-forge pandapower pyside6 matplotlib openpyxl sqlalchemy pandas numpy -y
#   pip install plotly
#
# If you prefer, this script will write a requirements.txt file for you.

import os, sys, re, traceback, webbrowser, tempfile, base64, logging
from io import BytesIO
from typing import Dict
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D

# PySide6 GUI
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QFileDialog,
    QMessageBox, QHeaderView, QGroupBox, QSplitter, QLabel, QScrollArea,
    QComboBox, QProgressDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

# Optional imports (pandapower)
try:
    import pandapower as pp
    import pandapower.plotting as plot
    HAS_PANDAPOWER = True
except Exception:
    pp = None; plot = None; HAS_PANDAPOWER = False

# Database (SQLAlchemy)
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sin45")

# ================================
# Helper: write requirements.txt
# ================================
REQUIREMENTS = [
    "pandapower",
    "pyside6",
    "matplotlib",
    "openpyxl",
    "sqlalchemy",
    "pandas",
    "numpy",
    "plotly",
]
def write_requirements_txt(dest="requirements.txt"):
    try:
        if not os.path.exists(dest):
            with open(dest, "w", encoding="utf-8") as f:
                f.write("\n".join(REQUIREMENTS))
            logger.info("requirements.txt criado.")
    except Exception:
        logger.exception("Falha ao escrever requirements.txt")

# Write requirements on first import/run
write_requirements_txt()

# ---------------------------
# Parser: Anarede / Organon
# ---------------------------
class AnaredeParser:
    """
    Parser robusto para .PWF / .DAT (AnaRede / Organon Decks).
    Retorna dict de DataFrames: 'bus','line','gen','load','shunt','trafo' conforme encontrado.
    """
    @staticmethod
    def parse_pwf_to_dataframes(filepath: str) -> Dict[str, pd.DataFrame]:
        blocks = {'DBAR': [], 'DLIN': [], 'DGER': [], 'DCAR': [], 'DBSH': [], 'DTRA': []}
        cur = None
        with open(filepath, 'r', encoding='latin-1', errors='ignore') as f:
            for raw in f:
                ln = raw.rstrip('\n').rstrip('\r')
                if not ln.strip(): continue
                s = ln.strip()
                if s.startswith('(') or s.startswith('!'): continue
                if s.startswith('99999'):
                    cur = None; continue
                m = re.match(r'^(\w{4})', s)
                if m and m.group(1).upper() in blocks:
                    cur = m.group(1).upper(); continue
                if cur: blocks[cur].append(s)

        dfs = {}
        # DBAR -> barras
        if blocks['DBAR']:
            rows=[]
            for ln in blocks['DBAR']:
                try:
                    # many ANAREDE formats: try robust slices
                    num = int(ln[0:5])
                    name = ln[5:22].strip() if len(ln)>=22 else ln[5:12].strip()
                    vn = float(ln[28:34]) if len(ln)>=34 and ln[28:34].strip() else 230.0
                    rows.append({'bus_id':num, 'name':name, 'vn_kv':vn})
                except Exception:
                    toks = re.findall(r'[-+]?\d*\.\d+|\d+', ln)
                    if toks:
                        try:
                            num = int(toks[0]); vn = float(toks[-1]); rows.append({'bus_id':num,'name':'', 'vn_kv':vn})
                        except:
                            continue
            dfs['bus'] = pd.DataFrame(rows)

        # DLIN -> linhas
        if blocks['DLIN']:
            rows=[]
            for ln in blocks['DLIN']:
                try:
                    de = int(ln[0:5])
                    para = int(ln[6:11])
                    r_pu = float(ln[21:29])
                    x_pu = float(ln[30:38])
                    b_pu = float(ln[39:47])
                    rows.append({'from_bus':de, 'to_bus':para, 'R(pu)':r_pu, 'X(pu)':x_pu, 'B(pu)':b_pu})
                except Exception:
                    toks = re.findall(r'[-+]?\d*\.\d+|\d+', ln)
                    if len(toks) >= 5:
                        try:
                            de=int(toks[0]); para=int(toks[1]); r=float(toks[2]); x=float(toks[3]); b=float(toks[4])
                            rows.append({'from_bus':de, 'to_bus':para, 'R(pu)':r, 'X(pu)':x, 'B(pu)':b})
                        except:
                            continue
            dfs['line'] = pd.DataFrame(rows)

        # DGER -> geradores
        if blocks['DGER']:
            rows=[]
            for ln in blocks['DGER']:
                try:
                    bus = int(ln[0:5]); p = float(ln[21:29])
                    rows.append({'bus_id':bus, 'p_mw':p})
                except Exception:
                    toks = re.findall(r'[-+]?\d*\.\d+|\d+', ln)
                    if len(toks) >= 2:
                        try:
                            bus=int(toks[0]); p=float(toks[1]); rows.append({'bus_id':bus,'p_mw':p})
                        except: continue
            dfs['gen'] = pd.DataFrame(rows)

        # DCAR -> cargas
        if blocks['DCAR']:
            rows=[]
            for ln in blocks['DCAR']:
                try:
                    bus = int(ln[0:5]); p = float(ln[21:29])
                    q = float(ln[30:38]) if len(ln)>=38 else 0.0
                    rows.append({'bus_id':bus, 'p_mw':p, 'q_mvar':q})
                except Exception:
                    toks = re.findall(r'[-+]?\d*\.\d+|\d+', ln)
                    if len(toks) >= 2:
                        try:
                            bus=int(toks[0]); p=float(toks[1]); q=float(toks[2]) if len(toks)>2 else 0.0
                            rows.append({'bus_id':bus,'p_mw':p,'q_mvar':q})
                        except: continue
            dfs['load'] = pd.DataFrame(rows)

        # DBSH -> shunt
        if blocks['DBSH']:
            rows=[]
            for ln in blocks['DBSH']:
                try:
                    bus = int(ln[0:5]); b = float(ln[21:29])
                    rows.append({'bus_id':bus, 'b_pu':b})
                except Exception:
                    toks = re.findall(r'[-+]?\d*\.\d+|\d+', ln)
                    if len(toks)>=2:
                        try:
                            bus=int(toks[0]); b=float(toks[1]); rows.append({'bus_id':bus,'b_pu':b})
                        except: continue
            dfs['shunt'] = pd.DataFrame(rows)

        # DTRA -> trafos (if available) - naive parse
        if blocks['DTRA']:
            rows=[]
            for ln in blocks['DTRA']:
                toks = re.findall(r'[-+]?\d*\.\d+|\d+', ln)
                if len(toks) >= 4:
                    try:
                        hv = int(toks[0]); lv = int(toks[1]); sn = float(toks[2]); vk=float(toks[3])
                        rows.append({'hv_bus':hv,'lv_bus':lv,'sn_mva':sn,'vk_percent':vk})
                    except:
                        continue
            dfs['trafo'] = pd.DataFrame(rows)

        return dfs

# --------------------------
# Database manager (SQLite)
# --------------------------
class DB:
    def __init__(self, dbpath="sin45.sqlite"):
        self.engine = create_engine(f"sqlite:///{dbpath}", connect_args={"check_same_thread": False})

    def save_df(self, df: pd.DataFrame, name: str):
        try:
            df.to_sql(name, self.engine, if_exists='replace', index=False)
        except SQLAlchemyError as e:
            logger.exception("DB save error: %s", e)
            raise

    def load_df(self, name: str) -> pd.DataFrame:
        try:
            return pd.read_sql_table(name, self.engine)
        except Exception:
            return pd.DataFrame()

    def list_tables(self):
        with self.engine.connect() as c:
            res = c.execute("SELECT name FROM sqlite_master WHERE type='table';")
            return [r[0] for r in res.fetchall()]

# -------------------------
# Core Model: SmartGrid
# -------------------------
class SmartGrid:
    def __init__(self, sn_mva=100.0):
        self.sn_mva = sn_mva
        self.net = None
        self.dataframes = {}
        self.db = DB()
        self.pp = pp  # pandapower module or None

    def set_dataframes(self, dfs: Dict[str, pd.DataFrame]):
        self.dataframes = dfs.copy()
        for k, df in self.dataframes.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                try:
                    self.db.save_df(df, k)
                except Exception:
                    pass

    def load_pwf(self, filepath: str):
        dfs = AnaredeParser.parse_pwf_to_dataframes(filepath)
        for k, v in dfs.items():
            if k in self.dataframes:
                try:
                    self.dataframes[k] = pd.concat([self.dataframes[k], v], ignore_index=True)
                except:
                    self.dataframes[k] = v
            else:
                self.dataframes[k] = v
            if not self.dataframes[k].empty:
                self.db.save_df(self.dataframes[k], k)
        return dfs

    def load_excel(self, filepath: str):
        xls = pd.ExcelFile(filepath)
        for s in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=s)
            key = s.lower().replace(" ", "_")
            self.dataframes[key] = df
            if not df.empty:
                self.db.save_df(df, key)
        return self.dataframes

    def create_network_from_dataframes(self):
        if self.pp is None:
            raise RuntimeError("pandapower não está disponível no ambiente.")
        net = self.pp.create_empty_network(sn_mva=self.sn_mva)
        bus_map = {}
        df_bus = self.dataframes.get('bus')
        if df_bus is None or df_bus.empty:
            raise ValueError("Dados de 'bus' ausentes. Carregue o .PWF ou Excel com DBAR.")
        dfb = df_bus.copy()
        if 'bus_id' not in dfb.columns:
            candidates = [c for c in dfb.columns if 'barra' in c.lower() or 'bus' in c.lower()]
            if candidates:
                dfb.rename(columns={candidates[0]: 'bus_id'}, inplace=True)
        if 'name' not in dfb.columns:
            possible = [c for c in dfb.columns if 'nome' in c.lower()]
            if possible: dfb.rename(columns={possible[0]: 'name'}, inplace=True)
        dfb['vn_kv'] = pd.to_numeric(dfb.get('vn_kv', dfb.get('vn', 230.0)), errors='coerce').fillna(230.0)
        dfb['bus_id'] = pd.to_numeric(dfb['bus_id'], errors='coerce').astype(int)

        for _, r in dfb.iterrows():
            idx = self.pp.create_bus(net, name=str(r.get('name', r['bus_id'])), vn_kv=float(r['vn_kv']), in_service=True)
            bus_map[int(r['bus_id'])] = idx

        bus_vn_map = {int(r['bus_id']): float(r['vn_kv']) for _, r in dfb.iterrows()}

        # Generators
        df_gen = self.dataframes.get('gen')
        if isinstance(df_gen, pd.DataFrame) and not df_gen.empty:
            for _, g in df_gen.iterrows():
                try:
                    bid = int(g.get('bus_id', g.get('Barra', g.get('barra'))))
                    idx = bus_map.get(bid)
                    if idx is None: continue
                    p = float(g.get('p_mw', g.get('p', 0)))
                    self.pp.create_gen(net, bus=idx, p_mw=p, vm_pu=1.0)
                except Exception:
                    continue

        # Loads
        df_load = self.dataframes.get('load')
        if isinstance(df_load, pd.DataFrame) and not df_load.empty:
            for _, l in df_load.iterrows():
                try:
                    bid = int(l.get('bus_id', l.get('Barra', l.get('barra'))))
                    idx = bus_map.get(bid)
                    if idx is None: continue
                    p = float(l.get('p_mw', l.get('p', 0)))
                    q = float(l.get('q_mvar', l.get('q', 0)))
                    self.pp.create_load(net, bus=idx, p_mw=p, q_mvar=q)
                except Exception:
                    continue

        # Shunts
        df_shunt = self.dataframes.get('shunt')
        if isinstance(df_shunt, pd.DataFrame) and not df_shunt.empty:
            for _, s in df_shunt.iterrows():
                try:
                    bid = int(s.get('bus_id'))
                    idx = bus_map.get(bid)
                    if idx is None: continue
                    b_pu = float(s.get('b_pu', 0.0))
                    self.pp.create_shunt(net, bus=idx, p_mw=0, q_mvar=b_pu * net.sn_mva)
                except Exception:
                    continue

        # Lines / Transformers
        df_line = self.dataframes.get('line')
        if isinstance(df_line, pd.DataFrame) and not df_line.empty:
            for _, ln in df_line.iterrows():
                try:
                    fb_orig = int(ln.get('from_bus', ln.get('De', ln.get('de'))))
                    tb_orig = int(ln.get('to_bus', ln.get('Para', ln.get('para'))))
                    fb = bus_map.get(fb_orig); tb = bus_map.get(tb_orig)
                    if fb is None or tb is None: continue
                    vn_from = bus_vn_map.get(fb_orig, 230.0)
                    vn_to   = bus_vn_map.get(tb_orig, 230.0)
                    if abs(vn_from - vn_to) > 1.0:
                        vk_pct = float(ln.get('vk_percent', ln.get('vk', ln.get('X(pu)', 0.1) * 100)))
                        vkr_pct = float(ln.get('vkr_percent', ln.get('R(pu)', 0.0) * 100))
                        sn_mva = float(ln.get('sn_mva', 100.0))
                        if vn_from > vn_to:
                            hv_bus = fb; lv_bus = tb; vn_hv=vn_from; vn_lv=vn_to
                        else:
                            hv_bus = tb; lv_bus = fb; vn_hv=vn_to; vn_lv=vn_from
                        try:
                            self.pp.create_transformer_from_parameters(net, hv_bus=hv_bus, lv_bus=lv_bus,
                                                                       sn_mva=sn_mva, vn_hv_kv=vn_hv, vn_lv_kv=vn_lv,
                                                                       vkr_percent=vkr_pct, vk_percent=vk_pct,
                                                                       pfe_kw=0, i0_percent=0)
                        except Exception:
                            try:
                                self.pp.create_transformer(net, hv_bus=hv_bus, lv_bus=lv_bus, std_type='25 MVA 230/69 kV')
                            except:
                                continue
                    else:
                        r_pu = float(ln.get('R(pu)', ln.get('R_PU', 0.0)))
                        x_pu = float(ln.get('X(pu)', ln.get('X_PU', 0.0)))
                        b_pu = float(ln.get('B(pu)', ln.get('B_PU', 0.0)))
                        vn_kv = vn_from
                        z_base = (vn_kv ** 2) / self.sn_mva if vn_kv > 0 else 1.0
                        r_ohm = r_pu * z_base
                        x_ohm = x_pu * z_base
                        c_nf = (b_pu / (2 * np.pi * 60 * z_base) * 1e9) if z_base > 0 and b_pu != 0 else 0.0
                        try:
                            self.pp.create_line_from_parameters(net, from_bus=fb, to_bus=tb,
                                                                length_km=float(ln.get('length_km', 1.0)),
                                                                r_ohm_per_km=r_ohm, x_ohm_per_km=x_ohm,
                                                                c_nf_per_km=c_nf, max_i_ka=float(ln.get('max_i_ka', 1.0)))
                        except Exception:
                            try:
                                self.pp.create_line(net, from_bus=fb, to_bus=tb, length_km=1.0, std_type='149-AL1/24-ST1A 110.0')
                            except:
                                continue
                except Exception:
                    continue

        # ensure an ext_grid exists
        if net.ext_grid.empty and not net.bus.empty:
            self.pp.create_ext_grid(net, bus=net.bus.index[0], vm_pu=1.0)

        self.net = net
        return net

    def run_power_flow(self):
        if self.pp is None:
            raise RuntimeError("pandapower não instalado.")
        if self.net is None:
            raise ValueError("Rede não construída.")
        try:
            self.pp.runpp(self.net, algorithm='nr', max_iteration=50, enforce_q_lims=True, numba=True)
            return getattr(self.net, 'converged', False)
        except Exception:
            try:
                self.pp.diagnostic(self.net)
            except:
                pass
            raise

    def export_to_excel(self, filepath):
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for k, df in self.dataframes.items():
                if isinstance(df, pd.DataFrame) and not df.empty:
                    df.to_excel(writer, sheet_name=str(k)[:31], index=False)
            if self.net is not None:
                for attr in ['res_bus', 'res_line', 'res_trafo', 'res_gen', 'res_load', 'res_ext_grid']:
                    if hasattr(self.net, attr):
                        df = getattr(self.net, attr)
                        if df is not None and not df.empty:
                            df.to_excel(writer, sheet_name=str(attr)[:31], index=False)

# ---------------------------
# View: Matplotlib Canvases
# ---------------------------
class NetworkCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = plt.figure(figsize=(10,8), tight_layout=True)
        gs = gridspec.GridSpec(3,1, height_ratios=[20,1,1], hspace=0.1)
        self.ax_diag = self.fig.add_subplot(gs[0])
        self.ax_legend = self.fig.add_subplot(gs[1])
        self.ax_cbar = self.fig.add_subplot(gs[2])
        super().__init__(self.fig)
        self.setParent(parent)
        self.network_map = {
            'bus_size': 0.06, 'bus_zorder': 10,
            'bus_transfer_col': '#1f77b4', 'bus_gen_col': '#2ca02c', 'bus_load_col': '#ff7f0e',
            'line_lw': 0.7, 'trafo_col':'purple', 'ext_grid_col':'gold', 'shunt_col':'cyan'
        }

    def plot_network(self, net, plot_results=False):
        for ax in [self.ax_diag, self.ax_legend, self.ax_cbar]:
            ax.clear()
        self.ax_legend.axis('off'); self.ax_cbar.axis('off')
        self.ax_diag.set_xticks([]); self.ax_diag.set_yticks([])

        if net is None or (hasattr(net,'bus') and net.bus.empty):
            self.ax_diag.text(0.5,0.5, "Nenhuma rede para exibir", ha='center', va='center', color='gray')
            self.draw(); return

        try:
            if HAS_PANDAPOWER:
                if not hasattr(net, 'bus_geodata') or net.bus_geodata.empty:
                    plot.create_generic_coordinates(net, overwrite=True)

                bus_colors = []
                gen_buses = set(net.gen.bus) if not net.gen.empty else set()
                ext_buses = set(net.ext_grid.bus) if not net.ext_grid.empty else set()
                load_buses = set(net.load.bus) if not net.load.empty else set()
                for b in net.bus.index:
                    if b in gen_buses or b in ext_buses:
                        if b in load_buses:
                            bus_colors.append('#800080')  # gen+load
                        else:
                            bus_colors.append(self.network_map['bus_gen_col'])
                    elif b in load_buses:
                        bus_colors.append(self.network_map['bus_load_col'])
                    else:
                        bus_colors.append(self.network_map['bus_transfer_col'])

                bus_col = plot.create_bus_collection(net, buses=net.bus.index, size=self.network_map['bus_size'], color=bus_colors, zorder=self.network_map['bus_zorder'])
                collections = [bus_col]

                if not net.trafo.empty:
                    tr_col = plot.create_trafo_collection(net, linewidths=1.2, color=self.network_map['trafo_col'], zorder=5)
                    collections.append(tr_col)

                line_handles = []
                if not net.line.empty:
                    try:
                        vns = net.bus.loc[net.line.from_bus, 'vn_kv'].values
                    except Exception:
                        vns = np.zeros(len(net.line.index))
                    unique_vns = sorted(pd.unique(vns))
                    cmap = plt.get_cmap('viridis', max(2, len(unique_vns)))
                    for i, vn in enumerate(unique_vns):
                        lines_at_v = net.line.index[vns == vn]
                        if len(lines_at_v) == 0: continue
                        color = cmap(i)
                        lc = plot.create_line_collection(net, lines=lines_at_v, color=color, use_bus_geodata=True,
                                                        linewidths=self.network_map['line_lw'], zorder=1)
                        self.ax_diag.add_collection(lc)
                        line_handles.append(Line2D([0],[0], color=color, lw=2, label=f'{vn:.1f} kV'))

                if not net.load.empty:
                    collections.append(plot.create_load_collection(net, size=self.network_map['bus_size'], zorder=12))
                if not net.gen.empty:
                    collections.append(plot.create_gen_collection(net, size=self.network_map['bus_size'], zorder=12))
                if not net.ext_grid.empty:
                    collections.append(plot.create_ext_grid_collection(net, size=self.network_map['bus_size']*1.2, zorder=12, color=self.network_map['ext_grid_col']))

                plot.draw_collections(collections, ax=self.ax_diag)

                if plot_results and hasattr(net, 'res_line') and not net.res_line.empty and 'loading_percent' in net.res_line:
                    cmap_res = plt.get_cmap('coolwarm')
                    max_load = max(100, net.res_line.loading_percent.max() * 1.2)
                    norm = plt.Normalize(0, max_load)
                    lc_res = plot.create_line_collection(net, lines=net.res_line.index, cmap=cmap_res, norm=norm, use_bus_geodata=True, linewidths=2.2, zorder=2)
                    lc_res.set_array(net.res_line.loading_percent.values)
                    self.ax_diag.add_collection(lc_res)
                    sm = plt.cm.ScalarMappable(cmap=cmap_res, norm=norm); sm.set_array([])
                    cbar = self.fig.colorbar(sm, cax=self.ax_cbar, orientation='horizontal', label='Carregamento da Linha (%)')

                bus_handles = [
                    Line2D([0],[0], marker='o', color='w', label='Barra', markerfacecolor=self.network_map['bus_transfer_col'], markersize=6),
                    Line2D([0],[0], marker='o', color='w', label='Barra (Geração)', markerfacecolor=self.network_map['bus_gen_col'], markersize=6),
                    Line2D([0],[0], marker='o', color='w', label='Barra (Carga)', markerfacecolor=self.network_map['bus_load_col'], markersize=6)
                ]
                comp_handles = [Line2D([0],[0], marker='s', color=self.network_map['ext_grid_col'], label='Rede Externa', markersize=6, linestyle='None')]
                all_handles = bus_handles + line_handles + comp_handles
                if all_handles:
                    self.ax_legend.legend(handles=all_handles, loc='center', ncol=min(6, len(all_handles)), frameon=False)
                self.ax_diag.set_title("Diagrama Unifilar (coleções) - performance otimizadas")
                self.ax_diag.autoscale_view()
            else:
                self.ax_diag.text(0.5,0.5,"Pandapower não instalado - visualização limitada", ha='center')
        except Exception:
            logger.exception("Erro ao desenhar diagrama")
            self.ax_diag.text(0.5,0.5, f"Erro ao desenhar diagrama: {traceback.format_exc()}", ha='center', color='red')
        self.draw()

class ResultsCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig, (self.ax_v, self.ax_l) = plt.subplots(2,1, figsize=(8,6), tight_layout=True)
        super().__init__(self.fig)
        self.setParent(parent)

    def plot_voltage_and_loading(self, net):
        self.ax_v.clear(); self.ax_l.clear()
        try:
            if hasattr(net, 'res_bus') and not net.res_bus.empty:
                vm = net.res_bus.vm_pu
                top = pd.concat([vm.nlargest(20), vm.nsmallest(20)]).drop_duplicates().sort_values()
                colors = ['#d9534f' if v < 0.95 else '#f0ad4e' if v > 1.05 else '#5cb85c' for v in top]
                top.plot(kind='barh', ax=self.ax_v, color=colors)
                self.ax_v.set_title("Tensão nas Barras (p.u.) - top/low")
                self.ax_v.axvline(1.05, color='r', linestyle='--'); self.ax_v.axvline(0.95, color='r', linestyle='--')
            else:
                self.ax_v.text(0.5,0.5,"Sem res_bus", ha='center')

            if hasattr(net, 'res_line') and not net.res_line.empty:
                load = net.res_line.loading_percent.nlargest(30).sort_values()
                load.plot(kind='barh', ax=self.ax_l)
                self.ax_l.set_title("Top Linhas - Carregamento (%)")
            else:
                self.ax_l.text(0.5,0.5,"Sem res_line", ha='center')
        except Exception:
            logger.exception("Erro ao plotar resultados")
            self.ax_v.text(0.5,0.5, "Erro ao plotar resultados", ha='center', color='red')
        self.draw()

# -------------------
# Main Window / App
# -------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SIN45 Manager - Mestre Pedro Victor")
        self.resize(1600, 920)
        self.setStyleSheet("QWidget{background:#232323;color:#EEE;} QGroupBox{border:1px solid #444;} QPushButton{padding:8px}")

        # model
        self.model = SmartGrid(sn_mva=100.0)

        # layout
        central = QWidget(); self.setCentralWidget(central)
        h = QHBoxLayout(central)
        splitter = QSplitter(Qt.Horizontal); h.addWidget(splitter)

        # left controls + tabs
        left = QWidget(); vbox = QVBoxLayout(left)
        tools = QGroupBox("Ferramentas"); tl = QVBoxLayout(tools)
        self.btn_load_pwf = QPushButton("Carregar .PWF / .DAT"); self.btn_load_xlsx = QPushButton("Importar Excel (.xlsx)")
        self.btn_build = QPushButton("Construir Rede"); self.btn_build.setObjectName("build_button")
        self.btn_runpf = QPushButton("▶ Executar Fluxo de Potência"); self.btn_runpf.setObjectName("run_button")
        for b in [self.btn_load_pwf, self.btn_load_xlsx, self.btn_build, self.btn_runpf]:
            tl.addWidget(b)
        tools.setLayout(tl); vbox.addWidget(tools)

        # graphs selector
        selGb = QGroupBox("Visualização"); sL = QVBoxLayout(selGb)
        self.graph_select = QComboBox(); self.graph_select.addItems(["Diagrama (coleções)","Tensões (barras)","Carregamento (linhas)","Fluxo p (linhas)"])
        self.checkbox_overlay = QPushButton("Alternar overlay resultados"); self.checkbox_overlay.setCheckable(True)
        sL.addWidget(self.graph_select); sL.addWidget(self.checkbox_overlay)
        selGb.setLayout(sL); vbox.addWidget(selGb)

        # tabs for dataframes
        self.tabs = QTabWidget(); vbox.addWidget(self.tabs); self.tables = {}

        # export / persistence
        exportGb = QGroupBox("Exportar / DB"); el = QVBoxLayout(exportGb)
        self.btn_export_xlsx = QPushButton("Exportar .XLSX"); self.btn_report = QPushButton("Gerar Relatório HTML")
        self.btn_save_db = QPushButton("Salvar em SQLite"); self.btn_list_db = QPushButton("Listar DB Tables")
        el.addWidget(self.btn_export_xlsx); el.addWidget(self.btn_report); el.addWidget(self.btn_save_db); el.addWidget(self.btn_list_db)
        exportGb.setLayout(el); vbox.addWidget(exportGb)
        vbox.addStretch()
        splitter.addWidget(left)

        # right visualization panel
        right = QWidget(); rv = QVBoxLayout(right)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); rv.addWidget(scroll)
        content = QWidget(); scroll.setWidget(content); cv = QVBoxLayout(content)

        self.metrics = QGroupBox("Métricas"); ml = QHBoxLayout(self.metrics)
        self.lbl_gen = QLabel("Geração: N/A"); self.lbl_load = QLabel("Carga: N/A")
        ml.addWidget(self.lbl_gen); ml.addWidget(self.lbl_load); cv.addWidget(self.metrics)

        self.net_canvas = NetworkCanvas(self); self.net_canvas.setMinimumHeight(520); cv.addWidget(self.net_canvas)
        self.res_canvas = ResultsCanvas(self); self.res_canvas.setMinimumHeight(360); cv.addWidget(self.res_canvas)
        rv.addStretch(); splitter.addWidget(right)
        splitter.setSizes([620,980])

        # connect signals
        self.btn_load_pwf.clicked.connect(self.on_load_pwf)
        self.btn_load_xlsx.clicked.connect(self.on_load_xlsx)
        self.btn_build.clicked.connect(self.on_build_network)
        self.btn_runpf.clicked.connect(self.on_runpf)
        self.btn_export_xlsx.clicked.connect(self.on_export_xlsx)
        self.btn_report.clicked.connect(self.on_generate_report)
        self.btn_save_db.clicked.connect(self.on_save_db)
        self.btn_list_db.clicked.connect(self.on_list_db)
        self.graph_select.currentTextChanged.connect(self.on_graph_change)
        self.checkbox_overlay.clicked.connect(self.on_overlay_toggle)

        # initial empty view
        self.net_canvas.plot_network(None)
        self.res_canvas.plot_voltage_and_loading(type('empty',(),{'res_bus':pd.DataFrame(),'res_line':pd.DataFrame()}))
        self.overlay = False

    # ---------- UI helpers ----------
    def add_table_tab(self, name: str, df: pd.DataFrame):
        key = name.lower().replace(" ", "_")
        if key not in self.tables:
            table = QTableWidget(); self.tables[key] = table; self.tabs.addTab(table, name.capitalize())
        else:
            table = self.tables[key]
        df2 = df.copy()
        df2 = df2.fillna('').astype(str)
        table.setColumnCount(len(df2.columns)); table.setRowCount(len(df2.index))
        table.setHorizontalHeaderLabels(list(df2.columns))
        for i, row in enumerate(df2.itertuples(index=False)):
            for j, val in enumerate(row):
                table.setItem(i, j, QTableWidgetItem(str(val)))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def update_metrics_widget(self):
        net = self.model.net
        gen = 0.0; load = 0.0
        if net is not None:
            try:
                gen = net.res_gen.p_mw.sum() if hasattr(net,'res_gen') and not net.res_gen.empty else (net.res_ext_grid.p_mw.sum() if hasattr(net,'res_ext_grid') and not net.res_ext_grid.empty else 0.0)
                load = net.res_load.p_mw.sum() if hasattr(net,'res_load') and not net.res_load.empty else 0.0
            except Exception:
                pass
        self.lbl_gen.setText(f"Geração: {gen:.3f} MW"); self.lbl_load.setText(f"Carga: {load:.3f} MW")

    # ---------- Actions ----------
    def on_load_pwf(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Abrir PWF/DAT", "", "Decks (*.pwf *.dat);;All files (*)")
        if not fp: return
        try:
            dfs = self.model.load_pwf(fp)
            for k, df in dfs.items():
                if isinstance(df, pd.DataFrame) and not df.empty:
                    self.add_table_tab(k, df)
            QMessageBox.information(self, "OK", f"{os.path.basename(fp)} carregado ({len(dfs)} blocos).")
            self.net_canvas.plot_network(None)
        except Exception as e:
            QMessageBox.critical(self, "Erro parse PWF", str(e))

    def on_load_xlsx(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Abrir Excel", "", "Excel (*.xlsx *.xls)")
        if not fp: return
        try:
            dfs = self.model.load_excel(fp)
            for k, df in dfs.items():
                if isinstance(df, pd.DataFrame) and not df.empty:
                    self.add_table_tab(k, df)
            QMessageBox.information(self, "OK", f"{os.path.basename(fp)} carregado.")
        except Exception as e:
            QMessageBox.critical(self, "Erro abrir Excel", str(e))

    def on_build_network(self):
        ui_dfs = {}
        for i in range(self.tabs.count()):
            title = self.tabs.tabText(i)
            key = title.lower().replace(" ", "_")
            table = self.tables.get(key)
            if table:
                cols = [table.horizontalHeaderItem(c).text() for c in range(table.columnCount())]
                rows=[]
                for r in range(table.rowCount()):
                    row=[]
                    for c in range(table.columnCount()):
                        item = table.item(r,c)
                        row.append(item.text() if item else '')
                    rows.append(row)
                try:
                    df = pd.DataFrame(rows, columns=cols)
                    for col in df.columns:
                        df[col] = pd.to_numeric(df[col].replace('', np.nan), errors='ignore')
                    ui_dfs[key]=df
                except Exception:
                    ui_dfs[key]=pd.DataFrame(rows, columns=cols)
        if ui_dfs:
            self.model.set_dataframes(ui_dfs)
        pdialog = QProgressDialog("Construindo rede...", None, 0, 0, self)
        pdialog.setWindowModality(Qt.WindowModal); pdialog.setAutoClose(True); pdialog.show()
        QTimer.singleShot(50, pdialog.repaint)
        try:
            net = self.model.create_network_from_dataframes()
            pdialog.close()
            QMessageBox.information(self, "Sucesso", "Rede construída.")
            self.net_canvas.plot_network(net, plot_results=False)
            self.update_metrics_widget()
        except Exception as e:
            pdialog.close()
            logger.exception("Erro build network")
            QMessageBox.critical(self, "Erro construir rede", str(e))

    def on_runpf(self):
        if self.model.net is None:
            QMessageBox.warning(self, "Aviso", "Construa a rede primeiro.")
            return
        try:
            ok = self.model.run_power_flow()
            if ok:
                QMessageBox.information(self, "Sucesso", "Fluxo de potência convergiu.")
            else:
                QMessageBox.warning(self, "Fluxo", "Fluxo executado, mas NÃO convergiu.")
            net = self.model.net
            if hasattr(net,'res_bus') and not net.res_bus.empty: self.add_table_tab("res_bus", net.res_bus)
            if hasattr(net,'res_line') and not net.res_line.empty: self.add_table_tab("res_line", net.res_line)
            self.update_metrics_widget()
            self.render_chosen_graph()
        except Exception as e:
            logger.exception("Erro runpp")
            QMessageBox.critical(self, "Erro PF", str(e))

    def on_export_xlsx(self):
        fp, _ = QFileDialog.getSaveFileName(self, "Salvar Excel", "", "Excel (*.xlsx)")
        if not fp: return
        try:
            self.model.export_to_excel(fp)
            QMessageBox.information(self, "Exportado", f"Exportado para {fp}")
        except Exception as e:
            QMessageBox.critical(self, "Erro export", str(e))

    def on_generate_report(self):
        try:
            if self.model.net is None:
                QMessageBox.warning(self, "Aviso", "Execute o fluxo antes do relatório.")
                return
            tmp = tempfile.gettempdir()
            diag = os.path.join(tmp, "sin45_diag.png"); res = os.path.join(tmp, "sin45_res.png")
            self.net_canvas.fig.savefig(diag, bbox_inches='tight', facecolor=self.net_canvas.fig.get_facecolor())
            self.res_canvas.fig.savefig(res, bbox_inches='tight', facecolor=self.res_canvas.fig.get_facecolor())
            with open(diag,'rb') as f: d_b64 = base64.b64encode(f.read()).decode('utf-8')
            with open(res,'rb') as f: r_b64 = base64.b64encode(f.read()).decode('utf-8')
            bus_html = self.model.net.res_bus.to_html() if hasattr(self.model.net,'res_bus') else "<p>sem res_bus</p>"
            line_html = self.model.net.res_line.to_html() if hasattr(self.model.net,'res_line') else "<p>sem res_line</p>"
            html = f"<html><body><h1>Relatório SIN45</h1><h2>Diagrama</h2><img src='data:image/png;base64,{d_b64}' style='width:100%'/><h2>Resultados</h2><img src='data:image/png;base64,{r_b64}' style='width:100%'/><h3>res_bus</h3>{bus_html}<h3>res_line</h3>{line_html}</body></html>"
            out = os.path.join(tmp, "sin45_report.html")
            with open(out,'w', encoding='utf-8') as f: f.write(html)
            webbrowser.open(f"file://{out}")
            QMessageBox.information(self, "Relatório", f"Abrindo relatório: {out}")
        except Exception:
            logger.exception("Erro gerar relatório")
            QMessageBox.critical(self, "Erro relatório", traceback.format_exc())

    def on_save_db(self):
        try:
            for k, df in self.model.dataframes.items():
                if isinstance(df, pd.DataFrame) and not df.empty:
                    self.model.db.save_df(df, k)
            QMessageBox.information(self, "DB", "Dados salvos em SQLite.")
        except Exception as e:
            QMessageBox.critical(self, "Erro DB", str(e))

    def on_list_db(self):
        try:
            tables = self.model.db.list_tables()
            QMessageBox.information(self, "Tabelas DB", "\n".join(tables) if tables else "Nenhuma tabela.")
        except Exception as e:
            QMessageBox.critical(self, "Erro DB", str(e))

    def on_graph_change(self):
        self.render_chosen_graph()

    def on_overlay_toggle(self):
        self.overlay = self.checkbox_overlay.isChecked()
        self.render_chosen_graph()

    def render_chosen_graph(self):
        choice = self.graph_select.currentText()
        net = self.model.net
        try:
            if choice.startswith("Diagrama"):
                self.net_canvas.plot_network(net, plot_results=self.overlay)
            elif choice.startswith("Tensões"):
                if net is None: self.net_canvas.plot_network(None)
                self.res_canvas.plot_voltage_and_loading(net)
            elif choice.startswith("Carregamento"):
                if net is None: self.net_canvas.plot_network(None)
                self.res_canvas.plot_voltage_and_loading(net)
            elif choice.startswith("Fluxo p"):
                self.res_canvas.ax_v.clear(); self.res_canvas.ax_l.clear()
                if net is not None and hasattr(net,'res_line') and not net.res_line.empty:
                    p = net.res_line.p_from_mw
                    p_combined = pd.concat([p.nlargest(20), p.nsmallest(20)]).drop_duplicates().sort_values()
                    p_combined.plot(kind='barh', ax=self.res_canvas.ax_v)
                    self.res_canvas.ax_v.set_title("Fluxo Ativo (p_from_mw) - top/low")
                else:
                    self.res_canvas.ax_v.text(0.5,0.5,"Sem res_line", ha='center')
                self.res_canvas.draw()
            else:
                self.net_canvas.plot_network(net, plot_results=self.overlay)
        except Exception:
            logger.exception("Erro render graph")
            QMessageBox.critical(self, "Erro plot", traceback.format_exc())

# --------------
# Entrypoint
# --------------
def main():
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    return app.exec()

if __name__ == "__main__":
    main()
