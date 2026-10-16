# -*- coding: utf-8 -*-

# Pandapower desktop manager + Parser AnaRede (.PWF/.DAT) + PySide6 GUI + SQLite persistence
# Requisitos (recomendo conda):
#    conda create -n sin45 python=3.10 -y
#    conda activate sin45
#    conda install -c conda-forge pandapower pyside6 matplotlib openpyxl sqlalchemy pandas numpy -y
#    pip install plotly  # opcional
# OBS: se usar pip para pandapower pode ser mais complicado — prefira conda.

import os, sys, re, traceback, webbrowser, tempfile, base64, logging
from io import BytesIO
from typing import Dict, Optional
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
    QComboBox, QProgressDialog, QListWidget, QStackedWidget, QDialog,
    QFormLayout, QLineEdit, QTextEdit, QDialogButtonBox, QListWidgetItem
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QIcon
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

# Optional imports (pandapower)
try:
    import pandapower as pp
    import pandapower.plotting as plot
    HAS_PANDAPOWER = True
except Exception as e:
    pp = None; plot = None; HAS_PANDAPOWER = False

# Database
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sin45")

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
                    # fallback parse with regex numbers
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
        self._init_plans_table()

    def save_df(self, df: pd.DataFrame, name: str):
        try:
            df.to_sql(name, self.engine, if_exists='replace', index=False)
            logger.info(f"DataFrame '{name}' salvo no banco de dados.")
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
            res = c.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            return [r[0] for r in res.fetchall()]

    def _init_plans_table(self):
        """Cria e popula a tabela de planos se ela não existir."""
        if 'plans' in self.list_tables():
            return
        logger.info("Tabela 'plans' não encontrada, criando e populando com dados padrão.")
        default_plans = pd.DataFrame([
            {'plan_id': 1, 'name': 'Grátis', 'price': '0', 'description': 'Inteligência para tarefas do dia a dia', 'features': 'Acesso ao GPT-5\nCarregamento de arquivos limitado\nGeração de imagens mais lenta e limitada', 'popular': 0, 'button_text': 'Seu plano atual', 'style_class': 'free'},
            {'plan_id': 2, 'name': 'Plus', 'price': '20', 'description': 'Mais acesso à inteligência avançada', 'features': 'GPT-5 com reflexão avançada\nMais mensagens e carregamentos\nMais criação de imagens com maior velocidade', 'popular': 1, 'button_text': 'Assinar Plus', 'style_class': 'plus'},
            {'plan_id': 3, 'name': 'Pro', 'price': '200', 'description': 'Acesso completo ao melhor do ChatGPT', 'features': 'GPT-5 com reflexão pro\nMensagens e carregamentos ilimitados\nCriação de imagens ilimitada e mais rápida', 'popular': 0, 'button_text': 'Assinar Pro', 'style_class': 'pro'},
        ])
        self.save_df(default_plans, 'plans')


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
        self.load_all_from_db()

    def load_all_from_db(self):
        """Carrega todos os dataframes relevantes do banco de dados na inicialização."""
        table_names = self.db.list_tables()
        for name in table_names:
            self.dataframes[name] = self.db.load_df(name)
        logger.info(f"Modelo inicializado com tabelas do DB: {list(self.dataframes.keys())}")


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
        # merge existing
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

    def load_excel(self, filepath: str, sheet_name: str):
        """Carrega uma aba específica de um arquivo Excel e salva no DB."""
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        key = sheet_name.lower().replace(" ", "_")
        self.dataframes[key] = df
        if not df.empty:
            self.db.save_df(df, key)
        logger.info(f"Dados da aba '{sheet_name}' importados para a tabela '{key}'.")
        return {key: df}


    def create_network_from_dataframes(self):
        if self.pp is None:
            raise RuntimeError("pandapower não está disponível no ambiente.")
        net = self.pp.create_empty_network(sn_mva=self.sn_mva)
        bus_map = {}
        # bus dataframe requirement
        df_bus = self.dataframes.get('bus')
        if df_bus is None or df_bus.empty:
            raise ValueError("Dados de 'bus' ausentes. Carregue o .PWF ou Excel com DBAR.")
        dfb = df_bus.copy()
        # normalize columns
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

        # helper to get vn_kv by original bus id
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
                    # convert to q_mvar-like using SN
                    self.pp.create_shunt(net, bus=idx, p_mw=0, q_mvar=b_pu * net.sn_mva)
                except Exception:
                    continue

        # Lines / Transformers: we must detect based on vn difference and create accordingly
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
                    # if significant voltage difference => transformer
                    if abs(vn_from - vn_to) > 1.0:
                        # convert R/X (if in pu) to percent for transformer vk/vkr heuristics
                        vk_pct = float(ln.get('vk_percent', ln.get('vk', ln.get('X(pu)', 0.1) * 100)))
                        vkr_pct = float(ln.get('vkr_percent', ln.get('R(pu)', 0.0) * 100))
                        sn_mva = float(ln.get('sn_mva', 100.0))
                        # pick hv/lv bus indices
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
                            # fallback create standard trafo
                            try:
                                self.pp.create_transformer(net, hv_bus=hv_bus, lv_bus=lv_bus, std_type='25 MVA 230/69 kV')
                            except:
                                continue
                    else:
                        # It's a line: if R/X/B are provided in pu convert to ohm
                        r_pu = float(ln.get('R(pu)', ln.get('R_PU', 0.0)))
                        x_pu = float(ln.get('X(pu)', ln.get('X_PU', 0.0)))
                        b_pu = float(ln.get('B(pu)', ln.get('B_PU', 0.0)))
                        vn_kv = vn_from
                        z_base = (vn_kv ** 2) / self.sn_mva if vn_kv > 0 else 1.0
                        r_ohm = r_pu * z_base
                        x_ohm = x_pu * z_base
                        c_nf = (b_pu / (2 * np.pi * 60 * z_base) * 1e9) if z_base > 0 and b_pu != 0 else 0.0
                        # create line
                        try:
                            self.pp.create_line_from_parameters(net, from_bus=fb, to_bus=tb,
                                                                 length_km=float(ln.get('length_km', 1.0)),
                                                                 r_ohm_per_km=r_ohm, x_ohm_per_km=x_ohm,
                                                                 c_nf_per_km=c_nf, max_i_ka=float(ln.get('max_i_ka', 1.0)))
                        except Exception:
                            # fallback simplified line
                            try:
                                self.pp.create_line(net, from_bus=fb, to_bus=tb, length_km=1.0, std_type='149-AL1/24-ST1A 110.0')
                            except:
                                continue
                except Exception:
                    continue

        # ensure an ext_grid exists
        if net.ext_grid.empty and not net.bus.empty:
            self.pp.create_ext_grid(net, bus=net.bus.index[0], vm_pu=1.0)

        # save net and return
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
            # try to get diagnostic
            try:
                self.pp.diagnostic(self.net)
            except:
                pass
            raise

    def export_to_excel(self, filepath):
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Salva todas as tabelas do modelo, incluindo 'plans'
            for k, df in self.dataframes.items():
                if isinstance(df, pd.DataFrame) and not df.empty:
                    df.to_excel(writer, sheet_name=str(k)[:31], index=False)
            
            # Salva os resultados do pandapower se existirem
            if self.net is not None:
                for attr in ['res_bus', 'res_line', 'res_trafo', 'res_gen', 'res_load', 'res_ext_grid']:
                    if hasattr(self.net, attr):
                        df = getattr(self.net, attr)
                        if df is not None and not df.empty:
                            df.to_excel(writer, sheet_name=str(attr)[:31], index=True) # Index=True for results

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
            # make coords if missing
            if HAS_PANDAPOWER:
                if not hasattr(net, 'bus_geodata') or net.bus_geodata.empty:
                    plot.create_generic_coordinates(net, overwrite=True)
                # build collections
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
                # create bus collection
                bus_col = plot.create_bus_collection(net, buses=net.bus.index, size=self.network_map['bus_size'], color=bus_colors, zorder=self.network_map['bus_zorder'])
                collections = [bus_col]
                # trafos
                if not net.trafo.empty:
                    tr_col = plot.create_trafo_collection(net, linewidths=1.2, color=self.network_map['trafo_col'], zorder=5)
                    collections.append(tr_col)
                # lines: create line collections grouped by vn to keep legend small
                line_handles = []
                if not net.line.empty:
                    # get from_bus vn
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
                # other markers
                if not net.load.empty:
                    collections.append(plot.create_load_collection(net, size=self.network_map['bus_size'], zorder=12))
                if not net.gen.empty:
                    collections.append(plot.create_gen_collection(net, size=self.network_map['bus_size'], zorder=12))
                if not net.ext_grid.empty:
                    collections.append(plot.create_ext_grid_collection(net, size=self.network_map['bus_size']*1.2, zorder=12, color=self.network_map['ext_grid_col']))
                # draw main collections
                plot.draw_collections(collections, ax=self.ax_diag)
                # overlay results: loading_percent on lines
                if plot_results and hasattr(net, 'res_line') and not net.res_line.empty and 'loading_percent' in net.res_line:
                    cmap_res = plt.get_cmap('coolwarm')
                    max_load = max(100, net.res_line.loading_percent.max() * 1.2)
                    norm = plt.Normalize(0, max_load)
                    lc_res = plot.create_line_collection(net, lines=net.res_line.index, cmap=cmap_res, norm=norm, use_bus_geodata=True, linewidths=2.2, zorder=2)
                    lc_res.set_array(net.res_line.loading_percent.values)
                    self.ax_diag.add_collection(lc_res)
                    sm = plt.cm.ScalarMappable(cmap=cmap_res, norm=norm); sm.set_array([])
                    cbar = self.fig.colorbar(sm, cax=self.ax_cbar, orientation='horizontal', label='Carregamento da Linha (%)')
                # legend
                bus_handles = [
                    Line2D([0],[0], marker='o', color='w', label='Barra', markerfacecolor=self.network_map['bus_transfer_col'], markersize=6),
                    Line2D([0],[0], marker='o', color='w', label='Barra (Geração)', markerfacecolor=self.network_map['bus_gen_col'], markersize=6),
                    Line2D([0],[0], marker='o', color='w', label='Barra (Carga)', markerfacecolor=self.network_map['bus_load_col'], markersize=6)
                ]
                comp_handles = [Line2D([0],[0], marker='s', color=self.network_map['ext_grid_col'], label='Rede Externa', markersize=6, linestyle='None')]
                all_handles = bus_handles + line_handles + comp_handles
                if all_handles:
                    self.ax_legend.legend(handles=all_handles, loc='center', ncol=min(6, len(all_handles)), frameon=False)
                self.ax_diag.set_title("Diagrama Unifilar (coleções) - zoom e performance otimizadas")
                self.ax_diag.autoscale_view()
            else:
                # fallback: simple node plot from dataframes (no pandapower)
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


# ---------------------------
# View: Páginas da Aplicação
# ---------------------------

class PandapowerPage(QWidget):
    """Encapsula toda a UI original do gerenciador de rede."""
    def __init__(self, model: SmartGrid, parent=None):
        super().__init__(parent)
        self.model = model
        self.tables = {}
        self.overlay = False

        # Layout principal da página
        h = QHBoxLayout(self)
        self.splitter = QSplitter(Qt.Horizontal); h.addWidget(self.splitter)

        # Painel da Esquerda (Controles e Tabelas)
        left = QWidget(); vbox = QVBoxLayout(left)
        tools = QGroupBox("Ferramentas de Rede"); tl = QVBoxLayout(tools)
        self.btn_load_pwf = QPushButton("Carregar .PWF / .DAT"); self.btn_load_xlsx = QPushButton("Importar Rede (.xlsx)")
        self.btn_build = QPushButton("Construir Rede"); self.btn_build.setObjectName("build_button")
        self.btn_runpf = QPushButton("▶ Executar Fluxo de Potência"); self.btn_runpf.setObjectName("run_button")
        for b in [self.btn_load_pwf, self.btn_load_xlsx, self.btn_build, self.btn_runpf]:
            tl.addWidget(b)
        tools.setLayout(tl); vbox.addWidget(tools)

        selGb = QGroupBox("Visualização de Gráficos"); sL = QVBoxLayout(selGb)
        self.graph_select = QComboBox(); self.graph_select.addItems(["Diagrama (coleções)","Tensões (barras)","Carregamento (linhas)","Fluxo p (linhas)"])
        self.checkbox_overlay = QPushButton("Alternar overlay resultados"); self.checkbox_overlay.setCheckable(True)
        sL.addWidget(self.graph_select); sL.addWidget(self.checkbox_overlay)
        selGb.setLayout(sL); vbox.addWidget(selGb)

        self.tabs = QTabWidget(); vbox.addWidget(self.tabs, 1)

        exportGb = QGroupBox("Exportar / DB"); el = QVBoxLayout(exportGb)
        self.btn_export_xlsx = QPushButton("Exportar Tudo (.XLSX)"); self.btn_report = QPushButton("Gerar Relatório HTML")
        self.btn_save_db = QPushButton("Salvar em SQLite"); self.btn_list_db = QPushButton("Listar Tabelas DB")
        el.addWidget(self.btn_export_xlsx); el.addWidget(self.btn_report); el.addWidget(self.btn_save_db); el.addWidget(self.btn_list_db)
        exportGb.setLayout(el); vbox.addWidget(exportGb)
        
        self.splitter.addWidget(left)

        # Painel da Direita (Visualização)
        right = QWidget(); rv = QVBoxLayout(right)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); rv.addWidget(scroll)
        content = QWidget(); scroll.setWidget(content); cv = QVBoxLayout(content)

        self.metrics = QGroupBox("Métricas"); ml = QHBoxLayout(self.metrics)
        self.lbl_gen = QLabel("Geração: N/A"); self.lbl_load = QLabel("Carga: N/A")
        ml.addWidget(self.lbl_gen); ml.addWidget(self.lbl_load); cv.addWidget(self.metrics)

        self.net_canvas = NetworkCanvas(self); self.net_canvas.setMinimumHeight(520); cv.addWidget(self.net_canvas)
        self.res_canvas = ResultsCanvas(self); self.res_canvas.setMinimumHeight(360); cv.addWidget(self.res_canvas)
        rv.addStretch(); self.splitter.addWidget(right)
        self.splitter.setSizes([620,980])

        # Conectar Sinais
        self.btn_load_pwf.clicked.connect(self.on_load_pwf)
        self.btn_load_xlsx.clicked.connect(self.on_load_xlsx)
        self.btn_build.clicked.connect(self.on_build_network)
        self.btn_runpf.clicked.connect(self.on_runpf)
        self.btn_export_xlsx.clicked.connect(self.on_export_xlsx)
        self.btn_report.clicked.connect(self.on_generate_report)
        self.btn_save_db.clicked.connect(self.on_save_db)
        self.btn_list_db.clicked.connect(self.on_list_db)
        self.graph_select.currentTextChanged.connect(self.render_chosen_graph)
        self.checkbox_overlay.clicked.connect(self.on_overlay_toggle)

        # Visão Inicial
        self.refresh_display()

    def refresh_display(self):
        """Atualiza todas as visualizações com os dados do modelo."""
        self.tabs.clear()
        self.tables.clear()
        network_dfs = ['bus', 'line', 'gen', 'load', 'shunt', 'trafo', 'res_bus', 'res_line']
        for name, df in self.model.dataframes.items():
            if name in network_dfs and not df.empty:
                self.add_table_tab(name, df)
        self.render_chosen_graph()
        self.update_metrics_widget()


    def add_table_tab(self, name: str, df: pd.DataFrame):
        key = name.lower().replace(" ", "_")
        if key not in self.tables:
            table = QTableWidget(); self.tables[key] = table; self.tabs.addTab(table, name.capitalize())
        else:
            table = self.tables[key]
        df2 = df.copy().fillna('').astype(str)
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
            except Exception: pass
        self.lbl_gen.setText(f"Geração: {gen:.3f} MW"); self.lbl_load.setText(f"Carga: {load:.3f} MW")

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
            # Para redes, importamos todas as abas.
            xls = pd.ExcelFile(fp)
            loaded_dfs = {}
            for s in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=s)
                key = s.lower().replace(" ", "_")
                self.model.dataframes[key] = df
                if not df.empty:
                    self.model.db.save_df(df, key)
                loaded_dfs[key] = df
            
            for k, df in loaded_dfs.items():
                self.add_table_tab(k, df)
            QMessageBox.information(self, "OK", f"{os.path.basename(fp)} carregado.")
        except Exception as e:
            QMessageBox.critical(self, "Erro abrir Excel", str(e))
    
    def on_build_network(self):
        ui_dfs = {}
        for i in range(self.tabs.count()):
            key = self.tabs.tabText(i).lower()
            table = self.tables.get(key)
            if table:
                cols = [table.horizontalHeaderItem(c).text() for c in range(table.columnCount())]
                rows = [[(table.item(r,c).text() if table.item(r,c) else '') for c in range(table.columnCount())] for r in range(table.rowCount())]
                df = pd.DataFrame(rows, columns=cols)
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col].replace('', np.nan), errors='ignore')
                ui_dfs[key]=df
        if ui_dfs:
            self.model.set_dataframes(ui_dfs)
        
        pdialog = QProgressDialog("Construindo rede...", None, 0, 0, self); pdialog.setWindowModality(Qt.WindowModal); pdialog.show()
        QTimer.singleShot(50, pdialog.repaint)
        try:
            net = self.model.create_network_from_dataframes()
            pdialog.close()
            QMessageBox.information(self, "Sucesso", "Rede construída.")
            self.net_canvas.plot_network(net, plot_results=False)
            self.update_metrics_widget()
        except Exception as e:
            pdialog.close(); logger.exception("Erro build network")
            QMessageBox.critical(self, "Erro construir rede", str(e))

    def on_runpf(self):
        if self.model.net is None:
            return QMessageBox.warning(self, "Aviso", "Construa a rede primeiro.")
        try:
            ok = self.model.run_power_flow()
            QMessageBox.information(self, "Sucesso" if ok else "Aviso", f"Fluxo de potência {'convergiu' if ok else 'NÃO convergiu'}.")
            net = self.model.net
            if hasattr(net,'res_bus') and not net.res_bus.empty: self.add_table_tab("res_bus", net.res_bus)
            if hasattr(net,'res_line') and not net.res_line.empty: self.add_table_tab("res_line", net.res_line)
            self.update_metrics_widget()
            self.render_chosen_graph()
        except Exception as e:
            logger.exception("Erro runpp")
            QMessageBox.critical(self, "Erro PF", str(e))

    def on_export_xlsx(self):
        fp, _ = QFileDialog.getSaveFileName(self, "Salvar Tudo em Excel", "sin45_export.xlsx", "Excel (*.xlsx)")
        if not fp: return
        try:
            self.model.export_to_excel(fp)
            QMessageBox.information(self, "Exportado", f"Todos os dados exportados para {fp}")
        except Exception as e:
            QMessageBox.critical(self, "Erro export", str(e))

    def on_generate_report(self):
        if self.model.net is None: return QMessageBox.warning(self, "Aviso", "Execute o fluxo antes.")
        try:
            tmp = tempfile.gettempdir()
            diag = os.path.join(tmp, "sin45_diag.png"); res = os.path.join(tmp, "sin45_res.png")
            self.net_canvas.fig.savefig(diag, bbox_inches='tight')
            self.res_canvas.fig.savefig(res, bbox_inches='tight')
            with open(diag,'rb') as f: d_b64 = base64.b64encode(f.read()).decode('utf-8')
            with open(res,'rb') as f: r_b64 = base64.b64encode(f.read()).decode('utf-8')
            bus_html = self.model.net.res_bus.to_html() if hasattr(self.model.net,'res_bus') else ""
            line_html = self.model.net.res_line.to_html() if hasattr(self.model.net,'res_line') else ""
            html = f"<html><body><h1>Relatório SIN45</h1><h2>Diagrama</h2><img src='data:image/png;base64,{d_b64}' style='width:100%'/><h2>Resultados</h2><img src='data:image/png;base64,{r_b64}' style='width:100%'/><h3>res_bus</h3>{bus_html}<h3>res_line</h3>{line_html}</body></html>"
            out = os.path.join(tmp, "sin45_report.html")
            with open(out,'w', encoding='utf-8') as f: f.write(html)
            webbrowser.open(f"file://{out}")
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
    
    def on_overlay_toggle(self):
        self.overlay = self.checkbox_overlay.isChecked()
        self.render_chosen_graph()

    def render_chosen_graph(self):
        choice = self.graph_select.currentText()
        net = self.model.net
        try:
            self.net_canvas.setVisible(choice.startswith("Diagrama"))
            self.res_canvas.setVisible(not choice.startswith("Diagrama"))

            if choice.startswith("Diagrama"):
                self.net_canvas.plot_network(net, plot_results=self.overlay)
            elif choice.startswith("Tensões"):
                self.res_canvas.plot_voltage_and_loading(net)
            elif choice.startswith("Carregamento"):
                self.res_canvas.plot_voltage_and_loading(net) # Reuses same canvas
            elif choice.startswith("Fluxo p"):
                self.res_canvas.ax_v.clear(); self.res_canvas.ax_l.clear()
                if net and hasattr(net,'res_line') and not net.res_line.empty:
                    p = net.res_line.p_from_mw
                    p_combined = pd.concat([p.nlargest(20), p.nsmallest(20)]).drop_duplicates().sort_values()
                    p_combined.plot(kind='barh', ax=self.res_canvas.ax_v)
                    self.res_canvas.ax_v.set_title("Fluxo Ativo (p_from_mw) - top/low")
                else:
                    self.res_canvas.ax_v.text(0.5,0.5,"Sem res_line", ha='center')
                self.res_canvas.draw()
        except Exception:
            logger.exception("Erro render graph")
            QMessageBox.critical(self, "Erro plot", traceback.format_exc())


class PlanCard(QGroupBox):
    """Widget para exibir um único plano de assinatura."""
    edit_requested = Signal(int)
    delete_requested = Signal(int)
    
    def __init__(self, plan_data: pd.Series, parent=None):
        super().__init__(parent)
        self.plan_id = plan_data['plan_id']
        
        self.setObjectName("PlanCard")
        layout = QVBoxLayout(self)
        
        if plan_data.get('popular', 0):
            header_layout = QHBoxLayout()
            name_label = QLabel(plan_data['name']); name_label.setObjectName("PlanTitle")
            popular_label = QLabel("POPULAR"); popular_label.setObjectName("PopularPill")
            header_layout.addWidget(name_label)
            header_layout.addStretch()
            header_layout.addWidget(popular_label)
            layout.addLayout(header_layout)
        else:
            name_label = QLabel(plan_data['name']); name_label.setObjectName("PlanTitle")
            layout.addWidget(name_label)
        
        price_text = f"<span style='font-size: 28px; font-weight: bold;'>${plan_data['price']}</span> USD / mês"
        price_label = QLabel(price_text)
        layout.addWidget(price_label)

        desc_label = QLabel(plan_data['description']); desc_label.setObjectName("PlanDescription")
        layout.addWidget(desc_label)

        self.subscribe_button = QPushButton(plan_data['button_text'])
        self.subscribe_button.setObjectName(plan_data['style_class']) # free, plus, pro
        layout.addWidget(self.subscribe_button)
        
        line = QFrame(); line.setFrameShape(QFrame.HLine); line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        features_label = QLabel(plan_data['features'].replace('\n', '<br>'))
        features_label.setWordWrap(True)
        layout.addWidget(features_label)
        
        layout.addStretch()

        # Botões de CRUD
        crud_layout = QHBoxLayout()
        edit_button = QPushButton("Editar"); edit_button.clicked.connect(lambda: self.edit_requested.emit(self.plan_id))
        delete_button = QPushButton("Excluir"); delete_button.clicked.connect(lambda: self.delete_requested.emit(self.plan_id))
        crud_layout.addWidget(edit_button)
        crud_layout.addWidget(delete_button)
        layout.addLayout(crud_layout)

class PlanEditDialog(QDialog):
    """Diálogo para adicionar ou editar um plano."""
    def __init__(self, plan_data: Optional[pd.Series] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Plano" if plan_data is not None else "Adicionar Plano")
        
        self.layout = QFormLayout(self)
        
        self.name_edit = QLineEdit(plan_data['name'] if plan_data is not None else "")
        self.price_edit = QLineEdit(str(plan_data['price']) if plan_data is not None else "0")
        self.desc_edit = QLineEdit(plan_data['description'] if plan_data is not None else "")
        self.features_edit = QTextEdit(plan_data['features'] if plan_data is not None else "")
        self.button_text_edit = QLineEdit(plan_data['button_text'] if plan_data is not None else "")
        self.style_class_edit = QLineEdit(plan_data['style_class'] if plan_data is not None else "")
        self.popular_edit = QComboBox(); self.popular_edit.addItems(["Não", "Sim"])
        if plan_data is not None and plan_data['popular']: self.popular_edit.setCurrentIndex(1)

        self.layout.addRow("Nome:", self.name_edit)
        self.layout.addRow("Preço (USD):", self.price_edit)
        self.layout.addRow("Descrição:", self.desc_edit)
        self.layout.addRow("Recursos (um por linha):", self.features_edit)
        self.layout.addRow("Texto do Botão:", self.button_text_edit)
        self.layout.addRow("Classe de Estilo:", self.style_class_edit)
        self.layout.addRow("Popular:", self.popular_edit)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def get_data(self) -> dict:
        return {
            'name': self.name_edit.text(),
            'price': self.price_edit.text(),
            'description': self.desc_edit.text(),
            'features': self.features_edit.toPlainText(),
            'button_text': self.button_text_edit.text(),
            'style_class': self.style_class_edit.text(),
            'popular': 1 if self.popular_edit.currentIndex() == 1 else 0
        }

class PlansPage(QWidget):
    """Página para exibir e gerenciar planos de assinatura."""
    def __init__(self, model: SmartGrid, parent=None):
        super().__init__(parent)
        self.model = model
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        
        # Header
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)
        title = QLabel("Faça upgrade do seu plano"); title.setObjectName("PageTitle")
        header_layout.addWidget(title)
        main_layout.addLayout(header_layout)
        
        # Controles
        controls_layout = QHBoxLayout()
        self.add_plan_button = QPushButton("Adicionar Novo Plano")
        self.import_plans_button = QPushButton("Importar Planos (.xlsx)")
        controls_layout.addWidget(self.add_plan_button)
        controls_layout.addWidget(self.import_plans_button)
        main_layout.addLayout(controls_layout)

        # Container dos Cards
        self.cards_container = QWidget()
        self.cards_layout = QHBoxLayout(self.cards_container)
        self.cards_layout.setAlignment(Qt.AlignTop)
        main_layout.addWidget(self.cards_container)
        
        # Conectar Sinais
        self.add_plan_button.clicked.connect(self.on_add_plan)
        self.import_plans_button.clicked.connect(self.on_import_plans)

        self.refresh_plans()

    def refresh_plans(self):
        """Limpa e recria os cards de planos a partir do modelo."""
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        plans_df = self.model.dataframes.get('plans')
        if plans_df is None or plans_df.empty:
            return

        for _, plan_row in plans_df.iterrows():
            card = PlanCard(plan_row)
            card.edit_requested.connect(self.on_edit_plan)
            card.delete_requested.connect(self.on_delete_plan)
            self.cards_layout.addWidget(card)

    def on_add_plan(self):
        dialog = PlanEditDialog(parent=self)
        if dialog.exec():
            new_data = dialog.get_data()
            plans_df = self.model.dataframes.get('plans', pd.DataFrame())
            new_id = (plans_df['plan_id'].max() + 1) if not plans_df.empty else 1
            new_data['plan_id'] = new_id
            
            new_row = pd.DataFrame([new_data])
            self.model.dataframes['plans'] = pd.concat([plans_df, new_row], ignore_index=True)
            self.model.db.save_df(self.model.dataframes['plans'], 'plans')
            self.refresh_plans()
            QMessageBox.information(self, "Sucesso", "Novo plano adicionado.")
            
    def on_edit_plan(self, plan_id: int):
        plans_df = self.model.dataframes['plans']
        plan_data = plans_df[plans_df['plan_id'] == plan_id].iloc[0]
        
        dialog = PlanEditDialog(plan_data, self)
        if dialog.exec():
            updated_data = dialog.get_data()
            for key, value in updated_data.items():
                self.model.dataframes['plans'].loc[plans_df['plan_id'] == plan_id, key] = value
            self.model.db.save_df(self.model.dataframes['plans'], 'plans')
            self.refresh_plans()
            QMessageBox.information(self, "Sucesso", f"Plano {plan_id} atualizado.")

    def on_delete_plan(self, plan_id: int):
        reply = QMessageBox.question(self, "Confirmar Exclusão", f"Tem certeza que deseja excluir o plano ID {plan_id}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            plans_df = self.model.dataframes['plans']
            self.model.dataframes['plans'] = plans_df[plans_df['plan_id'] != plan_id]
            self.model.db.save_df(self.model.dataframes['plans'], 'plans')
            self.refresh_plans()
            QMessageBox.information(self, "Sucesso", f"Plano {plan_id} excluído.")

    def on_import_plans(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Importar Planos do Excel", "", "Excel (*.xlsx *.xls)")
        if not fp: return
        try:
            self.model.load_excel(fp, sheet_name='plans')
            self.refresh_plans()
            QMessageBox.information(self, "Sucesso", "Planos importados do Excel e salvos no banco de dados.")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Importar", f"Não foi possível importar a aba 'plans':\n{e}")

# -------------------
# Main Window / App
# -------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SIN45 Manager - Mestre Pedro Victor")
        self.resize(1600, 920)
        self.setStyleSheet("""
            QWidget { background-color: #2E2E2E; color: #F0F0F0; }
            QMainWindow { background-color: #232323; }
            QGroupBox { border: 1px solid #444; margin-top: 1em; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QPushButton { padding: 8px; background-color: #4A4A4A; border: 1px solid #666; border-radius: 4px; }
            QPushButton:hover { background-color: #5A5A5A; }
            QPushButton#run_button { background-color: #28a745; }
            QPushButton#build_button { background-color: #007bff; }
            QListWidget { border: none; background-color: #232323; }
            QListWidget::item { padding: 12px; }
            QListWidget::item:selected { background-color: #007bff; }
            QTabWidget::pane { border: 1px solid #444; }
            QTableWidget { gridline-color: #444; }

            /* Estilos da Página de Planos */
            #PageTitle { font-size: 24px; font-weight: bold; padding: 10px; }
            #PlanCard { border: 1px solid #555; border-radius: 8px; }
            #PlanTitle { font-size: 18px; font-weight: bold; }
            #PopularPill { background-color: #6c757d; color: white; padding: 2px 8px; border-radius: 8px; }
            #PlanDescription { color: #AAAAAA; }
            QPushButton#free { background-color: #FFFFFF; color: #2E2E2E; font-weight: bold; }
            QPushButton#plus { background-color: #6f42c1; color: white; font-weight: bold; }
            QPushButton#pro { background-color: #343a40; color: white; font-weight: bold; }
        """)

        # model
        self.model = SmartGrid(sn_mva=100.0)

        # layout
        central = QWidget(); self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        # Navegação
        self.nav = QListWidget(); self.nav.setFixedWidth(200)
        self.nav.addItem("Gerenciador de Rede")
        self.nav.addItem("Planos de Assinatura")
        main_layout.addWidget(self.nav)

        # Páginas
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        self.pandapower_page = PandapowerPage(self.model)
        self.plans_page = PlansPage(self.model)

        self.stacked_widget.addWidget(self.pandapower_page)
        self.stacked_widget.addWidget(self.plans_page)

        # Conectar Sinais
        self.nav.currentRowChanged.connect(self.stacked_widget.setCurrentIndex)
        self.nav.setCurrentRow(0)

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

