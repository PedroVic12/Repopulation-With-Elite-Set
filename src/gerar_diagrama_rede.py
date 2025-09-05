
import pandas as pd
import pandapower as pp
import pandapower.networks as pn
import pandapower.plotting as plot
import pandapower.topology
import matplotlib.pyplot as plt
import traceback
import os
import networkx as nx
import argparse
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D

# Classe RedeEletricaModel adaptada do simulador_ONS_SIN.py
class RedeEletricaModel:
    def __init__(self):
        self.net = None
        self.network_name = ""
        self.dataframes = {}
        self.bus_map = {}

    def load_network(self, network_name):
        self.network_name = network_name
        self.dataframes.clear()
        try:
            if network_name == "IEEE 14": self.net = pn.case14()
            elif network_name == "IEEE 30": self.net = pn.case_ieee30()
            elif network_name == "IEEE 57": self.net = pn.case57()
            elif network_name == "IEEE 118": self.net = pn.case118()
            else: return False, f"Caso de rede '{network_name}' desconhecido."
            self.net.name = network_name
            return True, f"Rede '{network_name}' carregada com sucesso."
        except Exception as e:
            return False, f"Erro ao carregar a rede '{network_name}': {e}"

    def load_network_from_excel(self, filepath):
        try:
            xls = pd.ExcelFile(filepath)
            self.dataframes = {sheet_name: xls.parse(sheet_name) for sheet_name in xls.sheet_names}
            self.network_name = "SIN 45 Barras"
            success, message = self._create_network_from_dataframes()
            if success: self.net.name = self.network_name
            return success, message
        except Exception as e:
            return False, f"Falha ao processar o arquivo Excel: {e}"

    def _create_network_from_dataframes(self):
        df_load_gen = self.dataframes.get('load_gen')
        slack_buses = df_load_gen[df_load_gen['Tipo de Barra (*)'] == 2]
        if len(slack_buses) != 1: return False, f"Erro Crítico: A rede deve ter UMA barra Slack. Encontradas: {len(slack_buses)}."
        self.net = pp.create_empty_network()
        self.bus_map.clear()
        df_bus = self.dataframes.get('bus')
        df_line = self.dataframes.get('line')
        df_shunt = self.dataframes.get('shunt')
        for _, row in df_bus.iterrows():
            bus_id, name_str = int(row['Barra']), str(row['Nome'])
            try: vn_kv = float(name_str.replace(',', '.').split('.')[-1])
            except (ValueError, IndexError): vn_kv = 230.0
            new_idx = pp.create_bus(self.net, name=name_str, vn_kv=vn_kv)
            self.bus_map[bus_id] = new_idx
        gen_col = next((c for c in df_load_gen.columns if 'pot' in c.lower()), 'Potência Ativa (MW)')
        for _, row in df_load_gen.iterrows():
            bus_idx = self.bus_map.get(int(row['Barra']))
            if bus_idx is None: continue
            if row['Carga Ativa (MW)'] > 0: pp.create_load(self.net, bus=bus_idx, p_mw=row['Carga Ativa (MW)'], q_mvar=row['Carga Reativa (Mvar)'])
            if row['Tipo de Barra (*)'] == 2: pp.create_ext_grid(self.net, bus=bus_idx, vm_pu=1.0)
            elif row.get(gen_col, 0) > 0: pp.create_gen(self.net, bus=bus_idx, p_mw=row[gen_col], vm_pu=1.0)
        if 'shunt' in self.dataframes: 
            for _, row in df_shunt.iterrows():
                bus_idx = self.bus_map.get(int(row['Barra']))
                if bus_idx is not None: pp.create_shunt(self.net, bus=bus_idx, q_mvar=row.iloc[1] * (self.net.bus.vn_kv.at[bus_idx] ** 2))
        for _, row in df_line.iterrows():
            from_bus, to_bus = self.bus_map.get(int(row['De'])), self.bus_map.get(int(row['Para']))
            if from_bus is None or to_bus is None: continue
            from_vn, to_vn = self.net.bus.vn_kv.at[from_bus], self.net.bus.vn_kv.at[to_bus]
            if abs(from_vn - to_vn) > 1e-3:
                hv_bus, lv_bus = (from_bus, to_bus) if from_vn > to_vn else (to_bus, from_bus)
                pp.create_transformer_from_parameters(self.net, hv_bus, lv_bus, 100.0, max(from_vn, to_vn), min(from_vn, to_vn), row['R(pu)']*100.0, row['X(pu)']*100.0, 0, 0)
            else:
                z_base = (from_vn ** 2) / 100.0
                pp.create_line_from_parameters(self.net, from_bus, to_bus, 1.0, row['R(pu)']*z_base, row['X(pu)']*z_base, (row['B(pu)']/(2*3.14159*60*z_base))*1e9, 10.0)
        return True, "Rede SIN 45 criada com sucesso."

def create_generic_coordinates_workaround(net):
    graph = pandapower.topology.create_nxgraph(net)
    pos = nx.spring_layout(graph, seed=42)
    coords = pd.DataFrame.from_dict(pos, orient='index', columns=['x', 'y'])
    coords.index.name = 'bus'
    net.bus_geodata = coords
    return net

def plot_rede_completa(net, network_name, bus_map={}):
    fig, ax = plt.subplots(figsize=(20, 15))
    ax.set_title(f"Diagrama Unifilar - {network_name}", fontsize=20, fontweight='bold')
    colors = {"bus": "#005c99", "line": "grey", "trafo": "purple", "gen": "red", "load": "green", "shunt": "orange", "ext_grid": "yellow"}
    legend_handles = []

    # Plotagem de Linhas e Trafos
    if network_name == "SIN 45 Barras":
        ramos = {
            "Ramo 1 (Verde)": {"pairs": [(1,19),(12,19),(12,13),(13,14),(14,15),(15,16),(16,17),(17,30)], "color": "green"},
            "Ramo 2 (Azul)": {"pairs": [(1,28),(26,28),(25,26),(24,25),(23,24),(3,23)], "color": "blue"},
            "Ramo 3 (Vermelho)": {"pairs": [(4,5),(5,7),(7,8),(8,9)], "color": "red"}
        }
        plotted_lines = set()
        for name, data in ramos.items():
            line_coords, line_indices = [], []
            for b1, b2 in data["pairs"]:
                idx1, idx2 = bus_map.get(b1), bus_map.get(b2)
                if idx1 is not None and idx2 is not None:
                    line = net.line[((net.line.from_bus == idx1) & (net.line.to_bus == idx2)) | ((net.line.from_bus == idx2) & (net.line.to_bus == idx1))]
                    if not line.empty:
                        line_idx = line.index[0]
                        line_indices.append(line_idx)
                        line_coords.append([(net.bus_geodata.loc[idx1].x, net.bus_geodata.loc[idx1].y), (net.bus_geodata.loc[idx2].x, net.bus_geodata.loc[idx2].y)])
            if line_coords: 
                ax.add_collection(LineCollection(line_coords, color=data["color"], linewidths=2.5, zorder=1))
                legend_handles.append(Line2D([0], [0], color=data["color"], lw=2, label=name))
                plotted_lines.update(line_indices)
        other_lines_coords = [[(net.bus_geodata.loc[l.from_bus].x, net.bus_geodata.loc[l.from_bus].y), (net.bus_geodata.loc[l.to_bus].x, net.bus_geodata.loc[l.to_bus].y)] for i, l in net.line.iterrows() if i not in plotted_lines]
        ax.add_collection(LineCollection(other_lines_coords, color=colors["line"], linewidths=1.5, zorder=1))
        legend_handles.append(Line2D([0], [0], color=colors["line"], lw=2, label="Outras Linhas"))
    else:
        line_coords = [[(net.bus_geodata.loc[l.from_bus].x, net.bus_geodata.loc[l.from_bus].y), (net.bus_geodata.loc[l.to_bus].x, net.bus_geodata.loc[l.to_bus].y)] for _, l in net.line.iterrows()]
        ax.add_collection(LineCollection(line_coords, color=colors["line"], linewidths=1.5, zorder=1))
        legend_handles.append(Line2D([0], [0], color=colors["line"], lw=2, label="Linha"))

    if not net.trafo.empty:
        trafo_coords = [[(net.bus_geodata.loc[t.hv_bus].x, net.bus_geodata.loc[t.hv_bus].y), (net.bus_geodata.loc[t.lv_bus].x, net.bus_geodata.loc[t.lv_bus].y)] for _, t in net.trafo.iterrows()]
        ax.add_collection(LineCollection(trafo_coords, color=colors["trafo"], linewidths=2.5, zorder=1))
        legend_handles.append(Line2D([0], [0], color=colors["trafo"], lw=2, label="Transformador"))

    # Plotagem de Elementos de Nó
    ax.scatter(net.bus_geodata.x, net.bus_geodata.y, s=100, color=colors["bus"], zorder=10)
    legend_handles.append(Line2D([0], [0], marker='o', color='w', label='Barra', markerfacecolor=colors["bus"], markersize=12))
    def draw_node(element, marker, size, color, label):
        if not net[element].empty:
            coords = net.bus_geodata.loc[net[element].bus]
            ax.scatter(coords.x, coords.y, s=size, marker=marker, color=color, zorder=11)
            legend_handles.append(Line2D([0], [0], marker=marker, color='w', label=label, markerfacecolor=color, markersize=12))
    draw_node('gen', '^', 200, colors["gen"], 'Gerador')
    draw_node('load', 'v', 200, colors["load"], 'Carga')
    draw_node('shunt', 's', 200, colors["shunt"], 'Shunt')
    draw_node('ext_grid', 's', 250, colors["ext_grid"], 'Rede Externa')

    ax.legend(handles=legend_handles, loc='upper right', fontsize=12, title="Legenda")
    ax.set_facecolor('#f0f2f5')
    fig.patch.set_facecolor('#f0f2f5')
    plt.tight_layout()
    output_path = f"diagrama_{network_name.replace(' ', '_')}.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Diagrama salvo em: {os.path.abspath(output_path)}")
    plt.close(fig)

def main():
    parser = argparse.ArgumentParser(description="Gerador de Diagramas de Redes Elétricas")
    parser.add_argument("network_name", type=str, help="Nome da rede a ser plotada (e.g., 'IEEE 14', 'SIN 45 Barras')")
    args = parser.parse_args()

    model = RedeEletricaModel()
    bus_map = {}
    
    if args.network_name == "SIN 45 Barras":
        filepath = "SIN_45_barras_dataset.xlsx"
        if not os.path.exists(filepath):
            print(f"Erro: Arquivo '{filepath}' não encontrado.")
            return
        success, message = model.load_network_from_excel(filepath)
        bus_map = model.bus_map
    else:
        success, message = model.load_network(args.network_name)

    if not success:
        print(message)
        return
    print(message)

    print("Gerando coordenadas e diagrama...")
    model.net = create_generic_coordinates_workaround(model.net)
    plot_rede_completa(model.net, args.network_name, bus_map)

if __name__ == '__main__':
    main()
