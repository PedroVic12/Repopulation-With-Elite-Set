# File: Repopulation-With-Elite-Set/src/utils/functions_fitness/
import os
import sys
import pandas as pd
import pathlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from models.RedeEletrica.rede_eletrica import RedeEletricaPandaPower
from models.AlgEvolutivoRCE.Setup import Setup

BASE_DIR = pathlib.Path(__file__).resolve().parent
HASH_TABLE_PATH = BASE_DIR.parent.parent / "output" / "hash_table.xlsx"

#! Tabela agendamentos em xlsx hardcoded
agendamento_df = pd.DataFrame(
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


def funcao_objetivo_IEEE30(individuo, setupobj, _debug=False):
    """
    # Esta função avalia o agendamento de desligamentos e contingências na rede elétrica, calculando o fitness baseado em violações de tensões e carregamentos.
    # A função utiliza a classe RedeEletricaPandaPower para simular o fluxo de carga e calcular as violações com base em um agendamento fornecido.
    # a função retorna o fitness total do agendamento, que é a soma das violações de todos os cenários avaliados.
    ## A função também utiliza uma tabela hash para armazenar os resultados de cenários já avaliados, evitando cálculos redundantes.
    #
    Returns:
        float/int: fitness_result
    """
    # Função objetivo para o problema de otimização da rede elétrica IEEE 30 barras

    #! 1) Criar a rede elétrica IEEE 30 barras, Inicializar a classe com a rede e carrega a tabela de agendamento
    rede = RedeEletricaPandaPower("30", debug=_debug)

    #! Colocando pesos como input do usuario e os dados de entrada do agendamento
    rede.pesos["tensao"] = {"min": 100, "max": 100}
    rede.pesos["loading_linhas"] = 100
    rede.pesos["loading_trafos"] = 100

    # Calcular a duração total do agendamento em horas
    duracao_total_agendamento = (
        agendamento_df["inicio"] + agendamento_df["duracao"]
    ).max()
    rede.validar_dados(agendamento_df, contingencia_df)

    # passando a variavel de decisão na função objetivo
    agendamento_df["inicio"] = individuo

    # =====================================================

    # 2)  Avaliar cenários e criar matriz de cenários
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

    #! Calculo  de otimização para achar o fitness de cada cenario
    violacoes_total = []

    # Generate hash key (teste 01)
    contingencias = contingencia_df["contingencia"].to_list()
    num_carregamentos = 3
    num_contingencias = len(contingencias)  # 3
    num_desligamentos = len(agendamento_df)  # 10

    try:
        # 3) Processar cada cenário da matriz de cenários
        for cenario in matriz_cenarios:
            perfil = cenario[0]
            estado_ramos = cenario[1:]

            # 4) Ajustar carregamento para o perfil do cenário
            rede.ajustar_cargas(perfil)

            # Loop through contingencies before calculating violations for the scenario
            for contingencia_atual in range(num_contingencias):
                contingencia_atual += 1

                # Uso da hash key para ja utilizar cenarios calculados
                hash_key = rede.hashtableindex(
                    perfil,
                    num_carregamentos,
                    contingencia_atual,
                    num_contingencias,
                    estado_ramos,
                )

                #! RZ_01jun2025 - verifica se o cenário já foi calculado na tabela hash
                if setupobj.tabela_hash[hash_key] < 0.0:

                    # 5)  Ligar todos os ramos antes de aplicar mudanças
                    rede.religar_todos_os_ramos_agendamento()

                    # 6) Fazendo os deligamentos com base na tabela em .xlsx e nos cenários calculados
                    rede.desligar_elementos_agendamento(estado_ramos)

                    # 7) Identifica ramos afetados pela contingência
                    ramo_contingencia = list(
                        contingencia_df.loc[
                            contingencia_df["contingencia"] == contingencia_atual,
                            ["from", "to"],
                        ].values[0]
                    )
                    rede.log(
                        f"\n{contingencia_atual}) Ramo da contingencia = { ramo_contingencia}\n"
                    )

                    # 8) Desliga os ramos afetados
                    rede.desligar_contingencia(ramo_contingencia)

                    # 9) Executar fluxo de potência para o cenário com contingência
                    if rede.executar_fluxo_de_potencia():

                        # 10) Calcular violações com pesos e armazenar os resultados
                        fitness, violacoes_df = rede.calcular_violacoes_fitness()

                    else:
                        fitness = rede.pesos[
                            "demanda"
                        ]  # penalidade com valor default de 99

                    # 11) Store violation in the hash table
                    setupobj.tabela_hash[hash_key] = fitness

                    # incrementa contador de execuções da função objetivo
                    setupobj.objectiveruns += 1

                #! 12) Retorna o valores calculados de fluxo de potencia na variavel fitness
                else:
                    fitness = setupobj.tabela_hash[hash_key]
                    if _debug:
                        print("Fitness do cenario recuperado = ", fitness)
                    setupobj.hashtablereads += 1

                violacoes_total.append(fitness)

            #! Ver apenas o true in service de barras e transformadores
            # rede.show_status()

        # 12) Calcular fitness final com somatorio das vioações com pesos de todos os cenarios
        fitness_final = sum(violacoes_total)
        rede.log(f"\nFitness do agendamento = {fitness_final:.2f}\n", level="success")
        return fitness_final

    except Exception as e:
        print(f"\nErro ao calcular a função objetivo: {e}")


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
    "LIMITE_VAR": [0, 23],
}


def simulate_IEEE_30_cenario():
    """Função de teste corrigida para validar a função objetivo."""
    print("--- Iniciando Simulação de Teste para IEEE 30 ---")

    setup = Setup(
        params=params_json_teste,
        fitness_function=funcao_objetivo_IEEE30,
        tamanho_hash=hashtablesize(),
    )

    # Chama a função objetivo passando o setup
    fitness = funcao_objetivo_IEEE30(
        individuo=params_json_teste["ARRAY_VAR"], setupobj=setup, _debug=False
    )

    print("\n--- Resultados da Simulação de Teste ---")
    print(f"Fitness final calculado: {fitness}")
    print(f"Execuções da função (cálculos caros): {setup.objectiveruns}")
    print(f"Leituras da tabela hash (cache hits): {setup.hashtablereads}")
    print("-----------------------------------------")

    return fitness


# Para rodar o teste, descomente a linha abaixo
# simulate_IEEE_30_cenario()
