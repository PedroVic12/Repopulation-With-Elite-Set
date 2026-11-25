import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import dash_bootstrap_components as dbc


class GraphUpdater:
    def __init__(self, graph_id, title, x_label, y_label, z_label=None):
        self.graph_id = graph_id
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.z_label = z_label

    def get_graph(self):
        return dcc.Graph(id=self.graph_id)

    def update_graph(self, x, y, z=None, mode="markers", graph_type="scatter3d"):
        if graph_type == "scatter3d":
            fig = go.Figure()
            fig.add_trace(go.Scatter3d(x=x, y=y, z=z, mode=mode, marker=dict(size=5)))
            fig.update_layout(
                title=self.title,
                scene=dict(
                    xaxis_title=self.x_label,
                    yaxis_title=self.y_label,
                    zaxis_title=self.z_label,
                ),
            )
        return fig


class DashboardApp:
    def __init__(self):
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.app.title = "Resumo Geral de Engenharia Elétrica"
        self.graphs = {
            "grafico1": GraphUpdater("grafico1", "Campo Elétrico 3D", "X", "Y", "Z"),
            "grafico2": GraphUpdater("grafico2", "Campo Magnético 3D", "X", "Y", "Z"),
        }
        self.layout()
        self.callbacks()

    def layout(self):
        self.app.layout = dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Nav(
                                [
                                    dbc.NavLink("Home", href="#", active="exact"),
                                    dbc.NavLink(
                                        "Gráfico 1", href="#grafico1", active="exact"
                                    ),
                                    dbc.NavLink(
                                        "Gráfico 2", href="#grafico2", active="exact"
                                    ),
                                ],
                                vertical=True,
                                pills=True,
                            ),
                            width=2,
                        ),
                        dbc.Col(
                            dbc.Container(
                                [
                                    html.H1(
                                        "Resumo Geral de Engenharia Elétrica",
                                        style={
                                            "textAlign": "center",
                                            "marginBottom": "20px",
                                        },
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                self.graphs["grafico1"].get_graph(),
                                                md=6,
                                            ),
                                            dbc.Col(
                                                self.graphs["grafico2"].get_graph(),
                                                md=6,
                                            ),
                                        ]
                                    ),
                                ],
                                fluid=True,
                            ),
                            width=10,
                        ),
                    ],
                    className="g-0",
                ),
            ],
            fluid=True,
        )

    def callbacks(self):
        @self.app.callback(Output("grafico1", "figure"), Input("grafico1", "id"))
        def update_grafico1(_):
            # Supondo que `get_campo_eletrico_data()` é uma função que retorna dados
            data = get_campo_eletrico_data()
            x = [item["x"] for item in data]
            y = [item["y"] for item in data]
            z = [item["z"] for item in data]
            return self.graphs["grafico1"].update_graph(x, y, z)

        @self.app.callback(Output("grafico2", "figure"), Input("grafico2", "id"))
        def update_grafico2(_):
            # Supondo que `get_campo_magnetico_data()` é uma função que retorna dados
            data = get_campo_magnetico_data()
            x = [item["x"] for item in data]
            y = [item["y"] for item in data]
            z = [item["z"] for item in data]
            return self.graphs["grafico2"].update_graph(x, y, z)

    def run(self):
        self.app.run_server(debug=True)


def get_campo_eletrico_data():
    # Função fictícia que retorna dados do campo elétrico em 3D
    return [
        {"x": 1, "y": 2, "z": 3},
        {"x": 4, "y": 5, "z": 6},
        {"x": 7, "y": 8, "z": 9},
        {"x": 10, "y": 11, "z": 12},
        {"x": 13, "y": 14, "z": 15},
    ]


def get_campo_magnetico_data():
    # Função fictícia que retorna dados do campo magnético em 3D
    return [
        {"x": 2, "y": 3, "z": 4},
        {"x": 5, "y": 6, "z": 7},
        {"x": 8, "y": 9, "z": 10},
        {"x": 11, "y": 12, "z": 13},
        {"x": 14, "y": 15, "z": 16},
    ]


if __name__ == "__main__":
    dashboard = DashboardApp()
    dashboard.run()
