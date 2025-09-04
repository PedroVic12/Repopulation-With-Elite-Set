import pandas as pd
import pandapower as pp
import pandapower.plotting as plot
import pandapower.topology
import matplotlib.pyplot as plt
import traceback
import os
import networkx as nx
from matplotlib.collections import LineCollection

# Classe RedeEletricaModel adaptada do simulador_ONS_SIN.py
class RedeEletricaModel:
    def __init__(self):
        self.net = None
        self.network_name = ""
        self.dataframes = {}
        self.bus_map = {}

    def load_network_from_excel(self, filepath):
        try:
            xls = pd.ExcelFile(filepath)
            sheet_names = xls.sheet_names
            required_sheets = ['bus', 'line', 'load_gen', 'shunt']
            
            if not all(sheet in sheet_names for sheet in required_sheets):
                missing = [s for s in required_sheets if s not in sheet_names]
                return False, f"Arquivo Excel inválido. Faltam as abas: {', '.join(missing)}"

            self.dataframes = {sheet_name: xls.parse(sheet_name) for sheet_name in sheet_names}
            self.network_name = "SIN 45 Barras"
            
            success, message = self._create_network_from_dataframes()
            if success:
                self.net.name = self.network_name
            return success, message
        except Exception as e:
            return False, f"Falha ao processar o arquivo Excel: {e}"

    def _create_network_from_dataframes(self):
        try:
            self.net = pp.create_empty_network()
            self.bus_map.clear()
            
            df_bus = self.dataframes.get('bus')
            df_load_gen = self.dataframes.get('load_gen')
            df_line = self.dataframes.get('line')
            df_shunt = self.dataframes.get('shunt')

            slack_buses = df_load_gen[df_load_gen['Tipo de Barra (*)'] == 2]
            if len(slack_buses) != 1:
                return False, f"Erro de Dados: {len(slack_buses)} barras de referência (Slack) encontradas. A rede deve ter exatamente uma."

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

            gen_col = next((c for c in df_load_gen.columns if 'potencia' in c.lower()), 'Potencia Ativa (MW)')
            for _, row in df_load_gen.iterrows():
                bus_idx = self.bus_map.get(int(row['Barra']))
                if bus_idx is None: continue
                if row['Carga Ativa (MW)'] > 0:
                    pp.create_load(self.net, bus=bus_idx, p_mw=row['Carga Ativa (MW)'], q_mvar=row['Carga Reativa (Mvar)'])
                if row['Tipo de Barra (*)'] == 2:
                    pp.create_ext_grid(self.net, bus=bus_idx, vm_pu=1.0, name="Slack Bus")
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
                    pp.create_line_from_parameters(self.net, from_bus=from_bus, to_bus=to_bus, length_km=1.0, r_ohm_per_km=row['R(pu)'] * z_base_ohm, x_ohm_per_km=row['X(pu)'] * z_base_ohm, c_nf_per_km=(row['B(pu)'] / (2 * 3.14159 * 60 * z_base_ohm)) * 1e9, max_i_ka=0.5)
            
            return True, "Rede SIN 45 criada com sucesso a partir do arquivo."
        except Exception as e:
            return False, f"Erro ao construir rede a partir dos dados: {e}\n{traceback.format_exc()}"

def create_generic_coordinates_workaround(net):
    """
    Generates generic coordinates for the network buses using networkx spring_layout.
    This is a workaround for issues with the built-in pandapower function.
    """
    graph = pandapower.topology.create_nxgraph(net)
    pos = nx.spring_layout(graph, seed=42)
    coords = pd.DataFrame.from_dict(pos, orient='index', columns=['x', 'y'])
    coords.index.name = 'bus'
    net.bus_geodata = coords
    return net

def plot_rede_completa(net):
    """
    Plota o diagrama completo da rede com legenda detalhada e elementos coloridos.
    """
    fig, ax = plt.subplots(figsize=(20, 15))
    ax.set_title("Diagrama Unifilar - SIN 45 Barras", fontsize=20, fontweight='bold')

    colors = {
        "bus": "#005c99", "line": "grey", "trafo": "purple", "gen": "red",
        "load": "green", "shunt": "orange", "ext_grid": "yellow"
    }
    
    # Manually create line collection
    line_coords = []
    for _, line in net.line.iterrows():
        from_bus_coords = net.bus_geodata.loc[line.from_bus]
        to_bus_coords = net.bus_geodata.loc[line.to_bus]
        line_coords.append([(from_bus_coords.x, from_bus_coords.y), (to_bus_coords.x, to_bus_coords.y)])
    
    lc = LineCollection(line_coords, color=colors["line"], linewidths=1.5, zorder=1)
    ax.add_collection(lc)

    # Manually create trafo collection
    trafo_coords = []
    for _, trafo in net.trafo.iterrows():
        hv_bus_coords = net.bus_geodata.loc[trafo.hv_bus]
        lv_bus_coords = net.bus_geodata.loc[trafo.lv_bus]
        trafo_coords.append([(hv_bus_coords.x, lv_bus_coords.y), (lv_bus_coords.x, lv_bus_coords.y)])
        
    tc = LineCollection(trafo_coords, color=colors["trafo"], linewidths=2.5, zorder=1)
    ax.add_collection(tc)

    # Plot buses and other node elements using ax.scatter
    bus_coords = net.bus_geodata
    ax.scatter(bus_coords.x, bus_coords.y, s=100, color=colors["bus"], zorder=10, label='Barra (Bus)')

    def draw_node_elements(ax, net, element_type, marker, size, color, zorder, label):
        if not net[element_type].empty:
            element_bus_coords = net.bus_geodata.loc[net[element_type].bus]
            ax.scatter(element_bus_coords.x, element_bus_coords.y, s=size, marker=marker, color=color, zorder=zorder, label=label)

    draw_node_elements(ax, net, 'gen', marker='^', size=200, color=colors["gen"], zorder=11, label='Gerador (Gen)')
    draw_node_elements(ax, net, 'load', marker='v', size=200, color=colors["load"], zorder=11, label='Carga (Load)')
    draw_node_elements(ax, net, 'shunt', marker='s', size=200, color=colors["shunt"], zorder=11, label='Shunt')
    draw_node_elements(ax, net, 'ext_grid', marker='s', size=250, color=colors["ext_grid"], zorder=11, label='Rede Externa (Slack)')

    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='Barra (Bus)', markerfacecolor=colors["bus"], markersize=12),
        Line2D([0], [0], color=colors["line"], lw=2, label='Linha de Transmissão'),
        Line2D([0], [0], color=colors["trafo"], lw=2, label='Transformador'),
        Line2D([0], [0], marker='^', color='w', label='Gerador (Gen)', markerfacecolor=colors["gen"], markersize=12),
        Line2D([0], [0], marker='v', color='w', label='Carga (Load)', markerfacecolor=colors["load"], markersize=12),
        Line2D([0], [0], marker='s', color='w', label='Shunt', markerfacecolor=colors["shunt"], markersize=12),
        Line2D([0], [0], marker='s', color='w', label='Rede Externa (Slack)', markerfacecolor=colors["ext_grid"], markersize=14)
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=12, title="Legenda")
    
    ax.set_facecolor('#f0f2f5')
    fig.patch.set_facecolor('#f0f2f5')
    plt.tight_layout()
    
    output_path = "diagrama_rede_completo.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Diagrama da rede salvo em: {os.path.abspath(output_path)}")
    plt.close(fig)

def main():
    filepath = "SIN_45_barras_dataset.xlsx"
    if not os.path.exists(filepath):
        print(f"Erro: Arquivo '{filepath}' não encontrado.")
        return

    model = RedeEletricaModel()
    
    print("Carregando rede do Excel...")
    success, message = model.load_network_from_excel(filepath)
    
    if not success:
        print(f"Falha ao carregar a rede: {message}")
        return
        
    print(message)
    
    print("Gerando coordenadas (workaround) e o diagrama da rede...")
    model.net = create_generic_coordinates_workaround(model.net)
    
    plot_rede_completa(model.net)

if __name__ == '__main__':
    main()