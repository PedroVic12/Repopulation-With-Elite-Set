from matplotlib import pyplot as plt
import streamlit as st
import pandas as pd
import numpy as np
from Setup import params
from IPython.display import display
import plotly.graph_objects as go





# Componente de Cartão
def Card(title, content, key=None):
    with st.container():
        st.markdown(f"""
        <div style="padding: 1.5rem; border-radius: 0.5rem; background-color: #2c3e50; margin-bottom: 1rem;">
            <h4 style="margin-top: 0;">{title}</h4>
            <p>{content}</p>
        </div>
        """, unsafe_allow_html=True)


def RCEFrameworkPage():
        st.title("Página de Gráficos")

        # Cards na primeira linha
        col1, col2, col3 = st.columns(3)
        
        with col1:
            Card("Best Solution Gen", "145")
        
        with col2:
            Card("Solution Fitness", "0.0024449194511966255")
            
        with col3:
            Card("Best Variables", "[-0.003, 0.001, -1.768, 1.185, -1.900, 0.227, 4.695, -2.824, -1.265, -7.298]")
        
        
        # Como não temos acesso ao arquivo original, vamos criar dados fictícios para o gráfico RCE
        st.write("Como não temos acesso ao arquivo RCE original, vamos criar um gráfico com dados simulados.")
        
        # Criar dados fictícios para o gráfico
        gen = np.arange(1, 101)
        min_fitness = 0.5 * np.exp(-0.02 * gen) + 0.01 * np.random.rand(100)
        avg_fitness = 0.7 * np.exp(-0.015 * gen) + 0.02 * np.random.rand(100)
        max_fitness = 0.9 * np.exp(-0.01 * gen) + 0.03 * np.random.rand(100)
        
        # Criar figura Plotly diretamente
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        fig.add_trace(
            go.Scatter(
                x=gen,
                y=min_fitness,
                mode="lines+markers",
                name="Minimum Fitness",
                marker=dict(symbol="star", color="blue"),
                line=dict(color="blue"),
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=gen,
                y=avg_fitness,
                mode="lines+markers",
                name="Average Fitness",
                marker=dict(symbol="cross", color="red"),
                line=dict(color="red"),
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=gen,
                y=max_fitness,
                mode="lines+markers",
                name="Maximum Fitness",
                marker=dict(symbol="circle", color="green"),
                line=dict(color="green"),
            )
        )
        
        fig.update_layout(
            title="Simulação do Gráfico RCE",
            xaxis_title="Geração",
            yaxis_title="Fitness",
            legend_title="Legenda",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Adicionar algumas métricas
        col1, col2, col3 = st.columns(3)
        col1.metric("Melhor Fitness", f"{min_fitness[-1]:.6f}", delta=f"{min_fitness[0] - min_fitness[-1]:.6f}")
        col2.metric("Gerações Executadas", f"{len(gen)}", delta=None)
        col3.metric("Tempo de Execução", "2m 34s", delta=None)


    


#!pip install streamlit pandas plotly openpyxl

class ChatBot:
    """Classe para gerenciar o chatbot lateral."""

    def __init__(self):
        if 'messages' not in st.session_state:
            st.session_state.messages = []




    def display_chat(self):
        """Exibe o chat e processa as mensagens."""
        st.sidebar.title("Chatbot")

        # Exibir mensagens anteriores
        for message in st.session_state.messages:
            with st.sidebar.chat_message(message["role"]):
                st.sidebar.write(message["content"])

        # Campo de entrada para nova mensagem
        if prompt := st.sidebar.chat_input("Digite sua mensagem..."):
            # Adicionar mensagem do usuário
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Simular resposta do bot (ping-pong)
            response = "pong" if prompt.lower() == "ping" else "Como posso ajudar?"
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()



class DashboardApp:
    """Classe principal para criar o dashboard interativo com Streamlit."""

    def __init__(self):
        st.set_page_config(layout="wide", page_title="Dashboard Interativo")
        self.df = None
        self.chatbot = ChatBot()
        self.fit_array = []

        # Inicializar estado para o chatbot
        if 'show_chat' not in st.session_state:
            st.session_state.show_chat = False

        # Configurar tema escuro
        st.markdown("""
            <style>
            .stApp {
                background-color: #1a1a2e;
                color: white;
            }
            </style>
        """, unsafe_allow_html=True)

    #! Funções antigas do framework em plotty
    def visualize(self, logbook, pop, problem_type="minimaze", repopulation=True, DEBUG = True):
        generation = logbook.select("gen")
        statics = self.calculate_stats(logbook)

        if problem_type == "maximize":
            # Se o problema for de maximização, inverter os valores de fitness para exibir corretamente o gráfico
            statics = {
                key: [-value for value in values] for key, values in statics.items()
            }

        if repopulation:
            best_solution_index = statics["min_fitness"].index(
                min(statics["min_fitness"])
            )
            #print(best_solution_index)
            best_solution_variables = pop[0]
            best_solution_fitness = statics["min_fitness"][best_solution_index]
        else:
            best_solution_index = statics["min_fitness"].index(
                min(statics["min_fitness"])
            )
            best_solution_variables = logbook.select("min")
            best_solution_fitness = min(statics["min_fitness"])

        # Soluções do problema
        print("============================================================================================")
        print("  >>> Soluções do problema")
        print("============================================================================================")
        print("\nBest solution generation = ", best_solution_index)
        print("\nBest solution variables =\n", best_solution_variables)
        print("\nBest solution fitness = ", best_solution_fitness)
        print("============================================================================================")
        try:
            fig = self.graficoRCE(generation, statics, repopulation)

            return best_solution_index, best_solution_variables, best_solution_fitness
        except:
            print("Erro validation :(")

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


    def graficoRCE(self, gen, lista, repopulation=False):
            


            title = f"Estrategia RCE - Crossover: {params['CROSSOVER']*100}% e Mutação: {params['MUTACAO']*100}% " if repopulation else "Sem Repopulação RCE"

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=gen,
                    y=lista["min_fitness"],
                    mode="lines+markers",
                    name="Minimum Fitness",
                    marker=dict(symbol="star", color="blue"),
                    line=dict(color="blue"),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=gen,
                    y=lista["avg_fitness"],
                    mode="lines+markers",
                    name="Average Fitness",
                    marker=dict(symbol="cross", color="red"),
                    line=dict(color="red"),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=gen,
                    y=lista["max_fitness"],
                    mode="lines+markers",
                    name="Maximum Fitness",
                    marker=dict(symbol="circle", color="green"),
                    line=dict(color="green"),
                )
            )

            fig.update_layout(
                title=title,
                xaxis_title="Generation",
                yaxis_title="Fitness",
                legend_title="Legend",
                template="plotly_white",
            )
            fig.show()

            return fig




    # Funcções do Streamlit
    def setup_header(self):
        """Configura o cabeçalho do dashboard."""
        col1, col2, col3 = st.columns([1, 8, 1])

        with col1:
            st.button("≡")

        with col2:
            st.title("Dashboard Interativo")

        with col3:
            if st.button("🔔"):
                st.session_state.show_chat = not st.session_state.show_chat

    def render_rce_page(self, logbook, pop,  repopulation=True):
        """Renderiza a página RCE com cards, gráficos e métricas."""
        st.title("Página de Resultados RCE")


        generation = logbook.select("gen")
        statics = self.calculate_stats(logbook)

 
        if repopulation:
                best_solution_index = statics["min_fitness"].index(
                    min(statics["min_fitness"])
                )
                #print(best_solution_index)
                best_solution_variables = pop[0]
                best_solution_fitness = statics["min_fitness"][best_solution_index]
        else:
                best_solution_index = statics["min_fitness"].index(
                    min(statics["min_fitness"])
                )
                best_solution_variables = logbook.select("min")
                best_solution_fitness = min(statics["min_fitness"])

        # Soluções do problema
        print("============================================================================================")
        print("  >>> Soluções do problema: ")
        print("============================================================================================")
        print("\nBest solution generation = ", best_solution_index)
        print("\nBest solution variables =\n", best_solution_variables)
        print("\nBest solution fitness = ", best_solution_fitness)
        print("============================================================================================")

        print("\nDados estatisticos")
        values_stats = {
            "min_fitness": np.mean(statics["min_fitness"]),
            "max_fitness": np.mean(statics["max_fitness"]),
            "avg_fitness": np.mean(statics["avg_fitness"]),
            "std_fitness": np.mean(statics["std_fitness"]),
        }
        print(values_stats)
        print("============================================================================================")

        # Cards na primeira linha
        col1, col2, col3 = st.columns(3)

        with col1:
            self.create_card("Best Solution Gen", f"{best_solution_index}")

        with col2:
            self.create_card("Solution Fitness", f"{best_solution_fitness:.4f}")

        with col3:
            self.create_card("Best Variables", f"{best_solution_variables}")

        # Gráfico de evolução do fitness
        st.subheader("Evolução do Fitness")
        self.plot_fitness_evolution(logbook)

        # Métricas
        col1, col2, col3 = st.columns(3)
        col1.metric("Melhor Fitness", f"{best_solution_fitness:.4f}")
        col2.metric("Gerações Executadas", f"{generation[-1]}")
        #col3.metric("Tempo de Execução", "2m 34s")  # Exemplo estático, pode ser dinâmico

    def create_card(self, title, content):
        """Cria um card estilizado."""
        st.markdown(f"""
        <div style="padding: 1.5rem; border-radius: 0.5rem; background-color: #2c3e50; margin-bottom: 1rem;">
            <h4 style="margin-top: 0;">{title}</h4>
            <p>{content}</p>
        </div>
        """, unsafe_allow_html=True)

    def plot_fitness_evolution(self, logbook):
        """Plota o gráfico de evolução do fitness."""
        gen = logbook.select("gen")
        min_fitness = logbook.select("min")
        avg_fitness = logbook.select("avg")
        max_fitness = logbook.select("max")

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=gen,
                y=min_fitness,
                mode="lines+markers",
                name="Minimum Fitness",
                marker=dict(symbol="star", color="blue"),
                line=dict(color="blue"),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=gen,
                y=avg_fitness,
                mode="lines+markers",
                name="Average Fitness",
                marker=dict(symbol="cross", color="red"),
                line=dict(color="red"),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=gen,
                y=max_fitness,
                mode="lines+markers",
                name="Maximum Fitness",
                marker=dict(symbol="circle", color="green"),
                line=dict(color="green"),
            )
        )

        fig.update_layout(
            title="Evolução do Fitness",
            xaxis_title="Geração",
            yaxis_title="Fitness",
            legend_title="Legenda",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )

        st.plotly_chart(fig, use_container_width=True)

    def run(self, logbook=None, pop=None, best_variables=None, best_fitness=None):
        """Executa o dashboard."""
        self.setup_header()

        # Renderizar a página RCE se os dados forem fornecidos
        if logbook and pop:
            self.render_rce_page(logbook, pop)

        # Menu direito do chatbot
        if st.session_state.show_chat:
            with st.sidebar:
                st.markdown("---")  # Separador
                self.chatbot.display_chat()
                st.markdown("---")  # Separador

        self.footer()

    def footer(self):
        """Exibe o rodapé do dashboard."""
        st.markdown("""
            <footer>
            <p>Powered by <a href="https://streamlit.io/">Streamlit</a> and <a href="https://plotly.com/python/">Plotly</a></p>
            </footer>
        """, unsafe_allow_html=True)