
# gera o arquivo para rodar dentro do colab

#%%writefile app.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

import pickle
import plotly.io as pio
import os

import numpy as np
import matplotlib.pyplot as plt

#!pip install streamlit pandas plotly openpyxl

from .Setup import params


class DashboardApp:
    """Classe principal para criar o dashboard interativo com Streamlit."""

    def __init__(self):
        st.set_page_config(layout="wide", page_title="Dashboard Interativo")
        self.df = None
        self.fit_array = []

    # codigo antigo

    def generateSimpleDataset(self):
        # Geração dos dados
        data = pd.DataFrame(
            {"x": np.linspace(-5, 5, 400), "y": np.linspace(-5, 5, 400)}
        )
        # Generate meshgrid data
        x = np.linspace(-5.15, 5.15, 100)
        y = np.linspace(-5.15, 5.15, 100)
        X, Y = np.meshgrid(x, y)

        # Calculate function values
        # print(X.shape,Y.shape)
        return X, Y


    def default_rastrigin(self, x, y):
        return 20 + x**2 + y**2 - 10 * (np.cos(2 * np.pi * x) + np.cos(2 * np.pi * y))

    def plot_Rastrigin_2D(self, X, Y, Z_rastrigin, logbook, best_variables=[]):
        fig = plt.figure(figsize=(18, 10))
        ax1 = fig.add_subplot(231)
        generation = logbook.select("gen")
        statics = self.calculate_stats(logbook)
        title = f"Estrategia RCE - Crossover: {params['CROSSOVER']*100}% e Mutação: {params['MUTACAO']*100}% " if len(generation) > 1 else "Sem Repopulação RCE"

        line1 = ax1.plot(
            generation, statics["min_fitness"], "*b-", label="Minimum Fitness"
        )
        line2 = ax1.plot(
            generation, statics["avg_fitness"], "+r-", label="Average Fitness"
        )
        line3 = ax1.plot(
            generation, statics["max_fitness"], "og-", label="Maximum Fitness"
        )
        ax1.set_xlabel("Generations")
        ax1.set_ylabel("Func. Fitness")
        ax1.set_title(title)
        lns = line1 + line2 + line3
        labs = [l.get_label() for l in lns]
        ax1.legend(lns, labs, loc="upper right")

        #! Graficos barras
        ax3 = fig.add_subplot(232)

        if len(generation) > 1:
            best_solutions = [
                min(statics["min_fitness"]) for i in range(len(generation))
            ]
            avg_fitness = statics["avg_fitness"]
            generations = np.arange(1, len(generation) + 1)

            ax3.plot(
                generations,
                avg_fitness,
                marker="o",
                color="r",
                linestyle="--",
                label="Média Fitness por Geração",
            )
            ax3.bar(
                generations,
                statics["min_fitness"],
                color="green",
                label="Melhor Fitness por Geração",
            )
            ax3.set_title("Best Fitness por Geração")
            ax3.set_xlabel("Geração")
            ax3.set_ylabel("Fitness")
            ax3.legend()

        #! Rastrigin 3D (rainer nao gosta)
        #ax5 = fig.add_subplot(233, projection="3d")
        #ax5.plot_surface(X, Y, Z_rastrigin, cmap="viridis", edgecolor="none")
        #ax5.set_title("Rastrigin Function 3D")
        #ax5.set_xlabel("X")
        #ax5.set_ylabel("Y")
        #ax5.set_zlabel("Z")

        plt.tight_layout()
        plt.show()

    def show_rastrigin_benchmark(self, logbook, best=[]):
        X, Y = self.generateSimpleDataset()

        Z_3D_rastrigin = self.default_rastrigin(X, Y)

        self.plot_Rastrigin_2D(X, Y, Z_3D_rastrigin, logbook, best)

    def graficoRCE(self, gen, lista,  repopulation=False):
        title = f"Estrategia RCE - Crossover: {params['CROSSOVER']*100}% e Mutação: {params['MUTACAO']*100}% " if repopulation else "Sem Repopulação RCE"

        # Create a new figure before plotting
        figure = go.Figure()   # Create new figure if None

        figure.add_trace(
            go.Line(
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
            go.Line(
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
            go.Line(
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
            xaxis_title="Generation",
            yaxis_title="Fitness",
            legend_title="Algoritimo Evolutivo",
            template="plotly", #      ['ggplot2', 'seaborn', 'simple_white', 'plotly', 'plotly_white', ...]
            overwrite= True
            )

        return figure

    # --- visualize MODIFICADO (salva dados e chama Streamlit) ---
    def visualize(self, logbook, pop, repopulation=True, DEBUG=False, current_params=None, execution_num=1):
        """
        Processa dados, imprime no console, RETORNA figura e resultados,
        E salva os arquivos de dados e figura com um número de execução.
        """
        generation = []
        statics = {}
        array_values = []

        best_solution_index = -1
        best_solution_variables = []
        best_solution_fitness = float('inf')

        try:
            generation = logbook.select("gen")
            statics = self.calculate_stats(logbook)

            if DEBUG:
                print("\n\nDEBUG: Dados para gráfico (generation x statics)")
                print(len(statics["min_fitness"])) # DEBGU = 90

            min_fitness_values = statics.get("min_fitness", [])
            #print(len(min_fitness_values))
            if not min_fitness_values: raise ValueError("Min fitness list is empty")
            best_solution_fitness = min(min_fitness_values)
            best_solution_index = min_fitness_values.index(best_solution_fitness)

            
            # Foi feito os SLICING  porque o deap acumula os resultados  de fitness na varaiveal statics
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

            print("\n\n")
            print("="*90)
            print(f"  >>> Soluções do problema (Execução {execution_num} - Console Output) <<<")
            print("="*90)
            print(f"Best Generation: {best_solution_index}")
            print(f"Best Variables: {best_solution_variables}")
            print(f"Best Fitness: {best_solution_fitness}")
            print("="*90)

            

            grafico_RCE = self.graficoRCE(generation, array_values, repopulation=repopulation)

            # Exibir a figura no notebook
            #fig.show()

             # --- MODIFIED: Define filenames based on execution_num ---
            if execution_num is None:
                # Decide fallback behavior or raise error if number is always required
                # Option 1: Raise error (safer if logic depends on it)
                print("WARN: execution_num not provided. Using default filenames.")

                raise ValueError("Execution number (execution_num) must be provided to visualize for saving files.")

            else:

                # check se o diretorio output exists
                if not os.path.exists("./output"):
                    os.makedirs("./output")
                    print("Diretório 'output' criado com sucesso.")
                else:
                    print("Diretório 'output' já existe.")

                data_file = f"./output/dashboard_data_{execution_num}.pkl"
                fig_file = f"./output/dashboard_fig_{execution_num}.json"
                print(f"INFO: Arquivos de saída para execução {execution_num}: {data_file}, {fig_file}")

                # --- Salvar dados e figura para o script Streamlit ---
                print(f"INFO: Salvando dados para visualizador Streamlit (Execução {execution_num})...\n") # Added execution num here
                data_to_save = {
                    'execution_num': execution_num, # Store execution number in data
                    'best_gen_idx': best_solution_index,
                    'best_vars': best_solution_variables,
                    'best_fitness': best_solution_fitness,
                    'params': current_params if current_params else params,
                    'logbook_data': {
                        'generation': generation,
                        'statics': statics
                    }
                }

            # Salvar a figura em formato HTML
            fig_filename = f"output/grafico_execucao_{execution_num}.html"
            grafico_RCE.write_html(fig_filename)
            print(f"INFO: Figura salva em {fig_filename}")


            # Salva os dados no arquivo .pkl numerado
            with open(data_file, 'wb') as f:
                pickle.dump(data_to_save, f)


            # Salva a figura no arquivo .json numerado
            fig_json = pio.to_json(grafico_RCE)
            with open(fig_file, 'w') as f:
                f.write(fig_json)
            print(f"INFO: Dados e figura para execução {execution_num} salvos com sucesso.") # Added execution num here

        except Exception as e:
            print(f"ERRO em visualize (Execução {execution_num}): {e}") # Added execution num here
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
            df.to_excel("./statistics_RCE.xlsx", index=False)

        return avg_fitness, std_fitness
