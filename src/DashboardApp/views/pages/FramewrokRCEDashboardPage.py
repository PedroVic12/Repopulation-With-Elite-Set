

# --- Componentes da Interface de Usuário ---
from ..components.dash_rce_components import ConsolidatedResultsComponent, CardSolutions, StatisticsTableComponent, GraficoRCEComponent 


#backend
from controllers.Utils import Controller,FOLDER_NAME, Utils
import os

# Frontend
import streamlit as st




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
        #print("State atualizado:", key, "=", value)  


# --- Classe Principal do Aplicativo ---
class FrameworkRCEDashboard:
    def __init__(self, options = None):
        self.controller = Controller()
        self.utils = Utils()
        self.execution_numbers = self.controller.execution_numbers
        self.menu_lateral = DrawerSideBar()
        self.options = options

        # Inicializa os estados necessários
        UseState.initialize_state("selected_execution", None)
        UseState.initialize_state("active_tab", 0)

    def handle_tab_change(self, tab_index: int, execution_number: int):
        """Gerencia mudanças de aba e atualiza o estado."""
        UseState.set_state("active_tab", tab_index)
        UseState.set_state("selected_execution", execution_number)

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

        self.header()

        # Opções de execução para multiplos parametros de algoritmo Genético
        st.write("## Opções de Execução")
        st.write(self.options)

        # Renderiza os resultados consolidados
        ConsolidatedResultsComponent.render()

        #! Seleção de execução com tabs para cada execução
        with st.container():
            st.subheader("Seleção da Execução")
            
            # Cria abas
            tabs = st.tabs([f"Execução {num}" for num in self.execution_numbers])

            # Renderiza o conteúdo de cada aba
            for i, (tab, exec_num) in enumerate(zip(tabs, self.execution_numbers)):
                with tab:
                    # Atualiza o estado da aba ativa
                    if UseState.get_state("active_tab") != i:
                        self.handle_tab_change(i, exec_num)

                    # botao para sincronizar os dados do JSON e o arquivo python run
                    json_button = st.button("Carregar Dados", key=f"load_data_{exec_num}")
                    if json_button:
                        # Atualiza o estado da execução selecionada
                        self.atualizar_pagina()

                    else:
                        dados = self.utils.load_execution_data(exec_num, debug=False)

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

    @st.dialog("Loading...")
    def CircleLoading():
        st.write(f"Why is your favorite function Benchmark?")
        st.image("/home/pedrov12/Documentos/GitHub/Repopulation-With-Elite-Set/src/assets/uff_logo.jpg")

    def header(self):
        """Cabeçalho do aplicativo."""
        st.markdown("---")
        st.title("Framework Repopulation-With-Elite-Set RCE")
        st.markdown("---")

        # Adiciona CSS personalizado para estilizar o botão
        st.markdown(
            """
            <style>
            div.stButton > button {
                background-color: #4CAF50; /* Verde */
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

        # Botão com ícone de play para executar um script Python
        if st.button("▶️ Executar Script", type="secondary"):
            # Use raw string and quotes for Windows path with spaces
            script_path = FOLDER_NAME.parent / "run_rce_framework.py"
            
            # Cria um espaço temporário para o "diálogo"
            dialog_placeholder = st.empty()

            try:
                # Verifica se o GIF existe
                img_gif_loading = FOLDER_NAME.parent / "assets" / "humans_evolution.gif"
                
                if img_gif_loading.exists():
                    with dialog_placeholder.container():
                        st.image(str(img_gif_loading), width=1200)
                        st.subheader("Executando o script principal no terminal... por favor aguarde...")

                # Executa o script usando aspas duplas para o caminho
                command = f'python "{script_path}"'
                return_code = os.system(command)

                # Remove o "diálogo" após a execução
                dialog_placeholder.empty()

                if return_code == 0:
                    st.success("Script executado com sucesso!")
                    st.rerun()
                else:
                    st.error(f"Erro ao executar o script. Código de retorno: {return_code}")

            except Exception as e:
                dialog_placeholder.empty()
                st.error(f"Erro ao executar o script: {e}")

        if not self.execution_numbers:
            st.error("Nenhum arquivo de resultado encontrado.")
            st.stop()


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