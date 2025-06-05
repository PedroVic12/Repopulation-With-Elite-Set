
import time
import numpy as np
import pandas as pd

# Import RCE Framework
from AlgEvolutivoRCE.Setup import Setup
from AlgEvolutivoRCE.alg_evolutivo_rce import AlgoritimoEvolutivoRCE

# Utils 
from config import FOLDER_NAME, options_main_file, entrada_de_dados,load_many_executions
import json
import pathlib


#!DOCS PVRV - 04/06/25
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
from utils.functions_fitness.functions_benchmarking import rosenbrock_benchmark,esfera_benchmark,rastrigin, evaluate, funcao_objetivo_IEEE14


results_consolidados = []  # Initialize an empty list to store results
execution_times = []  # Lista para armazenar os tempos de execução
BASE_DIR = pathlib.Path(__file__).resolve().parent 

#! Lendo os parametros em JSON em /AlgEvolutivoRCE/params.json
def load_params(file_path):
    with open(file_path, "r") as file:
        params = json.load(file)
    return params

# Load parameters from the JSON file in any configuration of PC
params = load_params(f"{BASE_DIR}/AlgEvolutivoRCE/params.json")

# windows
#params = load_params(r"C:\Users\Pedro Victor R V\Documents\GitHub\Repopulation-With-Elite-Set\src\AlgEvolutivoRCE\params.json")


def run_framework():
    """Função principal para executar o framework de otimização."""
    
    
    from datetime import datetime
    start = datetime.now()
    
    #! Entrada de dados simulando que seja uma planillha em excel
    dados = entrada_de_dados()

    # Instanciando os Objetos
    setup = Setup(params, fitness_function = funcao_objetivo_IEEE14,
                  tamanho_hash=(dados["num_contingencias"] * dados["num_carregamentos"]*(2**dados["num_desligamentos"])))   
    
    alg = AlgoritimoEvolutivoRCE(setup, DEBUG = True)

    # Loop Algoritmo Evolutivo podendo receber a função objetivo e as variaveis do problema
    pop_with_repopulation, logbook_with_repopulation, best_variables = alg.run(
        RCE=True,
    )
    
    end = datetime.now()
    elapsed = end - start
    print(f"\n\nElapsed Time in execution : {elapsed}")
    print("\n\nEvolução concluída  - 100%")
    
    
    # Consolidado output console e dashboard
    f = open("output.txt", "w")
    print(best_variables, file=f)
    print(elapsed, file=f)
    print(logbook_with_repopulation, file=f)
    f.close()

    # Passando os valores do array direto no dataframe com os index como chave (hash = chave, valor)
    hash_df1 = pd.DataFrame(setup.tabela_hash, columns=['Fitness'])
    hash_df1.sort_values(by='Fitness', ascending=False, inplace=True)
    hash_df1.to_excel("hash_table.xlsx", index=False)

    # # Resultados
    #x, y, z, fig = alg.dashboard.visualize(
    #     logbook_with_repopulation, pop_with_repopulation,
    # )



def run_framework_many_executions():
    
    """Função para executar o framework com múltiplas execuções."""
    
    # Load parameters from the JSON file in any configuration of PC
    params = load_params(f"{BASE_DIR}/AlgEvolutivoRCE/params.json")
    
    # Instanciando os Objetos
    setup = Setup(params, fitness_function = funcao_objetivo_IEEE14,
                  tamanho_hash=(entrada_de_dados()["num_contingencias"] * entrada_de_dados()["num_carregamentos"]*(2**entrada_de_dados()["num_desligamentos"])))   
    
    alg = AlgoritimoEvolutivoRCE(setup, DEBUG = True)

    # Run the utility function to load many executions
    load_many_executions(options_main_file, alg)



if __name__ == "__main__":
    # Check if the user wants to run multiple executions or a single execution
    if options_main_file["key"]:
        print("Running multiple executions...")
        run_framework_many_executions()
    else:
        print("Running a single execution...")
        run_framework()
