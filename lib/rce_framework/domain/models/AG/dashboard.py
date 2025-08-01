import pathlib
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import pickle
import json

class DashboardApp:
    def __init__(self, options):
        st.set_page_config(layout="wide", page_title="Dashboard Interativo")
        self.df = None
        self.fit_array = []
        self.options = options
        self.BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
        self.FOLDER_NAME = self.BASE_DIR / "src" / "output"
        self.FOLDER_NAME.mkdir(parents=True, exist_ok=True)

    def graficoRCE(self, gen, lista, repopulation=False):
        params = self.options
        title = f"Estrategia RCE - Crossover: {params['CROSSOVER']*100}% e Mutação: {params['MUTACAO']*100}% " if repopulation else "Sem Repopulação RCE"
        figure = go.Figure()
        figure.add_trace(go.Scatter(x=gen, y=lista[0], mode="lines+markers", name="Valor Min Fitness", marker=dict(symbol="star", color="blue"), line=dict(color="blue")))
        figure.add_trace(go.Scatter(x=gen, y=lista[1], mode="lines+markers", name="Média Fitness", marker=dict(symbol="cross", color="red"), line=dict(color="red")))
        figure.add_trace(go.Scatter(x=gen, y=lista[2], mode="lines+markers", name="Valor Max Fitness", marker=dict(symbol="circle", color="green"), line=dict(color="green")))
        figure.update_layout(title=title, legend_title="Algoritimo Evolutivo", template="seaborn")
        return figure

    def visualize(self, logbook, pop, repopulation=True, DEBUG=False, current_params=None, execution_num=1, num_configs=1):
        generation = []
        statics = {}
        array_values = []
        best_solution_index = -1
        best_solution_variables = []
        best_solution_fitness = float('inf')
        try:
            generation = logbook.select("gen")
            statics = self.calculate_stats(logbook)
            min_fitness_values = statics.get("min_fitness", [])
            if not min_fitness_values: raise ValueError("Min fitness list is empty")
            best_solution_fitness = min(min_fitness_values)
            best_solution_index = min_fitness_values.index(best_solution_fitness)
            array_values.append(statics.get("min_fitness", [])[(execution_num -1) * int(len(generation)/execution_num):(execution_num * int(len(generation)/execution_num)) -1])
            array_values.append(statics.get("avg_fitness", [])[(execution_num -1) * int(len(generation)/execution_num):(execution_num * int(len(generation)/execution_num)) -1])
            array_values.append(statics.get("max_fitness", [])[(execution_num -1) * int(len(generation)/execution_num):(execution_num * int(len(generation)/execution_num)) -1])
            if repopulation:
                best_solution_variables = pop[0] if pop else []
            else:
                best_solution_variables = pop[0] if pop else []
            print("="*90)
            print(f"  >>> Soluções do problema (Execução {execution_num} - Console Output) <<<")
            print("="*90)
            print(f"Best Generation: {best_solution_index}")
            print(f"Best Variables: {best_solution_variables}")
            print(f"Best Fitness: {best_solution_fitness}")
            print("="*90)
            grafico_RCE = self.graficoRCE(generation, array_values, repopulation=repopulation)
            if execution_num is None:
                raise ValueError("Execution number (execution_num) must be provided to visualize for saving files.")
            else:
                output_path = f"{self.FOLDER_NAME}"
                data_file = f"{output_path}/dashboard_data_{execution_num}.pkl"
                fig_file = f"{output_path}/dashboard_fig_{num_configs}_{execution_num}.json"
                data_to_save = {
                    'execution_num': execution_num,
                    'best_gen_idx': best_solution_index,
                    'best_vars': best_solution_variables,
                    'best_fitness': best_solution_fitness,
                    'params': current_params if current_params else self.options,
                    'logbook_data': {
                        'generation': generation,
                        'statics': statics
                    }
                }
            fig_filename = f"{output_path}/grafico_execucao_{num_configs}_{execution_num}.html"
            grafico_RCE.write_html(fig_filename)
            with open(data_file, 'wb') as f:
                pickle.dump(data_to_save, f)
            print(f"\n[INFO]: Dados e figura para execução {execution_num} salvos com sucesso.")
            print(fig_filename)
        except Exception as e:
            print(f"\n\n\nERRO em visualize (Execução {execution_num}): {e}")
            st.sidebar.info("Erro em visualize: ",e)
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
