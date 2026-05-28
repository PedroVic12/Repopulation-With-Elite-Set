# -*- coding: utf-8 -*-
import json
import pickle
import plotly.io as pio
import plotly.graph_objects as go
import pandas as pd
import os
import pathlib
import time 
import streamlit as st


def load_params_from_file(path):
    with open(path, 'r') as file:
        params = json.load(file)
    return params

path_json = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "params.json"
path_options = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "options.json"
PARAMETROS_JSON = load_params_from_file(path_json)
OPTIONS_JSON = load_params_from_file(path_options)
#print("PARAMETROS_JSON DEFAULT:", PARAMETROS_JSON)  
current_dir = pathlib.Path(__file__).parent





def get_folder_path():
    BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent

    # Define o caminho relativo para a pasta "output" dentro do projeto
    FOLDER_NAME = BASE_DIR / "output"

    # Cria a pasta "output" se ela não existir
    FOLDER_NAME.mkdir(parents=True, exist_ok=True)
    #print("\nFOLDER_NAME =", FOLDER_NAME)
    #print("FOLDER RAIZ do projeto =", FOLDER_NAME.parent)
    #print("\n")

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
                #print(f"Arquivo {file_path} removido com sucesso.")
                
            st.success(f"Todos os arquivos na pasta {data_file_selected} foram removidos com sucesso.")

        except Exception as e:

            st.error(f"Erro ao remover arquivo {file_path}: {e}")

    def get_html_content_from_folder(self, folder_path_str: str) -> dict:
        """
        Lê o conteúdo de todos os arquivos HTML em uma pasta especificada.

        Args:
            folder_path_str (str): O caminho para a pasta contendo os arquivos HTML.

        Returns:
            dict: Um dicionário onde as chaves são os nomes dos arquivos HTML
                  e os valores são o conteúdo desses arquivos.
                  Retorna um dicionário vazio se a pasta não existir ou não houver arquivos HTML.
        """
        folder_path = pathlib.Path(folder_path_str)
        files = []

        if not folder_path.is_dir():
            st.error(f"Erro: O caminho '{folder_path_str}' não é um diretório válido ou não existe.")
            return files

        for html_file in folder_path.glob("*.html"):
            try:
                #with open(html_file, "r", encoding="utf-8") as f:
                    #html_contents[html_file.name] = f.read()
                #print(f"Lido com sucesso: {html_file.name}")
                files.append(html_file.name)

            except Exception as e:
                st.error(f"Erro ao ler o arquivo {html_file.name}: {e}")
        
        if not files:
            st.info(f"Nenhum arquivo HTML encontrado em '{folder_path_str}'.")

        return files

    def load_files(self, exec_num):
        """Carrega os dados .pkl e a figura .json para a execução especificada."""
        data = None
        data_file_selected = os.path.join(FOLDER_NAME, f"dashboard_data_{exec_num}.pkl")

        # Carregar Dados
        try:
            with open(data_file_selected, "rb") as f:
                data = pickle.load(f)
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo .pkl: {e}")
            raise

        return data

    # --- Funções Auxiliares ---
    def find_available_executions(self):
        """
        Encontra arquivos .pkl de execução recursivamente, extrai os nomes de run, 
        configuração e execução, e retorna um dicionário estruturado.
        """
        # Procura recursivamente na pasta output
        data_files = list(FOLDER_NAME.rglob("dashboard_data_config*_exec*.pkl"))
        executions = {}
        warnings = []
        import re

        for f_path in data_files:
            # Tenta pegar o nome da pasta de run (ex: run_2026-05-27_10-28-33)
            run_name = f_path.parent.parent.name
            if not run_name.startswith("run_"):
                run_name = "Default Run"

            match = re.search(r"config(\d+)_exec(\d+)", f_path.stem)
            if match:
                config_num = int(match.group(1))
                exec_num = int(match.group(2))
                
                # Chave única combinando Run e Config
                run_config_key = f"{run_name} | Config {config_num}"
                
                if run_config_key not in executions:
                    executions[run_config_key] = []
                executions[run_config_key].append(exec_num)
            else:
                warnings.append(
                    f"Não foi possível extrair o número de execução do arquivo: {f_path.name}"
                )
        
        # Ordena as execuções para cada chave
        for key in executions:
            executions[key] = sorted(executions[key])
            
        return dict(sorted(executions.items())), warnings

    def select_execution(self, execution_numbers):
        """Exibe o seletor na barra lateral e retorna o número da execução selecionada."""
        st.sidebar.header("Seleção da Execução")
        selected_num = st.sidebar.selectbox(
            "Selecione o número da execução para visualizar:",
            execution_numbers,  # Já vem ordenada da função anterior
        )
        return selected_num

    def load_execution_data(self, run_config_key, exec_num, debug=False):
        """
        Carrega os dados .pkl para a chave de run/config e execução especificadas.
        """
        import re
        data = None
        
        # Extrai run_name e config_num da chave
        try:
            run_name, config_part = run_config_key.split(" | ")
            config_num = re.search(r"Config (\d+)", config_part).group(1)
        except Exception as e:
            st.error(f"Erro ao parsear chave de execução: {e}")
            return None

        file_name = f"dashboard_data_config{config_num}_exec{exec_num}.pkl"
        
        # Procura o arquivo na estrutura de pastas
        if run_name == "Default Run":
             data_file_selected = FOLDER_NAME / file_name
        else:
             data_file_selected = FOLDER_NAME / run_name / f"config_{config_num}" / file_name

        def initial_screen():
            st.title("Bem-vindo ao Dashboard RCE")
            st.info("O framework ainda não foi executado. Execute o framework para visualizar os resultados.")
            st.markdown("---")

        if not os.path.exists(FOLDER_NAME):
            initial_screen()
            return None

        if debug:
            st.sidebar.info(f"[DEBUG] Tentando carregar: {data_file_selected}")

        try:
            with open(data_file_selected, "rb") as f:
                data = pickle.load(f)
            if debug:
                st.sidebar.success(
                    f"INFO: Dados da {run_config_key}/exec {exec_num} carregados."
                )
        except FileNotFoundError:
            st.warning(f"Arquivo de dados não encontrado: {data_file_selected}")
        except Exception as e:
            st.error(f"Erro ao carregar dados de {file_name}: {e}")

        return data


from .ConfigRepository import ConfigRepository

class ConfigController:
    """Controlador para gerenciar a lógica de negócio das configurações."""
    def __init__(self):
        output_path = get_folder_path()
        self.repository = ConfigRepository(output_path)

    def get_formatted_configs(self) -> dict[int, pd.DataFrame]:
        """
        Busca todas as configurações e as formata em DataFrames do Pandas para exibição.

        Returns:
            dict: Dicionário onde a chave é o número da config e o valor é um DataFrame
                  com seus parâmetros.
        """
        configs = self.repository.get_all_configs()
        formatted_configs = {}
        for config_num, params in configs.items():
            # Exclui chaves que não são parâmetros diretos do AG
            params_to_display = {
                k: v for k, v in params.items() 
                if k in ["MUTACAO", "CROSSOVER", "NUM_GENERATIONS", "POP_SIZE"]
            }
            df = pd.DataFrame.from_dict(params_to_display, orient='index', columns=['Valor'])
            df.index.name = "Parâmetro"
            formatted_configs[config_num] = df
        
        return formatted_configs


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

        st.info("Controller configurado com sucesso.")

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
    




def run_utils_test():
    utils = Utils()

    files = utils.get_html_content_from_folder(FOLDER_NAME)

    print("Arquivos HTML encontrados na pasta:", files)
    print("Caminho da pasta de saída:", FOLDER_NAME)

#run_utils_test()