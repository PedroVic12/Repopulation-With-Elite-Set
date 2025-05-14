

# --- Componentes da Interface de Usuário ---
from ..components.dash_rce_components import ConsolidatedResultsComponent, SummaryComponent, StatisticsTableComponent, GraficoRCEComponent 


#backend
from controllers.Utils import Controller,FOLDER_NAME, Utils


# Frontend
import streamlit as st
import os
import pickle
import json



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




# --- Classe Principal do Aplicativo ---
class FrameworkRCEDashboard:
    def __init__(self):
        self.controller = Controller()
        self.utils = Utils()
        self.execution_numbers = self.controller.execution_numbers
        self.menu_lateral = DrawerSideBar()
        
        # Initialize session state if not exists
        if "selected_execution" not in st.session_state:
            st.session_state["selected_execution"] = None
        if "active_tab" not in st.session_state:
            st.session_state["active_tab"] = 0

    def handle_tab_change(self, tab_index: int, execution_number: int):
        """Gerencia mudanças de aba e atualiza o estado."""
        st.session_state["active_tab"] = tab_index
        st.session_state["selected_execution"] = execution_number


    def header(self):
        """Cabeçalho do aplicativo."""
        st.title("Framework Repopulation-With-Elite-Set RCE")
        st.subheader("Resultados Consolidados Gerais de todas as execuções")

        if not self.execution_numbers:
            st.error("Nenhum arquivo de resultado encontrado.")
            st.stop()

    def render_html_files(self, html_files):
        """Renderiza os arquivos .html no Streamlit."""
        for html_file in html_files:
            try:
                st.subheader(f"Grafico: {html_file.name}")
                with open(html_file, "r", encoding="utf-8") as f:
                    html_content = f.read()
                    # Renderiza o conteúdo HTML no Streamlit
                    st.components.v1.html(html_content, height=800, scrolling=True)
            except Exception as e:
                st.error(f"Erro ao renderizar o arquivo {html_file.name}: {e}")

    def run(self):
        self.header()

        # Renderiza os resultados consolidados
        ConsolidatedResultsComponent.render()

        # Seleção de execução com tabs
        with st.container():
            st.subheader("Seleção da Execução")
            
            # Create tabs
            tabs = st.tabs([f"Execução {num}" for num in self.execution_numbers])
            
            # Handle tab content and state
            for i, (tab, exec_num) in enumerate(zip(tabs, self.execution_numbers)):
                with tab:
                    if i != st.session_state["active_tab"]:
                        self.handle_tab_change(i, exec_num)
                    
                    st.write(f"Visualizando dados da execução {exec_num}")
                    
                    # Add a select button for each tab
                    if st.button(f"Selecionar Execução {exec_num}", key=f"select_btn_{exec_num}"):
                        self.handle_tab_change(i, exec_num)
                        st.rerun()

        # Display selected execution data
        if st.session_state["selected_execution"] is not None:
            st.markdown("---")
            st.subheader(f"Dados da Execução {st.session_state['selected_execution']}")


            number_state = st.session_state['selected_execution']

            # Load the selected execution data
            print(f"Loading data for execution {number_state}")

            # Load and display data
            data, fig = self.utils.load_execution_data(number_state)

            if data:
                with st.container():
                    SummaryComponent.render(data, st.session_state["selected_execution"])
                with st.container():
                    GraficoRCEComponent.render(fig, st.session_state["selected_execution"])
                with st.container():
                    StatisticsTableComponent.render(data)
            else:
                st.error("Erro ao carregar os dados.")
        else:
            st.warning("Selecione uma execução para visualizar os dados.")

        self.footer()

    def footer(self):
        """Rodapé do aplicativo."""
        st.markdown("---")
        st.info("Desenvolvido por Pedro Victor Veras e Rainer Zanghi em um projeto PIBIC pela UFF - 2024/2025")
        st.info("Este é um exemplo de rodapé. Você pode personalizá-lo conforme necessário.")
        st.markdown("---")

