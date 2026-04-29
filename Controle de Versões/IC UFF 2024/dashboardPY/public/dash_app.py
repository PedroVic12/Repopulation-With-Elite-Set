from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from django_plotly_dash import DjangoDash

df = pd.read_csv(
    "https://raw.githubusercontent.com/Coding-with-Adam/Dash-by-Plotly/master/LangChain/Graph-Insights/domain-notable-ai-system.csv"
)


class DashApp:
    def __init__(self):
        self.app = DjangoDash("dash_app", external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.create_layout()
        self.add_callbacks()

    def create_layout(self):
        self.app.layout = html.Div(
            [
                dcc.Dropdown(
                    id="chart-type-dropdown",
                    options=[
                        {"label": "Bar Chart", "value": "bar"},
                        {"label": "Line Chart", "value": "line"},
                        {"label": "Scatter Chart", "value": "scatter"},
                    ],
                    value="bar",
                ),
                dcc.Graph(id="interactive-graph"),
            ]
        )

    def add_callbacks(self):
        @self.app.callback(
            Output("interactive-graph", "figure"),
            [Input("chart-type-dropdown", "value")],
        )
        def update_graph(selected_chart_type):
            if selected_chart_type == "bar":
                fig = px.bar(
                    df,
                    x="Year",
                    y="Annual number of AI systems by domain",
                    color="Entity",
                )
            elif selected_chart_type == "line":
                fig = px.line(
                    df,
                    x="Year",
                    y="Annual number of AI systems by domain",
                    color="Entity",
                )
            else:
                fig = px.scatter(
                    df,
                    x="Year",
                    y="Annual number of AI systems by domain",
                    color="Entity",
                )
            return fig


dash_app = DashApp()
