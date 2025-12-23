# -*- coding: utf-8 -*-
"""
Execução do framework RCE com configuração de várias execuções e variações de parâmetros.
PVRV - 20/08/2025
RZ - 16/10/2025 - resolvendo chamada a diversas funções objetivo
PVRV - 10/12/2025 - Adicionando passagem de argumentos via linha de comando para configuração e execução específicas
PVRV - 17/12/2025 - Correções gerais após artigo PIBIC e criação do .exe do projeto
"""

# Imports principais do framework
from AlgEvolutivoRCE.Setup import Setup
from AlgEvolutivoRCE.alg_evolutivo_rce import AlgoritimoEvolutivoRCE

# Utils - Trazer esses codigos para esse unico arquivo
from config import FOLDER_NAME, format_elapsed_time

#! Importando a minha função objetivo dentro do projeto
from utils.functions_fitness.functions_benchmarking import rastrigin

from utils.functions_fitness.function_IEEE_14_contigencias import funcao_objetivo_IEEE14, HASH_TABLE_PATH as HASH_TABLE_PATH_IEEE14, hashtablesize as hashtablesize_IEEE14
from utils.functions_fitness.function_IEEE_30_otimizacao import funcao_objetivo_IEEE30, HASH_TABLE_PATH as HASH_TABLE_PATH_IEEE30, hashtablesize as hashtablesize_IEEE30
from utils.functions_fitness.function_IEEE_57_otimizacao import funcao_objetivo_IEEE57, HASH_TABLE_PATH as HASH_TABLE_PATH_IEEE57, hashtablesize as hashtablesize_IEEE57
#from utils.functions_fitness.function_SIN_45_otimizacao import funcao_objetivo_SIN45, hashtablesize_sin45
from utils.functions_fitness.func_objetivo_SIN_45_otimizado_AG_ONS import funcao_objetivo_SIN45, HASH_TABLE_PATH as HASH_TABLE_PATH_SIN45, hashtablesize as hashtablesize_SIN45
from utils.functions_fitness.function_IEEE_118_otimizacao import funcao_objetivo_IEEE118, HASH_TABLE_PATH as HASH_TABLE_PATH_IEEE118, hashtablesize as hashtablesize_IEEE118

from database_controller import run_consolidar_resultados
import argparse

# Bibliotecas padrão
import json
import pathlib
import pandas as pd
import numpy as np
import os
from datetime import datetime



#! Passar tudo aqui para o config.py depois
# VARIAVEIS GLOBAIS
ARRAY_FITNESS_FUNCTIONS = [funcao_objetivo_IEEE14,funcao_objetivo_IEEE30, funcao_objetivo_IEEE57, funcao_objetivo_IEEE118, funcao_objetivo_SIN45]

HASH_TABLE_PATH = [ HASH_TABLE_PATH_IEEE14, HASH_TABLE_PATH_IEEE30, HASH_TABLE_PATH_IEEE57, HASH_TABLE_PATH_IEEE118, HASH_TABLE_PATH_SIN45 ]

HASHTABLE_SIZE_FUNCS = {
    "funcao_objetivo_IEEE14": hashtablesize_IEEE14,
    "funcao_objetivo_IEEE30": hashtablesize_IEEE30,
    "funcao_objetivo_IEEE57": hashtablesize_IEEE57,
    "funcao_objetivo_IEEE118": hashtablesize_IEEE118,
    "funcao_objetivo_SIN45": hashtablesize_SIN45,
}

BASE_DIR = pathlib.Path(__file__).resolve().parent

# variaveis de controle
CLI = False
#! Debug Mode para AG e logs.txt para o SEP
DEBUG_MODE = False
BECHMARKING_MODE = False
SHOW_SETTINGS = False

# Entrada de dados do usuario
print("\n--------------------------------")
print("No arquivo:", BASE_DIR / "utils" / "functions_fitness")
print("\nSELECIONE O SEU CASO DE SIMULAÇÃO DE AGENDAMENTO DE DESLIGAMENTOS DE CONTINGENCIAS E OTIMIZAÇÃO PARA REDES ELÉTRICAS")
print("\n--------------------------------")
for i in range(len(ARRAY_FITNESS_FUNCTIONS)):
    print(f"{i} - {ARRAY_FITNESS_FUNCTIONS[i].__name__}")
print("--------------------------------\n")


if CLI:
    print("Responda no terminal onde o seu laucher.py esta sendo executado")
    # choice = input("Digite o número da função objetivo: ")
    # NUMERO = int(choice)
    # print("\n")
    choice_benchmarking = input("Deseja usar o modo benchmarking? (S/N): default (N) ")
    BECHMARKING_MODE = True if choice_benchmarking.lower() == "s" else False
    print("\n")
    debug_mode = input("Deseja usar o modo debug? (S/N): default (N) ")
    DEBUG_MODE = True if debug_mode.lower() == "s" else False

#! https://budavariam.github.io/asciiart-text/

MSG_TERMINAL ="""

 __       _______ .___________. __      _______.   .______        ______     ______  __  ___  __  



|  |     |   ____||           |(_ )    /       |   |   _  \      /  __  \   /      ||  |/  / |  | 



|  |     |  |__   `---|  |----` |/    |   (----`   |  |_)  |    |  |  |  | |  ,----'|  '  /  |  | 



|  |     |   __|      |  |             \   \       |      /     |  |  |  | |  |     |    <   |  | 



|  `----.|  |____     |  |         .----)   |      |  |\  \----.|  `--'  | |  `----.|  .  \  |__| 



|_______||_______|    |__|         |_______/       | _| `._____| \______/   \______||__|'__\ (__) 


"""

print(f"\n{MSG_TERMINAL}\n")


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

        if isinstance(value, str) and value.strip().startswith('['):

            try:

                params[key] = json.loads(value)

                continue # Pula para o próximo item

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
def run_framework_many_executions(function_bechmarking=False, objective_function_index=0):
    numero = objective_function_index

    if function_bechmarking:
        print("Função objetivo selecionada: Rastrigin")
    else:
        print(f"Função objetivo selecionada: {ARRAY_FITNESS_FUNCTIONS[numero]}")

    start_time = datetime.now()

    # Lógica unificada: sempre executa a bateria de testes com base nos arquivos de configuração
    params_base = load_params(f"{BASE_DIR}/params.json")
    options = load_params(f"{BASE_DIR}/options.json")
    params_base = convert_values_to_int(params_base)

    varying_keys = [k for k in options if isinstance(options[k], list) and len(options[k]) > 0]
    varying_values = [options[k] for k in varying_keys]
    repeticoes = options.get('repeticoes_por_config', 1)

    from itertools import product
    combinations = [dict(zip(varying_keys, vals)) for vals in product(*varying_values)] if varying_keys else [{}]
    
    total_execs = len(combinations) * repeticoes
    print("\nResumo da Execução:")
    print(f"  Configurações Únicas: {len(combinations)}")
    print(f"  Execuções por Configuração: {repeticoes}")
    print(f"  Total de Execuções: {total_execs}\n")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    main_output_dir = BASE_DIR / "output" / f"run_{timestamp}"
    os.makedirs(main_output_dir, exist_ok=True)
    
    for config_idx, combo in enumerate(combinations, 1):
        config_dir = main_output_dir / f"config_{config_idx}"
        os.makedirs(config_dir, exist_ok=True)
        
        params = params_base.copy()
        params.update(combo)
        params = convert_values_to_int(params)
        
        print(f"\n[INFO] Iniciando configuração {config_idx} com: {combo}")

        for exec_num in range(1, repeticoes + 1):
            print(f"\n--- Iniciando execução {exec_num}/{repeticoes} ---")
            run_single_execution(params, fitness_func_idx=numero, is_benchmark=function_bechmarking,
                                 config_num=config_idx, exec_num=exec_num,
                                 output_dir=config_dir, total_start_time=start_time)

        print("\n" + "="*60 + f"\nFIM DA CONFIGURAÇÃO {config_idx}\n" + "=" * 60)

    print("\nTodas as execuções foram concluídas.")
    consolidate_results_in_background()


def run_single_execution(params, fitness_func_idx, is_benchmark, config_num, exec_num, output_dir, total_start_time):
    """Executa uma única instância do algoritmo genético."""
    
    start_exec = datetime.now()

    fitness_func = ARRAY_FITNESS_FUNCTIONS[fitness_func_idx] if not is_benchmark else rastrigin
    size_func = HASHTABLE_SIZE_FUNCS.get(fitness_func.__name__)
    tamanho_hash_val = size_func() if size_func else 0

    setup = Setup(
        params,
        fitness_function=fitness_func,
        tamanho_hash=tamanho_hash_val
    )
    print("Classe Setup iniciada para a execução.")

    # Carregar tabela hash (se existir)
    hash_table_path = HASH_TABLE_PATH[fitness_func_idx]
    if os.path.exists(hash_table_path):
        try:
            hash_excel = pd.read_excel(hash_table_path, index_col=0)
            if not hash_excel.empty:
                for key, value in hash_excel['Fitness'].items():
                    if isinstance(key, int) and key < len(setup.tabela_hash):
                        setup.tabela_hash[key] = value
                print(f"Tabela hash carregada com {len(hash_excel)} registros!")
        except Exception as e:
            print(f"Erro ao carregar hash_table: {e}")

    # Executa o algoritmo
    alg = AlgoritimoEvolutivoRCE(setup, DEBUG=DEBUG_MODE)
    print(f"Algoritmo Evolutivo iniciado. DEBUG MODE = {DEBUG_MODE}")
    pop_with_repopulation, logbook_with_repopulation, best_individual, all_individual_values = alg.run(RCE=True)
    best_variables = list(best_individual)
    
    end_exec = datetime.now()
    elapsed_exec = end_exec - start_exec
    formatted_time_exec = format_elapsed_time(elapsed_exec)

    print("\nEvolução concluída - 100%")
    best_solution_generation, _, _, _ = alg.dashboard.visualize(
        logbook_with_repopulation,
        pop_with_repopulation,
        config_num=config_num,
        execution_num=exec_num,
    )

    print(f"\nDuração desta Execução: {formatted_time_exec}")
    print(f"Tempo Total Acumulado: {format_elapsed_time(end_exec - total_start_time)}")
    print(f"Objective functions runs: {setup.objectiveruns}")
    print(f"Consultas HashTable: {setup.hashtablereads}\n")

    # Salvar resultados
    save_execution_results(output_dir, config_num, exec_num, params, best_individual, best_solution_generation, formatted_time_exec, fitness_func.__name__, all_individual_values)
    
    # Salvar tabela hash
    try:
        hash_df = pd.DataFrame(data=setup.tabela_hash, columns=['Fitness'])
        hash_df.to_excel(hash_table_path, index=False)
    except Exception as e:
        print(f"ERRO ao salvar a tabela hash: {e}")

def save_execution_results(output_dir, config_num, exec_num, params, best_individual, best_gen_idx, exec_time, func_name, all_individual_values):
    """Salva os resultados de uma execução em arquivos JSON."""
    
    # Salva dados de visualização
    vis_output_path = output_dir / f"config_{config_num}_exec_{exec_num}_visualization.json"
    try:
        for item in all_individual_values:
            if 'Variaveis de Decisão' in item and hasattr(item['Variaveis de Decisão'], 'tolist'):
                item['Variaveis de Decisão'] = item['Variaveis de Decisão'].tolist()
            elif isinstance(item['Variaveis de Decisão'], np.ndarray):
                item['Variaveis de Decisão'] = item['Variaveis de Decisão'].tolist()
        with open(vis_output_path, 'w', encoding='utf-8') as f:
            json.dump(all_individual_values, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar dados de visualização: {e}")

    # Salva resultado principal
    best_fitness = best_individual.fitness.values[0] if best_individual.fitness.valid else float('inf')
    result = {
        "config_num": config_num,
        "exec_num": exec_num,
        "params": params,
        "best_variables": list(best_individual),
        "best_fitness": best_fitness,
        "best_gen_idx": best_gen_idx,
        "time": exec_time,
        "fitness_function": func_name
    }
    output_path = output_dir / f"config_{config_num}_exec_{exec_num}_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
    
    print("Resultados e visualizações salvos com sucesso.")


def consolidate_results_in_background():
    """Inicia o processo de consolidação de resultados em segundo plano."""
    try:
        import subprocess
        import sys
        
        command = [
            sys.executable,
            "-c", 
            "from database_controller import run_consolidar_resultados; run_consolidar_resultados()"
        ]
        
        subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print("\nIniciando consolidação de resultados em segundo plano...")

    except Exception as e:
        print(f" Erro ao iniciar o subprocesso de consolidação: {e}")


#! Rodando o framework se for o arquivo principal
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Executa o framework RCE para otimização de redes elétricas.")

    parser.add_argument("--objective_function_index", type=int, default=0, help="Índice da função objetivo a ser usada (padrão: 0).")

    args = parser.parse_args()


    # Define o número da função objetivo a partir dos argumentos ou padrão
    numero_selecionado = args.objective_function_index

    if CLI:
        try:
            choice = input(f"Digite o número da função objetivo (padrão: {numero_selecionado}): ")
            if choice:
                numero_selecionado = int(choice)
        except (ValueError, IndexError):
            print("Seleção inválida. Usando o valor padrão.")

    run_framework_many_executions(
        function_bechmarking=BECHMARKING_MODE,
        objective_function_index=numero_selecionado
    )

# --- Exemplos de Uso via Linha de Comando (argparse) ---
#
# 1. Execução de uma bateria de testes completa (modo nativo):
#    - Este modo lê os arquivos 'src/params.json' e 'src/options.json'.
#    - 'options.json' define as variações de parâmetros e o número de repetições.
#    - O script criará um novo diretório de output com timestamp para salvar os resultados.
#    - Comando:
#      python3 src/run.py
#
# 2. Execução de uma única instância (modo utilizado pelo Launcher):
#    - Este modo é para executar uma única combinação de configuração e repetição.
#    - É ideal para ser chamado por um processo pai (como o launcher) que controla o loop geral.
#    - Requer que o diretório de output já tenha sido criado pelo processo pai.
#    - Comando de exemplo para a config 1, repetição 2, usando a função objetivo de índice 0 (IEEE14):
#      python3 src/run.py --config_num 1 --exec_num 2 --objective_function_index 0 --output_dir "src/output/run_2025-12-23_12-00-00"
#
