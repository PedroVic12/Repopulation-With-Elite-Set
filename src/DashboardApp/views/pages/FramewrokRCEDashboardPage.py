

# --- Componentes da Interface de Usuário ---
from ..components.dash_rce_components import ConsolidatedResultsComponent, SummaryComponent, StatisticsTableComponent, ConvergenceGraphComponent 


#backend
from controllers.Utils import Controller,FOLDER_NAME, Utils


# Frontend
import streamlit as st


# Configuração menu lateral
class DrawerSideBar:
    """Classe para gerenciar a barra lateral do aplicativo."""

    def __init__(self):
        """Inicializa a barra lateral com os números de execução disponíveis."""
        self.st = st


    def render(self):
        """Renderiza a barra lateral."""
        self.st.sidebar.title("Seleção da Execução com algortimo evolutivo")

        utils.load_execution_data(self.st.session_state["selected_execution"])
        self.st.sidebar.markdown("---") # Separador visual



controller = Controller()
menu_lateral = DrawerSideBar()
utils = Utils()


# --- Classe Principal do Aplicativo ---
class FrameworkRCEDashboard:
    """Classe principal do aplicativo Dashboard."""
    
    def __init__(self):
        """Inicializa o aplicativo."""
        #st.set_page_config(layout="wide", page_title="Visualizador de Execuções RCE")
        self.execution_numbers = utils.find_available_executions(
            
        )
        
        # Inicializa o estado da execução selecionada no session_state
        if "selected_execution" not in st.session_state:
            st.session_state["selected_execution"] = None


    def header(self):
        """Cabeçalho do aplicativo."""
        """Executa o aplicativo Dashboard."""
        st.title("Framework Repopulation-With-Elite-Set RCE")
        
        if not self.execution_numbers:
            st.error(f"Nenhum arquivo de resultado ('dashboard_data_*.pkl') encontrado na pasta '{FOLDER_NAME}'.")
            st.info("Certifique-se de que executou o script principal ('app.py' ou similar) que gera esses arquivos na pasta correta.")
            st.stop()
        

    def run(self):
        
        self.header()  # Chama o cabeçalho do aplicativo
        
        ConsolidatedResultsComponent.render()

        # Seleciona dinamicamente a execução com abas
        selected_execution = controller.select_execution_with_tabs(self.execution_numbers)
        
        # Atualiza o estado da execução selecionada no session_state
        if st.session_state["selected_execution"] != selected_execution:
            st.session_state["selected_execution"] = selected_execution
        
        # Exibe o valor da execução selecionada
        st.write(f"Execução selecionada: {st.session_state['selected_execution']}")
        
        # Carrega os dados da execução selecionada
        if st.session_state["selected_execution"]:
            data, fig = utils.load_execution_data()
            
            if data:
                # Área principal: cada componente é encapsulado em um container
                with st.container():

                    SummaryComponent.render(data, st.session_state["selected_execution"])

                
                with st.container():
                    ConvergenceGraphComponent.render(fig, st.session_state["selected_execution"])
                
                
                with st.container():
                    StatisticsTableComponent.render(data)
                
        else:
            st.warning("Nenhuma execução selecionada ou disponível.")


