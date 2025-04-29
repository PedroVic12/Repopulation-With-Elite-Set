
from DashBoard.views.pages.DashboardAppRCE import ConsolidatedResultsComponent, SummaryComponent, StatisticsTableComponent, ConvergenceGraphComponent, select_execution_with_tabs
from DashBoard.views.components.side_bar_widget import DrawerSideBar


#backend
from DashBoard.controllers.Utils import FOLDER_NAME, find_available_executions, load_execution_data 
from DashBoard.controllers.Utils import Controller


# Frontend
import streamlit as st

controller = Controller()
menu_lateral = DrawerSideBar()

class DashboardRCEFrontend:
    """Classe principal do aplicativo Dashboard."""
    
    def __init__(self):
        """Inicializa o aplicativo."""
        st.set_page_config(layout="wide", page_title="Visualizador de Execuções RCE")
        st.title("Framework Repopulation-With-Elite-Set RCE")
        
        menu_lateral.render()        

        controller.select_execution_with_tabs(self.execution_numbers)
        
        self.execution_numbers = find_available_executions()
        
        controller.setState(f"state_{self.execution_numbers}")

    def RCEPage(self):

        """Renderiza a página principal do aplicativo."""
        tab_selecionada = controller.select_execution_with_tabs(self.execution_numbers)

        if tab_selecionada:
            print(f"[debug] Execução selecionada: {tab_selecionada}")


        # Atualiza o estado da execução selecionada no session_state
        if st.session_state["selected_execution"] != tab_selecionada:
            st.session_state["selected_execution"] = tab_selecionada
        
        # Exibe o valor da execução selecionada
        st.write(f"Execução selecionada: {st.session_state['selected_execution']}")
        
        # Carrega os dados da execução selecionada
        if st.session_state["selected_execution"]:
            data, fig = load_execution_data(st.session_state["selected_execution"])
            
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


    def run(self):
        """Executa o aplicativo Dashboard."""
        st.title("Framework Repopulation-With-Elite-Set RCE")
        
        if not self.execution_numbers:
            st.error(f"Nenhum arquivo de resultado ('dashboard_data_*.pkl') encontrado na pasta '{FOLDER_NAME}'.")
            st.info("Certifique-se de que executou o script principal ('app.py' ou similar) que gera esses arquivos na pasta correta.")
            st.stop()
        
        
        ConsolidatedResultsComponent.render()

        # Seleciona dinamicamente a execução com abas
        selected_execution = select_execution_with_tabs(self.execution_numbers)
        
        # Carrega os dados e a figura para a execução selecionada
        self.RCEPage()

app = DashboardRCEFrontend()
app.run()