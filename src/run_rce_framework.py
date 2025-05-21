import time
import numpy as np
import pandas as pd

# Import RCE Framework
from AlgEvolutivoRCE.Setup import Setup
from AlgEvolutivoRCE.alg_evolutivo_rce import AlgoritimoEvolutivoRCE
from AlgEvolutivoRCE.Dashboard import DashboardApp

# Import functions benchmark
from utils.functions_fitness.functions_benchmarking import rosenbrock_benchmark,esfera_benchmark,rastrigin, evaluate

from get_folder import FOLDER_NAME
import json


def load_params(file_path):
    with open(file_path, "r") as file:
        params = json.load(file)
    return params


params = load_params("params.json")

options = {
        "key": True,
        "value": 10,
        "parametros_opcionais": [
             {"MUTACAO": [90,80,70]},
             {"CROSSOVER": [90,80,70]},
             {'NUM_GENERATIONS': [100, 200, 300]},

        ]
    }


def run_framework(RCE = False):
    if options["key"]:

        for i in range(options["value"]):
            print("\nExecução", i + 1)

            start_time = time.time()  # Inicia a contagem do tempo para cada execução

            # Loop principal do Algoritmo Evolutivo
            pop_with_repopulation, logbook_with_repopulation, best_variables = alg.run(RCE)
            print("\n\nEvolução concluída  - 100%")

            # Resultados
            x, y, z, fig = dashboard.visualize(logbook_with_repopulation, pop_with_repopulation, execution_num=i + 1)
            

            end_time = time.time()  # Finaliza a contagem do tempo para cada execução
            execution_time = end_time - start_time
            execution_times.append(execution_time)  # Armazena o tempo de execução

            # Append results to the list
            results_consolidados.append({"execution": i + 1, "solution_variables": y, "best_fitness": z, "execution_time": execution_time})

    else: # Use st.pyplot with stash=False to prevent overwriting
        print("False! Rodando o framework uma unica vez!")
        start_time = time.time()  # Inicia a contagem do tempo para a execução única

        # Loop principal do Algoritmo Evolutivo
        pop_with_repopulation, logbook_with_repopulation, best_variables = alg.run(RCE=True)
        print("\n\nEvolução concluída  - 100%")

        # Resultados
        x, y, z, fig = dashboard.visualize(logbook_with_repopulation, pop_with_repopulation)

        end_time = time.time()  # Finaliza a contagem do tempo para a execução única
        execution_time = end_time - start_time

        # Append results to the list (for single execution)
        results_consolidados.append({"execution": 1, "solution_variables": y, "best_fitness": z, "execution_time": execution_time})

        print(f"Tempo de execução: {execution_time:.2f} segundos")

    # Calcula a média e o desvio padrão dos tempos de execução
    avg_execution_time = np.mean(execution_times)
    std_execution_time = np.std(execution_times)

    print(f"Tempo médio de execução: {avg_execution_time:.2f} segundos")
    print(f"Desvio padrão do tempo de execução: {std_execution_time:.2f} segundos")


    # Create the DataFrame
    results_consolidados_df = pd.DataFrame(results_consolidados)

    # Check for empty or non-numerical columns before calculation
    if "solution_variables" in results_consolidados_df and results_consolidados_df["solution_variables"].apply(lambda x: isinstance(x, (int, float))).any():
            min_solution = results_consolidados_df["solution_variables"].apply(np.min)
            print("\nMínimo das Variáveis de Solução:", np.min(min_solution))
            results_consolidados_df["min_solution_variables"] = min_solution
    else:
            print("WARN: solution_variables column is empty or non-numerical. Skipping min calculation.")


    results_consolidados_df["execution_time"] = results_consolidados_df["execution_time"].apply(lambda x: f"{x:.2f} segundos")

    # exportar para excel
    results_consolidados_df.to_excel(f"{FOLDER_NAME}/results_consolidados.xlsx", index=False)
    print("SALVANDO EM... ",FOLDER_NAME)
     # Display or use the results
    print("\nResultados Consolidados:")
    results_consolidados_df.sort_values(by="best_fitness", inplace=True)
    results_consolidados_df.describe()

    # Display the DataFrame in a more readable format
    print("\nDataFrame:")
    print(results_consolidados_df.to_string(index=False))

    print("\n\n")
    print("FIM DO PROGRAMA")

results_consolidados = []  # Initialize an empty list to store results
execution_times = []  # Lista para armazenar os tempos de execução

if __name__ == "__main__":

    #! ainda seria possivel criar um pacote no pip e instanciar?
    setup = Setup(params, evaluate)
    alg = AlgoritimoEvolutivoRCE(setup, DEBUG=False)
    dashboard = DashboardApp(options)

    run_framework(
         RCE= True, # True = RCE, False = Algoritmo Evolutivo Deap com minimização
    )
    


