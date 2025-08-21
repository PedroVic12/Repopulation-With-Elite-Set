# -*- coding: utf-8 -*-
"""
Execução de UMA ÚNICA configuração do framework RCE.
Este script é chamado pelo laucher.py para cada configuração a ser executada.
"""

# Imports principais do framework
from AlgEvolutivoRCE_backup.Setup import Setup
from AlgEvolutivoRCE_backup.alg_evolutivo_rce import AlgoritimoEvolutivoRCE
from RedeEletrica_backup.rede_eletrica import RedeEletricaPandaPower

# Utils
from config_backup import FOLDER_NAME, entrada_de_dados, format_elapsed_time, load_many_executions
from utils.functions_fitness.functions_benchmarking import rastrigin
from utils.functions_fitness.function_IEEE_14_contigencias import funcao_objetivo_IEEE14

# Bibliotecas padrão
import json
import pathlib
import pandas as pd
import numpy as np
import os
import argparse
from datetime import datetime

BASE_DIR = pathlib.Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"


def load_params(file_path):
    """Carrega parâmetros de um arquivo JSON."""
    with open(file_path, "r") as file:
        return json.load(file)


def convert_values_to_int(params):
    """Converte valores dos parâmetros para int, float ou listas, se aplicável."""
    float_keys = {"MUTACAO", "CROSSOVER", "PORCENTAGEM"}
    list_keys = {"ARRAY_VAR", "LIMITE_VAR"}
    for key, value in params.items():
        if isinstance(value, str) and value.strip().startswith('['):
            try:
                params[key] = json.loads(value)
                continue
            except json.JSONDecodeError:
                pass
        if key.upper() in list_keys or isinstance(value, (list, dict)):
            continue
        try:
            if key.upper() in float_keys:
                params[key] = float(value)
            else:
                params[key] = int(float(value))
        except (ValueError, TypeError):
            pass
    return params


def run_single_execution(function_bechmarking=False):
    """
    Executa uma única configuração, lendo os parâmetros de `params.json`.
    Os resultados são salvos no diretório de saída principal.
    """
    print("--- Iniciando execução de configuração única ---")

    parser = argparse.ArgumentParser()
    parser.add_argument("--config_num", default=1, type=int)
    parser.add_argument("--exec_num", default=1, type=int)
    args = parser.parse_args()
    config_num = args.config_num
    exec_num = args.exec_num

    # 1. Carrega a configuração atual que o laucher salvou
    params = load_params(BASE_DIR / "params.json")
    params = convert_values_to_int(params)

    # Garante que o diretório de saída principal exista
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Salvando resultados em: {OUTPUT_DIR}")

    # Define função objetivo
    fitness_func = funcao_objetivo_IEEE14 if not function_bechmarking else rastrigin

    # Instancia Setup
    print(f"Executando Config {config_num}, Repetição {exec_num}: {params}")
    setup = Setup(
        params,
        fitness_function=fitness_func,
        tamanho_hash=(
            entrada_de_dados()["num_contingencias"]
            * entrada_de_dados()["num_carregamentos"]
            * (2 ** entrada_de_dados()["num_desligamentos"])
        )
    )
    print("Classe Setup iniciada.")

    # Consulta hash_table se existir
    hash_table_path = BASE_DIR / "hash_table.xlsx"
    if hash_table_path.exists():
        try:
            hash_excel = pd.read_excel(hash_table_path)
            if not hash_excel.empty:
                setup.tabela_hash = hash_excel['Fitness'].to_dict()
                print("Tabela hash carregada com sucesso!")
        except Exception as e:
            print(f"Erro ao carregar {hash_table_path}: {e}")

    # Executa algoritmo
    alg = AlgoritimoEvolutivoRCE(setup, DEBUG=False)
    print("Algoritmo Evolutivo iniciado.")
    pop_with_repopulation, logbook_with_repopulation, best_individual, all_individual_values = alg.run(RCE=True)
    print("Evolução concluída.")

    # Salva resultados
    best_variables = list(best_individual)
    best_fitness = best_individual.fitness.values[0] if best_individual.fitness.valid else float('inf')
    best_gen_idx = logbook_with_repopulation.select("gen")[-1] if logbook_with_repopulation else 'N/A'

    result = {
        "config_num": config_num,
        "exec_num": exec_num,
        "params": params,
        "best_variables": best_variables,
        "best_fitness": best_fitness,
        "best_gen_idx": best_gen_idx
    }
    
    # Salva o resultado desta execução em um arquivo JSON nomeado de forma única
    # para que o consolidador possa encontrá-lo.
    result_filename = f"config_{config_num}_exec_{exec_num}_results.json"
    output_path = OUTPUT_DIR / result_filename
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
        print(f"Resultado salvo em: {output_path}")
    except Exception as e:
        print(f"Erro ao salvar resultado: {e}")

    print("--- Execução de configuração única finalizada ---")


if __name__ == "__main__":
    run_single_execution(function_bechmarking=False)