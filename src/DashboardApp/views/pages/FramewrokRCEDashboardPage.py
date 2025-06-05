

# --- Componentes da Interface de Usuário ---
from ..components.dash_rce_components import ConsolidatedResultsComponent, CardSolutions, StatisticsTableComponent, GraficoRCEComponent, TabExamplePage


#backend
from controllers.Utils import Controller,FOLDER_NAME, Utils
import os

# Frontend
import streamlit as st
import time
import threading

#from ....config import ConfigManager


# Configuração da barra lateral
class DrawerSideBar:
    """Classe para gerenciar a barra lateral do aplicativo."""

    def __init__(self):
        """Inicializa a barra lateral."""
        self.st = st

    def render(self):
        """Renderiza a barra lateral."""
        self.st.sidebar.title("Seleção da Execução com Algoritmo Evolutivo")
        if st.button("Atualizar Estado"):
            st.session_state["selected_execution"] = None
            st.experimental_rerun()
        self.st.sidebar.markdown("---")  # Separador visual


## Controlador de Gerenciamento de Estado
class UseState:
    """Classe para gerenciar o estado do Streamlit."""

    @staticmethod
    def initialize_state(key, default_value):
        """Inicializa uma chave no session_state com um valor padrão."""
        if key not in st.session_state:
            st.session_state[key] = default_value

    @staticmethod
    def get_state(key, default_value=None):
        """Obtém o valor de uma chave no session_state."""
        return st.session_state.get(key, default_value)

    @staticmethod
    def set_state(key, value):
        """Define o valor de uma chave no session_state."""
        st.session_state[key] = value
        print("State atualizado:", key, "=", value)  


# --- Classe Principal do Aplicativo ---
class FrameworkRCEDashboard:
    def __init__(self, options = None):
        self.controller = Controller()
        self.utils = Utils()
        self.execution_numbers = self.controller.execution_numbers
        self.menu_lateral = DrawerSideBar()


    
        # Initialize options from parameter or use default
        self.options = options 


        # Inicializa os estados necessários
        UseState.initialize_state("selected_execution", None)
        UseState.initialize_state("active_tab", 0)
        UseState.initialize_state("saved_configurations", [])


    def handle_tab_change(self, tab_index: int, execution_number: int):
        """Gerencia mudanças de aba e atualiza o estado."""
        UseState.set_state("active_tab", tab_index)
        UseState.set_state("selected_execution", execution_number)

    

    def run(self):
        try:
            active_tab = UseState.get_state("active_tab")
            dados = self.utils.load_execution_data(active_tab + 1, debug=False)
        
            self.ConfigWebApp()

            self.header()
            
            # Renderiza os resultados consolidados
            ConsolidatedResultsComponent.render(dados)

            #! MEU TEMPLATE USANDO TABS com Seleção de execução com tabs para cada execução controlado pelo UseState
            with st.container():
                st.subheader("🔄 Seleção da Execução")
                
                # Cria abas
                tabs = st.tabs([f"Execução {num}" for num in self.execution_numbers])

                # Renderiza o conteúdo de cada aba
                for i, (tab, exec_num) in enumerate(zip(tabs, self.execution_numbers)):
                    with tab:
                        # Atualiza o estado da aba ativa
                        if UseState.get_state("active_tab") != i:
                            self.handle_tab_change(i, exec_num)

                        # Carrega os dados e o gráfico da execução
                        if dados:
                            try:
                                with st.container():
                                    CardSolutions.render(dados, exec_num)


                                with st.container():
                                    GraficoRCEComponent.render(exec_num)  # Passa o exec_num para carregar o gráfico correto
                                    
                                with st.container():
                                    StatisticsTableComponent.render(dados)
                                    st.write("Graficos e Tabelas")
                                    TabExamplePage()
                                    
                                    
                                    
                            except Exception as e:
                                st.error(f"Erro ao carregar os dados da execução {exec_num}.",e)

                        else:
                            st.error("Não foi encontrado nenhum conjunto de dados")
        

            self.footer()

        except Exception as error:
            st.warning(f"Erro ao carregar pagina: {error}")


    def ConfigWebApp(self):
        #? Debugando para Streamlit online -> Opções de execução para multiplos parametros de algoritmo Genético
        #options_dashboard = self.render_execution_options()
        #print("Configuraçãoes", options_dashboard)

        state = UseState.get_state("current_options")
        print("\n\nState do aplicativo:", state)

        st.info("⚠️ Configuração de parametros do Framework esta ainda em desenvolvimento, por favor, aguarde a versão 10.0 do Framework para uma melhor experiência de usuário.")
            # Botão com ícone de play para executar um script Python
        if st.button("▶️ Executar Script", type="primary"):
                    
                # Ensure we have current options in session state
                #if "current_options" not in st.session_state:
                #    st.error("Por favor, configure as opções .JSON e options_main_file primeiro!")
                #    return
                    
                # Use raw string and quotes for Windows path with spaces
                script_path = FOLDER_NAME.parent / "run_framework.py"

                # Run the script
                self.run_script(script_path)


    def render_execution_options(self):
        """Renderiza as opções de execução de forma interativa, permitindo a variação de parâmetros."""
        st.markdown("# ⚒️ Configuração do Framework")
        
        # Inicializa um dicionário para guardar as seleções do usuário
        config_params = {}

        with st.expander("🔧 Definição dos Parâmetros, Variações e Quantidade de execuções", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Configuração Geral")
                config_params['name'] = st.text_input("Nome da Bateria de Testes", "Experimento 1")
                config_params['repetitions'] = st.number_input(
                    "Repetições por Configuração", 
                    min_value=1, max_value=100, value=5, # Mudei o default para 5, faz mais sentido para estatística
                    help="Quantas vezes cada combinação única de parâmetros será executada (para validade estatística)."
                )

            with col2:
                st.subheader("Parâmetros do Algoritmo")
                # --- Parâmetro de Mutação ---
                vary_mutation = st.checkbox("Variar Taxa de Mutação?", key="vary_mutation")
                # Supondo que as opções venham de self.options
                mutation_options = self.options.get("parametros_opcionais", [{}])[0].get("MUTACAO", [0.01, 0.02, 0.05, 0.1])
                if vary_mutation:
                    config_params['mutation_values'] = st.multiselect(
                        "Selecione os valores de Mutação (%)", 
                        options=mutation_options, 
                        default=mutation_options[:2] # Pega os dois primeiros como default
                    )
                else:
                    config_params['mutation_values'] = [st.selectbox(
                        "Selecione o valor de Mutação (%)", 
                        options=mutation_options
                    )]

                # --- Parâmetro de Crossover ---
                vary_crossover = st.checkbox("Variar Taxa de Crossover?", key="vary_crossover")
                crossover_options = self.options.get("parametros_opcionais", [{}, {}])[1].get("CROSSOVER", [0.6, 0.7, 0.8, 0.9])
                if vary_crossover:
                    config_params['crossover_values'] = st.multiselect(
                        "Selecione os valores de Crossover (%)", 
                        options=crossover_options, 
                        default=crossover_options[:2]
                    )
                else:
                    config_params['crossover_values'] = [st.selectbox(
                        "Selecione o valor de Crossover (%)", 
                        options=crossover_options
                    )]

                # --- Parâmetro de Gerações ---
                # Adicionei a mesma lógica para o número de gerações
                vary_generations = st.checkbox("Variar Número de Gerações?", key="vary_generations")
                generation_options = self.options.get("parametros_opcionais", [{}, {}, {}])[2].get("NUM_GENERATIONS", [100, 200, 500])
                if vary_generations:
                    config_params['generation_values'] = st.multiselect(
                        "Selecione os valores de Nº de Gerações", 
                        options=generation_options,
                        default=generation_options[:1]
                    )
                else:
                    config_params['generation_values'] = [st.selectbox(
                        "Selecione o valor de Nº de Gerações",
                        options=generation_options
                    )]
        
        # Armazena a configuração atual no estado da sessão para uso posterior
        UseState.set_state("experiment_config", config_params)
        return config_params


    def atualizar_pagina(self):
        """Atualiza a página."""
        st.rerun()
        print("Atualizando a página...")

    



    
    def run_script(self, script_path):
        """Executa um script Python com barra de progresso única e GIF enquanto roda."""
        dialog_placeholder = st.empty()
        progress_placeholder = st.empty()

        try:
            img_gif_loading = FOLDER_NAME.parent / "assets" / "humans_evolution.gif"
            files = self.utils.get_html_content_from_folder(FOLDER_NAME)
            steps = len(files) * 10 if len(files) > 0 else 10

            if img_gif_loading.exists():
                with dialog_placeholder.container():
                    st.image(str(img_gif_loading), width=800)
                    st.subheader("Executando o programa principal com Algoritmo Evolutivo RCE no mesmo terminal, por favor aguarde...")

                    # Executa o script em thread separada para não travar a UI

                    def run_command():
                        command = f'python "{script_path}"'
                        self._return_code = os.system(command)

                    self._return_code = None
                    thread = threading.Thread(target=run_command)
                    thread.start()

                    for i in range(steps + 1):
                        if not thread.is_alive():
                            break
                        progress = i / steps
                        bar_html = f"""
                        <div style="background-color:#e0e0e0; border-radius:10px; width:100%; height:30px;">
                            <div style="background-color:#008000; width:{progress*100}%; height:30px; border-radius:10px;"></div>
                        </div>
                        <p style="text-align:center;">{int(progress*100)}%</p>
                        """
                        progress_placeholder.markdown(bar_html, unsafe_allow_html=True)
                        time.sleep(2)

                    # Aguarda thread terminar se ainda não terminou
                    thread.join()
                    return_code = self._return_code
            else:
                # Caso não tenha GIF, só executa o script
                command = f'python "{script_path}"'
                return_code = os.system(command)

            dialog_placeholder.empty()
            progress_placeholder.empty()

            if return_code == 0:
                st.success("Script executado com sucesso!")

        except Exception as e:
            dialog_placeholder.empty()
            st.error(f"Erro ao executar o script. Código de retorno: {return_code} e Erro: {e}")

        if not self.execution_numbers:
            st.error("Nenhum arquivo de resultado encontrado.")
            st.stop()
    
    def header(self):
        """Cabeçalho do aplicativo."""
        st.markdown("---")
        st.title("⚡ Framework Repopulation-With-Elite-Set RCE ⚡")
        st.write("V 10.1.5 - 2025/06/04")
        st.markdown("---")

        # Adiciona CSS personalizado para estilizar o botão
        st.markdown(
            """
            <style>
            div.stButton > button {
                background-color: #008000; /* Verde */
                color: white; /* Cor do texto */
                padding: 12px 20px;
                text-align: center;
                display: inline-block;
                font-size: 25px;
                margin: 2px 2px;
                cursor: pointer;
                border-radius: 8px;
            }
            div.stButton > button:hover {
                background-color: #45a049; /* Verde mais escuro ao passar o mouse */
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Adiciona CSS personalizado para estilizar as abas
        st.markdown(
            """
            <style>
            /* Estiliza as abas */
            div.streamlit-tabs div[data-baseweb="tab"] {
                font-size: 25px; /* Aumenta o tamanho da fonte */
                padding: 10px 10px; /* Aumenta o espaçamento interno */
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        
        


    


    def footer(self):
        """Rodapé do aplicativo."""
        st.markdown("---")
        st.info("Desenvolvido por Pedro Victor Veras e Rainer Zanghi em um projeto PIBIC pela UFF - 2024/2025")
        st.link_button(
            url="https://github.com/PedroVic12/Repopulation-With-Elite-Set",
            label="Visite a Documentação do Projeto nesse link",
            type="primary",
            icon="📖",
        )
        st.markdown("---")
