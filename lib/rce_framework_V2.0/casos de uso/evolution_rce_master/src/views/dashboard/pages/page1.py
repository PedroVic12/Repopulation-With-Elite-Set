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

print("testes")
tabela_evolutiva
tabela
tabela_resumo
tabela_cv


#! Views
layout = html.Div(
    [
        dbc.Row(
            [
                html.H3("Dashboard IC - Alg Evolutivos"),
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
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader("Best Solution Generation"),
                                dbc.CardBody([], id="best1"),
                            ],
                            color="light",
                        )
                    ],
                    md=2,
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader("Best Solution variables"),
                                dbc.CardBody([], id="best2"),
                            ],
                            color="light",
                        )
                    ],
                    md=2,
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader("Best Solution Fitness"),
                                dbc.CardBody([], id="best3"),
                            ],
                            color="light",
                        )
                    ],
                    md=2,
                ),
            ],
            style={"margin-top": "20px"},
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader("Tabela Consolidada"),
                                dbc.CardBody(
                                    [
                                        html.H5("Tabela Consolidada"),
                                        dcc.Graph(
                                            id="graph-tabela-consolidada",
                                            figure=px.bar(
                                                tabela,
                                                x="Resultado",
                                                y="Media Fitness",
                                                color="RCE Num Generations",
                                            ),
                                        ),
                                    ]
                                ),
                            ],
                            color="light",
                        )
                    ],
                    md=6,
                ),
            ],
            style={"margin-top": "20px"},
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader("Tabela Resumo"),
                                dbc.CardBody(
                                    [
                                        html.H5("Tabela Resumo"),
                                        dcc.Graph(
                                            id="graph-tabela-resumo",
                                            figure=px.bar(
                                                tabela_resumo,
                                                x="Max best Fitness",
                                                y="Media best Fitness values",
                                            ),
                                        ),
                                    ]
                                ),
                            ],
                            color="light",
                        )
                    ],
                    md=6,
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader("Coeficiente de Variação"),
                                dbc.CardBody(
                                    [
                                        html.H5("Coeficiente de Variação"),
                                        dcc.Graph(
                                            id="graph-tabela-cv",
                                            figure=px.bar(
                                                tabela_cv,
                                                x="Media best Fitness values",
                                                y="CV",
                                            ),
                                        ),
                                    ]
                                ),
                            ],
                            color="light",
                        )
                    ],
                    md=6,
                ),
            ],
            style={"margin-top": "20px"},
        ),
    ],
    id="main",
)


@app.callback(
    Output("best1", "children"),
    Output("best2", "children"),
    Output("best3", "children"),
    Input("dropdown", "value"),
)
def update_best_solutions(selected_results):
    # Filtra as tabelas com base no Resultado selecionado
    filtered_tabela = tabela[tabela["Resultado"].isin(selected_results)]

    # Obtém os valores das melhores soluções
    best_solution1 = filtered_tabela.iloc[0]["Variaveis de Decisão"]
    best_solution2 = filtered_tabela.iloc[1]["Variaveis de Decisão"]
    best_solution3 = filtered_tabela.iloc[2]["Variaveis de Decisão"]

    return (
        html.P(f"Melhor Solução 1: {best_solution1}"),
        html.P(f"Melhor Solução 2: {best_solution2}"),
        html.P(f"Melhor Solução 3: {best_solution3}"),
    )


@app.callback(
    Output("graph-convergencia", "figure"),
    Input("dropdown", "value"),
)
def update_grafico_convergencia(selected_results):
    filtered_tabela = tabela[tabela["Resultado"].isin(selected_results)]

    fig, ax1 = plt.subplots()

    generations = filtered_tabela["Generations"]
    best_fitness_values = filtered_tabela["Best Fitness"]
    media_fitness_values = filtered_tabela["Media Fitness"]
    std_fitness_values = filtered_tabela["STD Fitness"]

    ax1.set_xlabel("Geração")
    ax1.set_ylabel("Fitness")

    lns1 = ax1.plot(
        generations,
        best_fitness_values,
        "*b-",
        label="Melhor Fitness por Geração",
    )
    lns2 = ax1.plot(
        generations,
        media_fitness_values,
        "+r-",
        label="Média Fitness por Geração",
    )
    lns3 = ax1.plot(
        generations,
        std_fitness_values,
        "og-",
        label="Desvio Padrão do Fitness",
    )

    lns = lns1 + lns2 + lns3
    labs = [l.get_label() for l in lns]
    ax1.legend(lns, labs, loc="upper right")

    # Criar figura do Plotly
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


@app.callback(
    Output("graph-tabela-consolidada", "figure"),
    Input("dropdown", "value"),
)
def update_grafico_tabela_consolidada(selected_results):
    filtered_tabela = tabela[tabela["Resultado"].isin(selected_results)]

    fig = px.bar(
        filtered_tabela,
        x="Generations",
        y="Media Fitness",
        color="Generations",
    )

    fig.update_layout(
        title="Média de Fitness por Geração",
        xaxis_title="Geração",
        yaxis_title="Média de Fitness",
    )

    return fig


@app.callback(
    Output("graph-tabela-resumo", "figure"),
    Input("dropdown", "value"),
)
def update_grafico_tabela_resumo(selected_results):
    filtered_tabela = tabela_resumo[tabela_resumo["Resultado"].isin(selected_results)]

    fig = px.bar(
        filtered_tabela,
        x="Resultado",
        y="Media Fitness",
        color="Resultado",
    )

    fig.update_layout(
        title="Média de Fitness por Resultado",
        xaxis_title="Resultado",
        yaxis_title="Média de Fitness",
    )

    return fig


@app.callback(
    Output("graph-tabela-cv", "figure"),
    Input("dropdown", "value"),
)
def update_grafico_tabela_cv(selected_results):
    filtered_tabela = tabela_cv[tabela_cv["Resultado"].isin(selected_results)]

    fig = px.bar(
        filtered_tabela,
        x="Crossover",
        y="CV",
        color="Crossover",
    )

    fig.update_layout(
        title="Coeficiente de Variação por Crossover",
        xaxis_title="Crossover",
        yaxis_title="CV (%)",
    )

    return fig


@app.callback(
    Output("graph-params-evolutivos", "figure"),
    Input("dropdown", "value"),
)
def update_grafico_params_evolutivos(selected_results):
    filtered_tabela = tabela_evolutiva[
        tabela_evolutiva["Resultado"].isin(selected_results)
    ]

    fig = px.bar(
        filtered_tabela,
        x="Parâmetros",
        y="Valores",
        color="Parâmetros",
    )

    fig.update_layout(
        title="Parâmetros do Algoritmo Evolutivo",
        xaxis_title="Parâmetros",
        yaxis_title="Valores",
    )

    return fig
