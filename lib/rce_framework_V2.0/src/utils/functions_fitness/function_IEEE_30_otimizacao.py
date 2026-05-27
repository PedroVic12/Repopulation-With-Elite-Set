import os
import sys
import pandas as pd
import pathlib
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from models.RedeEletrica.rede_eletrica import RedeEletricaPandaPower
from models.AlgEvolutivoRCE.Setup import Setup
from models.AlgEvolutivoRCE.alg_evolutivo_rce import AlgoritimoEvolutivoRCE

BASE_DIR = pathlib.Path(__file__).resolve().parent
HASH_TABLE_PATH = BASE_DIR.parent.parent / "output" / "hash_table_ieee30.xlsx"

# =========================================================
# 📊 DADOS BASE
# =========================================================

agendamento_base = pd.DataFrame(
    [
        {"ramo": [1, 3], "inicio": "15:00", "duracao": 6, "prioridade": 4},
        {"ramo": [1, 5], "inicio": "15:00", "duracao": 5, "prioridade": 1},
        {"ramo": [5, 8], "inicio": "14:00", "duracao": 6, "prioridade": 1},
        {"ramo": [13, 14], "inicio": "18:00", "duracao": 6, "prioridade": 1},
        {"ramo": [15, 16], "inicio": "15:00", "duracao": 4, "prioridade": 1},
        {"ramo": [21, 23], "inicio": "14:00", "duracao": 5, "prioridade": 1},
        {"ramo": [7, 27], "inicio": "10:00", "duracao": 6, "prioridade": 1},
        {"ramo": [26, 28], "inicio": "14:00", "duracao": 5, "prioridade": 1},
        {"ramo": [9, 21], "inicio": "18:00", "duracao": 4, "prioridade": 1},
        {"ramo": [14, 17], "inicio": "15:00", "duracao": 5, "prioridade": 1},
    ]
)

contingencia_df = pd.DataFrame(
    [
        {"contingencia": 1, "from": 1, "to": 3},
        {"contingencia": 2, "from": 11, "to": 14},
        {"contingencia": 3, "from": 14, "to": 17},
    ]
)

# =========================================================
# 🔢 HASH TABLE SIZE
# =========================================================


def hashtablesize():
    return len(contingencia_df) * 3 * (2 ** len(agendamento_base))


# =========================================================
# 🚀 ANÁLISE DE CONTINGÊNCIAS
# =========================================================


def analise_contigencias_SEP(rede, setupobj, matriz_cenarios, df_ag):

    resultados = []
    violacoes_total = []

    for cenario_idx, cenario in enumerate(matriz_cenarios):

        perfil = cenario[0]
        estado_ramos = cenario[1:]

        rede.ajustar_cargas(perfil)

        for contingencia_atual in range(1, len(contingencia_df) + 1):

            hash_key = rede.hashtableindex(
                perfil, 3, contingencia_atual, len(contingencia_df), estado_ramos
            )

            ramo_cont = list(
                contingencia_df.loc[
                    contingencia_df["contingencia"] == contingencia_atual,
                    ["from", "to"],
                ].values[0]
            )

            if setupobj.tabela_hash[hash_key] < 0:

                rede.religar_todos_os_ramos_agendamento()
                rede.desligar_elementos_agendamento(estado_ramos)
                rede.desligar_contingencia(ramo_cont)

                if rede.executar_fluxo_de_potencia():
                    fitness, _ = rede.calcular_violacoes_fitness()
                else:
                    fitness = rede.pesos.get("demanda", 99)

                setupobj.tabela_hash[hash_key] = fitness
                setupobj.objectiveruns += 1

            else:
                fitness = setupobj.tabela_hash[hash_key]
                setupobj.hashtablereads += 1

            violacoes_total.append(fitness)

            # ✅ salvar dados estruturados
            if fitness > 0:
                for i, estado in enumerate(estado_ramos):
                    if estado == 1:
                        resultados.append(
                            {
                                "cenario": int(cenario_idx),
                                "perfil": int(perfil),
                                "contingencia": int(contingencia_atual),
                                "ramo_cont_from": int(ramo_cont[0]),
                                "ramo_cont_to": int(ramo_cont[1]),
                                "ramo_desligado_from": int(df_ag.iloc[i]["ramo"][0]),
                                "ramo_desligado_to": int(df_ag.iloc[i]["ramo"][1]),
                                "inicio": int(df_ag.iloc[i]["inicio"]),
                                "duracao": int(df_ag.iloc[i]["duracao"]),
                                "fitness": float(fitness),
                            }
                        )

    df = pd.DataFrame(resultados)

    return sum(violacoes_total), df


# =========================================================
# 🎯 FUNÇÃO OBJETIVO
# =========================================================


def funcao_objetivo_IEEE30(individuo, setupobj, _debug=False):

    rede = RedeEletricaPandaPower("30", debug=_debug)

    rede.pesos["tensao"] = {"min": 100, "max": 100}
    rede.pesos["loading_linhas"] = 100
    rede.pesos["loading_trafos"] = 100

    df_ag = agendamento_base.copy()
    df_ag["inicio"] = individuo

    # ✅ salvar info de agendamento no setup para o Dashboard
    setupobj.agendamento_info = df_ag.to_dict(orient="records")

    rede.validar_dados(df_ag, contingencia_df)

    matriz = rede.avalia_cenarios(
        horas=(df_ag["inicio"] + df_ag["duracao"]).max(),
        hora_inicio=df_ag["inicio"],
        duracao=df_ag["duracao"],
        ls=0,
        le=8,
        ms=8,
        me=18,
        hs=18,
        he=24,
    )

    fitness, df_resultados = analise_contigencias_SEP(rede, setupobj, matriz, df_ag)

    # ✅ salvar no setup (ESSENCIAL)
    setupobj.df_resultados = df_resultados

    return fitness


# =========================================================
# 🧪 EXECUÇÃO COMPLETA
# =========================================================

params_json_teste = {
    "ARRAY_VAR": [15, 15, 10, 21, 16, 13, 10, 14, 17, 18],
    "CROSSOVER": 0.90,
    "DELTA_MIN": 2,
    "IND_SIZE": 10,
    "LIMITE_VAR": [0, 23],
    "MUTACAO": 0.80,
    "NUM_GENERATIONS": 50,
    "NUM_VAR_DIFERENTES": 1,
    "POP_SIZE": 20,
    "PORCENTAGEM": 0.2,
    "RCE_REPOPULATION_GENERATIONS": 50,
}


def simulate_IEEE30():

    setup = Setup(
        params=params_json_teste,
        fitness_function=funcao_objetivo_IEEE30,
        tamanho_hash=hashtablesize(),
    )

    print("\n🚀 Executando Algoritmo Evolutivo...\n")

    start = datetime.now()

    alg = AlgoritimoEvolutivoRCE(setup, DEBUG=True)

    pop, logbook, best_individual, _ = alg.run(RCE=True)

    end = datetime.now()

    print("\n✅ Melhor indivíduo encontrado:")
    print(best_individual)

    print("\n🔎 Reprocessando melhor solução...\n")

    funcao_objetivo_IEEE30(best_individual, setup, _debug=False)

    df_final = getattr(setup, "df_resultados", pd.DataFrame())

    # ✅ IMPRESSÃO CORRETA
    if not df_final.empty:

        print("\n📊 CONTINGÊNCIAS CRÍTICAS:\n")

        print(
            df_final[
                [
                    "contingencia",
                    "ramo_cont_from",
                    "ramo_cont_to",
                    "ramo_desligado_from",
                    "ramo_desligado_to",
                    "inicio",
                    "fitness",
                ]
            ]
            .head(15)
            .to_string(index=False)
        )

    else:
        print("\n⚠️ Nenhum resultado encontrado")

    print("\n🎯 Melhor agendamento (horários):")
    print(sorted(set(best_individual)))

    print(f"\n⏱ Tempo execução: {end - start}")
    print(f"Execuções função objetivo: {setup.objectiveruns}")
    print(f"Leituras hash: {setup.hashtablereads}")

    # ✅ EXPORT
    if not df_final.empty:
        df_final.to_excel("resultado_agendamento.xlsx", index=False)

    # =========================================================
    # 📊 ANÁLISE PANDAS (PRA VOCÊ USAR DIRETO)
    # =========================================================

    if not df_final.empty:

        print("\n🔥 Contingências críticas:")
        print(df_final[df_final["fitness"] > 3].head())

        print("\n⏰ Horários mais críticos:")
        print(
            df_final.groupby("inicio")["fitness"]
            .mean()
            .sort_values(ascending=False)
            .head()
        )

        print("\n⚡ Ramos mais críticos:")
        print(
            df_final.groupby(["ramo_cont_from", "ramo_cont_to"])["fitness"]
            .mean()
            .sort_values(ascending=False)
            .head()
        )


# =========================================================
# new otimization model with streamlit interface and more variables of decision to be tested in the future

# PVRV - 26/05/2026
simulate_IEEE30()
