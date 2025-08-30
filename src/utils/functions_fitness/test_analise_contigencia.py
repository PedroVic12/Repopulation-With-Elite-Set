

import os
import sys
import pandas as pd
import pathlib

# Adiciona o diretório raiz do projeto ao sys.path para permitir importações de outros módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Importações dos módulos do projeto
from RedeEletrica_backup.rede_eletrica import RedeEletricaPandaPower
from AlgEvolutivoRCE_backup.Setup import Setup
from utils.functions_fitness.analise_contigencias_script import analise_contigencias_SEP



def analise_contigencias_SEP(rede, setupobj, matriz_cenarios , agendamento_df, contingencia_df):
    contingencias = contingencia_df['contingencia'].to_list()
    num_carregamentos = 3
    num_contingencias = len(contingencias) # 3
    num_desligamentos = len(agendamento_df) # 10
    violacoes_total = []

    size = num_contingencias* num_carregamentos*(2**num_desligamentos)
    print("Hash table INICIAL criada de tamanho = ", size)
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
                    setupobj.tabela_hash[hash_key] = fitness
                    
                    # incrementa contador de execuções da função objetivo
                    setupobj.objectiveruns += 1


                #! 12) Retorna o valores calculados de fluxo de potencia na variavel fitness
                else:
                    fitness = setupobj.tabela_hash[hash_key]
                    #print("Fitness do cenario recuperado = ", fitness)
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
        


# --- DADOS DE ENTRADA PARA O CASO IEEE 14 ---
# (Baseado em function_IEEE_14_contigencias.py)

agendamento_df = pd.DataFrame([
    {"ramo": [1, 4], "inicio": "14:00", "duracao": 6, "prioridade": 4},
    {"ramo": [1, 3], "inicio": "15:00", "duracao": 5, "prioridade": 1},
    {"ramo": [3, 6], "inicio": "14:00", "duracao": 6, "prioridade": 1},
    {"ramo": [11, 12], "inicio": "18:00", "duracao": 6, "prioridade": 1},
    {"ramo": [9, 10], "inicio": "15:00", "duracao": 4, "prioridade": 1}
])

contingencia_df = pd.DataFrame([
    {"contingencia": 1, "from": 2, "to": 3},
    {"contingencia": 2, "from": 5, "to": 12},
    {"contingencia": 3, "from": 12, "to": 13},
])

# Converte a coluna de início para horas inteiras
agendamento_df['inicio'] = agendamento_df['inicio'].apply(lambda x: int(x.split(':')[0]))

def get_info_ieee14():
    """Retorna informações sobre o tamanho do problema para o caso IEEE 14."""
    return {
        "ind_size": len(agendamento_df),
        "num_contingencias": len(contingencia_df),
        "num_carregamentos": 3
    }

info = get_info_ieee14()
size_hash = info["num_contingencias"] * info["num_carregamentos"] * (2 ** info["ind_size"])

# --- FUNÇÃO OBJETIVO REUTILIZANDO A ANÁLISE DE CONTINGÊNCIA ---

def funcao_objetivo_IEEE14_analise(individuo, setupobj, _debug=False):
    """
    Função objetivo que utiliza o algoritmo de análise de contingência (`analise_contigencias_SEP`)
    para calcular o fitness de um indivíduo (agendamento).
    """
    # 1. Inicializa a rede elétrica do caso IEEE 14
    rede = RedeEletricaPandaPower("14", debug=_debug)

    # 2. Define os pesos para o cálculo de violações
    rede.pesos["tensao"] = {"min": 100, "max": 100}
    rede.pesos["loading_linhas"] = 100
    rede.pesos["loading_trafos"] = 100

    # 3. Valida os dados de entrada
    duracao_total_agendamento = (agendamento_df['inicio'] + agendamento_df['duracao']).max()
    rede.validar_dados(agendamento_df, contingencia_df)

    # 4. Atribui o indivíduo (horários de início) ao agendamento
    agendamento_df["inicio"] = individuo

    # 5. Gera a matriz de cenários com base no agendamento
    matriz_cenarios = rede.avalia_cenarios(
        horas=duracao_total_agendamento,
        hora_inicio=agendamento_df['inicio'],
        duracao=agendamento_df['duracao'],
        ls=0, le=8,
        ms=8, me=18,
        hs=18, he=24
    )

    # 6. Executa a análise de contingência para calcular o fitness
    fitness_final = analise_contigencias_SEP(
        rede=rede,
        setupobj=setupobj,
        matriz_cenarios=matriz_cenarios,
        agendamento_df=agendamento_df,
        contingencia_df=contingencia_df
    )

    return fitness_final

# --- FUNÇÃO DE SIMULAÇÃO PARA TESTE ---

def run_simulation_test():
    """
    Executa uma simulação de teste para a função objetivo, validando a integração
    com a análise de contingência.
    """
    print("--- Iniciando Simulação de Teste para Análise de Contingência (IEEE 14) ---")

    # Horários de exemplo para o indivíduo
    horarios_teste = [14, 16, 18, 20, 22]

    # Parâmetros para o objeto Setup
    params_json = {
    "NUM_GENERATIONS": 40,
    "CROSSOVER": 0.95,
    "MUTACAO": 0.25,
    "POP_SIZE": 5,
    "IND_SIZE": len(horarios_teste),
    "RCE_REPOPULATION_GENERATIONS": 50,
    "NUM_VAR_DIFERENTES": 1,
    "PORCENTAGEM": 0.2,
    "DELTA_MIN": 2,
    "ARRAY_VAR": horarios_teste,
    
    "LIMITE_VAR": [
        0,
        31
    ]
}
    # Cria o objeto de setup
    setup_obj = Setup(
        params=params_json,
        fitness_function=funcao_objetivo_IEEE14_analise,
        tamanho_hash=size_hash
    )

    # Executa a função objetivo
    fitness = funcao_objetivo_IEEE14_analise(
        individuo=horarios_teste,
        setupobj=setup_obj,
        _debug=False  # Mude para True para ver logs detalhados
    )

    print("\n--- Resultados da Simulação de Teste ---")
    print(f"Fitness final calculado: {fitness}")
    print(f"Execuções da função objetivo (cálculos caros): {setup_obj.objectiveruns}")
    print(f"Leituras da tabela hash (cache hits): {setup_obj.hashtablereads}")
    print("----------------------------------------")

    return fitness

# --- PONTO DE ENTRADA DO SCRIPT ---
if __name__ == "__main__":
    run_simulation_test()
