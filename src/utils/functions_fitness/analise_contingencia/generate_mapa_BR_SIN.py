import pandas as pd
import pandapower as pp
import pandapower.plotting as plot
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import os

# Carregar o DataFrame de barras com coordenadas
df_bus_coords = pd.read_excel("/home/pedrov12/Documentos/GitHub/SIN_45_barras_com_coordenadas.xlsx")

# Carregar o script original para obter a classe SmartGridSin45
# Assumindo que o script original está no mesmo diretório ou no path
# Se não estiver, será necessário ajustar o sys.path ou importar de outra forma

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

    def create_network_from_dataframes(self, df_bus_coords):
        """Cria uma rede pandapower a partir dos DataFrames carregados e adiciona coordenadas."""
        if not self.dataframes:
            raise ValueError("Nenhum dado carregado para criar a rede.")

        self.net = pp.create_empty_network()
        
        df_bus = self.dataframes.get("bus")
        df_load_gen = self.dataframes.get("load_gen")
        if df_bus is None or df_load_gen is None:
            raise ValueError("As folhas 'bus' e 'load_gen' são necessárias.")

        # Converte colunas relevantes para numérico, tratando erros
        for col in ["Barra", "Tipo de Barra (*)", "Potência Ativa (MW)", "Carga Ativa (MW)", "Carga Reativa (Mvar)"]:
            if col in df_load_gen.columns:
                df_load_gen[col] = pd.to_numeric(df_load_gen[col], errors="coerce").fillna(0)
        
        df_bus["Barra"] = pd.to_numeric(df_bus["Barra"], errors="coerce").fillna(0)

        # Merge df_bus com df_bus_coords para obter as coordenadas
        df_bus = pd.merge(df_bus, df_bus_coords[["Barra", "latitude", "longitude"]], on="Barra", how="left")

        for _, row in df_bus.iterrows():
            bus_id = int(row["Barra"])
            try:
                # Lógica para extrair a tensão nominal do nome da barra
                name_str = str(row["Nome"])
                parts = name_str.replace(",", ".").split(".")
                vn_kv = float(parts[-1]) if len(parts) > 1 and parts[-1].isdigit() else 230.0
            except (ValueError, IndexError):
                vn_kv = 230.0 # Valor padrão

            new_idx = pp.create_bus(self.net, name=row["Nome"], vn_kv=vn_kv)
            self.bus_map[bus_id] = new_idx

            # Adicionar coordenadas ao net.bus
            self.net.bus.loc[new_idx, 'geo_latitude'] = row['latitude']
            self.net.bus.loc[new_idx, 'geo_longitude'] = row['longitude']

        # Adiciona limites de tensão para todas as barras para evitar KeyError
        self.net.bus["min_vm_pu"] = 0.95
        self.net.bus["max_vm_pu"] = 1.05

        # Adiciona cargas
        for _, row in df_load_gen.iterrows():
            if row["Carga Ativa (MW)"] > 0:
                bus_idx = self.bus_map.get(int(row["Barra"]))
                if bus_idx is not None:
                    pp.create_load(self.net, bus=bus_idx, p_mw=row["Carga Ativa (MW)"], q_mvar=row["Carga Reativa (Mvar)"])

        # Adiciona geradores e a rede externa (Swing)
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

        # Adiciona linhas e transformadores
        df_line = self.dataframes.get("line")
        if df_line is not None:
            
            # Converte colunas para numérico
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
                    print(f"Skipping line/transformer from bus {from_bus_id} to bus {to_bus_id}: One or both buses not found in network.")
                    continue
                
                from_vn_kv = self.net.bus.vn_kv.at[from_bus]
                to_vn_kv = self.net.bus.vn_kv.at[to_bus]

                #! Se as tensões das barras forem diferentes, é um transformador
                if abs(from_vn_kv - to_vn_kv) > 1e-3:
                    hv_bus, lv_bus = (from_bus, to_bus) if from_vn_kv > to_vn_kv else (to_bus, from_bus)
                    pp.create_transformer_from_parameters(
                        self.net, hv_bus=hv_bus, lv_bus=lv_bus, sn_mva=s_base_mva,
                        vn_hv_kv=max(from_vn_kv, to_vn_kv), vn_lv_kv=min(from_vn_kv, to_vn_kv),
                        vkr_percent=row["R(pu)"] * 100.0, vk_percent=row["X(pu)"] * 100.0,
                        pfe_kw=0, i0_percent=0
                    )
                else: #! Caso contrário, é uma linha de transmissão
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

    def plot_network_with_coords(self, filename='sin45_network_plot_coords.html', background_image_path=None):
        """ Gera um gráfico interativo da rede com coordenadas geográficas e imagem de fundo. """
        if self.net is None:
            print("Rede não criada. Não é possível gerar o gráfico.")
            return
        print(f"Gerando gráfico da rede em '{filename}'...")

        # Adicionar as coordenadas geográficas ao net.bus_geodata
        # O pandapower espera as coordenadas em net.bus_geodata com as colunas 'x' e 'y'
        # onde 'x' é longitude e 'y' é latitude.
        self.net.bus_geodata['x'] = self.net.bus['geo_longitude']
        self.net.bus_geodata['y'] = self.net.bus['geo_latitude']

        # Remover linhas com NaN em geo_latitude ou geo_longitude
        self.net.bus_geodata.dropna(subset=['x', 'y'], inplace=True)

        # Ajustar o layout do plot para usar as coordenadas geográficas
        # plot.create_generic_coordinates(self.net) # Isso criaria coordenadas genéricas, mas queremos as reais

        # Criar o plot com matplotlib para adicionar a imagem de fundo
        fig, ax = plt.subplots(figsize=(10, 10))

        if background_image_path and os.path.exists(background_image_path):
            img = plt.imread(background_image_path)
            # Obter os limites das coordenadas para posicionar a imagem
            min_lon = self.net.bus_geodata['x'].min()
            max_lon = self.net.bus_geodata['x'].max()
            min_lat = self.net.bus_geodata['y'].min()
            max_lat = self.net.bus_geodata['y'].max()

            # Ajustar os limites para a imagem de fundo
            # Estes valores podem precisar de ajuste fino dependendo da imagem e da área coberta
            # Por exemplo, para o Brasil, as coordenadas podem ser:
            # min_lon = -75.0; max_lon = -33.0
            # min_lat = -34.0; max_lat = 6.0

            # Para o caso de RJ/SP, podemos focar mais na região
            # min_lon = -55.0; max_lon = -40.0
            # min_lat = -30.0; max_lat = -15.0

            # Usando os limites das barras para começar
            ax.imshow(img, extent=[min_lon - 2, max_lon + 2, min_lat - 2, max_lat + 2], aspect='auto', zorder=0)

        # Plotar a rede pandapower no eixo do matplotlib
        plot.simple_plot(self.net, ax=ax, plot_bus_geodata=True, show_plot=False, 
                         bus_size=0.1, line_width=0.5, respect_switches=True)

        # Ajustar limites do plot para focar na região das barras
        ax.set_xlim(self.net.bus_geodata['x'].min() - 1, self.net.bus_geodata['x'].max() + 1)
        ax.set_ylim(self.net.bus_geodata['y'].min() - 1, self.net.bus_geodata['y'].max() + 1)

        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title("Rede SIN 45 Barras com Coordenadas Geográficas")
        plt.grid(True)
        plt.savefig(filename.replace('.html', '.png')) # Salvar como PNG para visualização
        plt.close(fig)
        print(f"Gráfico da rede com coordenadas e imagem de fundo salvo em '{filename.replace('.html', '.png')}'.")


# --- Execução --- 
SmartGrid_SIN45 = SmartGridSin45()
filepath = "/home/pedrov12/Documentos/GitHub/Repopulation-With-Elite-Set/src/SIN_45_barras_dataset.xlsx"
SmartGrid_SIN45.load_data_from_excel(filepath)
SmartGrid_SIN45.create_network_from_dataframes(df_bus_coords)

# Executar fluxo de potência (opcional, mas bom para ter resultados)
success, message = SmartGrid_SIN45.run_power_flow()
print(message)

# Caminho para a imagem de fundo (escolha uma das imagens salvas)
background_image = "/home/pedrov12/Documentos/GitHub/Repopulation-With-Elite-Set/src/utils/functions_fitness/Mapa Geoelétrico - Rede de Operação - Brasil - 2029.png" # Exemplo, você pode escolher outra

# Gerar o plot
SmartGrid_SIN45.plot_network_with_coords(filename='sin45_network_plot_coords.png', background_image_path=background_image)