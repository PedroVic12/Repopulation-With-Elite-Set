import pandas as pd
import numpy as np
import os, traceback

# SmartGrid: wrapper OOP para carregar .PWF/.DAT/.XLSX, criar rede pandapower e exportar resultados
class SmartGrid:
    def __init__(self, sn_mva=100.0):
        self.sn_mva = sn_mva
        self.net = None
        self.dataframes = {}
        # lazy import of pandapower
        try:
            import pandapower as pp
            self.pp = pp
        except Exception as e:
            self.pp = None
            self._pp_import_error = e

    def ensure_pandapower(self):
        if self.pp is None:
            raise ImportError(f"pandapower não encontrado: {self._pp_import_error}")

    def load_pwf(self, filepath, parser):
        """parser deve ser a classe AnaredeParser com método parse_pwf_to_dataframes"""
        dfs = parser.parse_pwf_to_dataframes(filepath)
        # merge com dataframes existentes respeitando chaves
        for k,v in dfs.items():
            if k in self.dataframes and isinstance(self.dataframes[k], pd.DataFrame):
                self.dataframes[k] = pd.concat([self.dataframes[k], v], ignore_index=True)
            else:
                self.dataframes[k] = v
        return dfs

    def load_excel(self, filepath):
        xls = pd.ExcelFile(filepath)
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            key = sheet.lower().replace(" ", "_")
            self.dataframes[key] = df
        return self.dataframes

    def create_network(self):
        self.ensure_pandapower()
        pp = self.pp
        self.net = pp.create_empty_network(sn_mva=self.sn_mva)
        bus_map = {}
        # buses
        df_bus = self.dataframes.get('bus')
        if df_bus is None or df_bus.empty:
            raise ValueError("Dados de 'bus' não encontrados.")
        # garante nomes das colunas: bus_id, name, vn_kv
        dfb = df_bus.copy()
        if 'bus_id' not in dfb.columns:
            possible = [c for c in dfb.columns if 'barra' in c.lower() or 'bus' in c.lower()]
            if possible: dfb.rename(columns={possible[0]:'bus_id'}, inplace=True)
        if 'name' not in dfb.columns and 'nome' in dfb.columns:
            dfb.rename(columns={'nome':'name'}, inplace=True)

        dfb['vn_kv'] = pd.to_numeric(dfb.get('vn_kv', 230.0), errors='coerce').fillna(230.0)
        dfb['bus_id'] = pd.to_numeric(dfb['bus_id'], errors='coerce').astype(int)

        for _, r in dfb.iterrows():
            idx = pp.create_bus(self.net, name=str(r.get('name', r['bus_id'])), vn_kv=float(r['vn_kv']), in_service=True)
            bus_map[int(r['bus_id'])] = idx

        # gens
        for gdf_key in ['gen', 'dger', 'dger']:
            df_gen = self.dataframes.get(gdf_key)
            if isinstance(df_gen, pd.DataFrame) and not df_gen.empty:
                for _, r in df_gen.iterrows():
                    try:
                        b = int(r.get('bus_id') if 'bus_id' in r.index else r.get('barra', r.get('Barra')))
                        idx = bus_map.get(b)
                        if idx is None: continue
                        p = float(r.get('p_mw', r.get('Potência Ativa (MW)', r.get('p', 0))))
                        pp.create_gen(self.net, bus=idx, p_mw=p, vm_pu=1.0)
                    except Exception:
                        continue

        # loads
        df_load = self.dataframes.get('load')
        if isinstance(df_load, pd.DataFrame) and not df_load.empty:
            for _, r in df_load.iterrows():
                try:
                    b = int(r.get('bus_id') if 'bus_id' in r.index else r.get('barra', r.get('Barra')))
                    idx = bus_map.get(b)
                    if idx is None: continue
                    p = float(r.get('p_mw', r.get('Carga Ativa (MW)', r.get('p', 0))))
                    q = float(r.get('q_mvar', r.get('Carga Reativa (Mvar)', r.get('q', 0))))
                    pp.create_load(self.net, bus=idx, p_mw=p, q_mvar=q)
                except Exception:
                    continue

        # lines
        df_line = self.dataframes.get('line')
        if isinstance(df_line, pd.DataFrame) and not df_line.empty:
            for _, r in df_line.iterrows():
                try:
                    fb = bus_map.get(int(r.get('from_bus', r.get('De', r.get('de')))))
                    tb = bus_map.get(int(r.get('to_bus', r.get('Para', r.get('para')))))
                    if fb is None or tb is None: continue
                    pp.create_line_from_parameters(self.net,
                        from_bus=fb, to_bus=tb,
                        length_km=float(r.get('length_km', 1.0)),
                        r_ohm_per_km=float(r.get('r_ohm_per_km', r.get('R(pu)',0))),
                        x_ohm_per_km=float(r.get('x_ohm_per_km', r.get('X(pu)',0.0))),
                        c_nf_per_km=float(r.get('c_nf_per_km', 0)),
                        max_i_ka=float(r.get('max_i_ka', 1.0))
                    )
                except Exception:
                    continue

        # create ext_grid if not present
        if self.net.ext_grid.empty and not self.net.bus.empty:
            self.pp.create_ext_grid(self.net, bus=self.net.bus.index[0], vm_pu=1.0)
        return self.net

    def run_power_flow(self, **kwargs):
        self.ensure_pandapower()
        try:
            self.pp.runpp(self.net, algorithm=kwargs.get('algorithm','nr'), max_iteration=kwargs.get('max_iteration',30), enforce_q_lims=True, numba=kwargs.get('numba',True))
            return getattr(self.net, 'converged', False)
        except Exception as e:
            # tenta diagnóstico básico
            try:
                self.pp.diagnostic(self.net)
            except Exception:
                pass
            raise

    def export_to_excel(self, filepath):
        # salva dataframes de entrada + res_* se existirem
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for k,v in self.dataframes.items():
                if isinstance(v, pd.DataFrame) and not v.empty:
                    v.to_excel(writer, sheet_name=str(k)[:31], index=False)
            if self.net is not None:
                for res_name in ['res_bus','res_line','res_gen','res_load','res_trafo','res_ext_grid']:
                    if hasattr(self.net, res_name) and getattr(self.net, res_name) is not None and not getattr(self.net, res_name).empty:
                        getattr(self.net, res_name).to_excel(writer, sheet_name=res_name[:31], index=False)
        return filepath

    def summary(self):
        s = {}
        s['dataframes'] = {k:(None if v is None else (v.shape if isinstance(v,pd.DataFrame) else 'list')) for k,v in self.dataframes.items()}
        if self.net is not None:
            s['num_buses'] = self.net.bus.shape[0]
            s['num_lines'] = self.net.line.shape[0] if hasattr(self.net,'line') else 0
        return s
