import os
import sys
import pandas as pd
import pathlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

BASE_DIR = pathlib.Path(__file__).resolve().parent
HASH_TABLE_PATH = BASE_DIR.parent.parent / "output" / "hash_table_sep_small.xlsx"

from models.RedeEletrica.rede_eletrica import RedeEletricaPandaPower
from models.AlgEvolutivoRCE.Setup import Setup

# =====================================================
# SEP 3 BARRAS
# =====================================================
agendamento_df_3 = pd.DataFrame(
    [{"ramo": [1, 2], "inicio": 14, "duracao": 6, "prioridade": 1}]
)
contingencia_df_3 = pd.DataFrame([{"contingencia": 1, "from": 0, "to": 1}])


def hashtablesize_3():
    return 3 * 3 * (2 ** len(agendamento_df_3))


def funcao_objetivo_SEP3(individuo, setupobj, _debug=False):
    rede = RedeEletricaPandaPower("3", debug=_debug)
    return generic_funcao_objetivo(
        individuo, setupobj, rede, agendamento_df_3, contingencia_df_3, _debug
    )


# =====================================================
# SEP 5 BARRAS
# =====================================================
agendamento_df_5 = pd.DataFrame(
    [
        {"ramo": [1, 2], "inicio": 14, "duracao": 6, "prioridade": 1},
        {"ramo": [3, 4], "inicio": 15, "duracao": 4, "prioridade": 1},
    ]
)
contingencia_df_5 = pd.DataFrame([{"contingencia": 1, "from": 0, "to": 1}])


def hashtablesize_5():
    return 3 * 3 * (2 ** len(agendamento_df_5))


def funcao_objetivo_SEP5(individuo, setupobj, _debug=False):
    rede = RedeEletricaPandaPower("5", debug=_debug)
    return generic_funcao_objetivo(
        individuo, setupobj, rede, agendamento_df_5, contingencia_df_5, _debug
    )


# =====================================================
# SEP 9 BARRAS
# =====================================================
agendamento_df_9 = pd.DataFrame(
    [
        {"ramo": [3, 4], "inicio": 14, "duracao": 6, "prioridade": 1},
        {"ramo": [7, 8], "inicio": 16, "duracao": 5, "prioridade": 1},
    ]
)
contingencia_df_9 = pd.DataFrame([{"contingencia": 1, "from": 0, "to": 3}])


def hashtablesize_9():
    return 3 * 3 * (2 ** len(agendamento_df_9))


def funcao_objetivo_SEP9(individuo, setupobj, _debug=False):
    rede = RedeEletricaPandaPower("9", debug=_debug)
    return generic_funcao_objetivo(
        individuo, setupobj, rede, agendamento_df_9, contingencia_df_9, _debug
    )


# =====================================================
# FUNÇÃO GENÉRICA (Baseada na IEEE 14)
# =====================================================
def generic_funcao_objetivo(
    individuo, setupobj, rede, agendamento_df, contingencia_df, _debug=False
):
    rede.pesos["tensao"] = {"min": 100, "max": 100}
    rede.pesos["loading_linhas"] = 100
    rede.pesos["loading_trafos"] = 100

    duracao_total_agendamento = (
        agendamento_df["inicio"] + agendamento_df["duracao"]
    ).max()
    rede.validar_dados(agendamento_df, contingencia_df)
    agendamento_df["inicio"] = individuo

    violacoes_total = []
    contingencias = contingencia_df["contingencia"].to_list()
    num_carregamentos = 3
    num_contingencias = len(contingencias)

    matriz_cenarios = rede.avalia_cenarios(
        horas=duracao_total_agendamento,
        hora_inicio=agendamento_df["inicio"],
        duracao=agendamento_df["duracao"],
        ls=0,
        le=8,
        ms=8,
        me=18,
        hs=18,
        he=24,
    )

    try:
        for cenario in matriz_cenarios:
            perfil = cenario[0]
            estado_ramos = cenario[1:]
            rede.ajustar_cargas(perfil)

            for contingencia_atual in range(num_contingencias):
                contingencia_atual += 1
                hash_key = rede.hashtableindex(
                    perfil,
                    num_carregamentos,
                    contingencia_atual,
                    num_contingencias,
                    estado_ramos,
                )

                if setupobj.tabela_hash[hash_key] < 0.0:
                    rede.religar_todos_os_ramos_agendamento()
                    rede.desligar_elementos_agendamento(estado_ramos)
                    ramo_contingencia = list(
                        contingencia_df.loc[
                            contingencia_df["contingencia"] == contingencia_atual,
                            ["from", "to"],
                        ].values[0]
                    )
                    rede.desligar_contingencia(ramo_contingencia)

                    if rede.executar_fluxo_de_potencia():
                        fitness, _ = rede.calcular_violacoes_fitness()
                    else:
                        fitness = rede.pesos["demanda"]

                    setupobj.tabela_hash[hash_key] = fitness
                    setupobj.objectiveruns += 1
                else:
                    fitness = setupobj.tabela_hash[hash_key]
                    setupobj.hashtablereads += 1

                violacoes_total.append(fitness)

        return sum(violacoes_total)
    except Exception as e:
        print(f"Erro ao calcular a função objetivo: {e}")
        return 999999
