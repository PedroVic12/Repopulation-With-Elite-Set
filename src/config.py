import json
from pathlib import Path
import pathlib
import streamlit as st
import pandas as pd
import time
import numpy as np
from IPython.display import display


# 4 parametros variando [Mutação, Crossover, Var DIFF, DELTA e restante fixo 

configuracoes_execucoes = {
        "key": True,
        "value": 5,
        "parametros_opcionais": [
             {"MUTACAO": [90,80,70, 60]},
             {"CROSSOVER": [90,80,70, 60]},
             {'NUM_GENERATIONS': [25, 50, 100, 500]},
             {'POP_SIZE': [10, 30, 50, 100]},

        ]
}

options_main_file = configuracoes_execucoes

 
def entrada_de_dados():
    
    #TODO
    # A ideia é simular a leitura de um arquivo JSON ou Excel que contenha os dados de agendamentos e contingências.
    
    
    # Tabela agendamentos em xlsx hardcoded
    agendamento_df = pd.DataFrame([
            {"ramo": [1, 4], "inicio": "14:00", "duracao": 6 ,"prioridade": 4},
            {"ramo": [1, 3], "inicio": "15:00", "duracao": 5, "prioridade": 1},
            {"ramo": [3, 6], "inicio": "14:00", "duracao": 6, "prioridade": 1},
            {"ramo": [11, 12], "inicio": "18:00", "duracao": 6, "prioridade": 1},
            {"ramo": [9, 10], "inicio": "15:00", "duracao": 4, "prioridade": 1}
        ])

    contingencia_df = pd.DataFrame([
                {"contingencia":1,  "from":2 , "to": 3},
                {"contingencia":2,  "from":5 , "to": 12},
                {"contingencia":3,  "from":12 , "to": 13},
        ])

        # Generate hash key (teste 01)
    contingencias = contingencia_df['contingencia'].to_list()
    num_carregamentos = 3
    num_contingencias = len(contingencias)  # 3
    num_desligamentos = len(agendamento_df)  # 5
    
    return {
        "contigencias": contingencias,
        "num_carregamentos": num_carregamentos,
        "num_contingencias": num_contingencias,
        "num_desligamentos": num_desligamentos,
        "horarios_agendamento": agendamento_df,
         
    }
    







def get_folder_path():
    BASE_DIR = pathlib.Path(__file__).resolve().parent  

    # Define o caminho relativo para a pasta "output" dentro do projeto
    FOLDER_NAME = BASE_DIR / "output"

    # Cria a pasta "output" se ela não existir
    FOLDER_NAME.mkdir(parents=True, exist_ok=True)
    print("\nFOLDER_NAME =", FOLDER_NAME)
    print("FOLDER RAIZ do projeto =", FOLDER_NAME.parent)
    print("\n")

    return FOLDER_NAME
FOLDER_NAME = get_folder_path()




results_consolidados = []  # Initialize an empty list to store results
execution_times = []  # Lista para armazenar os tempos de execução





def load_many_executions(dict_key_value, algoritmo):
    if dict_key_value["key"]:

        for i in range(dict_key_value["value"]):
            print("\nExecução", i + 1)

            start_time = time.time()  # Inicia a contagem do tempo para cada execução

            # Loop principal do Algoritmo Evolutivo
            pop_with_repopulation, logbook_with_repopulation, best_variables = algoritmo.run(RCE=True)
            print("\n\nEvolução concluída  - 100%")

            # Resultados
            x, y, z, grafico = algoritmo.dashboard.visualize(logbook_with_repopulation, pop_with_repopulation, execution_num=i + 1)

            end_time = time.time()  # Finaliza a contagem do tempo para cada execução
            execution_time = end_time - start_time
            execution_times.append(execution_time)  # Armazena o tempo de execução

            # Append results to the list
            results_consolidados.append({"execution": i + 1, "solution_variables": y, "best_fitness": z, "best_generations": x,"execution_time": execution_time})

    else: # Use st.pyplot with stash=False to prevent overwriting
        print("False! Rodando o framework uma unica vez!")
        start_time = time.time()  # Inicia a contagem do tempo para a execução única

        # Loop principal do Algoritmo Evolutivo
        pop_with_repopulation, logbook_with_repopulation, best_variables = algoritmo.run(RCE=True)
        print("\n\nEvolução concluída  - 100%")

        # Resultados
        x, y, z, fig = algoritmo.dashboard.visualize(logbook_with_repopulation, pop_with_repopulation)

        end_time = time.time()  # Finaliza a contagem do tempo para a execução única
        execution_time = end_time - start_time

        # Append results to the list (for single execution)
        results_consolidados.append({"execution": i + 1, "solution_variables": y, "best_fitness": z, "best_generations": x,"execution_time": execution_time})

        print(f"Tempo de execução: {execution_time:.2f} segundos")

    # Calcula a média e o desvio padrão dos tempos de execução
    avg_execution_time = np.mean(execution_times)
    std_execution_time = np.std(execution_times)

    print(f"Tempo médio de execução: {avg_execution_time:.2f} segundos")
    print(f"Desvio padrão do tempo de execução: {std_execution_time:.2f} segundos")


    # Create the DataFrame
    results_consolidados_df = pd.DataFrame(results_consolidados)

    results_consolidados_df["execution_time"] = results_consolidados_df["execution_time"].apply(lambda x: f"{x:.2f} segundos")

    # exportar para excel
    results_consolidados_df.to_excel("results_consolidados.xlsx", index=False)

     # Display or use the results
    print("\nResultados Consolidados:")
    results_consolidados_df.sort_values(by="best_fitness", inplace=True)
    display(results_consolidados_df)


