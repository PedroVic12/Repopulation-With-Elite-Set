import time
import numpy as np
import pandas as pd

# Import RCE Framework
from AlgEvolutivoRCE.Setup import Setup
from AlgEvolutivoRCE.alg_evolutivo_rce import AlgoritimoEvolutivoRCE

# Utils 
from config import FOLDER_NAME, options_main_file
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
from utils.functions_fitness.functions_benchmarking import rosenbrock_benchmark,esfera_benchmark,rastrigin, evaluate, funcao_objetivo_IEEE14


results_consolidados = []  # Initialize an empty list to store results
execution_times = []  # Lista para armazenar os tempos de execução
BASE_DIR = pathlib.Path(__file__).resolve().parent 
#print(BASE_DIR)

#! Lendo os parametros em JSON em /AlgEvolutivoRCE/params.json
def load_params(file_path):
    with open(file_path, "r") as file:
        params = json.load(file)
    return params

# Load parameters from the JSON file in any configuration of PC
params = load_params(f"{BASE_DIR}/AlgEvolutivoRCE/params.json")

# windows
#params = load_params(r"C:\Users\Pedro Victor R V\Documents\GitHub\Repopulation-With-Elite-Set\src\AlgEvolutivoRCE\params.json")




def run_framework(RCE = False):
    """Function to run the evolutionary algorithm framework in one or multiple executions.

    Args:
        RCE (bool, optional): _description_. Defaults to False.
    """
    if options_main_file["key"]:

        for i in range(options_main_file["value"]):
            print("\nExecução", i + 1)

            start_time = time.time()  # Inicia a contagem do tempo para cada execução

            # Loop principal do Algoritmo Evolutivo
            pop_with_repopulation, logbook_with_repopulation, best_variables = alg.run(RCE)
            print("\n\nEvolução concluída  - 100%")

            # Resultados
            x, y, z, fig = alg.dashboard.visualize(logbook_with_repopulation, pop_with_repopulation, execution_num=i + 1)
            

            end_time = time.time()  # Finaliza a contagem do tempo para cada execução
            execution_time = end_time - start_time
            execution_times.append(execution_time)  # Armazena o tempo de execução

            # Append results to the list
            results_consolidados.append({"execution": i + 1, "solution_variables": y, "best_fitness": z, "best_generations": x,"execution_time": execution_time})

    else: # Use st.pyplot with stash=False to prevent overwriting
        print("False! Rodando o framework uma unica vez!")
        start_time = time.time()  # Inicia a contagem do tempo para a execução única

        # Loop principal do Algoritmo Evolutivo
        pop_with_repopulation, logbook_with_repopulation, best_variables = alg.run(RCE=True)
        print("\n\nEvolução concluída  - 100%")

        # Resultados
        x, y, z, fig = alg.dashboard.visualize(logbook_with_repopulation, pop_with_repopulation)

        end_time = time.time()  # Finaliza a contagem do tempo para a execução única
        execution_time = end_time - start_time

        # Append results to the list (for single execution)
        results_consolidados.append({"execution": i + 1, "solution_variables": y, "best_fitness": z, "best_generations": x,"execution_time": execution_time})
        print(f"Tempo de execução: {execution_time:.2f} segundos")

    # Calcula a média e o desvio padrão dos tempos de execução
    avg_execution_time = np.mean(execution_times)
    std_execution_time = np.std(execution_times)

    # Create the DataFrame
    results_consolidados_df = pd.DataFrame(results_consolidados)
    results_consolidados_df["execution_time"] = results_consolidados_df["execution_time"].apply(lambda x: f"{x:.2f} segundos")

    # exportar para excel
    results_consolidados_df.to_excel(f"{FOLDER_NAME}/results_consolidados.xlsx", index=False)
    print("SALVANDO RESULTADOS DE TODAS EXECUÇÔES EM... ",FOLDER_NAME)
    
    print(f"Tempo médio de execução: {avg_execution_time:.2f} segundos")
    print(f"Desvio padrão do tempo de execução: {std_execution_time:.2f} segundos")

    # Display or use the results
    print("\nResultados Consolidados:")
    results_consolidados_df.sort_values(by="best_fitness", inplace=True)
    print(results_consolidados_df.to_string(index=False))
    print("\n\n")
    print("FIM DO PROGRAMA")





if __name__ == "__main__":

    #! ainda seria possivel criar um pacote no pip e instanciar?
    setup = Setup(params, funcao_objetivo_IEEE14)
    alg = AlgoritimoEvolutivoRCE(setup, DEBUG=False)

    run_framework(
         RCE= True, # True = RCE, False = Algoritmo Evolutivo Deap com minimização
    )


    


