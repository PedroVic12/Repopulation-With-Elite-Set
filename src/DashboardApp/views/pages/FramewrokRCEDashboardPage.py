

# --- Componentes da Interface de Usuário ---
from ..components.dash_rce_components import ConsolidatedResultsComponent, CardSolutions, StatisticsTableComponent, GraficoRCEComponent 


#backend
from controllers.Utils import Controller,FOLDER_NAME, Utils
import os

# Frontend
import streamlit as st

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


        self.init_state_class()
        
    def init_state_class():
        pass

    def handle_tab_change(self, tab_index: int, execution_number: int):
        """Gerencia mudanças de aba e atualiza o estado."""
        UseState.set_state("active_tab", tab_index)
        UseState.set_state("selected_execution", execution_number)

    def render_execution_options(self):
        """Renderiza as opções de execução de forma interativa."""

        st.markdown("### ⚒ Configuração do Framework")
        options = st.session_state.get("current_options", self.options)

        with st.expander("🔧 Configuração do conjunto de Parâmetros", expanded=False):
            config_name = st.text_input("Nome da Configuração", "Config 1")

            col1, col2 = st.columns(2)

            with col1:
                # Checkbox option
                key_enabled = st.checkbox(
                    "Habilitar Multiplas Execuções",
                    value=self.options.get("key", True),
                    help="Ativa/Desativa múltiplas execuções do algoritmo"
                )

                # Numeric input
                value_input = st.number_input(
                    "Quantidade de Execuções",
                    min_value=1,
                    max_value=100,
                    value=self.options.get("value", 5),
                    step=1,
                    help="Número de vezes que este conjunto de parâmetros será executado"
                )

                # Initialize current_config with a default value
                current_config = {
                    "name": config_name,
                    "key": key_enabled,
                    "value": value_input,
                    "parametros_opcionais": []  # Default to an empty list
                }

                if st.button("💾 Salvar Como Nova Configuração"):
                    saved_configs = UseState.get_state("saved_configurations", [])
                    saved_configs.append(current_config)
                    UseState.set_state("saved_configurations", saved_configs)
                    st.success(f"Configuração '{config_name}' salva! ({value_input}x execuções)")

            with col2:
                st.subheader("Parâmetros Opcionais")

                # Ensure options["parametros_opcionais"] exists
                if "parametros_opcionais" in self.options and isinstance(self.options["parametros_opcionais"], list):
                    # Display the mutation options
                    if len(self.options["parametros_opcionais"]) > 0:
                        mutation_options = self.options["parametros_opcionais"][0]["MUTACAO"]
                        selected_mutation = st.selectbox(
                            "Taxa de Mutação (%)",
                            options=mutation_options,
                            index=0,
                            help="Selecione a taxa de mutação desejada"
                        )

                    # Crossover Rate
                    if len(self.options["parametros_opcionais"]) > 1:
                        crossover_options = self.options["parametros_opcionais"][1]["CROSSOVER"]
                        selected_crossover = st.selectbox(
                            "Taxa de Crossover (%)",
                            options=crossover_options,
                            index=0,
                            help="Selecione a taxa de crossover desejada"
                        )

                    # Number of Generations
                    if len(self.options["parametros_opcionais"]) > 2:
                        generation_options = self.options["parametros_opcionais"][2]["NUM_GENERATIONS"]
                        selected_generations = st.selectbox(
                            "Número de Gerações",
                            options=generation_options,
                            index=0,
                            help="Selecione o número de gerações"
                        )
                else:
                    st.error("A estrutura de 'parametros_opcionais' está incorreta.")

        # Update options dictionary
        current_config = {
                "name": config_name,
                "key": key_enabled,
                "value": value_input,
                "parametros_opcionais": [
                    {"MUTACAO": selected_mutation},
                    {"CROSSOVER": selected_crossover},
                    {"NUM_GENERATIONS": selected_generations}
                ]
        }

            # Store current configuration in session state
        UseState.set_state("current_options", current_config)

        # Show current configuration
        # col1, col2 = st.columns(2)
        # with col1:
        #         st.markdown("### Configuração Atual:")
        #         st.json(current_config, expanded=False)

        # with col2:
        #         # Show saved configurations
        #         st.markdown("### Configurações Salvas:")
        #         saved_configs = UseState.get_state("saved_configurations", [])

        #         if saved_configs:
        #             for idx, config in enumerate(saved_configs):
        #                 with st.expander(f"📋 Config {idx+1}: {config['name']} ({config['value']}x execuções)",
        #                                 expanded=False):
        #                     st.write(config)
        #                     st.dataframe(config)
        #                     col1, col2 = st.columns(2)
        #                     with col1:
        #                         if st.button("🔄 Play Configuração", key=f"load_{idx}"):
        #                             self.options = config.copy()
        #                             st.success(f"Configuração '{config['name']}' carregada!")
        #                             #self.run_script(FOLDER_NAME.parent / "run_rce_framework.py")
        #                             st.rerun()
        #                     with col2:
        #                         if st.button("🗑️ Deletar", key=f"delete_{idx}"):
        #                             saved_configs.pop(idx)
        #                             UseState.set_state("saved_configurations", saved_configs)
        #                             st.success(f"Configuração removida!")
        #                             st.rerun()
        #         else:
        #             st.info("Nenhuma configuração salva ainda.")

        return current_config

    def run(self):

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
        
        # Opções de execução para multiplos parametros de algoritmo Genético
        options_dashboard = self.render_execution_options()
        dados = self.utils.load_execution_data(exec_num, debug=False)
        active_tab = UseState.get_state("active_tab")
        state = UseState.get_state("current_options")
        print("State do aplicativo:", state)



        st.info("⚠️ Configuração de parametros do Framework esta ainda em desenvolvimento, por favor, aguarde a versão 10.0 do Framework para uma melhor experiência de usuário.")
        # Botão com ícone de play para executar um script Python
        if st.button("▶️ Executar Script", type="primary"):
                  
            # Ensure we have current options in session state
            if "current_options" not in st.session_state:
                st.error("Por favor, configure as opções .JSON e options_main_file primeiro!")
                return
                
            # Use raw string and quotes for Windows path with spaces
            script_path = FOLDER_NAME.parent / "run_framework.py"

            # Run the script
            self.run_script(script_path)


      
        self.header()
        
        # Renderiza os resultados consolidados
        ConsolidatedResultsComponent.render(active_tab)

        #! Seleção de execução com tabs para cada execução
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
                                
                                
                        except Exception as e:
                            st.error(f"Erro ao carregar os dados da execução {exec_num}.",e)

                    else:
                        st.error("Não foi encontrado nenhum conjunto de dados")
      

        self.footer()

    def atualizar_pagina(self):
        """Atualiza a página."""
        st.rerun()
        print("Atualizando a página...")

    @st.dialog("Loading...")
    def CircleLoading():
        st.write(f"Why is your favorite function Benchmark?")
        st.image("/home/pedrov12/Documentos/GitHub/Repopulation-With-Elite-Set/src/assets/uff_logo.jpg")

    
    def run_script(self, script_path):
        """Executa um script Python."""
        # Cria um espaço temporário para o "diálogo"
        dialog_placeholder = st.empty()

        try:
                # Verifica se o GIF existe
                img_gif_loading = FOLDER_NAME.parent / "assets" / "humans_evolution.gif"
                
                if img_gif_loading.exists():
                    with dialog_placeholder.container():
                        st.image(str(img_gif_loading), width=800)
                        st.subheader("Executando o programa principal com Algoritmo Evolutivo RCE no mesmo terminal, por favor aguarde...")
                        st.progress(50, "Iniciando a execução do script...")
                        
                        
                
                # Executa o script usando aspas duplas para o caminho
                command = f'python "{script_path}"'
                return_code = os.system(command)

                # Remove o "diálogo" após a execução
                dialog_placeholder.empty()

                if return_code == 0:
                    st.success("Script executado com sucesso!")
                    self.atualizar_pagina()


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
