import sqlite3
import pandas as pd
import pandapower as pp
import pandapower.plotting as plot
import plotly.graph_objects as go
from rich.console import Console
from rich.table import Table

console = Console()

class Database:
    def __init__(self, db_path="network.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS buses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                vnom REAL,
                type TEXT
            );
            CREATE TABLE IF NOT EXISTS lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                from_bus INTEGER,
                to_bus INTEGER,
                r REAL,
                x REAL,
                b REAL,
                FOREIGN KEY(from_bus) REFERENCES buses(id) ON DELETE CASCADE,
                FOREIGN KEY(to_bus) REFERENCES buses(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS transformers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                from_bus INTEGER,
                to_bus INTEGER,
                r REAL,
                x REAL,
                tap_ratio REAL,
                FOREIGN KEY(from_bus) REFERENCES buses(id) ON DELETE CASCADE,
                FOREIGN KEY(to_bus) REFERENCES buses(id) ON DELETE CASCADE
            );
        """)
        self.conn.commit()

    def insert_bus(self, name, vnom, type_):
        self.cursor.execute("INSERT INTO buses (name, vnom, type) VALUES (?,?,?)", (name, vnom, type_))
        self.conn.commit()
        return self.cursor.lastrowid

    def insert_line(self, name, from_bus, to_bus, r, x, b):
        self.cursor.execute("INSERT INTO lines (name, from_bus, to_bus, r, x, b) VALUES (?,?,?,?,?,?)",
                            (name, from_bus, to_bus, r, x, b))
        self.conn.commit()

    def insert_transformer(self, name, from_bus, to_bus, r, x, tap_ratio):
        self.cursor.execute("INSERT INTO transformers (name, from_bus, to_bus, r, x, tap_ratio) VALUES (?,?,?,?,?,?)",
                            (name, from_bus, to_bus, r, x, tap_ratio))
        self.conn.commit()

    def delete_bus(self, bus_id):
        self.cursor.execute("DELETE FROM buses WHERE id=?", (bus_id,))
        self.conn.commit()

    def delete_line(self, line_id):
        self.cursor.execute("DELETE FROM lines WHERE id=?", (line_id,))
        self.conn.commit()

    def delete_transformer(self, tf_id):
        self.cursor.execute("DELETE FROM transformers WHERE id=?", (tf_id,))
        self.conn.commit()

    def get_all_buses(self):
        return self.cursor.execute("SELECT * FROM buses").fetchall()

    def get_all_lines(self):
        return self.cursor.execute("SELECT * FROM lines").fetchall()

    def get_all_transformers(self):
        return self.cursor.execute("SELECT * FROM transformers").fetchall()

    def close(self):
        self.conn.close()

    # NOVOS MÉTODOS PARA EDIÇÃO
    def update_bus(self, bus_id, name, vnom, type_):
        self.cursor.execute("UPDATE buses SET name=?, vnom=?, type=? WHERE id=?", 
                            (name, vnom, type_, bus_id))
        self.conn.commit()

    def update_line(self, line_id, name, from_bus, to_bus, r, x, b):
        self.cursor.execute("""UPDATE lines SET name=?, from_bus=?, to_bus=?, r=?, x=?, b=?
                             WHERE id=?""", (name, from_bus, to_bus, r, x, b, line_id))
        self.conn.commit()

    def update_transformer(self, tf_id, name, from_bus, to_bus, r, x, tap_ratio):
        self.cursor.execute("""UPDATE transformers SET name=?, from_bus=?, to_bus=?, r=?, x=?, tap_ratio=?
                             WHERE id=?""", (name, from_bus, to_bus, r, x, tap_ratio, tf_id))
        self.conn.commit()


class NetworkController:
    def __init__(self, db: Database):
        self.db = db

    def import_from_excel(self, file_path):
        """Lê planilhas com nomes definidos: 'barras', 'linhas', 'transformadores'"""
        df_buses = pd.read_excel(file_path, sheet_name='barras')
        df_lines = pd.read_excel(file_path, sheet_name='linhas')
        df_trafos = pd.read_excel(file_path, sheet_name='transformadores')

        # Insere no banco (validações simplificadas)
        for _, row in df_buses.iterrows():
            self.db.insert_bus(row['nome'], row['vnom'], row['tipo'])
        for _, row in df_lines.iterrows():
            self.db.insert_line(row['nome'], row['de'], row['para'], row['r'], row['x'], row['b'])
        for _, row in df_trafos.iterrows():
            self.db.insert_transformer(row['nome'], row['de'], row['para'], row['r'], row['x'], row['tap'])
        console.print("[green]Dados importados com sucesso![/green]")

    def build_pandapower_net(self):
        """Cria uma rede pandapower a partir do banco SQLite"""
        net = pp.create_empty_network()

        # Mapeia IDs do banco para índices da rede
        bus_map = {}

        # Barras
        for bus in self.db.get_all_buses():
            bid = bus[0]
            name = bus[1]
            vnom = bus[2]
            bus_type = bus[3]  # 'PQ', 'PV', 'ref'
            idx = pp.create_bus(net, name=name, vn_kv=vnom, type=bus_type)
            bus_map[bid] = idx

        # Linhas
        for line in self.db.get_all_lines():
            _, name, from_b, to_b, r, x, b = line
            pp.create_line_from_parameters(net, from_bus=bus_map[from_b], to_bus=bus_map[to_b],
                                           length_km=1.0, r_ohm_per_km=r, x_ohm_per_km=x, c_nf_per_km=b*1e9,
                                           max_i_ka=1.0, name=name)

        # Transformadores
        for tf in self.db.get_all_transformers():
            _, name, from_b, to_b, r, x, tap = tf
            pp.create_transformer_from_parameters(net, hv_bus=bus_map[from_b], lv_bus=bus_map[to_b],
                                                   sn_mva=100, vn_hv_kv=100, vn_lv_kv=100, vkr_percent=r*100,
                                                   vk_percent=x*100, pfe_kw=0, i0_percent=0, tap_side="hv",
                                                   tap_neutral=1.0, tap_step_percent=tap, name=name)

        return net

    def show_ybus(self, net):
        """Exibe a matriz Ybus usando rich"""
        ybus = net._ppc["Ybus"].todense()
        table = Table(title="Matriz Ybus (pu)")
        table.add_column("Barra", justify="right")
        for i in range(ybus.shape[1]):
            table.add_column(f"Barra {i+1}", justify="center")
        for i in range(ybus.shape[0]):
            row = [str(i+1)] + [f"{ybus[i,j].real:.3f}+{ybus[i,j].imag:.3f}j" for j in range(ybus.shape[1])]
            table.add_row(*row)
        console.print(table)

    def plot_diagram(self, net):
        """Gera diagrama unifilar interativo com plotly"""
        # Usamos o simple_plot do pandapower (matplotlib) e convertemos para plotly?
        # Ou criamos um gráfico de nós e arestas manualmente com plotly.
        # Vamos usar a função simple_plot do pandapower, que retorna uma figura matplotlib,
        # e depois a convertemos para plotly (ou mostramos direto no Qt).
        # Para manter a interatividade, podemos usar plotly scatter.
        # Exemplo simplificado: extrair coordenadas dos nós e desenhar linhas.
        # No entanto, o pandapower já tem um layout interno. Vamos usar o plotly para desenhar.

        # Extrai posições dos nós (usando spring layout do networkx, que o pandapower utiliza)
        try:
            import networkx as nx
            mg = pp.topology.create_nxgraph(net)
            pos = nx.spring_layout(mg)
        except:
            # Fallback: posições aleatórias
            import random
            pos = {bus: (random.random(), random.random()) for bus in net.bus.index}

        # Cria traces para as linhas
        edge_trace = []
        for line in net.line.itertuples():
            x0, y0 = pos[line.from_bus]
            x1, y1 = pos[line.to_bus]
            edge_trace.append(go.Scatter(x=[x0, x1, None], y=[y0, y1, None],
                                         mode='lines', line=dict(color='blue', width=1),
                                         hoverinfo='none', showlegend=False))

        # Traço para as barras
        bus_x = [pos[i][0] for i in net.bus.index]
        bus_y = [pos[i][1] for i in net.bus.index]
        bus_text = [f"Barra {i}<br>Vnom: {net.bus.vn_kv[i]} kV" for i in net.bus.index]
        bus_trace = go.Scatter(x=bus_x, y=bus_y, mode='markers+text',
                               marker=dict(size=10, color='red'),
                               text=net.bus.name.values, textposition="top center",
                               hovertext=bus_text, hoverinfo='text', showlegend=False)

        fig = go.Figure(data=edge_trace + [bus_trace])
        fig.update_layout(title="Diagrama Unifilar", showlegend=False,
                          xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig