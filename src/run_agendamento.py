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

# --- Importando a função objetivo de agendamento e seus dados ---
from utils.functions_fitness.test_analise_contigencia import (
    funcao_objetivo_IEEE14_analise,
    agendamento_df as agendamento_df_ieee14, # Renomeado para evitar conflitos
    hashtablesize as hashtablesize_ieee14
)

# Imports de outras funções objetivo (mantidas para referência)
from utils.functions_fitness.function_IEEE_30_otimizacao import funcao_objetivo_IEEE30, hashtablesize as hashtablesize_ieee30

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
ARRAY_FITNESS_FUNCTIONS = [funcao_objetivo_IEEE14_analise, funcao_objetivo_IEEE30]
NUMERO_FUNCAO_OBJETIVO = 1 #! 0 para a funcao_objetivo_IEEE14_analise

# Mapeia as funções de cálculo de hash
HASHTABLE_SIZE_FUNCS = {
    funcao_objetivo_IEEE14_analise.__name__: hashtablesize_ieee14,
    funcao_objetivo_IEEE30.__name__: hashtablesize_ieee30,
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
def run_agendamento_otimizado():
    fitness_func = ARRAY_FITNESS_FUNCTIONS[NUMERO_FUNCAO_OBJETIVO]
    print(f"\nFunção objetivo selecionada: {fitness_func.__name__}")
    print("Esta versão esta em desenvolvimento, funciona melhor na função objetivo de IEEE 14")

    params_base = load_params(f"{BASE_DIR}/params.json")
    options = load_params(f"{BASE_DIR}/options.json")
    params_base = convert_values_to_int(params_base)

    # --- AJUSTE DINÂMICO DO TAMANHO DO INDIVÍDUO ---
    # O tamanho do indivíduo deve ser igual ao número de agendamentos no problema.
    if fitness_func.__name__ == 'funcao_objetivo_IEEE14_analise':
        tamanho_correto_individuo = len(agendamento_df_ieee14)
        print(f"[INFO] O problema IEEE 14 requer {tamanho_correto_individuo} variáveis. Ajustando IND_SIZE.")
        params_base["IND_SIZE"] = tamanho_correto_individuo

    repeticoes = options.get('repeticoes_por_config', 1)
    start = datetime.now()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    main_output_dir = BASE_DIR / "output" / f"run_agendamento_{timestamp}"
    os.makedirs(main_output_dir, exist_ok=True)
    print(f"Salvando resultados em: {main_output_dir}")

    # Usa a função de hash correspondente
    size_func = HASHTABLE_SIZE_FUNCS.get(fitness_func.__name__)
    if not size_func:
        raise ValueError(f"Função de tamanho de hash não encontrada para {fitness_func.__name__}")

    setup = Setup(
        params_base,
        fitness_function=fitness_func,
        tamanho_hash=size_func()
    )

    config_number = 1

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
        
        # Exibe os tempos e contadores de forma clara
        print(f"\nDuração desta Execução: {formatted_time_exec}")
        print(f"Tempo Total Acumulado: {format_elapsed_time(end_exec - start)}")
        print(f"Objective functions runs: {setup.objectiveruns}")
        print(f"Consultas HashTable: {setup.hashtablereads}\n")

        # --- LÓGICA PARA MONTAR O RESULTADO FINAL DETALHADO ---
        best_fitness = best_individual.fitness.values[0] if best_individual.fitness.valid else float('inf')
        agendamento_final_otimizado = []

        # Lógica específica para a sua função
        if fitness_func.__name__ == 'funcao_objetivo_IEEE14_analise':
            for i, row in agendamento_df_ieee14.iterrows():
                agendamento_final_otimizado.append({
                    "ramo": row["ramo"],
                    "horario_inicio_otimizado": best_variables[i]
                })

        result = {
            "exec_num": exec_num,
            "params": params_base,
            "best_fitness": best_fitness,
            "best_variables_horarios": best_variables,
            "agendamento_detalhado": agendamento_final_otimizado,
            "best_gen_idx": best_solution_generation,
            "time": formatted_time_exec,
            "fitness_function": fitness_func.__name__
        }

        output_path = main_output_dir / f"exec_{exec_num}_results.json"
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=4, ensure_ascii=False, default=str)
            #print(f"Resultado salvo em: {output_path}")
        except Exception as e:
            print(f"Erro ao salvar resultado: {e}")
        
        
        config_number += 1


    print("\nExecução finalizada.")

if __name__ == "__main__":
    run_agendamento_otimizado()
