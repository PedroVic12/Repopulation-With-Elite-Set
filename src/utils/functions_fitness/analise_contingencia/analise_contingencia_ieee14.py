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

def funcao_objetivo_ieee14_analise(individuo, setupobj, _debug=False):
    """
    Função objetivo para análise de contingência do sistema IEEE 14 barras.
    """
    rede = RedeEletricaPandaPower("14", debug=_debug)
    rede.pesos["tensao"] = {"min": 100, "max": 100}
    rede.pesos["loading_linhas"] = 100
    rede.pesos["loading_trafos"] = 100
    
    # Usar uma cópia para evitar modificar o DataFrame global
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
    
    fitness_final, _ = analise_contigencias_SEP(
        rede=rede,
        setupobj=setupobj,
        matriz_cenarios=matriz_cenarios,
        agendamento_df=agendamento_df,
        contingencia_df=contingencia_df_ieee14
    )
    
    # A função deve retornar uma tupla para ser compatível com o framework DEAP
    return fitness_final,

# --- FUNÇÃO DE SIMULAÇÃO PARA TESTE ---
def run_simulation_test():
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
    fitness, = funcao_objetivo_ieee14_analise(
        individuo=horarios_teste,
        setupobj=setup_obj,
        _debug=False
    )

    print(f"\n--- Resultados da Simulação de Teste ---")
    print(f"Fitness final calculado: {fitness}")
    print(f"Execuções da função objetivo (cálculos caros): {setup_obj.objectiveruns}")
    print(f"Leituras da tabela hash (cache hits): {setup_obj.hashtablereads}")
    print("----------------------------------------")
    return fitness

if __name__ == "__main__":
    run_simulation_test()
