# File: Repopulation-With-Elite-Set/src/utils/functions_fitness/
import os
import sys
import pandas as pd
import pathlib


def analise_contigencias_SEP(
    rede, setupobj, matriz_cenarios, agendamento_df, contingencia_df
):
    """
    Executa a análise de contingências para um determinado agendamento de manutenção.

    Args:
        rede: Objeto da rede elétrica.
        setupobj: Objeto de setup do algoritmo genético.
        matriz_cenarios: Matriz com os cenários de operação (perfil de carga e estado dos ramos).
        agendamento_df: DataFrame com o agendamento de manutenção.
        contingencia_df: DataFrame com a lista de contingências a serem avaliadas.

    Returns:
        tuple: Uma tupla contendo o fitness final (float) e um dicionário com os ramos de contingência avaliados.
    """
    contingencias = contingencia_df["contingencia"].to_list()
    num_carregamentos = 3
    num_contingencias = len(contingencias)
    num_desligamentos = len(agendamento_df)
    violacoes_total = []

    contigencias_selecionadas = {"ramos": [], "contingencia": []}

    try:
        for cenario in matriz_cenarios:
            perfil = cenario[0]
            estado_ramos = cenario[1:]
            rede.ajustar_cargas(perfil)

            for contingencia_atual in range(1, num_contingencias + 1):
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

                    if ramo_contingencia not in contigencias_selecionadas["ramos"]:
                        contigencias_selecionadas["ramos"].append(ramo_contingencia)
                        contigencias_selecionadas["contingencia"].append(
                            contingencia_atual
                        )

                    if rede.executar_fluxo_de_potencia():
                        fitness, _ = rede.calcular_violacoes_fitness()
                    else:
                        fitness = rede.pesos.get(
                            "demanda", 99
                        )  # Usar .get para segurança

                    setupobj.tabela_hash[hash_key] = fitness
                    setupobj.objectiveruns += 1
                else:
                    fitness = setupobj.tabela_hash[hash_key]
                    setupobj.hashtablereads += 1

                violacoes_total.append(fitness)

        fitness_final = sum(violacoes_total)
        return fitness_final, contigencias_selecionadas

    except Exception as e:
        print(f"\nErro durante a análise de contingências: {e}")
        return float("inf"), {}


def custom_log(message, level="info", *args, **kwargs):
    if isinstance(level, list):
        level_str = str(level)
    else:
        level_str = level.upper()
    with open("logs_rede_IEEE_118.txt", "a") as f:
        f.write(f"[{level_str}] {message}\n")

    #! Keep original console output
    # print(f"[{level_str}] {message}")


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from RedeEletrica.rede_eletrica import RedeEletricaPandaPower
from AlgEvolutivoRCE.Setup import Setup

BASE_DIR = pathlib.Path(__file__).resolve().parent
HASH_TABLE_PATH = BASE_DIR.parent.parent / "output" / "hash_table.xlsx"

#! Tabela agendamentos em xlsx hardcoded
agendamento_df = pd.DataFrame(
    [
        {"ramo": [7, 29], "inicio": "20:00", "duracao": 6, "prioridade": 4},
        {"ramo": [44, 48], "inicio": "18:00", "duracao": 5, "prioridade": 1},
        {"ramo": [16, 112], "inicio": "21:00", "duracao": 6, "prioridade": 1},
        {
            "ramo": [61, 65],
            "inicio": "27:00",
            "duracao": 6,
            "prioridade": 1,
        },  # dia seguinte
        {"ramo": [75, 117], "inicio": "01:00", "duracao": 4, "prioridade": 1},
        {"ramo": [46, 68], "inicio": "21:00", "duracao": 5, "prioridade": 1},
        {"ramo": [84, 88], "inicio": "20:00", "duracao": 6, "prioridade": 1},
        {"ramo": [18, 33], "inicio": "14:00", "duracao": 5, "prioridade": 1},
        {"ramo": [3, 10], "inicio": "19:00", "duracao": 4, "prioridade": 1},
        {"ramo": [11, 15], "inicio": "20:00", "duracao": 5, "prioridade": 1},
    ]
)

contingencia_df = pd.DataFrame(
    [
        {"contingencia": 1, "from": 48, "to": 49},
        {"contingencia": 2, "from": 10, "to": 11},
        {"contingencia": 3, "from": 16, "to": 17},
    ]
)

# Converter horários de início para horas do dia
agendamento_df["inicio"] = agendamento_df["inicio"].apply(
    lambda x: int(x.split(":")[0])
)

# Calcular horário de término em horas do dia
agendamento_df["final"] = agendamento_df.apply(
    lambda row: (row["inicio"] + row["duracao"]) % 24, axis=1
)


def hashtablesize():
    contingencias = contingencia_df["contingencia"].to_list()
    num_carregamentos = 3
    num_contingencias = len(contingencias)  # 3
    num_desligamentos = len(agendamento_df)  # 10

    size = num_contingencias * num_carregamentos * (2**num_desligamentos)
    # print("Hash table INICIAL criada de tamanho = ", size)
    return size


def calcular_fitness_detalhado_IEEE118(individuo, setupobj, _debug=False):
    """
    Calcula o fitness e retorna um dicionário detalhado com DataFrames.
    """
    #! 1) Criar a rede elétrica IEEE 118 barras, Inicializar a classe com a rede e carrega a tabela de agendamento
    rede = RedeEletricaPandaPower("118", debug=False)
    rede.log = custom_log
    # rede.log = custom_log(
    #    "Função de fitness personalizada para IEEE 118: Iniciando cálculo detalhado.",
    #    level="info",
    # )
    rede.log("Iniciando simulação de teste para IEEE 118", level="info")

    #! Colocando pesos como input do usuario e os dados de entrada do agendamento
    rede.pesos["tensao"] = {"min": 100, "max": 100}
    rede.pesos["loading_linhas"] = 100
    rede.pesos["loading_trafos"] = 100

    # Copiar o DataFrame de agendamento para evitar modificações no original global
    agendamento_local_df = agendamento_df.copy()

    # Calcular a duração total do agendamento em horas
    duracao_total_agendamento = (
        agendamento_local_df["inicio"] + agendamento_local_df["duracao"]
    ).max()
    rede.validar_dados(agendamento_local_df, contingencia_df)

    # passando a variavel de decisão na função objetivo
    agendamento_local_df["inicio"] = individuo

    # =====================================================

    # 2)  Avaliar cenários e criar matriz de cenários
    matriz_cenarios = rede.avalia_cenarios(
        horas=duracao_total_agendamento,
        hora_inicio=agendamento_local_df["inicio"],
        duracao=agendamento_local_df["duracao"],
        ls=0,
        le=8,
        ms=8,
        me=18,
        hs=18,
        he=24,
    )

    #! Calculo  de otimização para achar o fitness de cada cenario
    violacoes_total = []
    violacoes_hash_table = {}

    # Generate hash key (teste 01)
    contingencias = contingencia_df["contingencia"].to_list()
    num_carregamentos = 3
    num_contingencias = len(contingencias)
    num_desligamentos = len(agendamento_local_df)

    contigencias_selecionadas = {"ramos": [], "contingencia": []}

    try:
        # 3) Processar cada cenário da matriz de cenários
        fitness_final, contigencias_selecionadas = analise_contigencias_SEP(
            rede=rede,
            setupobj=setupobj,
            matriz_cenarios=matriz_cenarios,
            agendamento_df=agendamento_local_df,
            contingencia_df=contingencia_df,
        )

        rede.log(f"\nFitness do agendamento = {fitness_final:.2f}\n", level="success")

        # Criar DataFrames para o retorno
        fitness_df = pd.DataFrame([{"fitness_final": fitness_final}])
        melhores_variaveis_df = pd.DataFrame(individuo, columns=["inicio_otimizado"])
        ramos_selecionados_df = agendamento_local_df.copy()
        contingencias_avaliadas_df = pd.DataFrame(contigencias_selecionadas)

        return {
            "fitness": fitness_df,
            "melhores_variaveis": melhores_variaveis_df,
            "ramos_selecionados": ramos_selecionados_df,
            "contingencias": contingencias_avaliadas_df,
        }

    except Exception as e:
        print(f"\nErro ao calcular a função objetivo: {e}")
        return None


def funcao_objetivo_IEEE118(individuo, setupobj, _debug=False):
    """
    Função objetivo wrapper que retorna apenas o valor de fitness para o otimizador.
    """
    resultados_detalhados = calcular_fitness_detalhado_IEEE118(
        individuo, setupobj, _debug
    )

    if resultados_detalhados:
        fitness_final = resultados_detalhados["fitness"]["fitness_final"].iloc[0]
        return (fitness_final,)
    else:
        # Retorna um valor de fitness muito alto em caso de erro
        return (99,)


# Dicionário de parâmetros para a função de teste
params_json_teste = {
    "NUM_GENERATIONS": 10,
    "CROSSOVER": 0.9,
    "MUTACAO": 0.1,
    "POP_SIZE": 4,
    "IND_SIZE": 10,
    "RCE_REPOPULATION_GENERATIONS": 5,
    "NUM_VAR_DIFERENTES": 1,
    "PORCENTAGEM": 0.2,
    "DELTA_MIN": 2,
    "ARRAY_VAR": [15, 15, 10, 21, 16, 13, 10, 14, 17, 18],
    "LIMITE_VAR": [0, 31],
}


def run_fitness_function():
    print("--- Iniciando Simulação de Teste para IEEE 118 ---")

    tabela_hash = hashtablesize()

    setup = Setup(
        params=params_json_teste,
        fitness_function=funcao_objetivo_IEEE118,
        tamanho_hash=tabela_hash,
    )

    # Testando a função de cálculo detalhado diretamente
    resultados_detalhados = calcular_fitness_detalhado_IEEE118(
        individuo=[
            24,
            3,
            24,
            26,
            1,
            24,
            24,
            27,
            24,
            24,
        ],  # agendamento ótimo em Zanghi(2016)
        setupobj=setup,
        _debug=False,
    )

    if resultados_detalhados:
        print("\n--- Resultados Detalhados da Simulação ---")

        print(resultados_detalhados["fitness"])

        print("\nRamos Selecionados para Manutenção (Agendamento Otimizado):")
        print(resultados_detalhados["ramos_selecionados"])

        print("\nContingências Avaliadas:")
        print("Despacho de cargas: 1) Leve | 2) Média | 3) pesada")
        print(resultados_detalhados["contingencias"])

        fitness = resultados_detalhados["fitness"]["fitness_final"].iloc[0]
        print("\nTamanho tabela hash = ", setup.tamanho_hash)
        print("Fitness calculado = ", fitness)
    else:
        print("A execução da função de fitness falhou.")


# run_fitness_function()
