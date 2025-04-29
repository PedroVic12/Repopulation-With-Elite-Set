# -*- coding: utf-8 -*-
import streamlit as st
import pickle
import plotly.io as pio
import plotly.graph_objects as go
import pandas as pd
import os
import glob # Importar glob para encontrar arquivos

# --- Configuração ---
FOLDER_NAME = "output" # Nome da pasta onde os arquivos estão localizados

# Garante que a pasta exista (útil se rodar antes do script gerador por algum motivo)
if not os.path.exists(FOLDER_NAME):
    st.warning(f"A pasta '{FOLDER_NAME}' não foi encontrada. Criando pasta vazia.")
    os.makedirs(FOLDER_NAME)

# --- Funções Auxiliares ---

def find_available_executions():
    """Encontra arquivos .pkl de execução na pasta especificada
       e retorna os números de execução ordenados."""
    # Modificado para buscar dentro da pasta FOLDER_NAME
    search_pattern = os.path.join(FOLDER_NAME, "dashboard_data_*.pkl")
    data_files = glob.glob(search_pattern)
    execution_numbers = []
    for f_path in data_files:
        try:
            # Extrai apenas o nome do arquivo do caminho completo
            filename_only = os.path.basename(f_path)
            # Extrai o número do nome do arquivo (ex: 'dashboard_data_5.pkl' -> 5)
            num_str = filename_only.split('_')[-1].split('.')[0]
            execution_numbers.append(int(num_str))
        except (IndexError, ValueError):
            st.warning(f"Não foi possível extrair o número de execução do arquivo: {f_path}")
    return sorted(execution_numbers) # Retorna a lista ordenada

def select_execution(execution_numbers):
    """Exibe o seletor na barra lateral e retorna o número da execução selecionada."""
    st.sidebar.header("Seleção da Execução")
    selected_num = st.sidebar.selectbox(
        "Selecione o número da execução para visualizar:",
        execution_numbers # Já vem ordenada da função anterior
    )
    return selected_num


class Controller:
    def __init__(self):
        print("Setting up the controller...")

        self.execution_numbers = find_available_executions()
        
        # Inicializa o estado da execução selecionada no session_state
        if "selected_execution" not in st.session_state:
            st.session_state["selected_execution"] = None

    def select_execution_with_tabs(self,execution_numbers):
        """Exibe as execuções como abas e retorna o número da execução selecionada dinamicamente."""
        st.header("Seleção da Execução")
        
        # Inicializa o estado da aba ativa no session_state
        if "active_tab_index" not in st.session_state:
            st.session_state["active_tab_index"] = 0  # Começa com a primeira aba ativa

        # Cria uma aba para cada número de execução
        tabs = st.tabs([f"Execução {num}" for num in execution_numbers])
        
        # Atualiza o índice da aba ativa com base na interação do usuário
        for i, tab in enumerate(tabs):
            with tab:
                if st.session_state["active_tab_index"] != i:
                    st.session_state["active_tab_index"] = i
                st.write(f"Você está visualizando os dados da execução {execution_numbers[i]}")

        # Retorna o número da execução correspondente à aba ativa
        return execution_numbers[st.session_state["active_tab_index"]]


    def setState(self, state):
                
        # # Inicializa o estado da execução selecionada no session_state
                if state not in st.session_state:
                    st.session_state["selected_execution"] = None




def load_execution_data(exec_num):
    """Carrega os dados .pkl e a figura .json para a execução especificada,
       buscando na pasta FOLDER_NAME."""
    data = None
    fig = None
    # Modificado para construir o caminho dentro de FOLDER_NAME
    data_file_selected = os.path.join(FOLDER_NAME, f"dashboard_data_{exec_num}.pkl")
    fig_file_selected = os.path.join(FOLDER_NAME, f"dashboard_fig_{exec_num}.json")

    st.sidebar.markdown("---") # Separador visual

    # Carregar Dados
    try:
        with open(data_file_selected, 'rb') as f:
            data = pickle.load(f)
        st.sidebar.success(f"Dados da execução {exec_num} carregados de '{FOLDER_NAME}'.")
    except FileNotFoundError:
        st.error(f"Erro Crítico: Arquivo de dados selecionado ({data_file_selected}) não encontrado.")
        st.stop() # Para se o arquivo esperado não for encontrado
    except Exception as e:
        st.error(f"Erro ao carregar dados de {data_file_selected}: {e}")
        st.stop() # Para em caso de erro de carregamento

    # Carregar Figura
    try:
        # Verifica a existência usando o caminho completo
        if os.path.exists(fig_file_selected):
            fig = pio.read_json(fig_file_selected)
            st.sidebar.success(f"Figura da execução {exec_num} carregada de '{FOLDER_NAME}'.")
        else:
            st.sidebar.warning(f"Arquivo da figura ({fig_file_selected}) não encontrado.")
            fig = None
    except Exception as e:
        st.error(f"Erro ao carregar figura de {fig_file_selected}: {e}")
        fig = None

    return data, fig


