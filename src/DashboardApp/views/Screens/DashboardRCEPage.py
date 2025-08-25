import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import numpy as np

# --- Adiciona o diretório raiz ao path para encontrar os módulos ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from database_controller import DatabaseController

# --- Definição dos Componentes da UI diretamente no arquivo ---

class CardSolutions:
    """Componente para exibir o resumo da melhor solução."""
    @staticmethod
    def render(data, exec_num, debug=False):
        best_gen_idx = data.get('best_gen_idx', 'N/A')
        best_fitness = data.get('best_fitness', float('nan'))
        num_generations = data.get('params', {}).get('NUM_GENERATIONS', 100)
        fitness_value = f"{float(best_fitness):.4f}" if isinstance(best_fitness, (int, float)) and not pd.isna(best_fitness) else "N/A"

        st.metric("🏆 Melhor Fitness", fitness_value)
        st.metric("📊 Melhor Geração", best_gen_idx)

        st.subheader("Variáveis de Decisão")
        vars_to_display = data.get('decision_vars', {})
        if not vars_to_display:
            best_vars_list = data.get('best_variables', [])
            if isinstance(best_vars_list, (list, tuple)) and best_vars_list:
                vars_to_display = {f"VAR {i+1}": val for i, val in enumerate(best_vars_list)}

        if vars_to_display:
            st.json(vars_to_display)
        else:
            st.info("Nenhuma variável de decisão disponível.")

class StatisticsTableComponent:
    """Componente para exibir a tabela de estatísticas."""
    @staticmethod
    def render(viz_data):
        if not viz_data:
            st.warning("Dados de visualização não disponíveis para a tabela de estatísticas.")
            return
        try:
            df_viz = pd.DataFrame(viz_data)
            st.dataframe(df_viz)
        except Exception as e:
            st.error(f"Erro ao renderizar tabela de estatísticas: {e}")

# --- Classe Principal do Dashboard ---

class FinalDashboardPage:
    def __init__(self):
        st.set_page_config(page_title="Dashboard RCE Framework", page_icon="⚡", layout="wide")
        self.db_controller = DatabaseController(base_dir=BASE_DIR)
        self.init_state()

    def init_state(self):
        if "df_consolidado" not in st.session_state:
            st.session_state.df_consolidado = self.db_controller.get_consolidated_data()
        if "executions_map" not in st.session_state:
            st.session_state.executions_map = self._get_executions_map()

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

    def render_header_and_footer(self):
        st.title("⚡ Dashboard RCE Framework ⚡")
        st.markdown("**Versão Final Consolidada**")
        # Footer pode ser adicionado no final do método run

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

        tab1, tab2, tab3 = st.tabs(["Solução", "Gráfico de Convergência", "Estatísticas"])

        with tab1:
            CardSolutions.render(results_data, exec_num)

        with tab2:
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
            StatisticsTableComponent.render(viz_data)

    def run(self):
        self.render_header_and_footer()

        if st.session_state.df_consolidado is None or st.session_state.df_consolidado.empty:
            st.warning("Nenhum resultado consolidado encontrado. Execute a consolidação através do Laucher.")
            return

        config_tabs = st.tabs([f"Config {cfg}" for cfg in sorted(st.session_state.executions_map.keys())])
        for i, tab in enumerate(config_tabs):
            with tab:
                config_num = sorted(st.session_state.executions_map.keys())[i]
                exec_numbers = st.session_state.executions_map[config_num]
                exec_tabs = st.tabs([f"Execução {en}" for en in exec_numbers])
                for j, exec_tab in enumerate(exec_tabs):
                    with exec_tab:
                        exec_num = exec_numbers[j]
                        self.render_execution_details(config_num, exec_num)
        
        st.markdown("---")
        st.info("Desenvolvido por Pedro Victor Veras e Rainer Zanghi em um projeto PIBIC pela UFF - 2024/2025")

if __name__ == "__main__":
    page = FinalDashboardPage()
    page.run()
