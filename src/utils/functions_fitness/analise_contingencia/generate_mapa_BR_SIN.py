import pandas as pd
import pandapower as pp
import pandapower.plotting.plotly as pplotly
import os

# Custom class to allow both attribute and dictionary access
class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

# Carregar o DataFrame de barras com coordenadas
# df_bus_coords = pd.read_excel("/home/pedrov12/Documentos/GitHub/SIN_45_barras_com_coordenadas.xlsx")

# --- Conteúdo da classe SmartGridSin45 (copiado e adaptado do arquivo original) ---
class SmartGridSin45:
    """
    Gere todos os dados, criação da rede pandapower e cálculos.
    """
    def __init__(self):
        self.net = None
        self.dataframes = {}
        self.bus_map = {} # Adicionado para mapear IDs de barras para índices do pandapower
        self.line_loading_threshold = 100 # Novo atributo para o limite de carregamento das linhas

    def load_data_from_excel(self, filepath):
        """Carrega dados de um ficheiro Excel para um dicionário de DataFrames."""
        try:
            xls = pd.ExcelFile(filepath)
            self.dataframes = {sheet_name: pd.read_excel(xls, sheet_name) for sheet_name in xls.sheet_names}
            return self.dataframes
        except Exception as e:
            raise ValueError(f"Não foi possível ler o ficheiro Excel: {e}")

    def create_network_from_dataframes(self):
        """Cria uma rede pandapower a partir dos DataFrames carregados e adiciona coordenadas."""
        if not self.dataframes:
            raise ValueError("Nenhum dado carregado para criar a rede.")

        self.net = pp.create_empty_network()
        
        df_bus = self.dataframes.get("bus")
        df_load_gen = self.dataframes.get("load_gen")
        if df_bus is None or df_load_gen is None:
            raise ValueError("As folhas 'bus' e 'load_gen' são necessárias.")

        for col in ["Barra", "Tipo de Barra (*)", "Potência Ativa (MW)", "Carga Ativa (MW)", "Carga Reativa (Mvar)"]:
            if col in df_load_gen.columns:
                df_load_gen[col] = pd.to_numeric(df_load_gen[col], errors="coerce").fillna(0)
        
        df_bus["Barra"] = pd.to_numeric(df_bus["Barra"], errors="coerce").fillna(0)

        for _, row in df_bus.iterrows():
            bus_id = int(row["Barra"])
            try:
                name_str = str(row["Nome"])
                parts = name_str.replace(",", ".").split(".")
                vn_kv = float(parts[-1]) if len(parts) > 1 and parts[-1].isdigit() else 230.0
            except (ValueError, IndexError):
                vn_kv = 230.0

            new_idx = pp.create_bus(self.net, name=row["Nome"], vn_kv=vn_kv)
            self.bus_map[bus_id] = new_idx

        self.net["bus"]["min_vm_pu"] = 0.95
        self.net["bus"]["max_vm_pu"] = 1.05

        for _, row in df_load_gen.iterrows():
            if row["Carga Ativa (MW)"] > 0:
                bus_idx = self.bus_map.get(int(row["Barra"]))
                if bus_idx is not None:
                    pp.create_load(self.net, bus=bus_idx, p_mw=row["Carga Ativa (MW)"], q_mvar=row["Carga Reativa (Mvar)"])

        for _, row in df_load_gen.iterrows():
            bus_idx = self.bus_map.get(int(row["Barra"]))
            if bus_idx is None: continue
            
            is_slack = row["Tipo de Barra (*)"] == 2
            is_gen = row["Potência Ativa (MW)"] > 0

            if is_gen:
                if is_slack:
                    pp.create_ext_grid(self.net, bus=bus_idx, vm_pu=1.0, name="Swing Bus")
                else:
                    pp.create_gen(self.net, bus=bus_idx, p_mw=row["Potência Ativa (MW)"], vm_pu=1.0)

        df_line = self.dataframes.get("line")
        if df_line is not None:
            for col in ["De", "Para", "R(pu)", "X(pu)", "B(pu)"]:
                 if col in df_line.columns:
                    df_line[col] = pd.to_numeric(df_line[col], errors="coerce").fillna(0)

            s_base_mva = 100.0
            for _, row in df_line.iterrows():
                from_bus_id = int(row["De"])
                to_bus_id = int(row["Para"])
                from_bus = self.bus_map.get(from_bus_id)
                to_bus = self.bus_map.get(to_bus_id)
                if from_bus is None or to_bus is None:
                    continue
                
                from_vn_kv = self.net['bus'].vn_kv.at[from_bus]
                to_vn_kv = self.net['bus'].vn_kv.at[to_bus]

                if abs(from_vn_kv - to_vn_kv) > 1e-3:
                    hv_bus, lv_bus = (from_bus, to_bus) if from_vn_kv > to_vn_kv else (to_bus, from_bus)
                    pp.create_transformer_from_parameters(
                        self.net, hv_bus=hv_bus, lv_bus=lv_bus, sn_mva=s_base_mva,
                        vn_hv_kv=max(from_vn_kv, to_vn_kv), vn_lv_kv=min(from_vn_kv, to_vn_kv),
                        vkr_percent=row["R(pu)"] * 100.0, vk_percent=row["X(pu)"] * 100.0,
                        pfe_kw=0, i0_percent=0
                    )
                else:
                    z_base_ohm = (from_vn_kv ** 2) / s_base_mva
                    r_ohm = row["R(pu)"] * z_base_ohm
                    x_ohm = row["X(pu)"] * z_base_ohm
                    c_nf = (row["B(pu)"] / (2 * 3.14159 * 60 * z_base_ohm)) * 1e9
                    pp.create_line_from_parameters(self.net, from_bus=from_bus, to_bus=to_bus, length_km=1.0,
                                                   r_ohm_per_km=r_ohm, x_ohm_per_km=x_ohm,
                                                   c_nf_per_km=c_nf, max_i_ka=0.5)
        return self.net

    def run_power_flow(self):
        if self.net is None:
            raise ValueError("A rede não foi criada.")
        try:
            pp.runpp(self.net)
            return True, "Fluxo de potência executado com sucesso."
        except Exception as e:
            return False, f"Falha no Cálculo de fluxo de potência: {e}"

    def plot_network(self, filename='sin45_network_plot.html'):
        """ Gera um gráfico interativo da rede e guarda como HTML. """
        if self.net is None:
            print("Rede não criada. Não é possível gerar o gráfico.")
            return
        
        print(f"Gerando gráfico da rede em '{filename}'...")
        try:
            net_to_plot_obj = AttrDict(self.net)
            fig = pplotly.simple_plotly(net_to_plot_obj)
            fig.write_html(filename)
            print(f"Gráfico guardado com sucesso! Pode abrir o ficheiro '{filename}' no navegador.")
        except Exception as e:
            print(f"Erro ao gerar o gráfico: {e}")

# --- Execução ---
SmartGrid_SIN45 = SmartGridSin45()
filepath = "/home/pedrov12/Documentos/GitHub/Repopulation-With-Elite-Set/src/utils/functions_fitness/SIN_45_barras_dataset.xlsx"
SmartGrid_SIN45.load_data_from_excel(filepath)
SmartGrid_SIN45.create_network_from_dataframes()

success, message = SmartGrid_SIN45.run_power_flow()
print(message)

SmartGrid_SIN45.plot_network(filename='sin45_network_plot.html')