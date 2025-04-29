
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


from .Setup import Setup, params
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


class FrontEndRCE:
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

    def graficoRCE(self, gen, lista, fig= None, repopulation=False):
        title = f"Estrategia RCE - Crossover: {params['CROSSOVER']*100}% e Mutação: {params['MUTACAO']*100}% " if repopulation else "Sem Repopulação RCE"

        fig = go.Figure() if fig is None else fig  # Create new figure if None


        fig.add_trace(
            go.Scatter(
                x=gen,
                y=lista["min_fitness"],
                mode="lines+markers",
                name="Valor Min Fitness",
                marker=dict(symbol="star", color="blue"),
                line=dict(color="blue"),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=gen,
                y=lista["avg_fitness"],
                mode="lines+markers",
                name="Média Fitness",
                marker=dict(symbol="cross", color="red"),
                line=dict(color="red"),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=gen,
                y=lista["max_fitness"],
                mode="lines+markers",
                name="Valor Max Fitness",
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
        pio.show(fig)


        return fig




    # --- visualize MODIFICADO (salva dados e chama Streamlit) ---
    def visualize(self, logbook, pop, repopulation=True, DEBUG=False, current_params=None, execution_num=1):
        """
        Processa dados, imprime no console, RETORNA figura e resultados,
        E salva os arquivos de dados e figura com um número de execução.
        """
        generation = []
        statics = {}
        best_solution_index = -1
        best_solution_variables = []
        best_solution_fitness = float('inf')

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
        # --- END MODIFICATION ---

        try:
            generation = logbook.select("gen")
            statics = self.calculate_stats(logbook)

            if DEBUG:
                print("\n\nDEBUG: Dados para gráfico (generation x statics)")
                print(statics)

            min_fitness_values = statics.get("min_fitness", [])
            if not min_fitness_values: raise ValueError("Min fitness list is empty")
            best_solution_fitness = min(min_fitness_values)
            best_solution_index = min_fitness_values.index(best_solution_fitness)

            if repopulation:
                best_solution_variables = pop[0] if pop else []
            else:
                print("WARN: Visualize - Lógica para 'best_solution_variables' sem repopulação usa fallback.")
                best_solution_variables = pop[0] if pop else []

            print("="*90)
            print(f"  >>> Soluções do problema (Execução {execution_num} - Console Output) <<<") # Added execution num here
            print("="*90)
            print(f"Best Generation: {best_solution_index}")
            print(f"Best Variables: {best_solution_variables}")
            print(f"Best Fitness: {best_solution_fitness}")
            print("="*90)

            # Create a new figure before plotting
            #fig = plt.figure(f"Figure for Execution {execution_num}") # Assign a name to the figure

            fig = self.graficoRCE(generation, statics, repopulation)

            #fig.show()
            # --- MODIFIED: Save data and figure for Streamlit script ---

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

            #print("INFO: Dados a serem salvos:", data_to_save)
            # Salva os dados no arquivo .pkl numerado
            with open(data_file, 'wb') as f:
                pickle.dump(data_to_save, f)
            # Salva a figura no arquivo .json numerado
            fig_json = pio.to_json(fig)
            with open(fig_file, 'w') as f:
                f.write(fig_json)
            print(f"INFO: Dados e figura para execução {execution_num} salvos com sucesso.") # Added execution num here

        except Exception as e:
            print(f"ERRO em visualize (Execução {execution_num}): {e}") # Added execution num here
            return -1, [], float('inf'), None

        return best_solution_index, best_solution_variables, best_solution_fitness, fig

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

    # componentes
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

    def load_data(self):
        """Carrega os dados de entrada a partir de um arquivo Excel."""
        with st.sidebar:

            st.markdown("---")  # Separa
            st.title("Carregar Dados")
            st.markdown("---")  # Separa

            uploaded_file = st.file_uploader("Envie um arquivo Excel", type=["xlsx", "xls"])
            if uploaded_file:
                try:
                    self.df = pd.read_excel(uploaded_file, sheet_name=None)  # Carrega todas as tabelas
                    st.success("Arquivo carregado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao carregar arquivo: {e}")
            else:
                st.info("Envie um arquivo Excel para começar.")

    def select_table(self):
        """Seleciona uma tabela do arquivo Excel carregado."""
        if self.df:
            table_name = st.sidebar.selectbox("Selecione a tabela", list(self.df.keys()))
            return self.df[table_name]
        return None

    def select_axes(self, df):
        """Seleciona as colunas para os eixos X e Y."""
        x_col = st.sidebar.selectbox("Selecione a coluna para o eixo X", df.columns)
        y_col = st.sidebar.selectbox("Selecione a coluna para o eixo Y", df.columns)
        return x_col, y_col

    def create_scatter_plot(self, df, x_col, y_col):
        """Cria um gráfico de dispersão."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df[x_col], y=df[y_col],
            mode='lines+markers', name=f'{y_col} vs {x_col}'
        ))
        fig.update_layout(
            title=f'Gráfico de {y_col} vs {x_col}',
            xaxis_title=x_col,
            yaxis_title=y_col,
            template='plotly_dark',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)

    def create_bar_plot(self, df, x_col, y_col):
        """Cria um gráfico de barras."""
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df[x_col], y=df[y_col], name=f'{y_col} vs {x_col}'
        ))
        fig.update_layout(
            title=f'Gráfico de Barras: {y_col} vs {x_col}',
            xaxis_title=x_col,
            yaxis_title=y_col,
            template='plotly_dark',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)

    def create_pie_chart(self, df, x_col, y_col):
        """Cria um gráfico de pizza."""
        fig = go.Figure(data=[go.Pie(
            labels=df[x_col], values=df[y_col]
        )])
        fig.update_layout(
            title=f'Gráfico de Pizza: {y_col} por {x_col}',
            template='plotly_dark',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)

    def display_statistics(self, df, stat_col):
        """Exibe estatísticas da coluna selecionada."""
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Mínimo", f"{df[stat_col].min():.2f}", delta=-0.5, delta_color="inverse")
        col2.metric("Máximo", f"{df[stat_col].max():.2f}", delta=-0.5, delta_color="inverse")
        col3.metric("Média", f"{df[stat_col].mean():.2f}", delta=-0.5, delta_color="inverse")
        col4.metric("Desvio Padrão", f"{df[stat_col].std():.2f}", delta=-0.5, delta_color="inverse")

    def footer(self):
        """Exibe o rodapé do dashboard."""
        st.markdown("""
            <footer>
            <p>Powered by <a href="https://streamlit.io/">Streamlit</a> and <a href="https://plotly.com/python/">Plotly</a></p>
            </footer>
        """, unsafe_allow_html=True)


    def RCE_HomePage(self):
        """Executa o dashboard."""
        self.setup_header()
        self.load_data()

        if self.df:
            selected_table = self.select_table()
            if selected_table is not None:
                # Seção de Estatísticas
                st.markdown("---")  # Separa
                st.sidebar.title("Análise do arquivo Excel")
                st.markdown("---")  # Separa

                stat_col = st.sidebar.selectbox("Selecione uma coluna para análise estatística", selected_table.columns)

                if stat_col:
                    self.display_statistics(selected_table, stat_col)

                # Configuração de Eixos para os Gráficos
                x_col, y_col = self.select_axes(selected_table)

                # Exibir tabela
                st.subheader("Tabela Selecionada")
                st.dataframe(selected_table, use_container_width=True)

                # Exibir gráficos
                st.subheader("Gráficos")
                graph_type = st.radio(
                    "Tipo de Gráfico",
                    ('Dispersão', 'Barras', 'Pizza'),
                    horizontal=True
                )

                if graph_type == 'Dispersão':
                    self.create_scatter_plot(selected_table, x_col, y_col)
                elif graph_type == 'Barras':
                    self.create_bar_plot(selected_table, x_col, y_col)
                elif graph_type == 'Pizza':
                    self.create_pie_chart(selected_table, x_col, y_col)

        # Menu direito do chatbot
        if st.session_state.show_chat:
            with st.sidebar:
                st.markdown("---")  # Separador
                self.chatbot.display_chat()
                st.markdown("---")  # Separador

        self.footer()



