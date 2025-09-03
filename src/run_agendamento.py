# -*- coding: utf-8 -*-
"""
Execução do framework RCE configurado para o problema de agendamento,
com a lógica para gerar o resultado final detalhado.
"""
import sys
import os

# Adiciona o diretório raiz do projeto ao sys.path para permitir importações de outros módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Imports principais do framework
from AlgEvolutivoRCE_backup.Setup import Setup
from AlgEvolutivoRCE_backup.alg_evolutivo_rce import AlgoritimoEvolutivoRCE
from config_backup import FOLDER_NAME, format_elapsed_time
from database_controller import run_consolidar_resultados

# --- Importando a função objetivo de agendamento e seus dados ---
from utils.functions_fitness.analise_contingencia.analise_contingencia_ieee14 import (
    funcao_objetivo_ieee14_analise,
    agendamento_df_ieee14,
    hashtablesize_ieee14,
    calcular_fitness_detalhado_ieee14_analise
)
from utils.functions_fitness.analise_contingencia.analise_contingencia_ieee30 import (
    funcao_objetivo_ieee30_analise,
    agendamento_df_ieee30,
    hashtablesize_ieee30,
    calcular_fitness_detalhado_ieee30_analise
)
from utils.functions_fitness.analise_contingencia.analise_contingencia_ieee118 import (
    funcao_objetivo_ieee118_analise,
    agendamento_df_ieee118,
    hashtablesize_ieee118,
    calcular_fitness_detalhado_ieee118_analise
)

# Bibliotecas padrão
import json
import pathlib
import pandas as pd
import numpy as np
import os
from datetime import datetime

# --- CONFIGURAÇÃO DA EXECUÇÃO ---
BASE_DIR = pathlib.Path(__file__).resolve().parent

# Seleciona a função de agendamento para ser executada (índice 0)
ARRAY_FITNESS_FUNCTIONS = [funcao_objetivo_ieee14_analise, funcao_objetivo_ieee30_analise, funcao_objetivo_ieee118_analise]
# NUMERO_FUNCAO_OBJETIVO = 0 #! Removido para ser passado como argumento

# Mapeia as funções de cálculo de hash
HASHTABLE_SIZE_FUNCS = {
    funcao_objetivo_ieee14_analise.__name__: hashtablesize_ieee14,
    funcao_objetivo_ieee30_analise.__name__: hashtablesize_ieee30,
    funcao_objetivo_ieee118_analise.__name__: hashtablesize_ieee118,
}

# Mapeia os dataframes de agendamento
AGENDAMENTO_DFS = {
    funcao_objetivo_ieee14_analise.__name__: agendamento_df_ieee14,
    funcao_objetivo_ieee30_analise.__name__: agendamento_df_ieee30,
    funcao_objetivo_ieee118_analise.__name__: agendamento_df_ieee118,
}

# Mapeia as funções de cálculo detalhado
DETAILED_FUNCS = {
    funcao_objetivo_ieee14_analise.__name__: calcular_fitness_detalhado_ieee14_analise,
    funcao_objetivo_ieee30_analise.__name__: calcular_fitness_detalhado_ieee30_analise,
    funcao_objetivo_ieee118_analise.__name__: calcular_fitness_detalhado_ieee118_analise,
}

# Desativa o modo interativo para este script
CLI = False
DEBUG_MODE = False

# --- FUNÇÕES AUXILIARES (do run.py original) ---
def load_params(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

def convert_values_to_int(params):
    float_keys = {"MUTACAO", "CROSSOVER", "PORCENTAGEM"}
    for key, value in params.items():
        if isinstance(value, str) and value.strip().startswith('['):
            try:
                params[key] = json.loads(value)
                continue
            except json.JSONDecodeError:
                pass
        try:
            if key.upper() in float_keys:
                params[key] = float(value)
            else:
                params[key] = int(float(value))
        except (ValueError, TypeError):
            pass
    return params

# --- FUNÇÃO PRINCIPAL DE EXECUÇÃO ---
def run_agendamento_otimizado(numero_funcao_objetivo: int, config_number: int):
    fitness_func = ARRAY_FITNESS_FUNCTIONS[numero_funcao_objetivo]
    print(f"\nFunção objetivo selecionada: {fitness_func.__name__}")
    print("Esta versão esta em desenvolvimento, funciona melhor na função objetivo de IEEE 14")

    params_base = load_params(f"{BASE_DIR}/params.json")
    options = load_params(f"{BASE_DIR}/options.json")
    params_base = convert_values_to_int(params_base)

    # --- AJUSTE DINÂMICO DO TAMANHO DO INDIVÍDUO ---
    agendamento_df = AGENDAMENTO_DFS.get(fitness_func.__name__)
    if agendamento_df is not None:
        tamanho_correto_individuo = len(agendamento_df)
        print(f"[INFO] O problema {fitness_func.__name__} requer {tamanho_correto_individuo} variáveis. Ajustando IND_SIZE.")
        params_base["IND_SIZE"] = tamanho_correto_individuo
    else:
        raise ValueError(f"DataFrame de agendamento não encontrado para {fitness_func.__name__}")

    repeticoes = options.get('repeticoes_por_config', 1)
    start = datetime.now()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    main_output_dir = BASE_DIR / "output" / f"run_agendamento_{{fitness_func.__name__}}_config_{{config_number}}_{timestamp}"
    os.makedirs(main_output_dir, exist_ok=True)
    print(f"Salvando resultados em: {main_output_dir}")

    size_func = HASHTABLE_SIZE_FUNCS.get(fitness_func.__name__)
    if not size_func:
        raise ValueError(f"Função de tamanho de hash não encontrada para {fitness_func.__name__}")

    setup = Setup(
        params_base,
        fitness_function=fitness_func,
        tamanho_hash=size_func()
    )

    config_dir = main_output_dir / f"config_{{config_number}}"
    os.makedirs(config_dir, exist_ok=True)

    for exec_num in range(1, repeticoes + 1):
        print(f"\n--- Iniciando execução {exec_num}/{repeticoes} ---")
        start_exec = datetime.now()

        alg = AlgoritimoEvolutivoRCE(setup, DEBUG=DEBUG_MODE)
        pop, logbook, best_individual, all_values = alg.run(RCE=True)
        best_variables = list(best_individual)

        end_exec = datetime.now()
        elapsed_exec = end_exec - start_exec
        formatted_time_exec = format_elapsed_time(elapsed_exec)

        print("\nEvolução concluída.")
        best_solution_generation, _, _, _ = alg.dashboard.visualize(
            logbook, pop,config_num=config_number, execution_num=exec_num,
        )
        
        print(f"\nDuração desta Execução: {formatted_time_exec}")
        print(f"Tempo Total Acumulado: {format_elapsed_time(end_exec - start)}")
        print(f"Objective functions runs: {setup.objectiveruns}")
        print(f"Consultas HashTable: {setup.hashtablereads}\n")

        # --- LÓGICA PARA MONTAR O RESULTADO FINAL DETALHADO ---
        best_fitness = best_individual.fitness.values[0] if best_individual.fitness.valid else float('inf')
        
        detailed_func = DETAILED_FUNCS.get(fitness_func.__name__)
        if not detailed_func:
            raise ValueError(f"Função de cálculo detalhado não encontrada para {fitness_func.__name__}")

        final_setup = Setup(params_base, fitness_function=fitness_func, tamanho_hash=size_func())
        final_results_detailed = detailed_func(
            individuo=best_variables,
            setupobj=final_setup
        )

        ramos_dict = final_results_detailed["ramos_selecionados"].to_dict('records')
        contingencias_dict = final_results_detailed["contingencias"].to_dict('records')

        result = {
            "config_num": config_number,
            "exec_num": exec_num,
            "params": params_base,
            "best_fitness": best_fitness,
            "best_variables_horarios": best_variables,
            "agendamento_detalhado": ramos_dict,
            "contingencias_avaliadas": contingencias_dict,
            "best_gen_idx": best_solution_generation,
            "time": formatted_time_exec,
            "fitness_function": fitness_func.__name__
        }

        output_path = config_dir / f"config_{{config_number}}_exec_{{exec_num}}_results.json"
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=4, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"Erro ao salvar resultado: {e}")

    print("\nExecução finalizada.")

if __name__ == "__main__":
    for i in range(1, 3): # Loop para 2 configurações
        print(f"\n--- INICIANDO CONFIGURAÇÃO {i}/2 ---")
        
        # Roda para IEEE 14
        print("\n*** EXECUTANDO PARA IEEE 14 ***")
        run_agendamento_otimizado(numero_funcao_objetivo=0, config_number=i)

        # Roda para IEEE 30
        print("\n*** EXECUTANDO PARA IEEE 30 ***")
        run_agendamento_otimizado(numero_funcao_objetivo=1, config_number=i)

    print("\n--- TODAS AS EXECUÇÕES FORAM FINALIZADAS ---")
    print("\nIniciando consolidação de resultados...")
    try:
        run_consolidar_resultados()
        print("Consolidação de resultados concluída com sucesso.")
    except Exception as e:
        print(f"Um erro inesperado ocorreu ao tentar consolidar os resultados: {e}")
