from dash import html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from pyrsistent import b
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash_bootstrap_templates import template_from_url, ThemeChangerAIO
from .app import *
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
import json


# from Class import Setup, AlgoritimoEvolutivoRCE, DataExploration
from Class.ModelsRCE import Setup, AlgoritimoEvolutivoRCE, DataExploration


def load_params(file_path):
    with open(file_path, "r") as file:
        params = json.load(file)
    return params


tabela_evolutiva = pd.read_excel(
    "/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/evolution_rce_master/src/views/tabelas/parametros_evolutivos.xlsx"
)
tabela = pd.read_excel(
    "/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/evolution_rce_master/src/views/tabelas/tabela_consolidada.xlsx"
)
tabela_resumo = pd.read_excel(
    "/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/evolution_rce_master/src/views/tabelas/tabela_resumo.xlsx"
)

tabela_cv = pd.read_excel(
    "/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/evolution_rce_master/src/assets/output/tabela_resumo_CV-21-06.xlsx"
)


# Setup
params = load_params(
    r"/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/evolution_rce_master/src/db/parameters.json"
)

data_visual = DataExploration()

setup = Setup(params)
print(setup)
alg = AlgoritimoEvolutivoRCE(setup)


def main_evolution():
    pop_with_repopulation, logbook_with_repopulation, best_variables = alg.run(RCE=True)
    print("\n\nEvolução concluída - 100%")
    alg.cout("VISUALIZANDO OS RESULTADOS")
    data_visual.show_rastrigin_benchmark(logbook_with_repopulation, best_variables)
    x, y, z = data_visual.visualize(
        logbook_with_repopulation, pop_with_repopulation, repopulation=True
    )
    return logbook_with_repopulation, pop_with_repopulation


def grafico_convergencia(gen, lista, repopulation=False):
    plotly_fig = go.Figure(
        data=[
            go.Scatter(
                x=gen,
                y=lista["min_fitness"],
                mode="lines+markers",
                name="Melhor Fitness",
            ),
            go.Scatter(
                x=gen,
                y=lista["avg_fitness"],
                mode="lines+markers",
                name="Média Fitness",
            ),
            go.Scatter(
                x=gen,
                y=lista["max_fitness"],
                mode="lines+markers",
                name="Desvio Padrão",
            ),
        ],
        layout={
            "title": "Com Repopulação RCE" if repopulation else "Sem Repopulação",
            "xaxis": {"title": "Geração"},
            "yaxis": {"title": "Fitness"},
        },
    )
    return plotly_fig


def show_grafico(logbook, pop, problem_type="minimaze", repopulation=True):
    generation = logbook.select("gen")
    statics = data_visual.calculate_stats(logbook)
    if problem_type == "maximize":
        statics = {key: [-value for value in values] for key, values in statics.items()}
    best_solution_index = statics["min_fitness"].index(min(statics["min_fitness"]))
    best_solution_variables = pop[0] if repopulation else logbook.select("min")
    best_solution_fitness = statics["min_fitness"][best_solution_index]
    data_visual.cout("Soluções do problema")
    print("\nBest solution generation = ", best_solution_index)
    print("\nBest solution variables =\n", best_solution_variables)
    print("\nBest solution fitness = ", best_solution_fitness)
    try:
        plotly_fig = grafico_convergencia(generation, statics, repopulation)
        return plotly_fig
    except Exception as e:
        print("Erro validation :(", e)


#! Dash layout
layout = html.Div(
    [
        dbc.Row(
            [
                html.H3("Dashboard IC - Algoritmos Evolutivos"),
                html.H2("Selecione os Resultados:"),
                dcc.Dropdown(
                    options=[
                        {"label": i, "value": i} for i in tabela["Resultado"].unique()
                    ],
                    multi=True,
                    value=list(tabela["Resultado"].unique()),
                    id="dropdown",
                ),
            ],
            style={"margin-bottom": "30px"},
        ),
        dbc.Row(
            [
                dbc.Col([dcc.Graph(id="graph-convergencia")], md=12),
            ],
            style={"margin-top": "20px"},
        ),
    ]
)


@app.callback(
    Output("graph-convergencia", "figure"),
    Input("dropdown", "value"),
)
def update_grafico_convergencia(selected_results):
    filtered_tabela = tabela[tabela["Resultado"].isin(selected_results)]
    generations = filtered_tabela["Generations"]
    best_fitness_values = filtered_tabela["Best Fitness"]
    media_fitness_values = filtered_tabela["Media Fitness"]
    std_fitness_values = filtered_tabela["STD Fitness"]
    plotly_fig = go.Figure(
        data=[
            go.Scatter(
                x=generations,
                y=best_fitness_values,
                mode="lines+markers",
                name="Melhor Fitness",
            ),
            go.Scatter(
                x=generations,
                y=media_fitness_values,
                mode="lines+markers",
                name="Média Fitness",
            ),
            go.Scatter(
                x=generations,
                y=std_fitness_values,
                mode="lines+markers",
                name="Desvio Padrão",
            ),
        ],
        layout={
            "title": "Evolução do Fitness",
            "xaxis": {"title": "Geração"},
            "yaxis": {"title": "Fitness"},
        },
    )
    return plotly_fig


logbook, pop = main_evolution()
print("Fim evolution")
