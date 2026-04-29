from dash import html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from pyrsistent import b
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash_bootstrap_templates import template_from_url, ThemeChangerAIO
from app import *

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
                                dbc.CardHeader("Melhor Solução 1"),
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
                                dbc.CardHeader("Melhor Solução 2"),
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
                                dbc.CardHeader("Melhor Solução 3"),
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
                                dbc.CardHeader("Parâmetros Evolutivos"),
                                dbc.CardBody(
                                    [
                                        html.H5("Parâmetros do Algoritmo Evolutivo"),
                                        # dcc.Graph(
                                        #     id="graph-params-evolutivos",
                                        #     figure=px.bar(
                                        #         tabela_evolutiva,
                                        #         x="CROSSOVER",
                                        #         y="NUM_GENERATIONS",
                                        #     ),
                                        # ),
                                        html.Table(
                                            [
                                                html.Tr(
                                                    [
                                                        html.Th(col)
                                                        for col in tabela_evolutiva.columns
                                                    ]
                                                )
                                            ]
                                            + [
                                                html.Tr([html.Td(data) for data in row])
                                                for row in tabela_evolutiva.values
                                            ],
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
                                dbc.CardHeader("Tabela Consolidada"),
                                dbc.CardBody(
                                    [
                                        html.H5("Tabela Consolidada"),
                                        # dcc.Graph(
                                        #     id="graph-tabela-consolidada",
                                        #     figure=px.bar(
                                        #         tabela,
                                        #         x="Resultado",
                                        #         y="Media Fitness",
                                        #     ),
                                        # ),
                                        html.Table(
                                            [
                                                html.Tr(
                                                    [
                                                        html.Th(col)
                                                        for col in tabela.columns
                                                    ]
                                                )
                                            ]
                                            + [
                                                html.Tr([html.Td(data) for data in row])
                                                for row in tabela.values
                                            ],
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
                                        # dcc.Graph(
                                        #     id="graph-tabela-resumo",
                                        #     figure=px.bar(
                                        #         tabela_resumo,
                                        #         x="Media best Fitness values",
                                        #         y="Media Fitness",
                                        #     ),
                                        # ),
                                        html.Table(
                                            [
                                                html.Tr(
                                                    [
                                                        html.Th(col)
                                                        for col in tabela_resumo.columns
                                                    ]
                                                )
                                            ]
                                            + [
                                                html.Tr([html.Td(data) for data in row])
                                                for row in tabela_resumo.values
                                            ],
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
                                        # dcc.Graph(
                                        #     id="graph-tabela-cv",
                                        #     figure=px.bar(
                                        #         tabela_cv,
                                        #         x="Crossover",
                                        #         y="CV",
                                        #     ),
                                        # ),
                                        html.Table(
                                            [
                                                html.Tr(
                                                    [
                                                        html.Th(col)
                                                        for col in tabela_cv.columns
                                                    ]
                                                )
                                            ]
                                            + [
                                                html.Tr([html.Td(data) for data in row])
                                                for row in tabela_cv.values
                                            ],
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
