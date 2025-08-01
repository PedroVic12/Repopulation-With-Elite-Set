import argparse

# -*- coding: utf-8 -#
# Import RCE Framework
from AlgEvolutivoRCE_backup.Setup import Setup
from AlgEvolutivoRCE_backup.alg_evolutivo_rce import AlgoritimoEvolutivoRCE

# Utils 
from config_backup import FOLDER_NAME, options_main_file, entrada_de_dados,load_many_executions, format_elapsed_time

import streamlit as st
import json
import pathlib
from datetime import datetime
import os
import pandas as pd


#!DOCS PVRV - 18/06/25
""" 
1) Para usar o frontend em Streamlit, execute o seguinte comando no terminal:

```bash
src/DashboardApp
```
```bash
# streamlit run dashboard_rce_app_v11.py
```

2) Para executar o Algoritmo Evolutivo com Reposição de Conjunto de Elite (RCE), execute esse mesmo script no terminal run_rce_framework.py, sugiro rodar o pip install -r requirements.txt antes de executar o script.: 


3) Atenção para entrada de parametros no arquivo params.json, que deve estar localizado na pasta AlgEvolutivoRCE.
   O arquivo params.json contém os parâmetros de configuração do algoritmo evolutivo, como taxa de mutação, taxa de crossover, número de gerações, variaveis de decisão e etc.
   Certifique-se de que seja passada uma função objetivo definida pelo usuario para o objeto `Setup` no momento da instanciação do Algoritmo Evolutivo, como por exemplo `rastrigin_benchmark`, `esfera_benchmark` ou `rosenbrock_benchmark e etc`.
   
"""

# Import functions benchmark
#? Foi Criado um arquivo em `utils/functions_fitness/functions_benchmarking.py` para armazenar as funções de benchmark usadas no primeiro artigo e a função de avaliação da rede IEEE 14.
# Voce foi olhar o arquivo config.py para gerenciar a quantidade de execuções do algoritimo.
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


def run_framework_single_execution(config_num=1, exec_num=1):
    """Função principal para executar o framework de otimização."""
    start = datetime.now()

    #! Entrada de dados simulando que seja uma planillha em excel
    dados = entrada_de_dados()

    # Instanciando os Objetos
    setup = Setup(params, fitness_function = lambda ind: funcao_objetivo_IEEE14(ind, setup),
                  tamanho_hash=(dados["num_contingencias"] * dados["num_carregamentos"]*(2**dados["num_desligamentos"])))

    def consulta_hashtable():
        #! TODO para melhor performace
        try:
            # Ler xlsx no início da run_framework e verificar logo depois de instanciar o setup se o xlsx existe e caso exista, coloca o conteúdo do xlsx no setup.tabela_hash.
            if os.path.exists(f"hash_table.xlsx"):
                print("\n\nFazendo consulta para setup.tabela_hash")

                hash_excel = pd.read_excel("hash_table.xlsx")

                if not hash_excel.empty and not hash_excel.isnull().values.any():
                    print(hash_excel.head())

                    setup.tabela_hash = hash_excel['Fitness'].to_dict()
                    neg_one_count = list(setup.tabela_hash.values()).count(-1)

                    if -1 in setup.tabela_hash.values():
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
    consulta_hashtable()


    alg = AlgoritimoEvolutivoRCE(setup, DEBUG = True)

    # Loop Algoritmo Evolutivo podendo receber a função objetivo e as variaveis do problema
    pop_with_repopulation, logbook_with_repopulation, best_variables = alg.run(
        RCE=True,
    )


    def output(start):
        print("\n\nEvolução concluída  - 100%")
        print(f"Best variables", best_variables)

        # Passando os valores do array direto no dataframe com os index como chave (hash = chave, valor)
        hash_df1 = pd.DataFrame(setup.tabela_hash, columns=['Fitness'])
        hash_df1.sort_values(by='Fitness', ascending=False, inplace=True)
        hash_df1.to_excel("hash_table.xlsx", index=False)

        # # Resultados
        x, y, z, fig = alg.dashboard.visualize(
            logbook_with_repopulation, pop_with_repopulation,
            config_num=config_num, execution_num=exec_num
        )

        print(f"Objective function runs : {setup.objectiveruns}")
        print(f"Hash table reads : {setup.hashtablereads}")

        end = datetime.now()
        elapsed = end - start
        formatted_time = format_elapsed_time(elapsed)
        print(f"Elapsed Time in execution : {formatted_time}")

    output(start)


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
    """Converte os valores de um dicionário para int, exceto para as chaves especificadas."""
    float_keys = {"MUTACAO", "CROSSOVER", "PORCENTAGEM"}
    for key, value in params.items():
        if key.upper() in float_keys:
            #print(key,value)
            params[key] = float(value)
        elif isinstance(value, list):
            print(f"Valor da chave {key} é uma lista, não será convertido para int.")
        else:
            params[key] = int(value)
    return params




def run_framework_groups_executions():
    """Função para executar o framework com múltiplas execuções baseadas em grupos de parâmetros."""
    
    # Parâmetros que devem ser float/int
    float_params = {"MUTACAO", "CROSSOVER", "PORCENTAGEM"}
    int_params = {"NUM_GENERATIONS", "POP_SIZE"}
    
    # Carrega os parâmetros default do AG (params.json)
    params = load_params(f"{BASE_DIR}/params.json")
    config = load_params(f"{BASE_DIR}/options.json")
    
    # Convert values to int, except for specified float keys
    params = convert_values_to_int(params)
    #options = convert_values_to_int(options)

    # Defina os nomes dos parâmetros variáveis
    param_names = ["MUTACAO", "CROSSOVER", "NUM_GENERATIONS", "POP_SIZE"]
    param_values = [config[name] for name in param_names]

    # Gera todas as combinações possíveis dos parâmetros variáveis
    combinacoes = list(itertools.product(*param_values))
    repeticoes = config.get('repeticoes_por_config', 1)
    
    print(f"Combinação = {combinacoes} | Repetição = {repeticoes}")

    for idx, valores in enumerate(combinacoes):
        params_exec = params.copy()
        

        for rep in range(repeticoes):
            
            print(f"Execução da configuração: {idx} = {rep}")
            
            # Atualiza mensagem na tela do Streamlit
            print(f"\n\nIniciando execução com a combinação: {dict(zip(param_names, valores))}")
            print(f"Combinação de Configuração {idx+1}/{len(combinacoes)} - Execução {rep+1}/{repeticoes}")

            dados = entrada_de_dados()
            print(f"\n\nIniciando execução com os parâmetros: {config}")
            setup = Setup(params_exec, fitness_function=funcao_objetivo_IEEE14,
                          tamanho_hash=(dados["num_contingencias"] * dados["num_carregamentos"] * (2 ** dados["num_desligamentos"])))
            
            #TODO for loop para conjunto de configurações de parametros_opcionais
            def consulta_hashtable():
                #! TODO para melhor performace
                try:
                    # Ler xlsx no início da run_framework e verificar logo depois de instanciar o setup se o xlsx existe e caso exista, coloca o conteúdo do xlsx no setup.tabela_hash.
                    if os.path.exists(f"hash_table.xlsx"):
                        print("\n\nFazendo consulta para setup.tabela_hash")

                        hash_excel = pd.read_excel("hash_table.xlsx")

                        if not hash_excel.empty and not hash_excel.isnull().values.any():
                            print(hash_excel.head())

                            setup.tabela_hash = hash_excel['Fitness'].to_dict()
                            neg_one_count = list(setup.tabela_hash.values()).count(-1)

                            if -1 in setup.tabela_hash.values():
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
            consulta_hashtable()

            
            # Usando o algoritimo Genetico do DEAP
            alg = AlgoritimoEvolutivoRCE(setup, DEBUG = False)

            # Run the utility function to load many executions
            load_many_executions(config, setup, alg)

                    
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
        
    # Instanciando o Setup para configuração
    setup = Setup(params, fitness_function = fitness_func,
                  tamanho_hash=(entrada_de_dados()["num_contingencias"] * entrada_de_dados()["num_carregamentos"]*(2**entrada_de_dados()["num_desligamentos"])))
    
    #TODO for loop para conjunto de configurações de parametros_opcionais
    def consulta_hashtable():
        #! TODO para melhor performace
        try:
            # Ler xlsx no início da run_framework e verificar logo depois de instanciar o setup se o xlsx existe e caso exista, coloca o conteúdo do xlsx no setup.tabela_hash.
            if os.path.exists(f"hash_table.xlsx"):
                print("\n\nFazendo consulta para setup.tabela_hash")

                hash_excel = pd.read_excel("hash_table.xlsx")

                if not hash_excel.empty and not hash_excel.isnull().values.any():
                    print(hash_excel.head())

                    setup.tabela_hash = hash_excel['Fitness'].to_dict()
                    neg_one_count = list(setup.tabela_hash.values()).count(-1)

                    if -1 in setup.tabela_hash.values():
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
    consulta_hashtable()

    
    # Usando o algoritimo Genetico do DEAP
    alg = AlgoritimoEvolutivoRCE(setup, DEBUG = False)

    # Run the utility function to load many executions
    load_many_executions(options, setup, alg, config_num=config_num, exec_num=exec_num)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Executa o framework RCE.')
    parser.add_argument('--config_num', type=int, default=1, help='Número da configuração')
    parser.add_argument('--exec_num', type=int, default=1, help='Número da execução')
    args = parser.parse_args()

    options = load_params(f"{BASE_DIR}/options.json")
    #export_all_configs_to_json(options)

    # Check if the user wants to run multiple executions or a single execution
    if options.get("key", True):
        print("Running multiple executions...")
        run_framework_many_executions(function_bechmarking=False, config_num=args.config_num, exec_num=args.exec_num)
    else:
        print("Running a single execution...")
        run_framework_single_execution(config_num=args.config_num, exec_num=args.exec_num)





