import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import dash_material_components as dmc
import dash_bootstrap_components as dbc
import numpy as np


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
        if graph_type == "scatter":
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x, y=y, mode=mode))
            fig.update_layout(
                title=self.title, xaxis_title=self.x_label, yaxis_title=self.y_label
            )
        elif graph_type == "scatter3d":
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
        elif graph_type == "pie":
            fig = go.Figure(data=[go.Pie(labels=x, values=y)])
            fig.update_layout(title=self.title)
        return fig


class DashboardApp:
    def __init__(self):
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.app.title = "Resumo Geral de Marketing"
        self.graphs = {
            "leads_mes_graph": GraphUpdater(
                "leads_mes_graph", "Leads por Mês Ano", "Mês", "Leads"
            ),
            "valor_membro_graph": GraphUpdater(
                "valor_membro_graph", "Valor Venda por Tipo Membro", "", ""
            ),
            "sphere_function_graph": GraphUpdater(
                "sphere_function_graph", "Função Sphere 3D", "X", "Y", "Z"
            ),
            "rastrigin_function_graph": GraphUpdater(
                "rastrigin_function_graph", "Função Rastrigin 3D", "X", "Y", "Z"
            ),
        }
        self.layout()
        self.callbacks()

    def layout(self):

        cards = dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H2("R$ 1.74 Mi"),
                                html.P("Gastos Marketing"),
                            ]
                        ),
                    ),
                    md=3,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H2("53,530"),
                                html.P("Leads"),
                            ]
                        ),
                    ),
                    md=3,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H2("33,674"),
                                html.P("Ingressantes"),
                            ]
                        ),
                    ),
                    md=3,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H2("R$ 4.8 Mi"),
                                html.P("Valor Venda"),
                            ]
                        ),
                    ),
                    md=3,
                ),
            ],
            className="mb-4",
        )

        graphs = dbc.Row(
            [
                dbc.Col(self.graphs["leads_mes_graph"].get_graph(), md=6),
                dbc.Col(self.graphs["valor_membro_graph"].get_graph(), md=6),
            ],
            className="mb-4",
        )

        graphs_3d = dbc.Row(
            [
                dbc.Col(self.graphs["sphere_function_graph"].get_graph(), md=6),
                dbc.Col(self.graphs["rastrigin_function_graph"].get_graph(), md=6),
            ],
            className="mb-4",
        )

        calendar_card = dbc.Card(
            dbc.CardBody(
                [
                    html.H4("Selecione a Data"),
                    dcc.DatePickerSingle(
                        id="date-picker", date="2024-01-01", display_format="DD/MM/YYYY"
                    ),
                    html.Div(id="date-output"),
                ]
            )
        )

        input_card = dbc.Card(
            dbc.CardBody(
                [
                    html.H4("Input Dinâmico"),
                    dcc.Input(id="input-text", value="Texto inicial", type="text"),
                    html.Button("Enviar", id="submit-button", n_clicks=0),
                    html.Div(id="output-div"),
                ]
            )
        )

        self.app.layout = dmc.Dashboard(
            children=[
                dmc.NavBar(title="Custom Dashboard"),
                dmc.Page(
                    orientation="columns",
                    children=[
                        dmc.Section(
                            id="section-1",
                            orientation="columns",
                            children=[cards],
                            cards=[
                                {
                                    "title": "Card 1a",
                                },
                                {"title": "Card 1b"},
                            ],
                        ),
                        dmc.Section(
                            id="section-2",
                            orientation="rows",
                            children=[graphs, calendar_card, input_card],
                            cards=[
                                {
                                    "title": "Card 1a",
                                },
                                {"title": "Card 1b"},
                            ],
                        ),
                        dmc.Section(
                            id="section-3",
                            orientation="rows",
                            children=[graphs_3d],
                            cards=[
                                {
                                    "title": "Card 1a",
                                },
                                {"title": "Card 1b"},
                            ],
                        ),
                    ],
                ),
            ]
        )

    def callbacks(self):
        @self.app.callback(
            Output("leads_mes_graph", "figure"), Input("leads_mes_graph", "id")
        )
        def update_leads_mes_graph(_):
            data = get_leads_data()
            meses = [item["mes"] for item in data]
            leads = [item["leads"] for item in data]
            return self.graphs["leads_mes_graph"].update_graph(meses, leads)

        @self.app.callback(
            Output("valor_membro_graph", "figure"), Input("valor_membro_graph", "id")
        )
        def update_valor_membro_graph(_):
            data = get_valor_membro_data()
            labels = [item["tipo_membro"] for item in data]
            values = [item["valor_venda"] for item in data]
            return self.graphs["valor_membro_graph"].update_graph(
                labels, values, graph_type="pie"
            )

        @self.app.callback(
            Output("sphere_function_graph", "figure"),
            Input("sphere_function_graph", "id"),
        )
        def update_sphere_function_graph(_):
            x, y, z = get_sphere_function_data()
            return self.graphs["sphere_function_graph"].update_graph(
                x, y, z, graph_type="scatter3d"
            )

        @self.app.callback(
            Output("rastrigin_function_graph", "figure"),
            Input("rastrigin_function_graph", "id"),
        )
        def update_rastrigin_function_graph(_):
            x, y, z = get_rastrigin_function_data()
            return self.graphs["rastrigin_function_graph"].update_graph(
                x, y, z, graph_type="scatter3d"
            )

        @self.app.callback(
            Output("date-output", "children"), Input("date-picker", "date")
        )
        def update_date_output(date):
            return f"Selecionou: {date}"

        @self.app.callback(
            Output("output-div", "children"),
            Input("submit-button", "n_clicks"),
            State("input-text", "value"),
        )
        def update_output(n_clicks, value):
            return f"Você escreveu: {value} e clicou {n_clicks} vezes."

    def run(self):
        self.app.run_server(debug=True)


def get_leads_data():
    return [
        {"mes": "Jul-19", "leads": 8852},
        {"mes": "Ago-19", "leads": 8357},
        {"mes": "Set-19", "leads": 8657},
        {"mes": "Out-19", "leads": 11084},
        {"mes": "Nov-19", "leads": 12489},
        {"mes": "Dez-19", "leads": 996},
    ]


def get_valor_membro_data():
    return [
        {"tipo_membro": "Black", "valor_venda": 15.27},
        {"tipo_membro": "Platinum", "valor_venda": 31.35},
        {"tipo_membro": "Gold", "valor_venda": 53.26},
    ]


def get_sphere_function_data():
    x = np.linspace(-5.12, 5.12, 100)
    y = np.linspace(-5.12, 5.12, 100)
    x, y = np.meshgrid(x, y)
    z = x**2 + y**2
    return x.flatten(), y.flatten(), z.flatten()


def get_rastrigin_function_data():
    x = np.linspace(-5.12, 5.12, 100)
    y = np.linspace(-5.12, 5.12, 100)
    x, y = np.meshgrid(x, y)
    z = (
        10 * 2
        + (x**2 - 10 * np.cos(2 * np.pi * x))
        + (y**2 - 10 * np.cos(2 * np.pi * y))
    )
    return x.flatten(), y.flatten(), z.flatten()


if __name__ == "__main__":
    dashboard = DashboardApp()
    dashboard.run()
