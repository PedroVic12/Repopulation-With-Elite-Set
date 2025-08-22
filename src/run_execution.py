# -*- coding: utf-8 -*-
"""
Execução de UMA ÚNICA configuração do framework RCE.
Este script é chamado pelo laucher.py para cada configuração a ser executada.
Utiliza o DatabaseController para I/O de arquivos.
"""

# Imports do projeto
from AlgEvolutivoRCE_backup.Setup import Setup
from AlgEvolutivoRCE_backup.alg_evolutivo_rce import AlgoritimoEvolutivoRCE
from RedeEletrica_backup.rede_eletrica import RedeEletricaPandaPower
from config_backup import entrada_de_dados
from utils.functions_fitness.functions_benchmarking import rastrigin
from utils.functions_fitness.function_IEEE_14_contigencias import funcao_objetivo_IEEE14
from database_controller import DatabaseController
import json


# Bibliotecas padrão
import argparse
import numpy as np


def convert_values_to_int(params):
    """Helper para converter tipos de valores do JSON que podem vir como string."""
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
    Executa uma única configuração, usando o DatabaseController.
    """
    print("--- Iniciando execução de configuração única ---")
    db_controller = DatabaseController()

    parser = argparse.ArgumentParser()
    parser.add_argument("--config_num", default=1, type=int)
    parser.add_argument("--exec_num", default=1, type=int)
    args = parser.parse_args()

    # 1. Carrega a configuração via DatabaseController
    params = db_controller.get_params()
    params = convert_values_to_int(params)

    print(f"Executando Config {args.config_num}, Repetição {args.exec_num}: {params}")

    # 2. Define a função objetivo
    fitness_func = funcao_objetivo_IEEE14 if not function_bechmarking else rastrigin

    # 3. Instancia e configura o Setup
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

    # 4. Executa o algoritmo
    alg = AlgoritimoEvolutivoRCE(setup, DEBUG=False)
    print("Algoritmo Evolutivo iniciado.")
    pop, logbook, best_individual, _ = alg.run(RCE=True)
    print("Evolução concluída.")

    # Salva dados de visualização (logbook)
    viz_filename = f"config_{args.config_num}_exec_{args.exec_num}_visualization.json"
    viz_path = db_controller.output_dir / viz_filename
    try:
        # O logbook do DEAP é uma lista de dicionários, serializável para JSON
        with open(viz_path, 'w', encoding='utf-8') as f:
            json.dump(logbook, f, indent=4, ensure_ascii=False)
        print(f"Dados de visualização salvos em: {viz_path}")
    except Exception as e:
        print(f"Erro ao salvar dados de visualização: {e}")

    # 5. Coleta e salva os resultados via DatabaseController
    result = {
        "config_num": args.config_num,
        "exec_num": args.exec_num,
        "params": params,
        "best_variables": list(best_individual),
        "best_fitness": best_individual.fitness.values[0] if best_individual.fitness.valid else float('inf'),
        "best_gen_idx": logbook.select("gen")[-1] if logbook else 'N/A'
    }
    
    db_controller.save_individual_result(result)

    print("--- Execução de configuração única finalizada ---")


if __name__ == "__main__":
    run_single_execution(function_bechmarking=False)
