# -*- coding: utf-8 -*-
"""
Execução do framework RCE com configuração de várias execuções e variações de parâmetros.
PVRV - 20/08/2025
RZ - 16/10/2025 - resolvendo chamada a diversas funções objetivo
"""

# Imports principais do framework
from models.AlgEvolutivoRCE.Setup import Setup
from models.AlgEvolutivoRCE.alg_evolutivo_rce import AlgoritimoEvolutivoRCE

# Utils - Trazer esses codigos para esse unico arquivo
from config import FOLDER_NAME, format_elapsed_time

#! Importando a minha função objetivo dentro do projeto
from utils.functions_fitness.functions_benchmarking import rastrigin

from utils.functions_fitness.function_IEEE_14_contigencias import (
    funcao_objetivo_IEEE14,
    HASH_TABLE_PATH as HASH_TABLE_PATH_IEEE14,
    hashtablesize as hashtablesize_IEEE14,
)
from utils.functions_fitness.function_IEEE_30_otimizacao import (
    funcao_objetivo_IEEE30,
    HASH_TABLE_PATH as HASH_TABLE_PATH_IEEE30,
    hashtablesize as hashtablesize_IEEE30,
)
from utils.functions_fitness.function_IEEE_57_otimizacao import (
    funcao_objetivo_IEEE57,
    HASH_TABLE_PATH as HASH_TABLE_PATH_IEEE57,
    hashtablesize as hashtablesize_IEEE57,
)

# from utils.functions_fitness.function_SIN_45_otimizacao import funcao_objetivo_SIN45, hashtablesize_sin45
from utils.functions_fitness.func_objetivo_SIN_45_otimizado_AG_ONS import (
    funcao_objetivo_SIN45,
    HASH_TABLE_PATH as HASH_TABLE_PATH_SIN45,
    hashtablesize as hashtablesize_SIN45,
)
from utils.functions_fitness.function_IEEE_118_otimizacao import (
    funcao_objetivo_IEEE118,
    HASH_TABLE_PATH as HASH_TABLE_PATH_IEEE118,
    hashtablesize as hashtablesize_IEEE118,
)

from utils.functions_fitness.function_SEP_small_cases import (
    funcao_objetivo_SEP3,
    funcao_objetivo_SEP5,
    funcao_objetivo_SEP9,
    hashtablesize_3,
    hashtablesize_5,
    hashtablesize_9,
    HASH_TABLE_PATH as HASH_TABLE_PATH_SEP_SMALL,
)

# from database_controller import run_consolidar_resultados
import argparse

# Bibliotecas padrão
import json
import pathlib
import pandas as pd
import numpy as np
import os
from datetime import datetime
import sys

# VARIAVEIS GLOBAIS
ARRAY_FITNESS_FUNCTIONS = [
    funcao_objetivo_IEEE14,
    funcao_objetivo_IEEE30,
    funcao_objetivo_IEEE57,
    funcao_objetivo_IEEE118,
    funcao_objetivo_SIN45,
    funcao_objetivo_SEP3,
    funcao_objetivo_SEP5,
    funcao_objetivo_SEP9,
]

HASH_TABLE_PATH = [
    HASH_TABLE_PATH_IEEE14,
    HASH_TABLE_PATH_IEEE30,
    HASH_TABLE_PATH_IEEE57,
    HASH_TABLE_PATH_IEEE118,
    HASH_TABLE_PATH_SIN45,
    HASH_TABLE_PATH_SEP_SMALL,
    HASH_TABLE_PATH_SEP_SMALL,
    HASH_TABLE_PATH_SEP_SMALL,
]

HASHTABLE_SIZE_FUNCS = {
    "funcao_objetivo_IEEE14": hashtablesize_IEEE14,
    "funcao_objetivo_IEEE30": hashtablesize_IEEE30,
    "funcao_objetivo_IEEE57": hashtablesize_IEEE57,
    "funcao_objetivo_IEEE118": hashtablesize_IEEE118,
    "funcao_objetivo_SIN45": hashtablesize_SIN45,
    "funcao_objetivo_SEP3": hashtablesize_3,
    "funcao_objetivo_SEP5": hashtablesize_5,
    "funcao_objetivo_SEP9": hashtablesize_9,
}

BASE_DIR = pathlib.Path(__file__).resolve().parent

# variaveis de controle
CLI = True

#! Debug Mode para AG e logs.txt para o SEP
DEBUG_MODE = True
BECHMARKING_MODE = False
SHOW_SETTINGS = False
NUMERO = 3  # Valor padrão


# Funções auxiliares
def load_params(file_path):
    """Carrega parâmetros de um arquivo JSON."""
    with open(file_path, "r") as file:
        return json.load(file)


def convert_values_to_int(params):
    """Converte valores dos parâmetros para int, float ou listas, se aplicável."""
    float_keys = {"MUTACAO", "CROSSOVER", "PORCENTAGEM"}
    for key, value in params.items():
        # Se for uma string que parece uma lista, tenta converter
        if isinstance(value, str) and value.strip().startswith("["):
            try:
                params[key] = json.loads(value)
                continue  # Pula para o próximo item
            except json.JSONDecodeError:
                # Se não for um JSON válido, ignora e mantém a string original
                pass

        # Lógica original para floats e ints
        try:
            if key.upper() in float_keys:
                params[key] = float(value)
            else:
                params[key] = int(float(value))
        except (ValueError, TypeError):
            # Ignora erros de conversão para valores que não são numéricos (como as listas já convertidas ou outras strings)
            pass
    return params


# Função principal para executar o framework com múltiplas execuções
def run_framework_many_executions(
    function_bechmarking=False,
    config_num_arg=None,
    exec_num_arg=None,
    objective_function_index=None,
):
    global NUMERO, DEBUG_MODE, BECHMARKING_MODE, CLI

    # 1. Carrega parâmetros base e opções
    params_base = load_params(f"{BASE_DIR}/params.json")
    options = load_params(f"{BASE_DIR}/options.json")
    params_base = convert_values_to_int(params_base)

    # Pegar modos do params.json ou usar default
    cli_mode = params_base.get("CLI_MODE", CLI)
    debug_mode_flag = params_base.get("DEBUG_MODE", DEBUG_MODE)
    benchmarking_mode_flag = params_base.get("BENCHMARKING_MODE", BECHMARKING_MODE)

    # Lógica de seleção da função
    if objective_function_index is not None:
        numero_da_funcao = int(objective_function_index)
        cli_mode = False  # Se veio argumento, não pergunta nada
    elif cli_mode:
        print("\n--------------------------------")
        print(f"No arquivo: {BASE_DIR / 'utils' / 'functions_fitness'}")
        print("\nSELECIONE O CASO DE SIMULAÇÃO:")
        print("--------------------------------")
        for i in range(len(ARRAY_FITNESS_FUNCTIONS)):
            print(f"{i} - {ARRAY_FITNESS_FUNCTIONS[i].__name__}")
        print("--------------------------------\n")
        
        try:
            choice = input("Digite o número da função objetivo: ")
            numero_da_funcao = int(choice)
            
            choice_bench = input("Deseja usar o modo benchmarking? (S/N): default (N) ")
            benchmarking_mode_flag = True if choice_bench.lower() == "s" else benchmarking_mode_flag
            
            choice_debug = input("Deseja usar o modo debug? (S/N): default (N) ")
            debug_mode_flag = True if choice_debug.lower() == "s" else debug_mode_flag
        except ValueError:
            print("Entrada inválida. Usando padrão.")
            numero_da_funcao = NUMERO
    else:
        numero_da_funcao = NUMERO

    if function_bechmarking or benchmarking_mode_flag:
        print("Função objetivo selecionada: Rastrigin")
        fitness_func_to_use = rastrigin
    else:
        if 0 <= numero_da_funcao < len(ARRAY_FITNESS_FUNCTIONS):
            fitness_func_to_use = ARRAY_FITNESS_FUNCTIONS[numero_da_funcao]
        else:
            print(f"Erro: Índice {numero_da_funcao} inválido. Usando IEEE14.")
            fitness_func_to_use = ARRAY_FITNESS_FUNCTIONS[0]
            numero_da_funcao = 0
            
        print(f"Função objetivo selecionada: {fitness_func_to_use.__name__}")

    #! debug pela CLI e pelo launcher de ter excpetion sempre checando esse valor
    print(
        "Tamanho do ARRAY de variáveis de decisão no params.json:",
        len(params_base.get("VARIAVEIS_DE_DECISAO", [])),
    )

    # 2. Descobre variações e número de execuções
    varying_keys = [
        k for k in options if isinstance(options[k], list) and len(options[k]) > 0
    ]
    varying_values = [options[k] for k in varying_keys]
    repeticoes = options.get("repeticoes_por_config", 1)

    # 3. Gera todas as combinações de parâmetros
    from itertools import product

    combinations = (
        [dict(zip(varying_keys, vals)) for vals in product(*varying_values)]
        if varying_keys
        else [{}]
    )

    # If caller requested a single configuration/execution via CLI args, restrict accordingly
    if config_num_arg is not None:
        idx = int(config_num_arg) - 1
        if 0 <= idx < len(combinations):
            combinations = [combinations[idx]]
        else:
            print(f"Índice de configuração inválido: {config_num_arg}")
            return

    #! Inicia o contador de tempo de execução
    start = datetime.now()

    # Exibe informações das configurações
    print(f"\nTotal de configurações únicas: {len(combinations)}")
    print(f"Execuções por configuração: {repeticoes}")

    # Cria um diretório de saída com timestamp para evitar sobreposições
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    main_output_dir = BASE_DIR / "output" / f"run_{timestamp}"
    os.makedirs(main_output_dir, exist_ok=True)

    config_num = 1
    for combo in combinations:
        # Cria um diretório específico para a configuração
        config_dir = main_output_dir / f"config_{config_num}"
        os.makedirs(config_dir, exist_ok=True)

        # Monta params para esta configuração
        params = params_base.copy()
        params.update(combo)
        params = convert_values_to_int(params)

        print(f"\n[INFO] Executando com a seguinte combinação de parâmetros: {combo}")

        #! 4) Define função objetivo
        fitness_func = fitness_func_to_use

        #! Pega a função de cálculo de tamanho de hash correspondente, se existir
        size_func = HASHTABLE_SIZE_FUNCS.get(fitness_func.__name__)

        tamanho_hash_val = 0
        if size_func:
            tamanho_hash_val = size_func()

        #! 5) Instancia Setup uma vez por configuração
        setup = Setup(
            params, fitness_function=fitness_func, tamanho_hash=tamanho_hash_val
        )

        print("Classe Setup iniciada para a configuração.")

        def consultaHashTable():
            # Consulta hash_table se existir (sub rotina)
            if os.path.exists(HASH_TABLE_PATH[numero_da_funcao]):
                try:
                    hash_excel = pd.read_excel(
                        HASH_TABLE_PATH[numero_da_funcao], index_col=0
                    )
                    if not hash_excel.empty:
                        for key, value in hash_excel["Fitness"].items():
                            if isinstance(key, int) and key < len(setup.tabela_hash):
                                setup.tabela_hash[key] = value
                        print(f"Tabela hash carregada e atualizada com {len(hash_excel)} registros!")
                except Exception as e:
                    print(f"Erro ao carregar hash_table.xlsx: {e}")
            else:
                hash_df = pd.DataFrame(data=setup.tabela_hash, columns=["Fitness"])
                hash_df.to_excel(HASH_TABLE_PATH[numero_da_funcao], index=False)
                print(f"Tabela hash INICIAL criada!")

        consultaHashTable()

        # Define o range de execuções a serem rodadas
        if exec_num_arg is not None:
            execution_range = range(int(exec_num_arg), int(exec_num_arg) + 1)
        else:
            execution_range = range(1, repeticoes + 1)

        for exec_num in execution_range:
            print(f"\n--- Iniciando execução {exec_num}/{repeticoes} ---")
            start_exec = datetime.now()

            #! 6) Executa algoritmo
            alg = AlgoritimoEvolutivoRCE(setup, DEBUG=debug_mode_flag)
            print(f"Algoritmo Evolutivo iniciado. DEBUG MODE = {debug_mode_flag}")
            (
                pop_with_repopulation,
                logbook_with_repopulation,
                best_individual,
                all_individual_values,
            ) = alg.run(RCE=True)
            best_variables = list(best_individual)

            end_exec = datetime.now()
            elapsed_exec = end_exec - start_exec
            formatted_time_exec = format_elapsed_time(elapsed_exec)

            #! 7) Visualize os Resultados
            print("\nEvolução concluída  - 100%")
            best_solution_generation, _, _, _ = alg.dashboard.visualize(
                logbook_with_repopulation,
                pop_with_repopulation,
                config_num=config_num,
                execution_num=exec_num,
            )

            print(f"\nDuração desta Execução: {formatted_time_exec}")
            print(f"Tempo Total Acumulado: {format_elapsed_time(end_exec - start)}")
            print(f"Objective functions runs: {setup.objectiveruns}")
            print(f"Consultas HashTable: {setup.hashtablereads}\n")

            #! 8) Salva os dados de visualização
            vis_output_path = config_dir / f"config_{config_num}_exec_{exec_num}_visualization.json"
            try:
                for item in all_individual_values:
                    if "Variaveis de Decisão" in item and hasattr(item["Variaveis de Decisão"], "tolist"):
                        item["Variaveis de Decisão"] = item["Variaveis de Decisão"].tolist()
                    elif isinstance(item.get("Variaveis de Decisão"), np.ndarray):
                        item["Variaveis de Decisão"] = item["Variaveis de Decisão"].tolist()
                with open(vis_output_path, "w", encoding="utf-8") as f:
                    json.dump(all_individual_values, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"Erro ao salvar dados de visualização: {e}")

            #! 9) Salva resultado individual como JSON
            best_fitness = best_individual.fitness.values[0] if best_individual.fitness.valid else float("inf")
            result = {
                "config_num": config_num,
                "exec_num": exec_num,
                "params": params,
                "best_variables": best_variables,
                "best_fitness": best_fitness,
                "best_gen_idx": best_solution_generation,
                "time": formatted_time_exec,
                "fitness_function": fitness_func.__name__,
            }
            output_path = config_dir / f"config_{config_num}_exec_{exec_num}_results.json"
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"Erro ao salvar resultado: {e}")

        config_num += 1

    print("\nTodas as execuções foram concluídas.")

    try:
        import subprocess
        command = [sys.executable, "-c", "from database_controller import run_consolidar_resultados; run_consolidar_resultados()"]
        subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print("\nIniciando consolidação de resultados em segundo plano...")
    except Exception as e:
        print(f" Erro ao iniciar consolidação: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_num", type=int)
    parser.add_argument("--exec_num", type=int)
    parser.add_argument("--objective_function_index", type=int)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--benchmark", action="store_true")

    args = parser.parse_args()

    if args.debug: DEBUG_MODE = True
    if args.benchmark: BECHMARKING_MODE = True

    run_framework_many_executions(
        function_bechmarking=BECHMARKING_MODE,
        config_num_arg=args.config_num,
        exec_num_arg=args.exec_num,
        objective_function_index=args.objective_function_index,
    )
