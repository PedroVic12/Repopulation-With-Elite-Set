# -*- coding: utf-8 -#
# Import RCE Framework
from AlgEvolutivoRCE_backup.Setup import Setup
from AlgEvolutivoRCE_backup.alg_evolutivo_rce import AlgoritimoEvolutivoRCE

# Utils 
from config_backup import FOLDER_NAME, entrada_de_dados, format_elapsed_time

import streamlit as st
import json
import pathlib
from datetime import datetime
import os
import pandas as pd
from utils.functions_fitness.functions_benchmarking import rosenbrock_benchmark,esfera_benchmark,rastrigin, evaluate
from utils.functions_fitness.function_IEEE_14_contigencias import funcao_objetivo_IEEE14

#! Lendo os parametros em JSON em /AlgEvolutivoRCE/params.json
def load_params(file_path):
    with open(file_path, "r") as file:
        params = json.load(file)
    return params



# Load parameters from the JSON file in any configuration of PC
results_consolidados = []  # Initialize an empty list to store results
execution_times = []  # Lista para armazenar os tempos de execução
BASE_DIR = pathlib.Path(__file__).resolve().parent 

params = load_params(f"{BASE_DIR}/params.json")
# windows
#params = load_params(r"C:\Users\Pedro Victor R V\Documents\GitHub\Repopulation-With-Elite-Set\src\AlgEvolutivoRCE\params.json")



############################# MUltiplas execuções com grupos de parâmetros #############################


import itertools

def export_all_configs_to_json(parametros):
    # parametros: dict com os 4 parâmetros, cada um sendo uma lista de valores possíveis
    keys = list(parametros.keys())
    values = [parametros[k] if isinstance(parametros[k], list) else [parametros[k]] for k in keys]
    configs = {}
    for idx, combination in enumerate(itertools.product(*values), 1):
        config_dict = dict(zip(keys, combination))
        configs[f"config {idx}"] = config_dict
    # Salva no arquivo
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(configs, f, indent=4, ensure_ascii=False)
    st.success(f"{len(configs)} configurações exportadas para config.json!")

def convert_values_to_int(params):
    """
    Converts dictionary values to appropriate types:
    - Float for specified keys
    - Preserves lists as-is
    - Converts other numeric values to int
    - Handles string representations of lists
    """
    float_keys = {"MUTACAO", "CROSSOVER", "PORCENTAGEM"}
    array_keys = {"ARRAY_VAR", "LIMITE_VAR"}
    
    for key, value in params.items():
        key_upper = key.upper()
        
        # Handle float values
        if key_upper in float_keys:
            try:
                if isinstance(value, str):
                    params[key] = float(value)
                else:
                    params[key] = float(value)  # Convert to float if not already
            except (ValueError, TypeError):
                print(f"Warning: Could not convert {key} to float. Keeping original value: {value}")
        
        # Handle array values
        elif key_upper in array_keys or (isinstance(value, str) and value.startswith('[') and value.endswith(']')):
            try:
                if isinstance(value, str):
                    # Safely evaluate string representation of list
                    import ast
                    params[key] = ast.literal_eval(value)
                # If it's already a list, keep it as is
                elif isinstance(value, (list, tuple)):
                    params[key] = list(value)
            except (ValueError, SyntaxError) as e:
                print(f"Warning: Could not parse array for {key}. Error: {e}")
        
        # Convert other numeric values to int
        else:
            try:
                if value is not None and str(value).strip():
                    params[key] = int(float(value))  # Convert to float first to handle string floats
            except (ValueError, TypeError):
                print(f"Warning: Could not convert {key} to int. Keeping original value: {value}")
    
    return params



def load_many_executions(options, setupobj, algoritmo, config_num=1, exec_num=1, all_configs_results=None):
    print("\n================================")
    print(f"\tExecução: {exec_num}")
    print("================================\n")
    start = datetime.now()
    
    
    # Loop principal do Algoritmo Evolutivo
    pop_with_repopulation, logbook_with_repopulation, best_variables = algoritmo.run(RCE=True)
    print("\n\nEvolução concluída  - 100%")
    print(f"Best variables", best_variables)
    
    
    # # Resultados
    x, y, z, fig = algoritmo.dashboard.visualize(
        logbook_with_repopulation, pop_with_repopulation,
        config_num=config_num, execution_num=exec_num
    )
    

    # Passando os valores do array direto no dataframe com os index como chave (hash = chave, valor)
    hash_df1 = pd.DataFrame(setupobj.tabela_hash, columns=['Fitness'])
    hash_df1.sort_values(by='Fitness', ascending=False, inplace=True)
    hash_df1.to_excel("hash_table.xlsx", index=False)


    print(f"\nObjective function runs : {setupobj.objectiveruns}")
    print(f"Hash table reads : {setupobj.hashtablereads}")

    end = datetime.now()
    elapsed = end - start
    formatted_time = format_elapsed_time(elapsed)

    print(f"Elapsed Time in execution : {formatted_time}")

    # Append results to the list for the current config
    if all_configs_results is not None:
        if config_num not in all_configs_results:
            all_configs_results[config_num] = []
        all_configs_results[config_num].append({
            "execution": exec_num,
            "solution_variables": y,
            "best_fitness": z,
            "best_generations": x,
            "execution_time": elapsed.total_seconds() # Save as seconds for easier aggregation
        })








#! PVRV - Função que executa um loop de execuncoes com 2 parametros .json                     
def run_framework_many_executions(function_bechmarking = False, config_num=1, exec_num=1):
    """Função para executar o framework com múltiplas execuções."""
    
    # Load parameters from the JSON file in any configuration of PC
    params = load_params(f"{BASE_DIR}/params.json")
    options = load_params(f"{BASE_DIR}/options.json")
    
    # Convert values to int, except for specified float keys
    #options = convert_values_to_int(options)s
    params = convert_values_to_int(params)
    
    print(f"\n\nIniciando execução do USER com os parâmetros: {options}")
    
    if not function_bechmarking:
        #! Função de avaliação da rede IEEE 14
        #! 2min a 3 min com config de AG básica mesmo com hashtable
        fitness_func = funcao_objetivo_IEEE14
    else:
        fitness_func = rastrigin
        
    #!  Instanciando o Setup para configuração
    setup = Setup(params, fitness_function = fitness_func,
                  tamanho_hash=(entrada_de_dados()["num_contingencias"] * entrada_de_dados()["num_carregamentos"]*(2**entrada_de_dados()["num_desligamentos"])))
    
    print("Classe Setup iniciada")

    #! SUBROTINA - for loop para conjunto de configurações de parametros_opcionais
    def consulta_hashtable(show_table = False):
        #! TODO para melhor performace
        try:
            # Ler xlsx no início da run_framework e verificar logo depois de instanciar o setup se o xlsx existe e caso exista, coloca o conteúdo do xlsx no setup.tabela_hash.
            if os.path.exists(f"hash_table.xlsx"):
                print("\n\nFazendo consulta para setup.tabela_hash")

                hash_excel = pd.read_excel("hash_table.xlsx")

                if not hash_excel.empty and not hash_excel.isnull().values.any():
                                     
                    setup.tabela_hash = hash_excel['Fitness'].to_dict()
                    neg_one_count = list(setup.tabela_hash.values()).count(-1)

                    if -1 in setup.tabela_hash.values():
                        if show_table:
                            print(hash_excel.head(5))
                            print("Cenários Default = ",len(setup.tabela_hash))
                            print(neg_one_count)
                    else:
                        fitness_counts = hash_excel['Fitness'].value_counts()
                        filtered_df = hash_excel[hash_excel['Fitness'] > 14]
                        print(fitness_counts.head())
                else:
                    print("O arquivo hash_table.xlsx está vazio ou contém valores nulos.")
            else:
                print("Arquivo da hash table não encontrado!")


        except Exception as e:
            print(f"Erro ao ler o arquivo xlsx: {e}")

            
    consulta_hashtable(show_table=True)

    
    # Usando o algoritimo Genetico do DEAP
    mode = False
    RCE_MODE = True
    alg = AlgoritimoEvolutivoRCE(setup, DEBUG = mode)

    print(f"\n\nAlgoritimo Evolutivo iniciado -  MODO: DEBUG = {mode} - RCE_MODE = {RCE_MODE}")

    # Run the utility function to load many executions
    all_results = {}
    load_many_executions(RCE_MODE, setup, alg, config_num=config_num, exec_num=exec_num, all_configs_results=all_results)

    # Salva os resultados consolidados
    all_data_for_df = []
    for config_num_key, results_list in all_results.items():
        for result_entry in results_list:
            # Add config_num to each result entry
            result_entry["config_num"] = config_num_key
            all_data_for_df.append(result_entry)

    if all_data_for_df:
        consolidated_df = pd.DataFrame(all_data_for_df)
        # Reorder columns to have config_num and execution at the beginning
        cols = ["config_num", "execution"] + [col for col in consolidated_df.columns if col not in ["config_num", "execution"]]
        consolidated_df = consolidated_df[cols]

        print(f"Consolidando {len(all_data_for_df)} entradas de resultados no Excel.")
        with pd.ExcelWriter(f"{FOLDER_NAME}/results_consolidados.xlsx") as writer:
            consolidated_df.to_excel(writer, sheet_name="Consolidated Results", index=False)
        print(f"Resultados consolidados salvos em {FOLDER_NAME}/results_consolidados.xlsx")

        # Também salva o último resultado em um cache leve para o Streamlit consumir diretamente
        try:
            import json
            from pathlib import Path
            cache_path = Path(FOLDER_NAME) / "streamlit_cache_exec.json"
            last_row = consolidated_df.iloc[-1].to_dict()
            # Campos esperados na página do Streamlit
            cache_payload = {
                "execution": int(last_row.get("execution", 1)),
                "solution_variables": last_row.get("solution_variables", []),
                "best_fitness": last_row.get("best_fitness", None),
                "best_generations": last_row.get("best_generations", None),
                "execution_time": last_row.get("execution_time", None),
                "config_num": int(last_row.get("config_num", 1)),
            }
            # Se solution_variables vier como string, tenta converter
            if isinstance(cache_payload["solution_variables"], str):
                try:
                    import ast
                    cache_payload["solution_variables"] = ast.literal_eval(cache_payload["solution_variables"]) 
                except Exception:
                    pass
            cache_path.write_text(json.dumps(cache_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Cache Streamlit salvo em {cache_path}")
        except Exception as e:
            print(f"Aviso: falha ao salvar cache do Streamlit: {e}")
    else:
        print("Nenhum resultado para consolidar.")




if __name__ == "__main__":
    print("Starting execution with benchmark function...")
    # Run with a simple benchmark function first
    run_framework_many_executions(function_bechmarking=False)