
import pathlib
import pandas as pd
import plotly.graph_objects as go

import pickle
import plotly.io as pio
import os

import numpy as np
import matplotlib.pyplot as plt


import json

def load_params(file_path):
    """Carrega os parâmetros de um arquivo JSON."""
    with open(file_path, 'r') as file:
        params = json.load(file)
    return params


#params = load_params(r"C:\Users\Pedro Victor R V\Documents\GitHub\Repopulation-With-Elite-Set\src\AlgEvolutivoRCE\params.json")
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
#print(BASE_DIR)
params = load_params(f"{BASE_DIR}/params.json")



def get_folder_path():
    BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent  

    # Define o caminho relativo para a pasta "output" dentro do projeto
    FOLDER_NAME = BASE_DIR / "src" / "output"

    # Cria a pasta "output" se ela não existir
    FOLDER_NAME.mkdir(parents=True, exist_ok=True)
    print("\nFOLDER_NAME [DEBUG] =", FOLDER_NAME)
    #print("FOLDER RAIZ =", FOLDER_NAME.parent)

    return FOLDER_NAME

FOLDER_NAME = get_folder_path()





class DashboardApp:
    """Classe principal para criar o dashboard interativo com Streamlit."""

    def __init__(self,options):
        self.df = None
        self.fit_array = []
        self.optirons = options
        
    def graficoRCE(self, gen, lista,  repopulation=False):
        title = f"Estrategia RCE - Crossover: {params['CROSSOVER']*100}% e Mutação: {params['MUTACAO']*100}% " if repopulation else "Sem Repopulação RCE"

        # Create a new figure before plotting
        figure = go.Figure()   # Create new figure if None

        figure.add_trace(
            go.Scatter(
                x=gen,
                #y=lista["min_fitness"],
                y = lista[0],
                mode="lines+markers",
                name="Valor Min Fitness",
                marker=dict(symbol="star", color="blue"),
                line=dict(color="blue"),
            )
        )
        

        figure.add_trace(
            go.Scatter(
                x=gen,
                #y=lista["avg_fitness"],
                y = lista[1],

                mode="lines+markers",
                name="Média Fitness",
                marker=dict(symbol="cross", color="red"),
                line=dict(color="red"),
            )
        )
        
        
        figure.add_trace(
            go.Scatter(
                x=gen,
                #y=lista["max_fitness"],
                y = lista[2],

                mode="lines+markers",
                name="Valor Max Fitness",
                marker=dict(symbol="circle", color="green"),
                line=dict(color="green"),
            )
        )
       

        figure.update_traces(overwrite= True)

        figure.update_layout(
            title=title,
            #xaxis_title="Generation",
            #yaxis_title="Fitness",
            legend_title="Algoritimo Evolutivo",
            template="seaborn", #      ['ggplot2', 'seaborn', 'simple_white', 'plotly', 'plotly_white', ...]
            overwrite= True
            )

        return figure

    # --- visualize MODIFICADO (salva dados e chama Streamlit) ---
    def visualize(self, logbook, pop, repopulation=True, DEBUG=False, current_params=None, config_num=1, execution_num=1, all_results=None):
        """
        Processa dados, imprime no console, RETORNA figura e resultados,
        E salva os arquivos de dados e figura com um número de execução.
        """
        all_results = []
        generation = []
        statics = {}
        array_values = []

        save_html_results = False

        best_solution_index = -1
        best_solution_variables = []
        best_solution_fitness = float('inf')

        try:
            generation = logbook.select("gen")
            statics = self.calculate_stats(logbook)

            if DEBUG:
                print("\n\nDEBUG: Dados para gráfico (generation x statics)")
                print(len(statics["min_fitness"]))

            min_fitness_values = statics.get("min_fitness", [])

            if not min_fitness_values: raise ValueError("Min fitness list is empty")
            best_solution_fitness = min(min_fitness_values)
            best_solution_index = min_fitness_values.index(best_solution_fitness)

            
            # Foi feito os SLICING  porque o deap acumula os resultados  de fitness na variável statics
            array_values.append(
                statics.get("min_fitness", [])[(execution_num -1) * int(len(generation)/execution_num):(execution_num * int(len(generation)/execution_num)) -1] 
            )
            array_values.append(
                statics.get("avg_fitness", [])[(execution_num -1) * int(len(generation)/execution_num):(execution_num * int(len(generation)/execution_num)) -1] 
            )
            array_values.append(
                statics.get("max_fitness", [])[(execution_num -1) * int(len(generation)/execution_num):(execution_num * int(len(generation)/execution_num)) -1] 
            )


            if repopulation:
                best_solution_variables = pop[0] if pop else []
            else:
                print("WARN: Visualize - Lógica para 'best_solution_variables' sem repopulação usa fallback.")
                best_solution_variables = pop[0] if pop else []

            print("\n")
            print("="*90)
            print(f"  >>> Soluções do problema (Execução {execution_num} - Console Output) <<<")
            print("="*90)
            print(f"Best Generation: {best_solution_index}")
            print(f"Best Variables: {best_solution_variables}")
            print(f"Best Fitness: {best_solution_fitness}")
            print("="*90)

            grafico_RCE = self.graficoRCE(generation, array_values, repopulation=repopulation)

            # --- Salvar dados e figura para o script Streamlit ---
            data_to_save = {
                'execution_num': execution_num,
                'config_num': config_num,
                'best_gen_idx': best_solution_index,
                'best_vars': best_solution_variables,
                'best_fitness': best_solution_fitness,
                'params': current_params if current_params else params,
                'logbook_data': {
                    'generation': generation,
                    'statics': statics
                }
            }

            # Adiciona os resultados da execução atual à lista
            all_results.append(data_to_save)

            if save_html_results:
                # Salvar a figura em formato HTML
                output_path = f"{FOLDER_NAME}"
                data_file = f"{output_path}/dashboard_data_config{config_num}_exec{execution_num}.json"

                fig_filename = f"{output_path}/grafico_execucao_config{config_num}_exec{execution_num}.html"
                grafico_RCE.write_html(fig_filename)

                # Salva a lista completa de resultados
                with open(data_file, 'w') as f:
                    json.dump(all_results, f, indent=4, ensure_ascii=False)
                    
                print(f"\n[INFO]: Salvando dados .json e figura .html para Config {config_num} / Execução {execution_num} na pasta output")


        except Exception as e:
            print(f"\n\n\nERRO em visualize (Execução {execution_num}): {e}")
            return -1, [], float('inf'), None

        return best_solution_index, best_solution_variables, best_solution_fitness, grafico_RCE

    def calculate_stats(self, logbook):

        fit_avg = logbook.select("avg")
        fit_std = logbook.select("std")
        fit_min = logbook.select("min")
        fit_max = logbook.select("max")

        self.fit_array.append(fit_min)
        self.fit_array.append(fit_avg)
        self.fit_array.append(fit_max)
        self.fit_array.append(fit_std)

        return {
            "min_fitness": fit_min,
            "max_fitness": fit_max,
            "avg_fitness": fit_avg,
            "std_fitness": fit_std,
        }

    def statistics_per_generation_df(self, logbook, save = True):
        generations = logbook.select("gen")
        min_fitness = logbook.select("min")
        avg_fitness = logbook.select("avg")
        max_fitness = logbook.select("max")
        std_fitness = logbook.select("std")

        data = {
            "Generation": generations,
            "Min Fitness": min_fitness,
            "Average Fitness": avg_fitness,
            "Max Fitness": max_fitness,
            "Std Fitness": std_fitness,
        }

        df = pd.DataFrame(data)
        if save:
            df.to_excel(f"{FOLDER_NAME}/statistics_RCE.xlsx", index=False)

        return avg_fitness, std_fitness
