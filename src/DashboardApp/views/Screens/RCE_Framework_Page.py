import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import numpy as np

# --- Adiciona o diretório raiz ao path para encontrar os módulos ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from database_controller import DatabaseController
from src.DashboardApp.views.Screens.components.dash_rce_components import (
    CardSolutions,
    StatisticsTableComponent
)
from src.DashboardApp.views.Screens.components.AgendamentoRedePage import AgendamentoRedePage

class RCEFrameworkDashboard:
    """Dashboard principal, restaurado e corrigido para incluir todas as funcionalidades solicitadas."""

    def __init__(self):
        st.set_page_config(page_title="Dashboard RCE Framework", page_icon="⚡", layout="wide")
        self.db_controller = DatabaseController(base_dir=BASE_DIR)
        self._init_state()

    def _init_state(self):
        """Inicializa o estado da sessão do Streamlit."""
        if "df_consolidado" not in st.session_state:
            st.session_state.df_consolidado = self.db_controller.get_consolidated_data()
        
        if "executions_map" not in st.session_state:
            st.session_state.executions_map = self._get_executions_map()

        if "locked_config" not in st.session_state:
            st.session_state.locked_config = None

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
        st.title("⚡ Dashboard RCE Framework (Versão Completa) ⚡")
        st.markdown("Análise de resultados de otimização com Repopulation-With-Elite-Set.")

    def render_footer(self):
        st.markdown("---")
        st.info("Desenvolvido por Pedro Victor Veras e Rainer Zanghi em um projeto PIBIC pela UFF - 2024/2025")

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
            CardSolutions.render(results_data, exec_num)
            st.markdown("---")
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

        executions_map = st.session_state.executions_map
        if not executions_map:
            st.warning("Nenhum resultado consolidado encontrado. Execute a consolidação através do Laucher.")
            st.stop()

        # Lógica do Toggle para fixar a visualização
        if st.session_state.locked_config:
            if st.button(f"🔓 Desfixar Configuração {st.session_state.locked_config}"):
                st.session_state.locked_config = None
                st.rerun()
            
            config_num = st.session_state.locked_config
            st.header(f"Configuração {config_num} (Fixada)")
            exec_numbers = executions_map.get(config_num, [])
            exec_tabs = st.tabs([f"Execução {en}" for en in exec_numbers])
            for j, exec_tab in enumerate(exec_tabs):
                with exec_tab:
                    self.render_execution_details(config_num, exec_numbers[j])
        else:
            config_keys = sorted(executions_map.keys())
            config_tabs = st.tabs([f"Config {cfg}" for cfg in config_keys])

            for i, tab in enumerate(config_tabs):
                with tab:
                    config_num = config_keys[i]
                    if st.button(f"📌 Fixar Configuração {config_num}", key=f"pin_{config_num}"):
                        st.session_state.locked_config = config_num
                        st.rerun()
                    
                    exec_numbers = executions_map.get(config_num, [])
                    exec_tabs = st.tabs([f"Execução {en}" for en in exec_numbers])
                    for j, exec_tab in enumerate(exec_tabs):
                        with exec_tab:
                            self.render_execution_details(config_num, exec_numbers[j])
        
        self.render_footer()

if __name__ == "__main__":
    page = RCEFrameworkDashboard()
    page.run()
