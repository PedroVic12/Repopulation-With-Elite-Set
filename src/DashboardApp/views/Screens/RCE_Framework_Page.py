import io
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

# --- Funções de Carregamento de Dados (Refatoradas) ---

@st.cache_data(ttl=60) # Adiciona cache para performance
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
        self.utils = Utils()
        self.options = options or {}
        self.executions = self.load_executions()
        
        # Inicializa estados necessários
        UseState.initialize_state("fixed_view", False)
        UseState.initialize_state("selected_view", "Soluções")
        UseState.initialize_state("fixed_tab", None)
        UseState.initialize_state("current_config", None)
        UseState.initialize_state("current_exec", None)

    def header(self):
        st.markdown("---")
        st.title("⚡ Dashboard Repopulation-With-Elite-Set RCE ⚡")
        st.subheader("Version 15.7.5 - 16/08/2025")
        st.subheader("Artigo Cientifico PIBIC - 28/08/2025")
        st.subheader("Desenvolvido por Pedro Victor Veras e Rainer Zanghi em um projeto PIBIC pela UFF - 2024/2025")
        st.subheader("Apresentação e Resumo UFF - 06/09/2025")
        st.markdown("---")

    def footer(self):
        st.markdown("---")
        st.info("Desenvolvido por Pedro Victor Veras e Rainer Zanghi em um projeto PIBIC pela UFF - 2024/2025")
        st.link_button(
            url="https://github.com/PedroVic12/Repopulation-With-Elite-Set",
            label="Visite a Documentação do Projeto nesse link",
            type="primary",
            icon="📖",
        )
        st.markdown("---")
    
    def load_executions(self) -> Dict[str, List[int]]:
        """Carrega as execuções disponíveis."""
        try:
            df_consolidado = load_consolidated_data(self.db_controller)
            if df_consolidado is None or df_consolidado.empty:
                st.warning("Nenhum dado de execução encontrado para carregar execuções.")
                return {}

            config_col, exec_col = self._validate_required_columns(df_consolidado)
            if not config_col or not exec_col:
                st.error("Não foi possível validar as colunas necessárias para carregar execuções.")
                return {}

            # Converte para string para garantir consistência
            df_consolidado[config_col] = df_consolidado[config_col].astype(str)
            df_consolidado[exec_col] = df_consolidado[exec_col].astype(str)

            # Agrupa as execuções por configuração
            executions = {}
            for config_num, group in df_consolidado.groupby(config_col):
                exec_numbers = sorted(group[exec_col].unique().tolist())
                executions[config_num] = exec_numbers
            
            return executions
        except Exception as e:
            st.error(f"Erro ao carregar execuções: {str(e)}")
            return {}
    
    def _get_column_name_insensitive(self, df, possible_names):
        """Obtém o nome correto da coluna, insensível a maiúsculas/minúsculas."""
        df_columns = [str(col).lower() for col in df.columns]
        for name in possible_names:
            if name.lower() in df_columns:
                return df.columns[df_columns.index(name.lower())]
        return None

    def _validate_required_columns(self, df):
        """Valida se as colunas necessárias existem no DataFrame.
        
        Suporta tanto nomes em inglês quanto em português.
        """
        # Mapeamento de possíveis nomes de colunas em português e inglês
        config_col_names = [
            'config_num', 'config', 'configuration',  # inglês
            'configuracao', 'configuração', 'num_config'  # português
        ]
        
        exec_col_names = [
            'exec_num', 'exec', 'execution', 'run_num', 'run',  # inglês
            'execucao', 'execução', 'num_exec'  # português
        ]
        
        # Tenta encontrar os nomes corretos das colunas
        config_col = self._get_column_name_insensitive(df, config_col_names)
        exec_col = self._get_column_name_insensitive(df, exec_col_names)
        
        # Fallback if not found by insensitive search
        if not config_col:
            config_col = next((col for col in df.columns if 'config' in str(col).lower()), None)
        if not exec_col:
            exec_col = next((col for col in df.columns if 'exec' in str(col).lower() or 'run' in str(col).lower()), None)
        
        # Final check: ensure identified columns actually exist in the DataFrame
        if config_col not in df.columns:
            config_col = None
        if exec_col not in df.columns:
            exec_col = None

        # If still not found, show detailed error
        if not config_col or not exec_col:
            st.error("❌ Erro: Não foi possível identificar as colunas necessárias.")
            st.error("Colunas necessárias:")
            st.error("- Número da Configuração (ex: 'config_num', 'configuracao')")
            st.error("- Número da Execução (ex: 'exec_num', 'execucao', 'run')")
            st.error(f"\nColunas encontradas no arquivo:\n{', '.join(f'\"{col}\"' for col in df.columns)}")
            st.error("\nPor favor, verifique se o arquivo contém as colunas necessárias.")
            return None, None
            
        # Armazena os nomes das colunas para uso posterior
        UseState.set_state("config_column_name", config_col)
        UseState.set_state("exec_column_name", exec_col)
            
        return config_col, exec_col

    def run(self):
        """Método principal para executar o dashboard."""
        st.title("⚡ Dashboard RCE Framework ⚡")
        st.markdown("---")
        
        # Carrega dados consolidados
        df_consolidado = load_consolidated_data(self.db_controller)
        if df_consolidado is None:
            st.error("Não foi possível carregar os dados consolidados.")
            return
            
        # Valida as colunas necessárias
        config_col, exec_col = self._validate_required_columns(df_consolidado)
        if not config_col or not exec_col:
            st.stop() # Stop if columns are not found

        # Store validated column names in session state for later use
        UseState.set_state("config_column_name", config_col)
        UseState.set_state("exec_column_name", exec_col)
        st.session_state['df_consolidado'] = df_consolidado # Store df_consolidado in session state

        # Display consolidated results
        st.header("✅ Resultados Consolidados")
        st.dataframe(df_consolidado)
        
        # Add download button for consolidated results
        csv = df_consolidado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Resultados Consolidados (CSV)",
            data=csv,
            file_name="resultados_consolidados.csv",
            mime="text/csv"
        )
        
        # Convert to Excel for download
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df_consolidado.to_excel(writer, index=False, sheet_name='Resultados Consolidados')
        excel_buffer.seek(0)
        st.download_button(
            label="📥 Baixar Resultados Consolidados (XLSX)",
            data=excel_buffer,
            file_name="resultados_consolidados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Populate self.executions based on df_consolidado
        available_configs = sorted(df_consolidado[config_col].unique())
        executions = {}
        for cfg in available_configs:
            exec_numbers = sorted(df_consolidado[df_consolidado[config_col] == cfg][exec_col].unique().tolist())
            executions[cfg] = exec_numbers
        self.executions = executions # Update self.executions

        # Render sidebar and main content based on fixed view state
        self._render_sidebar()
        self._render_main_content()
    
    def render_execution_details(self, config_num, exec_num):
        """Renderiza os detalhes (Soluções, Gráfico, etc.) para uma execução específica."""
        # Atualiza o estado atual
        UseState.set_state("current_config", config_num)
        UseState.set_state("current_exec", exec_num)
            
        results_data = load_individual_run_data(self.db_controller, config_num, exec_num, "results")
        viz_data = load_individual_run_data(self.db_controller, config_num, exec_num, "visualization")
        
        # Carregar dados da população final
        pop_final_path = OUTPUT_DIR / "pop_final.xlsx"
        pop_final_data = None
        if pop_final_path.exists():
            try:
                pop_final_data = pd.read_excel(pop_final_path)
            except Exception as e:
                st.warning(f"Erro ao carregar pop_final.xlsx: {str(e)}")
        
        # Definir abas
        tab_titles = ["Soluções", "Gráfico de Convergência", "População Final"]
        component_tabs = st.tabs(tab_titles)
        
        # Aba de Soluções
        with component_tabs[0]:
            if results_data:
                # Carregar dados consolidados para extrair decision_vars
                df_consolidado = load_consolidated_data(self.db_controller)
                if df_consolidado is not None:
                    exec_data = df_consolidado[
                        (df_consolidado[UseState.get_state("config_column_name")] == config_num) & 
                        (df_consolidado[UseState.get_state("exec_column_name")] == exec_num)
                    ].iloc[0] if not df_consolidado.empty else None
                    
                    if exec_data is not None:
                        decision_vars = {k: v for k, v in exec_data.items() if k.startswith('var_')}
                        results_data['decision_vars'] = decision_vars
                
                CardSolutions.render(results_data, exec_num, debug=False)
                st.markdown("--- ") # Add a separator after each solution card
            else:
                st.warning("Dados de solução (results.json) não encontrados.")
        
        # Aba de Gráfico de Convergência
        with component_tabs[1]:
            st.subheader("Gráfico de Convergência")
            if viz_data:
                try:
                    df_viz = pd.DataFrame(viz_data)
                    # DEAP logbook keys: gen, nevals, avg, std, min, max
                    rename_map = {
                        'gen': 'Generation',
                        'avg': 'Average Fitness',
                        'std': 'Std Deviation',
                        'min': 'Min Fitness (Best)',
                        'max': 'Max Fitness'
                    }
                    df_viz = df_viz.rename(columns=rename_map)
                    
                    # Plotar o gráfico
                    st.line_chart(df_viz, x='Generation', y=[col for col in rename_map.values() if col in df_viz.columns])
                except Exception as e:
                    st.error(f"Erro ao renderizar gráfico de convergência: {str(e)}")
            else:
                st.warning("Dados de visualização não disponíveis.")
        
        # Aba de População Final
        with component_tabs[2]:
            if pop_final_data is not None:
                st.dataframe(
                    pop_final_data,
                    use_container_width=True,
                    height=600,
                    hide_index=True
                )
                
                # Adicionar botão para baixar os dados
                csv = pop_final_data.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Baixar População Final",
                    data=csv,
                    file_name=f'populacao_final_config_{config_num}_exec_{exec_num}.csv',
                    mime='text/csv'
                )
            else:
                st.warning("Arquivo pop_final.xlsx não encontrado ou inválido.")
        
        # Adicionar espaço no final
        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
        
        # Mostrar parâmetros utilizados
        st.subheader("Parâmetros Utilizados")
        if results_data and 'params' in results_data:
            st.json(results_data['params'], expanded=False)
        else:
            st.warning("Dados de parâmetros não encontrados.")

        self.footer()

    def _render_sidebar(self):
        """Renderiza a barra lateral com controles."""
        with st.sidebar:
            st.header("Controles")
            
            # Toggle para fixar visualização
            fixed_view = UseState.get_state("fixed_view", False)
            if st.button("🔒 Fixar Visualização" if not fixed_view else "🔓 Liberar Visualização"):
                UseState.set_state("fixed_view", not fixed_view)
                st.rerun()
            
            # Seletor de visualização quando fixado
            if UseState.get_state("fixed_view"):
                selected_view_option = st.selectbox(
                    "Visualização Fixa:",
                    ["Soluções", "Gráfico de Convergência", "População Final"],
                    index=["Soluções", "Gráfico de Convergência", "População Final"].index(UseState.get_state("selected_view", "Soluções")),
                    key="fixed_view_option_selector"
                )
                UseState.set_state("selected_view", selected_view_option)

                # Selectors for specific config and exec when fixed view is active
                configs = list(self.executions.keys())
                if not configs:
                    st.warning("Nenhuma configuração encontrada.")
                    return
                
                selected_config = st.selectbox(
                    "Selecione a Configuração:",
                    configs,
                    format_func=lambda x: f"Configuração {x}",
                    key="fixed_config_selector"
                )
                
                if selected_config in self.executions and self.executions[selected_config]:
                    exec_numbers = self.executions[selected_config]
                    # Ensure selected_exec is valid for the current config
                    current_selected_exec = UseState.get_state("current_exec")
                    if current_selected_exec not in exec_numbers:
                        current_selected_exec = exec_numbers[0] # Default to first if not valid

                    selected_exec = st.selectbox(
                        "Selecione a Execução:",
                        exec_numbers,
                        index=exec_numbers.index(current_selected_exec) if current_selected_exec in exec_numbers else 0,
                        format_func=lambda x: f"Execução {x}",
                        key="fixed_exec_selector"
                    )
                    UseState.set_state("current_config", selected_config)
                    UseState.set_state("current_exec", selected_exec)
                else:
                    st.warning("Nenhuma execução disponível para a configuração selecionada.")
    
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
        fixed_view = UseState.get_state("fixed_view")
        if not fixed_view:
            # Dynamic view: iterate through all configs and executions
            # Get validated column names from session state
            config_col = UseState.get_state("config_column_name")
            exec_col = UseState.get_state("exec_column_name")

            if not config_col or not exec_col:
                st.error("Nomes de colunas de configuração/execução não encontrados no estado da sessão.")
                return

            # Load df_consolidado from session state (it's already loaded in run)
            df_consolidado = st.session_state.get('df_consolidado')
            if df_consolidado is None:
                st.error("Dados consolidados não encontrados no estado da sessão.")
                return

            available_configs = sorted(df_consolidado[config_col].unique())
            
            if not available_configs:
                st.info("Nenhuma configuração encontrada nos resultados consolidados.")
                return
                
            config_tabs = st.tabs([f"Config {key}" for key in available_configs])

            for i, config_tab in enumerate(config_tabs):
                with config_tab:
                    config_num = available_configs[i]
                    exec_numbers = sorted(df_consolidado[df_consolidado[config_col] == config_num][exec_col].unique())
                    
                    if not exec_numbers:
                        st.info("Nenhuma execução encontrada para esta configuração.")
                        continue

                    exec_tabs = st.tabs([f"Execução {num}" for num in exec_numbers])
                    for j, exec_tab in enumerate(exec_tabs):
                        with exec_tab:
                            exec_num = exec_numbers[j]
                            self.render_execution_details(config_num, exec_num)
        else:
            # Fixed view: display only the selected config/exec
            config_num = UseState.get_state("current_config")
            exec_num = UseState.get_state("current_exec")
            view_type = UseState.get_state("selected_view")
            
            if not all([config_num, exec_num]):
                st.info("Selecione uma configuração e execução para começar na visualização fixa.")
                return
                
            # Renderiza o componente selecionado na visualização fixa
            if view_type == "Soluções":
                self.render_execution_details(config_num, exec_num) # Call render_execution_details for solutions
            elif view_type == "Gráfico de Convergência":
                # Directly render the convergence graph component
                st.subheader("Gráfico de Convergência")
                viz_data = load_individual_run_data(self.db_controller, config_num, exec_num, "visualization")
                if viz_data:
                    try:
                        df_viz = pd.DataFrame(viz_data)
                        rename_map = {
                            'gen': 'Generation',
                            'avg': 'Average Fitness',
                            'std': 'Std Deviation',
                            'min': 'Min Fitness (Best)',
                            'max': 'Max Fitness'
                        }
                        df_viz = df_viz.rename(columns=rename_map)
                        st.line_chart(df_viz, x='Generation', y=[col for col in rename_map.values() if col in df_viz.columns])
                    except Exception as e:
                        st.error(f"Erro ao renderizar gráfico de convergência: {str(e)}")
                else:
                    st.warning("Dados de visualização não disponíveis.")
            elif view_type == "População Final":
                # Directly render the final population component
                st.subheader("População Final")
                pop_final_path = OUTPUT_DIR / "pop_final.xlsx"
                if pop_final_path.exists():
                    try:
                        pop_final_data = pd.read_excel(pop_final_path)
                        st.dataframe(
                            pop_final_data,
                            use_container_width=True,
                            height=600,
                            hide_index=True
                        )
                        csv = pop_final_data.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Baixar População Final",
                            data=csv,
                            file_name=f'populacao_final_config_{config_num}_exec_{exec_num}.csv',
                            mime='text/csv'
                        )
                    except Exception as e:
                        st.warning(f"Erro ao carregar pop_final.xlsx: {str(e)}")
                else:
                    st.warning("Arquivo pop_final.xlsx não encontrado ou inválido.")
    
    def _render_dynamic_view(self):
        """Renderiza a visualização dinâmica com abas."""
        # Get validated column names from session state
        config_col = UseState.get_state("config_column_name")
        exec_col = UseState.get_state("exec_column_name")

        if not config_col or not exec_col:
            st.error("Nomes de colunas de configuração/execução não encontrados no estado da sessão.")
            return

        # Load df_consolidado from session state (it's already loaded in run)
        df_consolidado = st.session_state.get('df_consolidado')
        if df_consolidado is None:
            st.error("Dados consolidados não encontrados no estado da sessão.")
            return

        available_configs = sorted(df_consolidado[config_col].unique())
        
        if not available_configs:
            st.info("Nenhuma configuração encontrada nos resultados consolidados.")
            return
            
        config_tabs = st.tabs([f"Config {key}" for key in available_configs])

        for i, config_tab in enumerate(config_tabs):
            with config_tab:
                config_num = available_configs[i]
                exec_numbers = sorted(df_consolidado[df_consolidado[config_col] == config_num][exec_col].unique())
                
                if not exec_numbers:
                    st.info("Nenhuma execução encontrada para esta configuração.")
                    continue

                exec_tabs = st.tabs([f"Execução {num}" for num in exec_numbers])
                for j, exec_tab in enumerate(exec_tabs):
                    with exec_tab:
                        exec_num = exec_numbers[j]
                        self.render_execution_details(config_num, exec_num)
    
    def _render_fixed_view(self):
        """Renderiza a visualização fixa selecionada."""
        config_num = UseState.get_state("current_config")
        exec_num = UseState.get_state("current_exec")
        view_type = UseState.get_state("selected_view")
        
        if not all([config_num, exec_num]):
            st.info("Selecione uma configuração e execução para começar na visualização fixa.")
            return
            
        # Renderiza o componente selecionado na visualização fixa
        if view_type == "Soluções":
            self.render_execution_details(config_num, exec_num) # Call render_execution_details for solutions
        elif view_type == "Gráfico de Convergência":
            # Directly render the convergence graph component
            st.subheader("Gráfico de Convergência")
            viz_data = load_individual_run_data(self.db_controller, config_num, exec_num, "visualization")
            if viz_data:
                try:
                    df_viz = pd.DataFrame(viz_data)
                    rename_map = {
                        'gen': 'Generation',
                        'avg': 'Average Fitness',
                        'std': 'Std Deviation',
                        'min': 'Min Fitness (Best)',
                        'max': 'Max Fitness'
                    }
                    df_viz = df_viz.rename(columns=rename_map)
                    st.line_chart(df_viz, x='Generation', y=[col for col in rename_map.values() if col in df_viz.columns])
                except Exception as e:
                    st.error(f"Erro ao renderizar gráfico de convergência: {str(e)}")
            else:
                st.warning("Dados de visualização não disponíveis.")
        elif view_type == "População Final":
            # Directly render the final population component
            st.subheader("População Final")
            pop_final_path = OUTPUT_DIR / "pop_final.xlsx"
            if pop_final_path.exists():
                try:
                    pop_final_data = pd.read_excel(pop_final_path)
                    st.dataframe(
                        pop_final_data,
                        use_container_width=True,
                        height=600,
                        hide_index=True
                    )
                    csv = pop_final_data.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Baixar População Final",
                        data=csv,
                        file_name=f'populacao_final_config_{config_num}_exec_{exec_num}.csv',
                        mime='text/csv'
                    )
                except Exception as e:
                    st.warning(f"Erro ao carregar pop_final.xlsx: {str(e)}")
            else:
                st.warning("Arquivo pop_final.xlsx não encontrado ou inválido.")
    
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
