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

def select_execution_with_tabs(execution_numbers):
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

# --- Componentes da Interface de Usuário ---

class SummaryComponent:
    """Componente para exibir o resumo da melhor solução."""
    
    @staticmethod
    def render(data, exec_num):
        """Exibe o cabeçalho e o resumo da melhor solução."""
        st.header(f"Resultados da Execução: {exec_num}")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f"""
                <div style="border: 2px solid #e6e6e6; border-radius: 5px; padding: 30px; margin: 10px 0; background-color: #d5d5d5;">
                <h3 style="color: #1f77b4;">Resumo da Melhor Solução</h3>
                <h4><strong>Melhor Fitness:</strong> {data.get('best_fitness', 'N/A'):.6f}</h4>
                <h4><strong>Melhor Geração (Índice):</strong> {data.get('best_gen_idx', 'N/A')}</h4>
                </div>
                """, unsafe_allow_html=True)
        with col2:
            st.subheader("BEST DECISION VARIABLES")
            st.write(data.get('best_vars', 'N/A'))

        with st.expander("Parâmetros Utilizados nesta Execução"):
            st.json(data.get('params', {}))


class StatisticsTableComponent:
    """Componente para exibir a tabela de estatísticas por geração."""
    
    @staticmethod
    def render(data):
        """Exibe a tabela de estatísticas por geração, se disponível."""
        if 'logbook_data' in data and isinstance(data['logbook_data'], dict):
            st.subheader("Estatísticas por Geração")
            try:
                log_data = data['logbook_data']
                statics = log_data.get('statics', {})
                stats_data = {
                    "Geração": log_data.get('generation', []),
                    "Min Fitness": statics.get('min_fitness', []),
                    "Média Fitness": statics.get('avg_fitness', []),
                    "Max Fitness": statics.get('max_fitness', []),
                    "Std Dev Fitness": statics.get('std_fitness', [])
                }
                lengths = {key: len(value) for key, value in stats_data.items()}
                if len(set(lengths.values())) <= 1:
                    if lengths and list(lengths.values())[0] > 0:
                        stats_df = pd.DataFrame(stats_data)
                        st.dataframe(stats_df, use_container_width=True)
                    else:
                        st.info("Não há dados de estatísticas por geração para exibir.")
                else:
                    st.warning("Dados de estatísticas por geração têm tamanhos inconsistentes.")
                    st.json(lengths)

            except Exception as e:
                st.warning(f"Não foi possível exibir tabela de estatísticas: {e}")
                st.write("Dados do logbook encontrados:")
                st.json(data.get('logbook_data', {}))
        else:
            st.info("Dados do logbook não encontrados ou em formato inválido no arquivo .pkl.")


class ConvergenceGraphComponent:
    """Componente para exibir o gráfico de convergência."""
    
    @staticmethod
    def render(fig, exec_num):
        """Exibe o gráfico de convergência na página principal."""
        st.header(f"Gráfico de Convergência (Execução {exec_num})")
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Figura não disponível para exibição.")


class ConsolidatedResultsComponent:
    """Componente para exibir os resultados consolidados."""
    
    @staticmethod
    def render():
        """Verifica e exibe a seção de resultados consolidados."""
        # Nome base do arquivo
        consolidated_excel_filename = "results_consolidados.xlsx"
        # Caminho completo para o arquivo
        consolidated_excel_path = consolidated_excel_filename

        # Verifica a existência usando o caminho completo
        if os.path.exists(consolidated_excel_path):
            st.markdown("---")
            st.header("Resultados Consolidados Gerais de todas as execuções")
            try:
                # Lê o excel usando o caminho completo
                df_consolidado = pd.read_excel(consolidated_excel_path)
                st.dataframe(df_consolidado)
                # Abre o arquivo usando o caminho completo para o botão de download
                with open(consolidated_excel_path, "rb") as fp:
                    st.download_button(
                        label="Baixar Resultados Consolidados (Excel)",
                        data=fp,
                        # Usa o nome base do arquivo para o download
                        file_name=consolidated_excel_filename,
                        mime="application/vnd.ms-excel"
                    )
            except Exception as e:
                st.error(f"Erro ao ler o arquivo consolidado {consolidated_excel_path}: {e}")
        else:
            st.info(f"Arquivo de resultados consolidados ({consolidated_excel_path}) não encontrado.")



class DashboardApp:
    """Classe principal do aplicativo Dashboard."""
    
    def __init__(self):
        """Inicializa o aplicativo."""
        #st.set_page_config(layout="wide", page_title="Visualizador de Execuções RCE")
        self.execution_numbers = find_available_executions()
        
        # Inicializa o estado da execução selecionada no session_state
        if "selected_execution" not in st.session_state:
            st.session_state["selected_execution"] = None

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
        
        # Atualiza o estado da execução selecionada no session_state
        if st.session_state["selected_execution"] != selected_execution:
            st.session_state["selected_execution"] = selected_execution
        
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


            
# --- Execução ---
if __name__ == "__main__":
    app = DashboardApp()
    app.run()