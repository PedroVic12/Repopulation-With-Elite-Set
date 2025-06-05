import json
import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc, Dash
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import dash_daq as daq
from Class.ModelsRCE import AlgoritimoEvolutivoRCE, Setup, DataExploration

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


# Carregar parâmetros
def load_params(file_path):
    with open(file_path, "r") as file:
        params = json.load(file)
    return params


params = load_params(
    "/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/evolution_rce_master/src/db/parameters.json"
)
setup = Setup(params)
alg = AlgoritimoEvolutivoRCE(setup)
data_visual = DataExploration()

# Layout do app
app.layout = html.Div(
    [
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H1(
                                "Dashboard do Algoritmo Evolutivo",
                                className="text-center",
                            ),
                            className="mb-4 mt-4",
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Button(
                                "Rodar Algoritmo Evolutivo",
                                id="run-button",
                                className="btn btn-primary btn-lg btn-block",
                            ),
                            className="mb-4",
                        )
                    ]
                ),
                dbc.Row([dbc.Col([dcc.Graph(id="fitness-graph")])]),
                dbc.Row([dbc.Col([dcc.Graph(id="population-graph")])]),
                dbc.Row([dbc.Col(html.Div(id="output-data"))]),
            ]
        )
    ]
)


# Callback para rodar o algoritmo e atualizar os gráficos
@app.callback(
    [
        Output("fitness-graph", "figure"),
        Output("population-graph", "figure"),
        Output("output-data", "children"),
    ],
    [Input("run-button", "n_clicks")],
)
def update_graph(n_clicks):
    if n_clicks is None:
        raise PreventUpdate

    # Rodar o algoritmo
    population, logbook, hof = alg.run(RCE=True)

    # Visualizar os dados
    fitness_figure = go.Figure()
    population_figure = go.Figure()

    return fitness_figure, population_figure, f"Melhor solução: {hof}"


if __name__ == "__main__":
    app.run_server(debug=True)
