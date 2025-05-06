

# --- Componentes da Interface de Usuário ---
from ..components.dash_rce_components import ConsolidatedResultsComponent, SummaryComponent, StatisticsTableComponent, ConvergenceGraphComponent 


#backend
from controllers.Utils import Controller,FOLDER_NAME, Utils


# Frontend
import streamlit as st
import os
import pickle
import json

# Corrige o erro no carregamento do JSON
def load_execution_data(self, exec_num):
    """Carrega os dados .pkl e a figura .json para a execução especificada."""
    data = None
    fig = None
    data_file_selected = os.path.join(FOLDER_NAME, f"dashboard_data_{exec_num}.pkl")
    fig_file_selected = os.path.join(FOLDER_NAME, f"dashboard_fig_{exec_num}.json")

    # Carregar Dados
    try:
        with open(data_file_selected, 'rb') as f:
            data = pickle.load(f)
        st.sidebar.success(f"Dados da execução {exec_num} carregados de '{FOLDER_NAME}'.")
    except FileNotFoundError:
        st.error(f"Erro Crítico: Arquivo de dados selecionado ({data_file_selected}) não encontrado.")
        return None, None
    except Exception as e:
        st.error(f"Erro ao carregar dados de {data_file_selected}: {e}")
        return None, None

    # Carregar Figura
    try:
        if os.path.exists(fig_file_selected):
            with open(fig_file_selected, 'r') as f:
                fig = json.load(f)  # Remove o argumento 'encoding'
            st.sidebar.success(f"Figura da execução {exec_num} carregada de '{FOLDER_NAME}'.")
        else:
            st.sidebar.warning(f"Arquivo da figura ({fig_file_selected}) não encontrado.")
    except Exception as e:
        st.error(f"Erro ao carregar figura de {fig_file_selected}: {e}")

    return data, fig


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
    """Classe principal do aplicativo Dashboard."""

    def __init__(self):
        self.controller = Controller()
        self.utils = Utils()
        self.execution_numbers = self.controller.execution_numbers
        # Inicializa o controlador e utilitários
        menu_lateral = DrawerSideBar()

    def header(self):
        """Cabeçalho do aplicativo."""
        st.title("Framework Repopulation-With-Elite-Set RCE")
        st.subheader("Resultados Consolidados Gerais de todas as execuções")

        if not self.execution_numbers:
            st.error("Nenhum arquivo de resultado encontrado.")
            st.stop()

    def run(self):
        self.header()

        # Renderiza os resultados consolidados
        ConsolidatedResultsComponent.render()

        # Seleção de execução
        with st.container():
            st.subheader("Seleção da Execução")
            selected_execution = self.controller.select_execution_with_tabs(self.execution_numbers)

            if st.button("Confirmar Execução Selecionada"):
                st.session_state["selected_execution"] = selected_execution
                st.rerun()

        # Exibe os dados da execução selecionada
        if "selected_execution" in st.session_state and st.session_state["selected_execution"] is not None:
            st.write(f"Você está visualizando os dados da execução {st.session_state['selected_execution']}")

            # Carrega os dados
            data, fig = self.utils.load_execution_data(st.session_state["selected_execution"])

            if data:
                with st.container():
                    SummaryComponent.render(data, st.session_state["selected_execution"])
                with st.container():
                    ConvergenceGraphComponent.render(fig, st.session_state["selected_execution"])
                with st.container():
                    StatisticsTableComponent.render(data)
            else:
                st.error("Erro ao carregar os dados.")
        else:
            st.warning("Nenhuma execução selecionada ou disponível.")

