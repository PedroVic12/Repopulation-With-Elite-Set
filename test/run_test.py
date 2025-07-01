# -*- coding: utf-8 -*-
# Import RCE Framework

import sys
import os
# Add the parent directory to the system path to import modules from the src folder
# This is necessary to run the script from the test folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the necessary modules from the src folder
from src.AlgEvolutivoRCE.Setup import Setup
from src.AlgEvolutivoRCE.alg_evolutivo_rce import AlgoritimoEvolutivoRCE

# Utils 
from src.config import FOLDER_NAME, options_main_file, entrada_de_dados,load_many_executions, format_elapsed_time

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
# streamlit run dashboard_rce_app_v9.py
```

2) Para executar o Algoritmo Evolutivo com Reposição de Conjunto de Elite (RCE), execute esse mesmo script no terminal run_rce_framework.py, sugiro rodar o pip install -r requirements.txt antes de executar o script.: 


3) Atenção para entrada de parametros no arquivo params.json, que deve estar localizado na pasta AlgEvolutivoRCE.
   O arquivo params.json contém os parâmetros de configuração do algoritmo evolutivo, como taxa de mutação, taxa de crossover, número de gerações, variaveis de decisão e etc.
   Certifique-se de que seja passada uma função objetivo definida pelo usuario para o objeto `Setup` no momento da instanciação do Algoritmo Evolutivo, como por exemplo `rastrigin_benchmark`, `esfera_benchmark` ou `rosenbrock_benchmark e etc`.
   
"""

# Import functions benchmark
#? Foi Criado um arquivo em `utils/functions_fitness/functions_benchmarking.py` para armazenar as funções de benchmark usadas no primeiro artigo e a função de avaliação da rede IEEE 14.
# Voce foi olhar o arquivo config.py para gerenciar a quantidade de execuções do algoritimo.
from src.utils.functions_fitness.functions_benchmarking import rosenbrock_benchmark,esfera_benchmark,rastrigin, evaluate, funcao_objetivo_IEEE14

results_consolidados = []  # Initialize an empty list to store results
execution_times = []  # Lista para armazenar os tempos de execução
BASE_DIR = pathlib.Path(__file__).resolve().parent 

#! Lendo os parametros em JSON em /AlgEvolutivoRCE/params.json
def load_params(file_path):
    with open(file_path, "r") as file:
        params = json.load(file)
    return params

# Load parameters from the JSON file in any configuration of PC
params = load_params(f"{BASE_DIR}/params.json")

# windows
#params = load_params(r"C:\Users\Pedro Victor R V\Documents\GitHub\Repopulation-With-Elite-Set\src\AlgEvolutivoRCE\params.json")


def run_framework():
    """Função principal para executar o framework de otimização."""
    start = datetime.now()

    #! Entrada de dados simulando que seja uma planillha em excel
    dados = entrada_de_dados()

    # Instanciando os Objetos
    setup = Setup(params, fitness_function = funcao_objetivo_IEEE14,
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
        )

        print(f"Objective function runs : {setup.objectiveruns}")
        print(f"Hash table reads : {setup.hashtablereads}")

        end = datetime.now()
        elapsed = end - start
        formatted_time = format_elapsed_time(elapsed)
        print(f"Elapsed Time in execution : {formatted_time}")

    output(start)



# função que converte todas as value de cada key do json em int menos em duas colunas passando o nome
def convert_values_to_int(params):
    """Converte os valores de um dicionário para int, exceto para as chaves especificadas."""
    float_keys = {"MUTACAO", "CROSSOVER", "PORCENTAGEM"}
    for key, value in params.items():
        if key.upper() in float_keys:
            print(key,value)
            params[key] = float(value)
        elif isinstance(value, list):
            print(f"Valor da chave {key} é uma lista, não será convertido para int.")
        else:
            params[key] = int(value)
    return params



import itertools

def test_run_framework_groups_executions():
    """Função para executar o framework com múltiplas execuções baseadas em grupos de parâmetros."""

    # Carrega os parâmetros default do AG (params.json)
    params = load_params(f"{BASE_DIR}/params.json")
    
    
    
    # Carrega as opções configuradas pelo usuário (options.json)
    config = load_params(f"{BASE_DIR}/options.json")
    
    convert_values_to_int(params)
    convert_values_to_int(config)

    # Extrai os parâmetros variáveis definidos pelo usuário
    param_opcionais = config['parametros_opcionais']
    param_names = [list(d.keys())[0] for d in param_opcionais]
    param_values = [list(d.values())[0] for d in param_opcionais]

    # Parâmetros que devem ser float
    float_params = {"MUTACAO", "CROSSOVER", "PORCENTAGEM"}

    # Gera todas as combinações possíveis dos parâmetros variáveis
    combinacoes = list(itertools.product(*param_values))
    repeticoes = config.get('repeticoes_por_config', 1)

    for idx, valores in enumerate(combinacoes):
        params_exec = params.copy()

        # Atualiza os parâmetros variáveis para esta combinação
        for name, value in zip(param_names, valores):
            if name.upper() in float_params:
                params_exec[name] = float(value)
            else:
                params_exec[name] = int(value)

        # Adiciona os parâmetros fixos do AG
        for rep in range(repeticoes):
            # Exibe a combinação atual e a repetição
            print(f"\n\nIniciando execução com a combinação: {dict(zip(param_names, valores))}")
            print(f"\nExecução combinação {idx+1}/{len(combinacoes)} - Repetição {rep+1}/{repeticoes}")
            dados = entrada_de_dados()
            setup = Setup(params_exec, fitness_function=funcao_objetivo_IEEE14,
                          tamanho_hash=(dados["num_contingencias"] * dados["num_carregamentos"] * (2 ** dados["num_desligamentos"])))
            alg = AlgoritimoEvolutivoRCE(setup, DEBUG=False)
            load_many_executions(config, setup, alg)


def test_run_framework_many_executions():
    
    """Função para executar o framework com múltiplas execuções."""
    
    # Load parameters from the JSON file in any configuration of PC
    params = load_params(f"{BASE_DIR}/params.json")
    options = load_params(f"{BASE_DIR}/options.json")
    
    convert_values_to_int(params)
    convert_values_to_int(options)
    
    print(f"Parâmetros do Algoritmo Evolutivo: {params}")   

    
    # Instanciando os Objetos
    setup = Setup(params, fitness_function = funcao_objetivo_IEEE14,
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

    

    alg = AlgoritimoEvolutivoRCE(setup, DEBUG = False)

    # Run the utility function to load many executions
    load_many_executions(options, setup, alg)



if __name__ == "__main__":
    # Check if the user wants to run multiple executions or a single execution
    if options_main_file["key"]:
        print("Running multiple executions...")
        test_run_framework_many_executions()
        #test_run_framework_groups_executions()
    else:
        print("Running a single execution...")
        run_framework()





