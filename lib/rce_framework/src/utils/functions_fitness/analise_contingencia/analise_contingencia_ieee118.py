import os
import sys
import pandas as pd
import pathlib
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from RedeEletrica_backup.rede_eletrica import RedeEletricaPandaPower
from AlgEvolutivoRCE_backup.Setup import Setup
from utils.functions_fitness.analise_contigencias_script import analise_contigencias_SEP

# --- DADOS DE ENTRADA PARA O CASO IEEE 118 ---
agendamento_df_ieee118 = pd.DataFrame([
    {"ramo": [7, 29], "inicio": "20:00", "duracao": 6 ,"prioridade": 4},
    {"ramo": [44, 48], "inicio": "18:00", "duracao": 5, "prioridade": 1},
    {"ramo": [16, 112], "inicio": "21:00", "duracao": 6, "prioridade": 1},
    {"ramo": [61, 65], "inicio": "27:00", "duracao": 6, "prioridade": 1},
    {"ramo": [75, 117], "inicio": "01:00", "duracao": 4, "prioridade": 1},
    {"ramo": [46, 68], "inicio": "21:00", "duracao": 5, "prioridade": 1},
    {"ramo": [84, 88], "inicio": "20:00", "duracao": 6, "prioridade": 1},
    {"ramo": [18, 33], "inicio": "14:00", "duracao": 5, "prioridade": 1},
    {"ramo": [3, 10], "inicio": "19:00", "duracao": 4, "prioridade": 1},
    {"ramo": [11, 15], "inicio": "20:00", "duracao": 5, "prioridade": 1},
])
contingencia_df_ieee118 = pd.DataFrame([
    {"contingencia":1,  "from":48 , "to": 49},
    {"contingencia":2,  "from":10 , "to": 11},
    {"contingencia":3,  "from":16 , "to": 17},
])
agendamento_df_ieee118['inicio'] = agendamento_df_ieee118['inicio'].apply(lambda x: int(x.split(':')[0]))

def hashtablesize_ieee118():
    num_contingencias = len(contingencia_df_ieee118)
    num_desligamentos = len(agendamento_df_ieee118)
    num_carregamentos = 3
    return num_contingencias * num_carregamentos * (2 ** num_desligamentos)

def calcular_fitness_detalhado_ieee118_analise(individuo, setupobj, _debug=False):
    """
    Calcula o fitness e retorna um dicionário detalhado com DataFrames.
    """
    rede = RedeEletricaPandaPower("118", debug=_debug)
    rede.pesos.update({"tensao": {"min": 100, "max": 100}, "loading_linhas": 100, "loading_trafos": 100})
    
    agendamento_df = agendamento_df_ieee118.copy()
    agendamento_df["inicio"] = individuo
    
    duracao_total_agendamento = (agendamento_df['inicio'] + agendamento_df['duracao']).max()
    rede.validar_dados(agendamento_df, contingencia_df_ieee118)
    
    matriz_cenarios = rede.avalia_cenarios(
        horas=duracao_total_agendamento,
        hora_inicio=agendamento_df['inicio'],
        duracao=agendamento_df['duracao'],
        ls=0, le=8, ms=8, me=18, hs=18, he=24
    )
    
    fitness_final, contigencias_selecionadas = analise_contigencias_SEP(
        rede=rede, setupobj=setupobj, matriz_cenarios=matriz_cenarios,
        agendamento_df=agendamento_df, contingencia_df=contingencia_df_ieee118
    )

    # Criar DataFrames para o retorno
    fitness_df = pd.DataFrame([{'fitness_final': fitness_final}])
    melhores_variaveis_df = pd.DataFrame(individuo, columns=['inicio_otimizado'])
    ramos_selecionados_df = agendamento_df
    contingencias_avaliadas_df = pd.DataFrame(contigencias_selecionadas)

    return {
        "fitness": fitness_df,
        "melhores_variaveis": melhores_variaveis_df,
        "ramos_selecionados": ramos_selecionados_df,
        "contingencias": contingencias_avaliadas_df
    }

def funcao_objetivo_ieee118_analise(individuo, setupobj, _debug=False):
    """
    Função objetivo wrapper que retorna apenas o valor de fitness para o otimizador.
    """
    resultados_detalhados = calcular_fitness_detalhado_ieee118_analise(individuo, setupobj, _debug)
    
    if resultados_detalhados:
        fitness_final = resultados_detalhados["fitness"]["fitness_final"].iloc[0]
        return fitness_final,
    else:
        return 9999999.9,

def run_simulate():
    print("--- Iniciando Simulação de Teste para Análise de Contingência (IEEE 118) ---")
    horarios_teste = [24,3,24,26,1,24,24,27,24,24]
    params = {
        "IND_SIZE": len(horarios_teste), "LIMITE_VAR": [0, 31],
        "NUM_GENERATIONS": 5, "POP_SIZE": 4, "CROSSOVER": 0.9, "MUTACAO": 0.1,
        "RCE_REPOPULATION_GENERATIONS": 5
    }
    setup_obj = Setup(params=params, fitness_function=funcao_objetivo_ieee118_analise, tamanho_hash=hashtablesize_ieee118())
    
    resultados_detalhados = calcular_fitness_detalhado_ieee118_analise(
        individuo=horarios_teste,
        setupobj=setup_obj,
        _debug=False
    )

    if resultados_detalhados:
        print("\n--- Resultados Detalhados da Simulação ---")
        
        print("\nFitness Final:")
        print(resultados_detalhados["fitness"])
        
        print("\nVariáveis de Decisão (Indivíduo):")
        print(resultados_detalhados["melhores_variaveis"])
        
        print("\nRamos Selecionados para Manutenção (Agendamento Otimizado):")
        print(resultados_detalhados["ramos_selecionados"])
        
        print("\nContingências Avaliadas:")
        print(resultados_detalhados["contingencias"])

        fitness = resultados_detalhados["fitness"]["fitness_final"].iloc[0]
        print(f"\nFitness calculado = {fitness}")
    else:
        print("A execução da função de fitness falhou.")

if __name__ == "__main__":
    run_simulate()