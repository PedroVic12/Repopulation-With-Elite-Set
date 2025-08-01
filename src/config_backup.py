from pathlib import Path
import pathlib
import pandas as pd
import numpy as np
from IPython.display import display
from datetime import datetime

from DashboardApp.controllers.Utils import FOLDER_NAME, PARAMETROS_JSON

# 4 parametros variando [Mutação, Crossover, Var DIFF, DELTA e restante fixo 

configuracoes_execucoes = {
        "key": True,
        "value": 7,
        "parametros_opcionais": [
            {"MUTACAO": [PARAMETROS_JSON['MUTACAO']]},
            {"CROSSOVER": [PARAMETROS_JSON['CROSSOVER']]},
            {'NUM_GENERATIONS': [PARAMETROS_JSON['NUM_GENERATIONS']]},
            {'POP_SIZE': [PARAMETROS_JSON['POP_SIZE']]},
        ]
}

options_main_file = configuracoes_execucoes

# Função para simular a entrada de dados, como se fosse a leitura de um arquivo JSON ou Excel
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
    


# Função para obter o caminho da pasta "output" dentro do projeto
def get_folder_path(debug = False):
    BASE_DIR = pathlib.Path(__file__).resolve().parent  

    # Define o caminho relativo para a pasta "output" dentro do projeto
    FOLDER_NAME = BASE_DIR / "output"

    # Cria a pasta "output" se ela não existir
    FOLDER_NAME.mkdir(parents=True, exist_ok=True)

    if debug:
        print("\nFOLDER_NAME =", FOLDER_NAME)
        print("FOLDER RAIZ do projeto =", FOLDER_NAME.parent)
        print("\n")

    return FOLDER_NAME


FOLDER_NAME = get_folder_path() # nome da pasta output resolvendo problemas de caminho
results_consolidados = []  # Initialize an empty list to store results
execution_times = []  # Lista para armazenar os tempos de execução


def format_elapsed_time(elapsed_time):
    """Formats the elapsed time into a human-readable string.

    Args:
        elapsed_time: A string representing the elapsed time in HH:MM:SS.ffffff format.

    Returns:
        A formatted string like "X h Y min Z s".
    """
    parts = str(elapsed_time).split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])

    formatted_time = ""
    if hours > 0:
        formatted_time += f"{hours} horas "
    if minutes > 0:
        formatted_time += f"{minutes} minutos "
    # Round seconds to the nearest second
    formatted_time += f"{int(round(seconds))} segundos"

    return formatted_time.strip()


def load_many_executions(options, setupobj, algoritmo):
    if options.get("key", True):
        for i in range(options["repeticoes_por_config"]):
            print("\n================================")
            print("\tExecução:", i + 1)
            print("================================\n")
            start = datetime.now()
            
            
            # Loop principal do Algoritmo Evolutivo
            pop_with_repopulation, logbook_with_repopulation, best_variables = algoritmo.run(RCE=True)
            print("\n\nEvolução concluída  - 100%")
            print(f"Best variables", best_variables)
            
            
            # # Resultados
            #TODO -> Mudar no metood visualize os nomes dos arquivos de cada execução. dasboard_config1_data1.pkl
            x, y, z, fig = algoritmo.dashboard.visualize(
                logbook_with_repopulation, pop_with_repopulation,
                execution_num = i + 1
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

            execution_times.append(elapsed)  # Armazena o tempo de execução

            # Append results to the list
            results_consolidados.append({"execution": i + 1, "solution_variables": y, "best_fitness": z, "best_generations": x,"execution_time": elapsed})



    # Calcula a média e o desvio padrão dos tempos de execução
    avg_execution_time = np.mean(execution_times)
    print(f"Tempo médio de execução: {avg_execution_time} segundos")


    # Create the DataFrame dos resultados
    results_consolidados_df = pd.DataFrame(results_consolidados)
    results_consolidados_df["execution_time"] = results_consolidados_df["execution_time"].apply(
        lambda x: f"{x.total_seconds():.2f} segundos" if hasattr(x, "total_seconds") else f"{x:.2f} segundos"
    )
    results_consolidados_df.to_excel(f"{FOLDER_NAME}/results_consolidados.xlsx", index=False)

    # Display or use the results
    print("\nResultados Consolidados salvo:")
    results_consolidados_df.sort_values(by="best_fitness", inplace=True)
    display(results_consolidados_df)


