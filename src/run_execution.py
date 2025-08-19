# -*- coding: utf-8 -*-
"""
Execução única do framework RCE
PVRV - 18/06/2025
"""

# Imports principais do framework
from AlgEvolutivoRCE_backup.Setup import Setup
from AlgEvolutivoRCE_backup.alg_evolutivo_rce import AlgoritimoEvolutivoRCE

# Utils
from config_backup import FOLDER_NAME, entrada_de_dados, format_elapsed_time, load_many_executions
from utils.functions_fitness.functions_benchmarking import rastrigin
from utils.functions_fitness.function_IEEE_14_contigencias import funcao_objetivo_IEEE14

# Bibliotecas padrão
import json
import pathlib
import pandas as pd
import os
from datetime import datetime


BASE_DIR = pathlib.Path(__file__).resolve().parent


def load_params(file_path):
    """Carrega parâmetros de um arquivo JSON."""
    with open(file_path, "r") as file:
        return json.load(file)


def convert_values_to_int(params):
    """Converte valores dos parâmetros para int ou float, se aplicável."""
    float_keys = {"MUTACAO", "CROSSOVER", "PORCENTAGEM"}
    for key, value in params.items():
        try:
            if key.upper() in float_keys:
                params[key] = float(value)
            else:
                params[key] = int(float(value))
        except Exception:
            pass
    return params


def run_framework_many_executions(function_bechmarking=False, config_num=1, exec_num=1):
    """Função principal para executar o framework com múltiplas execuções."""

    # 1. Carrega parâmetros
    params = load_params(f"{BASE_DIR}/params.json")
    options = load_params(f"{BASE_DIR}/options.json")
    params = convert_values_to_int(params)

    print(params)
    print(f"\n\nIniciando execução com parâmetros: {options}")

    # 2. Define função objetivo
    fitness_func = funcao_objetivo_IEEE14 if not function_bechmarking else rastrigin

    # 3. Instancia Setup
    setup = Setup(
        params,
        fitness_function=fitness_func,
        tamanho_hash=(
            entrada_de_dados()["num_contingencias"]
            * entrada_de_dados()["num_carregamentos"]
            * (2 ** entrada_de_dados()["num_desligamentos"])
        )
    )
    print("Classe Setup iniciada")

    # 4. Consulta hash_table se existir
    if os.path.exists("hash_table.xlsx"):
        try:
            hash_excel = pd.read_excel("hash_table.xlsx")
            if not hash_excel.empty:
                setup.tabela_hash = hash_excel['Fitness'].to_dict()
                print("Tabela hash carregada com sucesso!")
        except Exception as e:
            print(f"Erro ao carregar hash_table.xlsx: {e}")

    # 5. Executa algoritmo
    alg = AlgoritimoEvolutivoRCE(setup, DEBUG=False)
    print("Algoritmo Evolutivo iniciado.")

    # Loop principal do Algoritmo Evolutivo
    pop_with_repopulation, logbook_with_repopulation, best_variables = alg.run(RCE=True)
    print("\n\nEvolução concluída  - 100%")
    print(f"Best variables", best_variables)
    
    
    # # Resultados
    #x, y, z, fig = alg.dashboard.visualize(
    #    logbook_with_repopulation, pop_with_repopulation,
    #    config_num=config_num, execution_num=exec_num
    #)

    all_results = {}
    load_many_executions(options, setup, alg, config_num=config_num, exec_num=exec_num, all_configs_results=all_results)

    # 6. Salva resultados
    if all_results:
        df = pd.DataFrame([
            {**res, "config_num": cfg}
            for cfg, lista in all_results.items()
            for res in lista
        ])
        output_path = f"{FOLDER_NAME}/results_consolidados.xlsx"
        df.to_excel(output_path, sheet_name="Consolidated Results", index=False)
        print(f"Resultados consolidados salvos em {output_path}")
    else:
        print("Nenhum resultado para consolidar.")


if __name__ == "__main__":
    print("Starting execution with benchmark function...")
    run_framework_many_executions(function_bechmarking=False)
