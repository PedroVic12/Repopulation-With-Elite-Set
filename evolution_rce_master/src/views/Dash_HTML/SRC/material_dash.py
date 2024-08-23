import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import pandas as pd
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc

# Dados de exemplo
data = {
    "Gastos Marketing": 1.74,
    "Leads": 53530,
    "Ingressantes": 33674,
    "Valor Venda": 4.8,
    "Gastos por Origem": {
        "Afiliados": 643105,
        "Blog": 158143,
        "Email Marketing": 202304,
        "Facebook Ads": 921272,
        "Google Ads": 753490,
        "Outros": 1154270,
    },
    "Leads por Origem": {
        "Afiliados": 5277,
        "Blog": 10853,
        "Email Marketing": 21483,
        "Facebook Ads": 3179,
        "Google Ads": 7439,
        "Outros": 12299,
    },
    "Ingressantes por Origem": {
        "Afiliados": 3322,
        "Blog": 6802,
        "Email Marketing": 14684,
        "Facebook Ads": 1249,
        "Google Ads": 4350,
        "Outros": 2149,
    },
    "Valor Venda por Origem": {
        "Afiliados": 4182570,
        "Blog": 3547456,
        "Email Marketing": 9750656,
        "Facebook Ads": 1332712,
        "Google Ads": 4214270,
        "Outros": 5346950,
    },
    "Leads por Mês": [8852, 8357, 8657, 11084, 12489, 996],
    "Meses": ["Jul-19", "Ago-19", "Set-19", "Out-19", "Nov-19", "Dez-19"],
    "Valor Venda por Tipo Membro": {"Black": 15.27, "Platinum": 31.35, "Gold": 53.26},
}


class DashboardApp:
    def __init__(self):
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.app.title = "Resumo Geral de Marketing"
        self.layout()
        self.callbacks()

    def layout(self):
        self.app.layout = dbc.Container(
            [
                html.H1(
                    "Resumo Geral de Marketing",
                    style={"textAlign": "center", "marginBottom": "20px"},
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H2(f'R$ {data["Gastos Marketing"]} Mi'),
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
                                        html.H2(f'{data["Leads"]}'),
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
                                        html.H2(f'{data["Ingressantes"]}'),
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
                                        html.H2(f'R$ {data["Valor Venda"]} Mi'),
                                        html.P("Valor Venda"),
                                    ]
                                ),
                            ),
                            md=3,
                        ),
                    ],
                    className="mb-4",
                ),
                dbc.Row(
                    [
                        dbc.Col(dcc.Graph(id="leads-mes-graph"), md=6),
                        dbc.Col(dcc.Graph(id="valor-membro-graph"), md=6),
                    ]
                ),
            ],
            fluid=True,
        )

    def callbacks(self):
        @self.app.callback(
            Output("leads-mes-graph", "figure"), Input("leads-mes-graph", "id")
        )
        def update_leads_mes_graph(_):
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=data["Meses"],
                    y=data["Leads por Mês"],
                    mode="lines+markers",
                    name="Leads",
                )
            )
            fig.update_layout(
                title="Leads por Mês Ano", xaxis_title="Mês", yaxis_title="Leads"
            )
            return fig

        @self.app.callback(
            Output("valor-membro-graph", "figure"), Input("valor-membro-graph", "id")
        )
        def update_valor_membro_graph(_):
            labels = list(data["Valor Venda por Tipo Membro"].keys())
            values = list(data["Valor Venda por Tipo Membro"].values())
            fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
            fig.update_layout(title="Valor Venda por Tipo Membro")
            return fig

    def run(self):
        self.app.run_server(debug=True)


if __name__ == "__main__":
    dashboard = DashboardApp()
    dashboard.run()
