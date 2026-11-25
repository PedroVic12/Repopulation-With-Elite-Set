import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd


class SunburstGraph:
    def __init__(self, data):
        self.data = data
        self.app = dash.Dash(__name__)
        self.app.layout = self.create_layout()
        self.app.callback(
            Output("sunburst-graph", "figure"), Input("dropdown", "value")
        )(self.update_graph)

    def create_layout(self):
        return html.Div(
            [
                html.H1("Gráfico Sunburst Interativo"),
                dcc.Dropdown(
                    id="dropdown",
                    options=[{"label": col, "value": col} for col in self.data.columns],
                    value=self.data.columns[0],
                ),
                dcc.Graph(id="sunburst-graph"),
            ]
        )

    def update_graph(self, selected_column):
        fig = px.sunburst(self.data, path=["", selected_column], values="value")
        return fig

    def run(self):
        self.app.run_server(debug=True)


if __name__ == "__main__":
    # Carregar dados de exemplo
    df = px.data.gapminder()

    # Criar o gráfico sunburst
    sunburst = SunburstGraph(df)
    sunburst.run()
