import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao path para encontrar os módulos
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from database_controller import DatabaseController
from src.DashboardApp.views.Screens.components.custom_components import CardSolutions

class DashboardRCEPage:
    """Nova página de dashboard unificada e refatorada."""

    def __init__(self):
        st.set_page_config(
            page_title="Dashboard RCE Framework",
            page_icon="⚡",
            layout="wide"
        )
        self.db_controller = DatabaseController(base_dir=BASE_DIR.parent)
        self.init_state()

    def init_state(self):
        """Inicializa o estado da sessão do Streamlit."""
        if "df_consolidado" not in st.session_state:
            st.session_state.df_consolidado = self.db_controller.get_consolidated_data()
        if "executions_map" not in st.session_state:
            st.session_state.executions_map = self._get_executions_map()

    def _get_executions_map(self) -> dict:
        """Cria um mapa de execuções disponíveis a partir do dataframe consolidado."""
        df = st.session_state.df_consolidado
        if df is None or df.empty:
            return {}
        
        # Assume que as colunas se chamam 'config_num' e 'exec_num' após a consolidação
        if 'config_num' not in df.columns or 'exec_num' not in df.columns:
            st.error("O arquivo consolidado não contém as colunas 'config_num' ou 'exec_num'.")
            return {}

        return df.groupby('config_num')['exec_num'].apply(lambda x: sorted(x.unique().tolist())).to_dict()

    def render_header(self):
        """Renderiza o cabeçalho da página."""
        st.title("⚡ Dashboard Unificado RCE Framework ⚡")
        st.markdown("**Versão Refatorada** - Foco em performance e manutenibilidade.")
        st.markdown("---")

    def render_consolidated_results(self):
        """Renderiza a tabela de resultados consolidados."""
        if st.session_state.df_consolidado is not None and not st.session_state.df_consolidado.empty:
            with st.expander("Ver Resultados Consolidados", expanded=False):
                st.dataframe(st.session_state.df_consolidado)
        else:
            st.warning("Arquivo de resultados consolidados não encontrado. Execute a consolidação primeiro.")

    def render_execution_details(self, config_num, exec_num):
        """Renderiza os detalhes de uma execução específica (solução, gráfico, etc.)."""
        # 1. Carregar todos os dados necessários usando o controller
        results_data = self.db_controller.get_run_data(config_num, exec_num) or {}
        viz_data = self.db_controller.get_visualization_data(config_num, exec_num)
        df_consolidado = st.session_state.df_consolidado

        # 2. Enriquecer dados com a linha do consolidado
        if df_consolidado is not None and not df_consolidado.empty:
            row = df_consolidado[
                (df_consolidado['config_num'] == config_num) & 
                (df_consolidado['exec_num'] == exec_num)
            ]
            if not row.empty:
                results_data.update(row.iloc[0].to_dict())

        # 3. Reconstruir variáveis de decisão se necessário
        if not results_data.get('best_variables') and results_data:
            var_keys = sorted([k for k in results_data if str(k).startswith('best_var_')], 
                              key=lambda x: int(str(x).split('_')[-1]))
            if var_keys:
                best_vars_list = [results_data[k] for k in var_keys]
                results_data['best_variables'] = best_vars_list
                results_data['best_vars'] = best_vars_list
                results_data['decision_vars'] = {f'Var {i+1}': v for i, v in enumerate(best_vars_list)}

        # 4. Renderizar os componentes da UI
        tab_titles = ["Solução", "Gráfico de Convergência"]
        tab1, tab2 = st.tabs(tab_titles)

        with tab1:
            if results_data:
                CardSolutions.render(results_data, exec_num)
            else:
                st.warning(f"Não foram encontrados dados para Config {config_num}, Exec {exec_num}.")

        with tab2:
            st.subheader("Gráfico de Convergência")
            if viz_data:
                try:
                    df_viz = pd.DataFrame(viz_data)
                    if 'gen' in df_viz.columns:
                        stats_per_gen = df_viz.rename(columns={
                            'gen': 'Generation', 'avg': 'Average Fitness',
                            'min': 'Min Fitness (Best)', 'max': 'Max Fitness'
                        })
                        st.line_chart(stats_per_gen, x='Generation', y=['Average Fitness', 'Min Fitness (Best)', 'Max Fitness'])
                    elif 'Generations' in df_viz.columns:
                        stats_per_gen = df_viz.groupby('Generations')['Fitness'].agg(['mean', 'min', 'max']).reset_index()
                        stats_per_gen = stats_per_gen.rename(columns={
                            'Generations': 'Generation', 'mean': 'Average Fitness',
                            'min': 'Min Fitness (Best)', 'max': 'Max Fitness'
                        })
                        st.line_chart(stats_per_gen, x='Generation', y=['Average Fitness', 'Min Fitness (Best)', 'Max Fitness'])
                    else:
                        st.warning("Formato do arquivo de visualização não reconhecido.")
                except Exception as e:
                    st.error(f"Erro ao renderizar gráfico: {e}")
            else:
                st.warning("Dados de visualização não disponíveis.")

    def run(self):
        """Executa a renderização da página do dashboard."""
        self.render_header()
        self.render_consolidated_results()

        executions_map = st.session_state.executions_map
        if not executions_map:
            st.info("Nenhuma execução encontrada. Rode o framework para gerar resultados.")
            return

        st.markdown("### Visualização por Execução")
        config_keys = sorted(executions_map.keys())
        config_tabs = st.tabs([f"Config {cfg}" for cfg in config_keys])

        for i, tab in enumerate(config_tabs):
            with tab:
                config_num = config_keys[i]
                exec_numbers = executions_map[config_num]
                exec_tabs = st.tabs([f"Execução {en}" for en in exec_numbers])
                for j, exec_tab in enumerate(exec_tabs):
                    with exec_tab:
                        exec_num = exec_numbers[j]
                        self.render_execution_details(config_num, exec_num)

if __name__ == "__main__":
    page = DashboardRCEPage()
    page.run()
