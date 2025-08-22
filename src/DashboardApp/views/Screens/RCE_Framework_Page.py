import streamlit as st
import sys
import os
import pandas as pd
import numpy as np
import json
import pathlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

# --- Componentes da UI ---
from .components.dash_rce_components import (
    CardSolutions,
    ConsolidatedResultsComponent,
    GraficoPotenciaAtivaReativaComponent,
    GraficoRCEComponent,
    StatisticsTableComponent
)

# --- Configuração de Caminhos ---
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent.parent  # Ajuste conforme necessário
OUTPUT_DIR = BASE_DIR / "output"
sys.path.append(str(BASE_DIR))

# --- Controllers ---
from database_controller_revised import DatabaseController
from controllers.Utils import Controller, Utils, ConfigController

# --- Estado da Aplicação ---
class UseState:
    """Classe para gerenciar o estado da aplicação."""
    
    @staticmethod
    def initialize_state(key: str, default_value: Any) -> None:
        """Inicializa uma chave no session_state com um valor padrão."""
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    @staticmethod
    def get_state(key: str, default_value: Any = None) -> Any:
        """Obtém o valor de uma chave no session_state."""
        return st.session_state.get(key, default_value)
    
    @staticmethod
    def set_state(key: str, value: Any) -> None:
        """Define o valor de uma chave no session_state."""
        st.session_state[key] = value


# --- Classes Principais ---

class FrameworkRCEDashboard:
    """Classe principal do Dashboard RCE Framework."""
    
    def __init__(self, options=None):
        """Inicializa o dashboard com os controladores necessários."""
        self.db_controller = DatabaseController()
        self.utils = Controller()  # Importado de dash_rce_components
        self.options = options or {}
        self.executions = self.load_executions()
        
        # Inicializa estados necessários
        UseState.initialize_state("fixed_view", False)
        UseState.initialize_state("selected_view", "Soluções")
        UseState.initialize_state("fixed_tab", None)
        UseState.initialize_state("current_config", None)
        UseState.initialize_state("current_exec", None)
    
    def load_executions(self) -> Dict[str, List[int]]:
        """Carrega as execuções disponíveis."""
        try:
            return self.utils.find_available_executions()
        except Exception as e:
            st.error(f"Erro ao carregar execuções: {str(e)}")
            return {}
    
    def run(self):
        """Método principal para executar o dashboard."""
        st.title("RCE Framework Dashboard")
        
        # Carrega dados consolidados
        df_consolidado = load_consolidated_data(self.db_controller)
        if df_consolidado is None:
            st.error("Não foi possível carregar os dados consolidados.")
            return
            
        # Verifica as colunas disponíveis
        if 'config_num' not in df_consolidado.columns:
            st.error("Coluna 'config_num' não encontrada nos dados consolidados.")
            st.dataframe(df_consolidado.columns)  # Debug: mostra as colunas disponíveis
            return
            
        # Usa 'execution' se 'exec_num' não existir
        exec_col = 'exec_num' if 'exec_num' in df_consolidado.columns else 'execution'
        
        available_configs = sorted(df_consolidado['config_num'].unique())
        
        if not available_configs:
            st.info("Nenhuma configuração encontrada nos resultados consolidados.")
            return
            
        config_tabs = st.tabs([f"Config {key}" for key in available_configs])

        for i, config_tab in enumerate(config_tabs):
            with config_tab:
                config_num = available_configs[i]
                exec_numbers = sorted(df_consolidado[df_consolidado['config_num'] == config_num][exec_col].unique())
                
                if not exec_numbers:
                    st.info("Nenhuma execução encontrada para esta configuração.")
                    continue

                exec_tabs = st.tabs([f"Execução {num}" for num in exec_numbers])
                for j, exec_tab in enumerate(exec_tabs):
                    with exec_tab:
                        exec_num = exec_numbers[j]
                        self.render_execution_details(config_num, exec_num)
    
    def _render_sidebar(self):
        """Renderiza a barra lateral com controles."""
        with st.sidebar:
            st.header("Controles")
            self._render_view_controls()
            self._render_config_selector()
    
    def _render_view_controls(self):
        """Renderiza os controles de visualização."""
        with st.expander("🔧 Controles de Visualização", expanded=True):
            # Toggle para fixar visualização
            if st.button("🔒 Fixar Visualização" if not UseState.get_state("fixed_view") 
                        else "🔓 Liberar Visualização"):
                UseState.set_state("fixed_view", not UseState.get_state("fixed_view"))
                st.rerun()
            
            # Seletor de visualização quando fixado
            if UseState.get_state("fixed_view"):
                selected = st.selectbox(
                    "Visualização:",
                    ["Soluções", "População Final"],
                    key="view_selector"
                )
                UseState.set_state("selected_view", selected)
    
    def _render_config_selector(self):
        """Renderiza o seletor de configuração."""
        with st.expander("⚙️ Configuração", expanded=True):
            configs = list(self.executions.keys())
            if not configs:
                st.warning("Nenhuma configuração encontrada.")
                return
                
            selected_config = st.selectbox(
                "Selecione a configuração:",
                configs,
                format_func=lambda x: f"Configuração {x}",
                key="selected_config"
            )
            
            if selected_config in self.executions:
                exec_numbers = self.executions[selected_config]
                selected_exec = st.selectbox(
                    "Selecione a execução:",
                    exec_numbers,
                    format_func=lambda x: f"Execução {x}",
                    key="selected_exec"
                )
                
                if st.button("Carregar Dados"):
                    self.load_execution_data(selected_config, selected_exec)
    
    def _load_execution_data(self, config_num: str, exec_num: int):
        """Carrega os dados de uma execução específica."""
        try:
            with st.spinner("Carregando dados..."):
                # Exemplo de carregamento de dados - ajuste conforme necessário
                UseState.set_state("current_config", config_num)
                UseState.set_state("current_exec", exec_num)
                st.success("Dados carregados com sucesso!")
        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")
    
    def _render_main_content(self):
        """Renderiza o conteúdo principal do dashboard."""
        if not UseState.get_state("fixed_view"):
            self._render_dynamic_view()
        else:
            self._render_fixed_view()
    
    def _render_dynamic_view(self):
        """Renderiza a visualização dinâmica com abas."""
        config_num = UseState.get_state("current_config")
        exec_num = UseState.get_state("current_exec")
        
        if not all([config_num, exec_num]):
            st.info("Selecione uma configuração e execução para começar.")
            return
            
        # Renderiza os componentes na ordem desejada
        self._render_solutions_view(config_num, exec_num)
        self._render_statistics_view(config_num, exec_num)
        self._render_power_view(config_num, exec_num)
        self._render_population_view(config_num, exec_num)
    
    def _render_fixed_view(self):
        """Renderiza a visualização fixa selecionada."""
        config_num = UseState.get_state("current_config")
        exec_num = UseState.get_state("current_exec")
        
        if not all([config_num, exec_num]):
            st.info("Selecione uma configuração e execução para começar.")
            return
            
        view_type = UseState.get_state("selected_view")
        
        if view_type == "Soluções":
            self._render_solutions_view(config_num, exec_num)
        elif view_type == "População Final":
            self._render_population_view(config_num, exec_num)
    
    def _render_solutions_view(self, config_num: str, exec_num: int):
        """Renderiza a visualização de soluções."""
        st.header("Soluções")
        try:
            # Exemplo de carregamento de dados - ajuste conforme necessário
            data = self.db_controller.get_solution_data(config_num, exec_num)
            CardSolutions.render(data, exec_num)
        except Exception as e:
            st.error(f"Erro ao carregar soluções: {str(e)}")
    
    def _render_statistics_view(self, config_num: str, exec_num: int):
        """Renderiza a visualização de estatísticas."""
        st.header("Estatísticas")
        try:
            data = self.db_controller.get_statistics_data(config_num, exec_num)
            StatisticsTableComponent.render(data)
        except Exception as e:
            st.error(f"Erro ao carregar estatísticas: {str(e)}")
    
    def _render_power_view(self, config_num: str, exec_num: int):
        """Renderiza a visualização de potência."""
        st.header("Gráfico de Potência")
        try:
            GraficoPotenciaAtivaReativaComponent.render(exec_num)
        except Exception as e:
            st.error(f"Erro ao carregar gráfico de potência: {str(e)}")
    
    def _render_population_view(self, config_num: str, exec_num: int):
        """Renderiza a visualização da população final."""
        st.header("População Final")
        try:
            pop_final_path = OUTPUT_DIR / "pop_final.xlsx"
            if pop_final_path.exists():
                df = pd.read_excel(pop_final_path)
                st.dataframe(df)
                
                # Adiciona botão de download
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Baixar CSV",
                    data=csv,
                    file_name="populacao_final.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Arquivo pop_final.xlsx não encontrado.")
        except Exception as e:
            st.error(f"Erro ao carregar população final: {str(e)}")

# Ponto de entrada principal
if __name__ == "__main__":
    dashboard = FrameworkRCEDashboard()
    dashboard.run()
def load_consolidated_data(_db_controller):
    """Carrega os dados do arquivo Excel consolidado."""
    if not _db_controller.consolidated_results_file.exists():
        st.warning(f"Arquivo de resultados consolidados não encontrado em: {_db_controller.consolidated_results_file}")
        st.info("Por favor, execute a consolidação no Launcher para gerar o relatório.")
        return None
    try:
        return pd.read_excel(_db_controller.consolidated_results_file)
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo de resultados consolidados: {e}")
        return None

@st.cache_data(ttl=60)
def load_individual_run_data(_db_controller, config_num, exec_num, data_type):
    """Carrega dados de um arquivo JSON individual (results ou visualization)."""
    if data_type == "results":
        filename = f"config_{config_num}_exec_{exec_num}_results.json"
    elif data_type == "visualization":
        filename = f"config_{config_num}_exec_{exec_num}_visualization.json"
    else:
        return None

    file_path = _db_controller.output_dir / filename
    if not file_path.exists():
        # Não mostra warning para não poluir a tela, apenas retorna None
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo {file_path}: {e}")
        return None

# --- Classe Principal do Dashboard (Refatorada) ---

class FrameworkRCEDashboard:
    """Classe principal do Dashboard RCE Framework."""
    
    def __init__(self, options=None):
        """Inicializa o dashboard com os controladores necessários."""
        self.db_controller = DatabaseController()
        self.utils = Utils()  # Importado de dash_rce_components
        self.options = options or {}
        self.executions = self.load_executions()
        
        # Inicializa estados necessários
        UseState.initialize_state("fixed_view", False)
        UseState.initialize_state("selected_view", "Soluções")
        UseState.initialize_state("fixed_tab", None)
        UseState.initialize_state("current_config", None)
        UseState.initialize_state("current_exec", None)
    
    def run(self):
        """Método principal para executar o dashboard."""
        st.title("⚡ Dashboard RCE Framework ⚡")
        st.markdown("---")
        
        df_consolidado = load_consolidated_data(self.db_controller)

        if df_consolidado is None:
            st.stop()

        st.header("✅ Resultados Consolidados")
        st.dataframe(df_consolidado)
        
        available_configs = sorted(df_consolidado['config_num'].unique())
        
        if not available_configs:
            st.info("Nenhuma configuração encontrada nos resultados consolidados.")
            st.stop()

        config_tabs = st.tabs([f"Config {key}" for key in available_configs])

        for i, config_tab in enumerate(config_tabs):
            with config_tab:
                config_num = available_configs[i]
                exec_numbers = sorted(df_consolidado[df_consolidado['config_num'] == config_num]['exec_num'].unique())
                
                if not exec_numbers:
                    st.info("Nenhuma execução encontrada para esta configuração.")
                    continue

                exec_tabs = st.tabs([f"Execução {num}" for num in exec_numbers])
                for j, exec_tab in enumerate(exec_tabs):
                    with exec_tab:
                        exec_num = exec_numbers[j]
                        self.render_execution_details(config_num, exec_num)

    def _render_view_controls(self):
        """Renderiza os controles de visualização."""
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Toggle para fixar/liberar visualização
            fixed_view = UseState.get_state("fixed_view", False)
            if st.button("🔒 Fixar Visualização" if not fixed_view else "🔓 Liberar Visualização"):
                UseState.set_state("fixed_view", not fixed_view)
                st.rerun()
        
        with col2:
            # Seletor de visualização quando fixado
            if fixed_view:
                view_options = ["Soluções", "População Final"]
                selected_view = st.selectbox(
                    "Visualização fixa:",
                    options=view_options,
                    index=view_options.index(UseState.get_state("selected_view", "Soluções")),
                    key="view_selector"
                )
                UseState.set_state("selected_view", selected_view)
                UseState.set_state("fixed_tab", selected_view.lower().replace(" ", "_"))
                
                # Se estiver em modo fixo, mostra apenas a visualização selecionada
                config_num = UseState.get_state("current_config")
                exec_num = UseState.get_state("current_exec")
                
                if config_num is not None and exec_num is not None:
                    if selected_view == "Soluções":
                        self._render_solutions_view(config_num, exec_num)
                    else:
                        self._render_population_view(config_num, exec_num)
            else:
                # Se não estiver em modo fixo, mostra todas as abas
                config_keys = list(self.executions.keys())
                config_tabs = st.tabs([f"Config {key}" for key in config_keys])
                
                for i, config_tab in enumerate(config_tabs):
                    with config_tab:
                        config_num = config_keys[i]
                        exec_numbers = self.executions[config_num]
                        exec_tabs = st.tabs([f"Execução {num}" for num in exec_numbers])
                        
                        for j, exec_tab in enumerate(exec_tabs):
                            with exec_tab:
                                exec_num = exec_numbers[j]
                                self.render_execution_details(config_num, exec_num)

    def render_execution_details(self, config_num, exec_num):
        """Renderiza os detalhes (Soluções, Gráfico, etc.) para uma execução específica."""
        # Atualiza o estado atual
        UseState.set_state("current_config", config_num)
        UseState.set_state("current_exec", exec_num)
            
        results_data = load_individual_run_data(self.db_controller, config_num, exec_num, "results")
        viz_data = load_individual_run_data(self.db_controller, config_num, exec_num, "visualization")
        
        # Carregar dados da população final
        pop_final_path = os.path.join("src", "output", "pop_final.xlsx")
        pop_final_data = None
        if os.path.exists(pop_final_path):
            try:
                pop_final_data = pd.read_excel(pop_final_path)
            except Exception as e:
                st.warning(f"Erro ao carregar pop_final.xlsx: {str(e)}")
        
        # Definir abas
        tab_titles = ["Soluções", "Gráfico de Convergência", "População Final"]
        component_tabs = st.tabs(tab_titles)
        
        # Mostrar todas as abas se não estiver em modo fixo
        if not UseState.get_state("fixed_tab"):
            # Aba de Soluções
            with component_tabs[0]:
                if results_data:
                    CardSolutions.render(results_data, exec_num)
                else:
                    st.warning("Dados de resultados não disponíveis.")
            
            # Aba de Gráfico de Convergência
            with component_tabs[1]:
                st.subheader("Gráfico de Convergência")
                if viz_data:
                    try:
                        GraficoRCEComponent.render(exec_num)
                    except Exception as e:
                        st.error(f"Erro ao renderizar gráfico de convergência: {str(e)}")
                else:
                    st.warning("Dados de visualização não disponíveis.")
            
            # Aba de População Final
            with component_tabs[2]:
                if pop_final_data is not None:
                    st.dataframe(pop_final_data)
                    csv = pop_final_data.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Baixar CSV",
                        data=csv,
                        file_name="populacao_final.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("Arquivo pop_final.xlsx não encontrado ou inválido.")
        
        # Modo de visualização fixa
        else:
            selected_view = UseState.get_state("selected_view", "Soluções")
            
            if selected_view == "Soluções":
                if results_data:
                    CardSolutions.render(results_data, exec_num)
                else:
                    st.warning("Dados de resultados não disponíveis.")
            
            elif selected_view == "População Final":
                if pop_final_data is not None:
                    st.dataframe(pop_final_data)
                    csv = pop_final_data.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Baixar CSV",
                        data=csv,
                        file_name="populacao_final.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("Arquivo pop_final.xlsx não encontrado ou inválido.")
        
        # Adicionar espaço no final
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Mostrar parâmetros utilizados
        st.subheader("Parâmetros Utilizados")
        if results_data and 'params' in results_data:
            st.json(results_data['params'], expanded=False)
        else:
            st.warning("Dados de parâmetros não encontrados.")

# --- Ponto de Entrada ---
# Este arquivo é uma "página" e deve ser chamado por um app Streamlit principal.
# Para testar isoladamente, você pode adicionar:
# if __name__ == "__main__":
#     dashboard = FrameworkRCEDashboard()
#     dashboard.run()