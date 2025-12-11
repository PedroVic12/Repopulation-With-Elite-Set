import os
import sys
import pandas as pd
import pathlib
import json

# Adiciona o diretório raiz do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

# Importações dos módulos do projeto
from RedeEletrica_backup.rede_eletrica import RedeEletricaPandaPower
from AlgEvolutivoRCE_backup.Setup import Setup
from utils.functions_fitness.analise_contigencias_script import analise_contigencias_SEP

# --- DADOS DE ENTRADA PARA O CASO IEEE 14 ---
agendamento_df_ieee14 = pd.DataFrame([
    {"ramo": [1, 4], "inicio": "14:00", "duracao": 6, "prioridade": 4},
    {"ramo": [1, 3], "inicio": "15:00", "duracao": 5, "prioridade": 1},
    {"ramo": [3, 6], "inicio": "14:00", "duracao": 6, "prioridade": 1},
    {"ramo": [11, 12], "inicio": "18:00", "duracao": 6, "prioridade": 1},
    {"ramo": [9, 10], "inicio": "15:00", "duracao": 4, "prioridade": 1}
])
contingencia_df_ieee14 = pd.DataFrame([
    {"contingencia": 1, "from": 2, "to": 3},
    {"contingencia": 2, "from": 5, "to": 12},
    {"contingencia": 3, "from": 12, "to": 13},
])
agendamento_df_ieee14['inicio'] = agendamento_df_ieee14['inicio'].apply(lambda x: int(x.split(':')[0]))

def hashtablesize_ieee14():
    """Retorna o tamanho necessário para a tabela hash do caso IEEE 14."""
    num_contingencias = len(contingencia_df_ieee14)
    num_desligamentos = len(agendamento_df_ieee14)
    num_carregamentos = 3
    size = num_contingencias * num_carregamentos * (2 ** num_desligamentos)
    return size

def calcular_fitness_detalhado_ieee14_analise(individuo, setupobj, _debug=False):
    """
    Calcula o fitness e retorna um dicionário detalhado com DataFrames.
    """
    rede = RedeEletricaPandaPower("14", debug=_debug)
    rede.pesos["tensao"] = {"min": 100, "max": 100}
    rede.pesos["loading_linhas"] = 100
    rede.pesos["loading_trafos"] = 100
    
    agendamento_df = agendamento_df_ieee14.copy()
    agendamento_df["inicio"] = individuo
    
    duracao_total_agendamento = (agendamento_df['inicio'] + agendamento_df['duracao']).max()
    rede.validar_dados(agendamento_df, contingencia_df_ieee14)
    
    matriz_cenarios = rede.avalia_cenarios(
        horas=duracao_total_agendamento,
        hora_inicio=agendamento_df['inicio'],
        duracao=agendamento_df['duracao'],
        ls=0, le=8, ms=8, me=18, hs=18, he=24
    )
    
    fitness_final, contigencias_selecionadas = analise_contigencias_SEP(
        rede=rede,
        setupobj=setupobj,
        matriz_cenarios=matriz_cenarios,
        agendamento_df=agendamento_df,
        contingencia_df=contingencia_df_ieee14
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

def funcao_objetivo_ieee14_analise(individuo, setupobj, _debug=False):
    """
    Função objetivo wrapper que retorna apenas o valor de fitness para o otimizador.
    """
    resultados_detalhados = calcular_fitness_detalhado_ieee14_analise(individuo, setupobj, _debug)
    
    if resultados_detalhados:
        fitness_final = resultados_detalhados["fitness"]["fitness_final"].iloc[0]
        return fitness_final,
    else:
        # Retorna um valor de fitness muito alto em caso de erro
        return 9999999.9,

# --- FUNÇÃO DE SIMULAÇÃO PARA TESTE ---
def run_simulate():
    print("--- Iniciando Simulação de Teste para Análise de Contingência (IEEE 14) ---")
    horarios_teste = [14, 16, 18, 20, 22]
    params_json = {
        "NUM_GENERATIONS": 5, "CROSSOVER": 0.95, "MUTACAO": 0.25, "POP_SIZE": 4,
        "IND_SIZE": len(horarios_teste), "RCE_REPOPULATION_GENERATIONS": 2,
        "NUM_VAR_DIFERENTES": 1, "PORCENTAGEM": 0.2, "DELTA_MIN": 2,
        "ARRAY_VAR": horarios_teste, "LIMITE_VAR": [0, 31]
    }
    setup_obj = Setup(
        params=params_json,
        fitness_function=funcao_objetivo_ieee14_analise,
        tamanho_hash=hashtablesize_ieee14()
    )

    resultados_detalhados = calcular_fitness_detalhado_ieee14_analise(
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

run_simulate()