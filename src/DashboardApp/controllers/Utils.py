# -*- coding: utf-8 -*-
import streamlit as st
import pickle
import plotly.io as pio
import plotly.graph_objects as go
import pandas as pd
import os
import glob  # Importar glob para encontrar arquivos
import json
import pathlib


def get_folder_path():
    BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent

    # Define o caminho relativo para a pasta "output" dentro do projeto
    FOLDER_NAME = BASE_DIR / "output"

    # Cria a pasta "output" se ela não existir
    FOLDER_NAME.mkdir(parents=True, exist_ok=True)
    print("\nFOLDER_NAME =", FOLDER_NAME)
    print("FOLDER RAIZ do projeto =", FOLDER_NAME.parent)
    print("\n")

    return FOLDER_NAME

FOLDER_NAME = get_folder_path()


class Utils:
    """Classe Utilitária para funções auxiliares do Dashboard."""

    def __init__(self):
        pass

    def apagar_arquivos(self):

        data_file_selected = FOLDER_NAME
        try:
            for file in os.listdir(data_file_selected):
                file_path = os.path.join(data_file_selected, file)
                os.remove(file_path)
                print(f"Arquivo {file_path} removido com sucesso.")

        except Exception as e:

            print(f"Erro ao remover arquivo {file_path}: {e}")

    def load_files(self, exec_num):
        """Carrega os dados .pkl e a figura .json para a execução especificada."""
        data = None
        data_file_selected = os.path.join(FOLDER_NAME, f"dashboard_data_{exec_num}.pkl")

        # Carregar Dados
        try:
            with open(data_file_selected, "rb") as f:
                data = pickle.load(f)
        except Exception as e:
            print(f"Erro ao carregar o arquivo .pkl: {e}")
            raise

        return data

    # --- Funções Auxiliares ---
    def find_available_executions(self):
        """Encontra arquivos .pkl de execução na pasta especificada
        e retorna os números de execução ordenados."""
        # Use pathlib pattern matching
        data_files = list(FOLDER_NAME.glob("dashboard_data_*.pkl"))
        execution_numbers = []

        for f_path in data_files:
            try:
                # Extract number from filename using Path
                num_str = f_path.stem.split("_")[-1]
                execution_numbers.append(int(num_str))
            except (IndexError, ValueError):
                st.warning(
                    f"Não foi possível extrair o número de execução do arquivo: {f_path}"
                )

        return sorted(execution_numbers)

    def select_execution(self, execution_numbers):
        """Exibe o seletor na barra lateral e retorna o número da execução selecionada."""
        st.sidebar.header("Seleção da Execução")
        selected_num = st.sidebar.selectbox(
            "Selecione o número da execução para visualizar:",
            execution_numbers,  # Já vem ordenada da função anterior
        )
        return selected_num

    def load_execution_data(self, exec_num, debug=False):
        """Carrega os dados .pkl e a figura .json para a execução especificada,
        buscando na pasta FOLDER_NAME."""
        data = None

        # Use pathlib to construct paths
        data_file_selected = FOLDER_NAME / f"dashboard_data_{exec_num}.pkl"

        # verifica se a pasta esta vazia
        if not os.listdir(FOLDER_NAME):
            print("[INFO]A pasta está vazia OK...")

        else:
            if debug:
                print(f"[DEBUG] A pasta não está vazia, possui  arquivos em")
                print(FOLDER_NAME)
                # self.apagar_arquivos()

        # Carregar Dados
        try:
            with open(data_file_selected, "rb") as f:
                data = pickle.load(f)
            st.sidebar.success(
                f"INFO:Dados da execução {exec_num} carregados de '{FOLDER_NAME}'."
            )

        except FileNotFoundError:
            st.error(
                f"Erro Crítico: Arquivo de dados selecionado ({data_file_selected}) não encontrado."
            )
            st.stop()  # Para se o arquivo esperado não for encontrado
        except Exception as e:
            st.error(f"Erro ao carregar dados de {data_file_selected}: {e}")
            st.stop()  # Para em caso de erro de carregamento

        return data


class Controller:
    """Classe Controlador MVC"""

    def __init__(self, delete_files=False):
        self.utils = Utils()
        self.execution_numbers = self.utils.find_available_executions()
        self.set_state("selected_execution", None)
        self.set_state("active_tab_index", 0)

        # Garante que a pasta exista
        if not os.path.exists(FOLDER_NAME):
            st.warning(
                f"A pasta '{FOLDER_NAME}' não foi encontrada. Criando pasta vazia."
            )
            os.makedirs(FOLDER_NAME)

        if delete_files:
            # Apaga os arquivos da pasta primeiro
            for file in os.listdir(FOLDER_NAME):
                file_path = os.path.join(FOLDER_NAME, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    st.warning(f"Erro ao apagar arquivo {file_path}: {e}")

        print("Controller configurado com sucesso.")

    def set_state(self, key, default_value):
        """Gerencia o estado no st.session_state."""
        if key not in st.session_state:
            st.session_state[key] = default_value

    def select_execution_with_tabs(self, execution_numbers):
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
                # Atualiza o índice da aba ativa
                if st.session_state["active_tab_index"] != i:
                    st.session_state["active_tab_index"] = i

                # Exibe os dados da aba ativa
                if st.session_state["active_tab_index"] == i:
                    st.write(
                        f"Você está visualizando os dados da execução {execution_numbers[i]}"
                    )

        # Retorna o número da execução correspondente à aba ativa
        return execution_numbers[st.session_state["active_tab_index"]]
