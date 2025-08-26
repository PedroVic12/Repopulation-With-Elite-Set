import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import numpy as np
from components.dash_rce_components import (
    CardSolutions,
    StatisticsTableComponent
)
from components.AgendamentoRedePage import AgendamentoRedePage

# --- Adiciona o diretório raiz ao path para encontrar os módulos ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from database_controller import DatabaseController
class DashboardRCEPage:
    """Página de dashboard principal, seguindo o esquema do DASHBOARD_ALURA_TEMPLATE.py."""

    def __init__(self):
        st.set_page_config(page_title="Dashboard RCE Framework", page_icon="⚡", layout="wide")
        self.db_controller = DatabaseController(base_dir=BASE_DIR)
        self._init_state()

    def _init_state(self):
        """Inicializa o estado da sessão do Streamlit."""
        # Always initialize these to None first
        if "config_col" not in st.session_state:
            st.session_state.config_col = None
        if "exec_col" not in st.session_state:
            st.session_state.exec_col = None

        if "df_consolidado" not in st.session_state:
            st.session_state.df_consolidado = self.db_controller.get_consolidated_data()
        
        if "executions_map" not in st.session_state:
            st.session_state.executions_map = self._get_executions_map()

        if "selected_config" not in st.session_state:
            st.session_state.selected_config = None
        if "selected_exec" not in st.session_state:
            st.session_state.selected_exec = None

        # Now, update them if data is found
        df = st.session_state.df_consolidado
        if df is not None and not df.empty:
            config_col, exec_col = self._validate_required_columns(df)
            st.session_state.config_col = config_col
            st.session_state.exec_col = exec_col

    def _get_column_name_insensitive(self, df, possible_names):
        df_columns = [str(col).lower().strip() for col in df.columns]
        for name in possible_names:
            if name.lower() in df_columns:
                return df.columns[df_columns.index(name.lower())]
        return None

    def _validate_required_columns(self, df):
        config_col_names = ['config_num', 'config', 'configuration', 'configuracao', 'configuração']
        exec_col_names = ['exec_num', 'exec', 'execution', 'run', 'execucao', 'execução']
        config_col = self._get_column_name_insensitive(df, config_col_names)
        exec_col = self._get_column_name_insensitive(df, exec_col_names)
        return config_col, exec_col

    def _get_executions_map(self) -> dict:
        df = st.session_state.df_consolidado
        if df is None or df.empty: return {}
        config_col, exec_col = self._validate_required_columns(df)
        if not config_col or not exec_col: 
            st.error("O arquivo consolidado não contém as colunas de configuração ou execução.")
            return {}
        
        df[config_col] = df[config_col].astype(str)
        df[exec_col] = df[exec_col].astype(str)
        return df.groupby(config_col)[exec_col].apply(lambda x: sorted(x.unique())).to_dict()

    def render_header(self):
        st.title("⚡ Dashboard RCE Framework ⚡")
        st.markdown("Explore os resultados das execuções do algoritmo evolutivo.")

    def render_footer(self):
        st.markdown("---")
        st.info("Desenvolvido por Pedro Victor Veras e Rainer Zanghi em um projeto PIBIC pela UFF - 2024/2025")

    def render_sidebar_filters(self):
        with st.sidebar:
            st.header("🔍 Filtros de Execução")
            df = st.session_state.df_consolidado
            config_col = st.session_state.config_col
            exec_col = st.session_state.exec_col

            if df is None or df.empty or not config_col or not exec_col:
                st.warning("Nenhum dado de execução para filtrar.")
                return

            configs = sorted(df[config_col].unique())
            selected_config_option = st.selectbox("Configuração", options=configs, format_func=lambda x: f"Configuração {x}")
            
            if selected_config_option:
                execs = sorted(df[df[config_col] == selected_config_option][exec_col].unique())
                selected_exec_option = st.selectbox("Execução", options=execs, format_func=lambda x: f"Execução {x}")
                
                st.session_state.selected_config = selected_config_option
                st.session_state.selected_exec = selected_exec_option

    def render_execution_details(self, config_num, exec_num):
        results_data = self.db_controller.get_run_data(config_num, exec_num) or {}
        viz_data = self.db_controller.get_visualization_data(config_num, exec_num)
        df_consolidado = st.session_state.df_consolidado

        if df_consolidado is not None:
            config_col, exec_col = self._validate_required_columns(df_consolidado)
            if config_col and exec_col:
                row = df_consolidado[(df_consolidado[config_col].astype(str) == str(config_num)) & (df_consolidado[exec_col].astype(str) == str(exec_num))]
                if not row.empty:
                    results_data.update(row.iloc[0].to_dict())

        if not results_data.get('best_variables') and results_data:
            var_keys = sorted([k for k in results_data if str(k).startswith('best_var_')], key=lambda x: int(str(x).split('_')[-1]))
            if var_keys:
                best_vars_list = [results_data[k] for k in var_keys]
                results_data['best_variables'] = best_vars_list
                results_data['decision_vars'] = {f'VAR {i+1}': v for i, v in enumerate(best_vars_list)}

        tab1, tab2, tab3, tab4 = st.tabs(["Solução", "Gráfico de Convergência", "Estatísticas", "Agendamento"])

        with tab1:
            st.subheader("Detalhes da Solução")
            CardSolutions.render(results_data, exec_num)
            st.markdown("---")
            st.subheader("Agendamento de Rede Elétrica")
            AgendamentoRedePage(key_prefix=f"agend_{config_num}_{exec_num}", selected_exec=exec_num, solution_vars=results_data.get('best_variables'))

        with tab2:
            st.subheader("Gráfico de Convergência")
            if viz_data:
                try:
                    df_viz = pd.DataFrame(viz_data)
                    if 'gen' in df_viz.columns:
                        stats_df = df_viz.rename(columns={'gen': 'Generation', 'avg': 'Média', 'min': 'Mínimo', 'max': 'Máximo'})
                        st.line_chart(stats_df, x='Generation', y=['Média', 'Mínimo', 'Máximo'])
                    elif 'Generations' in df_viz.columns:
                        stats_df = df_viz.groupby('Generations')['Fitness'].agg(['mean', 'min', 'max']).reset_index()
                        stats_df = stats_df.rename(columns={'Generations': 'Generation', 'mean': 'Média', 'min': 'Mínimo', 'max': 'Máximo'})
                        st.line_chart(stats_df, x='Generation', y=['Média', 'Mínimo', 'Máximo'])
                except Exception as e:
                    st.error(f"Erro ao renderizar gráfico: {e}")
            else:
                st.warning("Dados de visualização não disponíveis.")
        
        with tab3:
            st.subheader("Tabela de Estatísticas")
            StatisticsTableComponent.render(viz_data)

        with tab4:
            st.warning("População Final não implementada nesta visualização.")

    def run(self):
        self.render_header()
        self.render_sidebar_filters()

        if st.session_state.df_consolidado is None or st.session_state.df_consolidado.empty:
            st.warning("Nenhum resultado consolidado encontrado. Execute a consolidação através do Laucher.")
            self.render_footer()
            return

        selected_config = st.session_state.selected_config
        selected_exec = st.session_state.selected_exec

        if selected_config is not None and selected_exec is not None:
            st.header(f"Detalhes da Execução: Configuração {selected_config} - Execução {selected_exec}")
            self.render_execution_details(selected_config, selected_exec)
        else:
            st.info("Selecione uma configuração e execução na barra lateral para visualizar os detalhes.")
        
        with st.expander("Ver Tabela de Resultados Consolidados", expanded=False):
            if st.session_state.df_consolidado is not None and not st.session_state.df_consolidado.empty:
                st.dataframe(st.session_state.df_consolidado)
            else:
                st.warning("Arquivo de resultados consolidados não encontrado.")
        
        self.render_footer()

if __name__ == "__main__":
    page = DashboardRCEPage()
    page.run()