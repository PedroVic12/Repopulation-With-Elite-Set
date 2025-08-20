# -*- coding: utf-8 -*-
"""
Execução única do framework RCE com Redis
PVRV - 18/06/2025
"""

# Imports principais do framework
from rce_framework.domain.models.AG.alg_evolutivo_rce import AlgoritimoEvolutivoRCE
from rce_framework.domain.models.AG.Setup import Setup

# Utils
from config.config import FOLDER_NAME, entrada_de_dados, format_elapsed_time
from utils.functions_fitness.functions_benchmarking import rastrigin
from utils.functions_fitness.function_IEEE_14_contigencias import funcao_objetivo_IEEE14

# Bibliotecas padrão
import json
import pathlib
import pandas as pd
import os
from datetime import datetime
from itertools import product

# Redis
from redis_controller import RedisController

BASE_DIR = pathlib.Path(__file__).resolve().parent


# ---------------- FUNÇÕES AUXILIARES ----------------

def load_params(file_path):
    """Carrega parâmetros de um arquivo JSON."""
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"[WARN] {file_path} não encontrado, ignorando.")
        return {}


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


def get_options():
    """Carrega configs do Redis ou options.json"""
    redis_ctrl = RedisController()
    redis_key = "rce:configs"

    # 1. Tenta carregar do Redis
    options = redis_ctrl.get_value(redis_key)
    if options:
        print("[INFO] Configurações carregadas do Redis.")
        return options

    # 2. Se não houver no Redis, carrega options.json
    options_path = f"{BASE_DIR}/options.json"
    options = load_params(options_path)
    if options:
        print("[INFO] Configurações carregadas de options.json.")
        # Salva no Redis para próximas execuções
        redis_ctrl.set_value(redis_key, options)
        return options

    # 3. Default vazio
    print("[WARN] Nenhuma configuração encontrada.")
    return {}


# ---------------- FUNÇÃO PRINCIPAL ----------------

def run_framework_many_executions(function_bechmarking=False):
    """Função principal para executar o framework com múltiplas execuções."""
    
    if function_bechmarking:
        print("Starting execution with benchmark function...")


    # 1. Carrega parâmetros base e opções
    params_base = load_params(f"{BASE_DIR}/params.json")
    params_base = convert_values_to_int(params_base)

    options = get_options()
    repeticoes = options.get("repeticoes_por_config", 1)

    # 2. Descobre variações
    varying_keys = [k for k in options if isinstance(options[k], list) and len(options[k]) > 0]
    varying_values = [options[k] for k in varying_keys]

    # 3. Gera todas as combinações de parâmetros
    combinations = [dict(zip(varying_keys, vals)) for vals in product(*varying_values)] if varying_keys else [{}]

    print(f"Total de configurações únicas: {len(combinations)}")
    print(f"Execuções por configuração: {repeticoes}")

    all_results = {}
    config_num = 1

    for combo in combinations:
        for exec_num in range(1, repeticoes + 1):
            # Monta params para esta execução
            params = params_base.copy()
            params.update(combo)
            params = convert_values_to_int(params)

            print(f"\n\nIniciando execução {exec_num}/{repeticoes} da configuração {config_num}: {params}")

            # Define função objetivo
            fitness_func = funcao_objetivo_IEEE14 if not function_bechmarking else rastrigin

            # Instancia Setup
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

            # Consulta hash_table se existir
            if os.path.exists("hash_table.xlsx"):
                try:
                    hash_excel = pd.read_excel("hash_table.xlsx")
                    if not hash_excel.empty:
                        setup.tabela_hash = hash_excel['Fitness'].to_dict()
                        print("Tabela hash carregada com sucesso!")
                except Exception as e:
                    print(f"Erro ao carregar hash_table.xlsx: {e}")

            # Executa algoritmo
            alg = AlgoritimoEvolutivoRCE(setup, DEBUG=False)
            print("Algoritmo Evolutivo iniciado.")
            pop_with_repopulation, logbook_with_repopulation, best_variables = alg.run(RCE=True)
            print("\n\nEvolução concluída  - 100%")
            print(f"Best variables", best_variables)

            # Salva resultados individuais
            result = {
                "config_num": config_num,
                "exec_num": exec_num,
                "params": params,
                "best_variables": best_variables,
            }
            all_results.setdefault(config_num, []).append(result)

        config_num += 1

    # 6. Salva resultados consolidados
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


# ---------------- MAIN ----------------
if __name__ == "__main__":
    run_framework_many_executions(function_bechmarking=False)
