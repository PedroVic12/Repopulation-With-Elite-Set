
# File: Repopulation-With-Elite-Set/src/utils/functions_fitness/function_IEEE_14_contigencias.py
import os
import sys
import pandas as pd
import pathlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

BASE_DIR = pathlib.Path(__file__).resolve().parent
HASH_TABLE_PATH = BASE_DIR.parent.parent / "output" / "hash_table.xlsx"

from RedeEletrica.rede_eletrica import RedeEletricaPandaPower
from AlgEvolutivoRCE.Setup import Setup
#=====================================================
# Tabela agendamentos em xlsx hardcoded
agendamento_df = pd.DataFrame([
    {"ramo": [1, 4], "inicio": "14:00", "duracao": 6 ,"prioridade": 4},
    {"ramo": [1, 3], "inicio": "15:00", "duracao": 5, "prioridade": 1},
    {"ramo": [3, 6], "inicio": "14:00", "duracao": 6, "prioridade": 1},
    {"ramo": [11, 12], "inicio": "18:00", "duracao": 6, "prioridade": 1},
    {"ramo": [9, 10], "inicio": "15:00", "duracao": 4, "prioridade": 1}
])

contingencia_df = pd.DataFrame([
        {"contingencia":1,  "from":2 , "to": 3},
        {"contingencia":2,  "from":5 , "to": 12},
        {"contingencia":3,  "from":12 , "to": 13},
])

# Converter horários de início para horas do dia
agendamento_df['inicio'] = agendamento_df['inicio'].apply(lambda x: int(x.split(':')[0]))

# Calcular horário de término em horas do dia
agendamento_df['final'] = agendamento_df.apply(lambda row: (row['inicio'] + row['duracao']) % 24, axis=1)
    
def hashtablesize():
    contingencias = contingencia_df['contingencia'].to_list()
    num_carregamentos = 3
    num_contingencias = len(contingencias) # 3
    num_desligamentos = len(agendamento_df) # 5
    
    size = num_contingencias* num_carregamentos*(2**num_desligamentos)
    #print("Hash table INICIAL criada de tamanho = ", size)
    return size


def funcao_objetivo_IEEE14(individuo, setupobj, _debug = False):
    
    """    
    # Esta função avalia o agendamento de desligamentos e contingências na rede elétrica, calculando o fitness baseado em violações de tensões e carregamentos.
    # A função utiliza a classe RedeEletricaPandaPower para simular o fluxo de carga e calcular as violações com base em um agendamento fornecido.
    # a função retorna o fitness total do agendamento, que é a soma das violações de todos os cenários avaliados.
    ## A função também utiliza uma tabela hash para armazenar os resultados de cenários já avaliados, evitando cálculos redundantes.
    # 


    Returns:
        float/int: fitness_result
    """
    # Função objetivo para o problema de otimização da rede elétrica IEEE 14 barras

    #! 1) Criar a rede elétrica IEEE 14 barras, Inicializar a classe com a rede e carrega a tabela de agendamento
    rede = RedeEletricaPandaPower("14", debug=_debug)


    #! Colocando pesos como input do usuario e os dados de entrada do agendamento
    rede.pesos["tensao"] = {"min": 100, "max": 100}
    rede.pesos["loading_linhas"] = 100
    rede.pesos["loading_trafos"] = 100


    # Calcular a duração total do agendamento em horas
    duracao_total_agendamento = (agendamento_df['inicio']+agendamento_df['duracao']).max()
    rede.validar_dados(agendamento_df, contingencia_df)

    # passando a variavel de decisão na função objetivo
    agendamento_df["inicio"] = individuo

    violacoes_total = []
    violacoes_hash_table = {}

    # Generate hash key values
    #! Variáveis de Calculo  de otimização para achar o fitness de cada cenario
    contingencias = contingencia_df['contingencia'].to_list()
    num_carregamentos = 3
    num_contingencias = len(contingencias) # 3
    num_desligamentos = len(agendamento_df) # 5
    
    #bd_aptidao_cenario = [-1.0]*(num_contingencias* num_carregamentos*(2**num_desligamentos) )

    #=====================================================
    # 2)  Avaliar cenários e criar matriz de cenários
    matriz_cenarios = rede.avalia_cenarios(
            horas = duracao_total_agendamento,
            hora_inicio=agendamento_df['inicio'],
            duracao=agendamento_df['duracao'],
            ls=0, le=8,
            ms=8, me=18,
            hs=18, he=24
        )

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
                hash_key = rede.hashtableindex(perfil, num_carregamentos, contingencia_atual, num_contingencias, estado_ramos)
                
                #! RZ_01jun2025 - verifica se o cenário já foi calculado na tabela hash
                if setupobj.tabela_hash[hash_key] < 0.0:
                    #!DEBUG = Cenario 288 calculado, ai calcula o cenario 235 e da erro (porque ainda nao existe!)
                    
                    #! Simulação e modelagem usando pandapower com metodos da RedeEleticaPandawer em subtorinas
                    #5)  Ligar todos os ramos antes de aplicar mudanças
                    rede.religar_todos_os_ramos_agendamento()

                    # 6) Fazendo os deligamentos com base na tabela em .xlsx e nos cenários calculados
                    rede.desligar_elementos_agendamento(estado_ramos)

                    # 7) Identifica ramos afetados pela contingência
                    ramo_contingencia = list(contingencia_df.loc[contingencia_df['contingencia'] == contingencia_atual, ['from', 'to']].values[0])
                    rede.log(f"\n{contingencia_atual}) Ramo da contingencia = { ramo_contingencia}\n")

                    # 8) Desliga os ramos afetados
                    rede.desligar_contingencia(ramo_contingencia)

                    # 9) Executar fluxo de potência para o cenário com contingência
                    if rede.executar_fluxo_de_potencia():                            
                            # 10) Calcular violações com pesos e armazenar os resultados
                            fitness, violacoes_df = rede.calcular_violacoes_fitness()

                    else:
                            fitness = rede.pesos["demanda"] # penalidade com valor default de 99



                    # 11) Store violation in the hash table
                    #!debug = Ele esta salvando primeiro cenario, o hashtable existe mas o proximo cenario ainda nao foi calculado... 
                    setupobj.tabela_hash[hash_key] = fitness
                    
                    # incrementa contador de execuções da função objetivo
                    setupobj.objectiveruns += 1


                #! 12) Retorna o valores calculados de fluxo de potencia na variavel fitness
                else:
                    fitness = setupobj.tabela_hash[hash_key]
                    #print("Fitness do cenario = ", fitness)
                    setupobj.hashtablereads += 1

                violacoes_total.append(fitness)

            #! Ver apenas o true in service de barras e transformadores
            #rede.show_status()

        # 12) Calcular fitness final com somatorio das vioações com pesos de todos os cenarios
        fitness_final = sum(violacoes_total)
        rede.log(f"\nFitness do agendamento = {fitness_final:.2f}\n", level = "success")

        return fitness_final

    except Exception as e:
        print(f"\nErro ao calcular a função objetivo: {e}")



def simulate_IEEE_14_cenario():
    
    
    horarios = [14,16,18,20,25]
    
    params_json = {
    "NUM_GENERATIONS": 40,
    "CROSSOVER": 0.95,
    "MUTACAO": 0.25,
    "POP_SIZE": 5,
    "IND_SIZE": 5,
    "RCE_REPOPULATION_GENERATIONS": 50,
    "NUM_VAR_DIFERENTES": 1,
    "PORCENTAGEM": 0.2,
    "DELTA_MIN": 2,
    "ARRAY_VAR": [
        14,
        15,
        14,
        18,
        15
    ],
    "LIMITE_VAR": [
        0,
        31
    ]
}
    
    setup_obj = Setup(
            params = params_json,
            fitness_function = funcao_objetivo_IEEE14,
            tamanho_hash = hashtablesize()
        )
    
    fitness = funcao_objetivo_IEEE14(
        individuo=horarios,
        setupobj= setup_obj,
        _debug = True

    )
    
    return fitness
    
#simulate_IEEE_14_cenario()    
    