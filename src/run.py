# -*- coding: utf-8 -*-
"""
Execução do framework RCE com configuração de várias execuções e variações de parâmetros.
PVRV - 20/08/2025
"""

# Imports principais do framework
from AlgEvolutivoRCE_backup.Setup import Setup
from AlgEvolutivoRCE_backup.alg_evolutivo_rce import AlgoritimoEvolutivoRCE

# Utils - Trazer esses codigos para esse unico arquivo
from config_backup import FOLDER_NAME, format_elapsed_time

#! Importando a minha função objetivo dentro do projeto
from utils.functions_fitness.functions_benchmarking import rastrigin
from utils.functions_fitness.function_IEEE_14_contigencias import funcao_objetivo_IEEE14, HASH_TABLE_PATH
from utils.functions_fitness.function_IEEE_118_otimizacao import funcao_objetivo_IEEE118, HASH_TABLE_PATH
from utils.functions_fitness.function_IEEE_30_otimizacao import funcao_objetivo_IEEE30, HASH_TABLE_PATH, hashtablesize
from utils.functions_fitness.function_IEEE_57_otimizacao import funcao_objetivo_IEEE57, HASH_TABLE_PATH
from utils.functions_fitness.function_SIN_45_otimizacao import funcao_objetivo_SIN45, hashtablesize_sin45

from database_controller import run_consolidar_resultados

# Bibliotecas padrão
import json
import pathlib
import pandas as pd
import numpy as np
import os
from datetime import datetime




# VARIAVEIS GLOBAIS
ARRAY_FITNESS_FUNCTIONS = [funcao_objetivo_IEEE14,funcao_objetivo_IEEE30, funcao_objetivo_IEEE57, funcao_objetivo_IEEE118, funcao_objetivo_SIN45]

HASHTABLE_SIZE_FUNCS = {
    "funcao_objetivo_IEEE30": hashtablesize,
    "funcao_objetivo_SIN45": hashtablesize_sin45,
    "funcao_objetivo_IEEE118": hashtablesize,
}

BASE_DIR = pathlib.Path(__file__).resolve().parent

# variaveis de controle
CLI = False
DEBUG_MODE = False
BECHMARKING_MODE = False
SHOW_SETTINGS = False
NUMERO = 3 # 0 1 3 4




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
    choice = input("Digite o número da função objetivo: ")
    NUMERO = int(choice)
    print("\n")
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
def run_framework_many_executions(function_bechmarking=False):


    if function_bechmarking:
        print("Função objetivo selecionada: Rastrigin")
    else:
        print(f"Função objetivo selecionada: {ARRAY_FITNESS_FUNCTIONS[NUMERO]}")


    # 1. Carrega parâmetros base e opções
    params_base = load_params(f"{BASE_DIR}/params.json")
    options = load_params(f"{BASE_DIR}/options.json")
    params_base = convert_values_to_int(params_base)

    # 2. Descobre variações e número de execuções
    varying_keys = [k for k in options if isinstance(options[k], list) and len(options[k]) > 0]
    varying_values = [options[k] for k in varying_keys]
    repeticoes = options.get('repeticoes_por_config', 1)

    # 3. Gera todas as combinações de parâmetros
    from itertools import product
    combinations = [dict(zip(varying_keys, vals)) for vals in product(*varying_values)] if varying_keys else [{}]
    
    #! Inicia o contador de tempo de execução
    start = datetime.now()

    # Exibe informações das configurações
    print(f"\nTotal de configurações únicas: {len(combinations)}")
    print(f"Execuções por configuração: {repeticoes}")

    # Cria um diretório de saída com timestamp para evitar sobreposições
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    main_output_dir = BASE_DIR / "output" / f"run_{timestamp}"
    os.makedirs(main_output_dir, exist_ok=True)
    #print(f"\nSalvando resultados em: {main_output_dir}")



    config_num = 1
    for combo in combinations:

        # Cria um diretório específico para a configuração
        config_dir = main_output_dir / f"config_{config_num}"
        os.makedirs(config_dir, exist_ok=True)

        # Monta params para esta configuração
        params = params_base.copy()
        params.update(combo)
        params = convert_values_to_int(params)

        #! 4) Define função objetivo
        fitness_func = ARRAY_FITNESS_FUNCTIONS[NUMERO] if not function_bechmarking else rastrigin

        # Pega a função de cálculo de tamanho de hash correspondente, se existir
        #size_func = HASHTABLE_SIZE_FUNCS.get(fitness_func.__name__, hashtablesize)

        #! 5) Instancia Setup uma vez por configuração
        print(f"\n\nIniciando configuração {config_num} com os params.json:\n{params}\n")
        setup = Setup(
            params,
            fitness_function=fitness_func,
            tamanho_hash=hashtablesize()
        )

        print("Classe Setup iniciada para a configuração.")

        def consultaHashTable():
            # Consulta hash_table se existir (sub rotina)
            if os.path.exists(HASH_TABLE_PATH):
                try:
                    
                    # Read from Excel, using the first column as the index (our hash key)
                    hash_excel = pd.read_excel(HASH_TABLE_PATH, index_col=0)
                    if not hash_excel.empty:
                        
                        # Update the list-based hash table from the loaded dictionary
                        for key, value in hash_excel['Fitness'].items():
                            
                            if isinstance(key, int) and key < len(setup.tabela_hash):
                                setup.tabela_hash[key] = value
                                
                        print(f"Tabela hash carregada e atualizada com {len(hash_excel)} registros!")
                except Exception as e:
                    print(f"Erro ao carregar hash_table.xlsx: {e}")
            else:
                # If the file doesn't exist, create it from the initial hash table
                hash_df = pd.DataFrame(data=setup.tabela_hash, columns=['Fitness'])
                hash_df.to_excel(HASH_TABLE_PATH, index=False)
                print(f"Tabela hash INICIAL com {len(setup.tabela_hash)} posições não existia e foi criada! - PVRV")

        #!PVRV - Retirando e colocando no inicio de cada funcao objetivo
        consultaHashTable()

        # O loop de repetições agora mede o tempo individualmente
        for exec_num in range(1, repeticoes + 1):
            print(f"\n--- Iniciando execução {exec_num}/{repeticoes} ---")

            # Inicia o cronômetro para esta execução específica
            start_exec = datetime.now()

            #! 6) Executa algoritmo
            alg = AlgoritimoEvolutivoRCE(setup, DEBUG=DEBUG_MODE)
            print(f"Algoritmo Evolutivo iniciado. DEBUG MODE = {DEBUG_MODE}")
            pop_with_repopulation, logbook_with_repopulation, best_individual, all_individual_values = alg.run(RCE=True)
            best_variables = list(best_individual)

            # Finaliza o cronômetro e calcula a duração desta execução
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

            # Exibe os tempos e contadores de forma clara
            print(f"\nDuração desta Execução: {formatted_time_exec}")
            print(f"Tempo Total Acumulado: {format_elapsed_time(end_exec - start)}")
            print(f"Objective functions runs: {setup.objectiveruns}")
            print(f"Consultas HashTable: {setup.hashtablereads}\n")

            #! 8) Salva os dados de visualização
            vis_output_path = config_dir / f"config_{config_num}_exec_{exec_num}_visualization.json"
            try:
                for item in all_individual_values:
                    if 'Variaveis de Decisão' in item and hasattr(item['Variaveis de Decisão'], 'tolist'):
                        item['Variaveis de Decisão'] = item['Variaveis de Decisão'].tolist()
                    elif isinstance(item['Variaveis de Decisão'], np.ndarray):
                        item['Variaveis de Decisão'] = item['Variaveis de Decisão'].tolist()
                    elif not isinstance(item['Variaveis de Decisão'], (list, str)):
                        item['Variaveis de Decisão'] = list(item['Variaveis de Decisão'])
                with open(vis_output_path, 'w', encoding='utf-8') as f:
                    json.dump(all_individual_values, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"Erro ao salvar dados de visualização: {e}")

            #! 9) Salva resultado individual como JSON
            best_fitness = best_individual.fitness.values[0] if best_individual.fitness.valid else float('inf')
            result = {
                "config_num": config_num,
                "exec_num": exec_num,
                "params": params,
                "best_variables": best_variables,
                "best_fitness": best_fitness,
                "best_gen_idx": best_solution_generation,
                "time": formatted_time_exec,  # Usa o tempo da execução individual
                "fitness_function": fitness_func.__name__
            }
            output_path = config_dir / f"config_{config_num}_exec_{exec_num}_results.json"
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"Erro ao salvar resultado: {e}")
            
            print("Resultados e visualizações salvos com sucesso.")

        # --- FIM DO LOOP DE REPETIÇÕES ---

        # Salva a tabela hash UMA VEZ no final de todas as execuções da configuração
        print("\n" + "="*60)
        print(f"FIM DA CONFIGURAÇÃO {config_num}")
        try:
            hash_df = pd.DataFrame(data=setup.tabela_hash, columns=['Fitness'])
            hash_df.to_excel(HASH_TABLE_PATH, index=False)
            print(f"Salvando tabela hash em {HASH_TABLE_PATH}... com tamanho de {len(setup.tabela_hash)} posições!")

        except Exception as e:
            print(f"ERRO ao salvar a tabela hash: {e}")


        config_num += 1
    
    print("\nTodas as execuções foram concluídas.")
    
    # Consolidar resultados automaticamente em um subprocesso
    try:
        import subprocess
        import sys
        
        command = [
            sys.executable, # Garante que está usando o mesmo interpretador Python
            "-c", 
            "from database_controller import run_consolidar_resultados; run_consolidar_resultados()"
        ]
        
        # Popen não bloqueia, o script principal pode terminar enquanto a consolidação roda.
        subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print("\nIniciando consolidação de resultados em segundo plano...")

    except Exception as e:
        print(f" Erro ao iniciar o subprocesso de consolidação: {e}")


if __name__ == "__main__":
    run_framework_many_executions(function_bechmarking=BECHMARKING_MODE)
