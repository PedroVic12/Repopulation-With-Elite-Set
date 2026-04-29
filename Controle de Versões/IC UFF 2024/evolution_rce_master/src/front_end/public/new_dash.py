import dash
from dash import dcc
from dash import html
import dash_ag_grid as dag
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
import dash_material_components as dmc  # Importe o MUI


# Criando a classe do backend
class Backend:
    def __init__(self):
        self.app = dash.Dash(
            __name__, external_stylesheets=[dbc.themes.CYBORG]
        )  # Use o tema MATERIAL do dbc
        self.df = pd.read_csv(
            "https://raw.githubusercontent.com/Coding-with-Adam/Dash-by-Plotly/master/LangChain/Graph-Insights/domain-notable-ai-system.csv"
        )
        self.chart_types = ["Bar Chart", "Line Chart", "Scatter Chart"]

        self.app.layout = dmc.Dashboard(  # Use o componente Dashboard do MUI
            children=[
                dmc.NavBar(
                    title="Interactive Data Visualization"
                ),  # Barra de navegação
                dmc.Page(
                    children=[
                        dmc.Section(
                            children=[
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            self.create_card("Card 1", "Content 1"),
                                            md=3,
                                        ),
                                        dbc.Col(
                                            self.create_card("Card 2", "Content 2"),
                                            md=3,
                                        ),
                                        dbc.Col(
                                            self.create_card("Card 3", "Content 3"),
                                            md=3,
                                        ),
                                        dbc.Col(
                                            self.create_card("Card 4", "Content 4"),
                                            md=3,
                                        ),
                                    ],
                                    className="mb-4",  # Adicione uma margem inferior
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dag.AgGrid(
                                                    id="data-table",
                                                    columnDefs=[
                                                        {
                                                            "headerName": "Year",
                                                            "field": "Year",
                                                        },
                                                        {
                                                            "headerName": "Annual number of AI systems by domain",
                                                            "field": "Annual number of AI systems by domain",
                                                        },
                                                        {
                                                            "headerName": "Entity",
                                                            "field": "Entity",
                                                        },
                                                    ],
                                                    rowData=self.df.to_dict("records"),
                                                    dashGridOptions={
                                                        "pagination": True,
                                                        "paginationPageSize": 10,
                                                    },
                                                )
                                            ],
                                            md=6,
                                        ),
                                        dbc.Col(
                                            [
                                                dcc.Dropdown(
                                                    id="chart-type",
                                                    options=[
                                                        {"label": i, "value": i}
                                                        for i in self.chart_types
                                                    ],
                                                    value="Bar Chart",
                                                ),
                                                dcc.Graph(id="interactive-graph"),
                                                html.Div(id="insights"),
                                            ],
                                            md=6,
                                        ),
                                    ]
                                ),
                            ],
                            cards=[
                                {
                                    "title": "Card 1a",
                                },
                                {"title": "Card 1b"},
                            ],
                        )
                    ]
                ),
            ]
        )

        # Callback para atualizar o gráfico e os insights
        @self.app.callback(
            [
                dash.Output("interactive-graph", "figure"),
                dash.Output("insights", "children"),
            ],
            [dash.Input("chart-type", "value")],
        )
        def update_graph(selected_chart):
            fig = self.create_chart(selected_chart)
            insights = self.generate_insights(selected_chart)
            return fig, insights

    def create_card(self, title, content):
        return dbc.Card(
            dbc.CardBody(
                [
                    html.H4(title, className="card-title"),
                    html.P(content, className="card-text"),
                ]
            )
        )

    def create_chart(self, selected_chart):
        fig = None
        if selected_chart == "Bar Chart":
            fig = px.bar(
                self.df,
                x="Year",
                y="Annual number of AI systems by domain",
                color="Entity",
            )
        elif selected_chart == "Line Chart":
            fig = px.line(
                self.df,
                x="Year",
                y="Annual number of AI systems by domain",
                color="Entity",
            )
        elif selected_chart == "Scatter Chart":
            fig = px.scatter(
                self.df,
                x="Year",
                y="Annual number of AI systems by domain",
                color="Entity",
            )

        fig.update_layout(
            title=f"{selected_chart} of AI Systems by Domain",
            xaxis_title="Year",
            yaxis_title="Annual Number of AI Systems",
            legend_title="Entity",
        )
        return fig

    def generate_insights(self, selected_chart):
        # Aqui você pode implementar lógica para gerar insights
        # baseados no tipo de gráfico selecionado.
        return f"This {selected_chart} shows the trends in the number of AI systems across different domains over time. You can see that..."

    def run(self):
        self.app.run_server(debug=True)


# Iniciar o backend
if __name__ == "__main__":
    backend = Backend()
    backend.run()
