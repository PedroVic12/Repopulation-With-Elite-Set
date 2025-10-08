# inspect_excel.py

```python
import os
import sys
import pandas as pd
import pathlib
import pandapower as pp

# Assuming SmartGridSin45 class is available in the context or imported
# For this temporary script, I'll copy the class definition from the user's file
# to make it self-contained.

# --- DADOS DO CASO SIN 45 ---
# Extraídos de SIMULATOR_SIN_45.py
class SmartGridSin45:
    """
    Gere todos os dados, criação da rede pandapower e cálculos.
    """
    def __init__(self):
        self.net = None
        self.dataframes = {}
        self.bus_map = {} # Adicionado para mapear IDs de barras para índices do pandapower

    def plot_network(self, filename='sin45_network_plot.html'):
        """ Gera um gráfico interativo da rede e guarda como HTML. """
        if self.net is None:
            print("Rede não criada. Não é possível gerar o gráfico.")
            return
        print(f"A gerar gráfico da rede em '{filename}'...")
        try:
            pp.runpp(self.net)
            fig = pp.plotting.plotly.simple_plotly(self.net)
            fig.write_html(filename)
            print(f"Gráfico guardado com sucesso! Pode abrir o ficheiro '{filename}' no navegador.")
        except Exception as e:
            print(f"Erro ao gerar o gráfico: {e}")

    def load_data_from_excel(self, filepath):
        """Carrega dados de um ficheiro Excel para um dicionário de DataFrames."""
        try:
            xls = pd.ExcelFile(filepath)
            self.dataframes = {sheet_name: pd.read_excel(xls, sheet_name) for sheet_name in xls.sheet_names}
            return self.dataframes
        except Exception as e:
            raise ValueError(f"Não foi possível ler o ficheiro Excel: {e}")

    def create_network_from_dataframes(self):
        """Cria uma rede pandapower a partir dos DataFrames carregados."""
        if not self.dataframes:
            raise ValueError("Nenhum dado carregado para criar a rede.")

        self.net = pp.create_empty_network()
        
        df_bus = self.dataframes.get('bus')
        df_load_gen = self.dataframes.get('load_gen')
        if df_bus is None or df_load_gen is None:
            raise ValueError("As folhas 'bus' e 'load_gen' são necessárias.")

        # Converte colunas relevantes para numérico, tratando erros
        for col in ['Barra', 'Tipo de Barra (*)', 'Potência Ativa (MW)', 'Carga Ativa (MW)', 'Carga Reativa (Mvar)']:
            if col in df_load_gen.columns:
                df_load_gen[col] = pd.to_numeric(df_load_gen[col], errors='coerce').fillna(0)
        
        df_bus['Barra'] = pd.to_numeric(df_bus['Barra'], errors='coerce').fillna(0)

        for _, row in df_bus.iterrows():
            bus_id = int(row['Barra'])
            try:
                # Lógica para extrair a tensão nominal do nome da barra
                name_str = str(row['Nome'])
                parts = name_str.replace(',', '.').split('.')
                vn_kv = float(parts[-1]) if len(parts) > 1 and parts[-1].isdigit() else 230.0
            except (ValueError, IndexError):
                vn_kv = 230.0 # Valor padrão

            new_idx = pp.create_bus(self.net, name=row['Nome'], vn_kv=vn_kv)
            self.bus_map[bus_id] = new_idx

        # CORREÇÃO: Adiciona limites de tensão para todas as barras para evitar KeyError
        self.net.bus['min_vm_pu'] = 0.95
        self.net.bus['max_vm_pu'] = 1.05

        # Adiciona cargas
        for _, row in df_load_gen.iterrows():
            if row['Carga Ativa (MW)'] > 0:
                bus_idx = self.bus_map.get(int(row['Barra']))
                if bus_idx is not None:
                    pp.create_load(self.net, bus=bus_idx, p_mw=row['Carga Ativa (MW)'], q_mvar=row['Carga Reativa (Mvar)'])

        # Adiciona geradores e a rede externa (slack)
        for _, row in df_load_gen.iterrows():
            bus_idx = self.bus_map.get(int(row['Barra']))
            if bus_idx is None: continue
            
            is_slack = row['Tipo de Barra (*)'] == 2
            is_gen = row['Potência Ativa (MW)'] > 0

            if is_gen:
                if is_slack:
                    pp.create_ext_grid(self.net, bus=bus_idx, vm_pu=1.0, name="Slack Bus")
                else:
                    pp.create_gen(self.net, bus=bus_idx, p_mw=row['Potência Ativa (MW)'], vm_pu=1.0)

        # Adiciona linhas e transformadores
        df_line = self.dataframes.get('line')
        if df_line is not None:
            # Converte colunas para numérico
            for col in ['De', 'Para', 'R(pu)', 'X(pu)', 'B(pu)']:
                 if col in df_line.columns:
                    df_line[col] = pd.to_numeric(df_line[col], errors='coerce').fillna(0)

            s_base_mva = 100.0
            for _, row in df_line.iterrows():
                from_bus = self.bus_map.get(int(row['De']))
                to_bus = self.bus_map.get(int(row['Para']))
                if from_bus is None or to_bus is None:
                    print(f"Skipping line/transformer from bus {int(row['De'])} to bus {int(row['Para'])}: One or both buses not found in network.")
                    continue
                
                from_vn_kv = self.net.bus.vn_kv.at[from_bus]
                to_vn_kv = self.net.bus.vn_kv.at[to_bus]

                # Se as tensões das barras forem diferentes, é um transformador
                if abs(from_vn_kv - to_vn_kv) > 1e-3:
                    hv_bus, lv_bus = (from_bus, to_bus) if from_vn_kv > to_vn_kv else (to_bus, from_bus)
                    pp.create_transformer_from_parameters(
                        self.net, hv_bus=hv_bus, lv_bus=lv_bus, sn_mva=s_base_mva,
                        vn_hv_kv=max(from_vn_kv, to_vn_kv), vn_lv_kv=min(from_vn_kv, to_vn_kv),
                        vkr_percent=row['R(pu)'] * 100.0, vk_percent=row['X(pu)'] * 100.0,
                        pfe_kw=0, i0_percent=0
                    )
                else: # Caso contrário, é uma linha de transmissão
                    z_base_ohm = (from_vn_kv ** 2) / s_base_mva
                    r_ohm = row['R(pu)'] * z_base_ohm
                    x_ohm = row['X(pu)'] * z_base_ohm
                    c_nf = (row['B(pu)'] / (2 * 3.14159 * 60 * z_base_ohm)) * 1e9
                    pp.create_line_from_parameters(self.net, from_bus=from_bus, to_bus=to_bus, length_km=1.0,
                                                   r_ohm_per_km=r_ohm, x_ohm_per_km=x_ohm,
                                                   c_nf_per_km=c_nf, max_i_ka=0.5)
        return self.net

    def run_power_flow(self):
        if self.net is None:
            raise ValueError("A rede não foi criada.")
        try:
            pp.runpp(self.net)
            return True, "Fluxo de potência do SIN 45 executado com sucesso."
        except Exception as e:
            return False, f"Falha no fluxo de potência: {e}"


# --- Temporary script to inspect Excel file ---
excel_file_path = "/home/pedrov12/Documentos/GitHub/Repopulation-With-Elite-Set/src/utils/functions_fitness/SIN_45_barras_dataset.xlsx"

smart_grid_inspector = SmartGridSin45()
try:
    smart_grid_inspector.load_data_from_excel(excel_file_path)
    
    df_bus = smart_grid_inspector.dataframes.get('bus')
    df_line = smart_grid_inspector.dataframes.get('line')

    if df_bus is not None:
        print("\n--- Conteúdo da aba 'bus' ---")
        print(df_bus.to_string())
    else:
        print("\nAba 'bus' não encontrada no arquivo Excel.")

    if df_line is not None:
        print("\n--- Conteúdo da aba 'line' (colunas 'De' e 'Para') ---")
        print(df_line[['De', 'Para']].to_string(index=False))
    else:
        print("\nAba 'line' não encontrada no arquivo Excel.")

except Exception as e:
    print(f"Erro ao inspecionar o arquivo Excel: {e}")

```