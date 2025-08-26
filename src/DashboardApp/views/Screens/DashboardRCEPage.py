import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import numpy as np
from .components.dash_rce_components import (
    CardSolutions,
    StatisticsTableComponent
)
from .components.AgendamentoRedePage import AgendamentoRedePage

# --- Adiciona o diretório raiz ao path para encontrar os módulos ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from database_controller import DatabaseController
print(f"Dashboard importing database_controller from: {DatabaseController.__module__}")
from dashboard_config import get_config
from consolidation_manager import ConsolidationManager

import streamlit.components.v1 as components
import os


def rede_template_view(html_path: str | None = None, height: int = 1200):
    """Renderiza o template HTML da rede IEEE dentro do Streamlit."""
    if html_path is None:
        html_path = "/home/pedrov12/Documentos/GitHub/Repopulation-With-Elite-Set/resultados - Artigo PIBIC/plot_rede_IEEE_template_dashboard.html"
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    except FileNotFoundError:
        st.error(f"Arquivo HTML não encontrado: {os.path.abspath(html_path)}")
        st.info("Crie o arquivo ou informe um caminho válido em rede_template_view(html_path=...)")
        return
    except Exception as e:
        st.error(f"Erro ao ler o arquivo HTML: {e}")
        return
    components.html(html_content, height=height, scrolling=True)


class TabPinningController:
    def __init__(self, config):
        self.config = config
        self.fixed_tab_keys = ["solution", "convergence", "statistics", "scheduling"]
        if "pin_tabs_active" not in st.session_state:
            st.session_state.pin_tabs_active = False

    def render_toggle(self):
        st.session_state.pin_tabs_active = st.toggle(
            "📌 Fixar Abas Essenciais",
            value=st.session_state.pin_tabs_active,
            help="Ativa/desativa a visualização apenas das abas de Solução, Convergência, Estatísticas e Agendamento."
        )

    def get_filtered_tab_names(self):
        return [
            self.config.TAB_NAMES[key] for key in (
                self.fixed_tab_keys if st.session_state.pin_tabs_active else self.config.TAB_NAMES.keys()
            )
        ]

    def get_filtered_tab_keys(self):
        return self.fixed_tab_keys if st.session_state.pin_tabs_active else list(self.config.TAB_NAMES.keys())


class FrameworkRCEDashboard:
    """Dashboard principal, preservando Header e Footer, com correção das abas fixáveis."""

    def __init__(self):
        self.db_controller = DatabaseController(base_dir=BASE_DIR)
        self.consolidation_manager = ConsolidationManager(base_dir=BASE_DIR)
        self.config = get_config()
        self.tab_pinning_controller = TabPinningController(self.config)
        self._init_state()

    def _init_state(self):
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
        config_col = self._get_column_name_insensitive(df, ['config_num', 'config', 'configuration', 'configuracao', 'configuração'])
        exec_col = self._get_column_name_insensitive(df, ['exec_num', 'exec', 'execution', 'run', 'execucao', 'execução'])
        return config_col, exec_col

    def _get_executions_map(self):
        df = st.session_state.df_consolidado
        if df is None or df.empty:
            return {}
        config_col, exec_col = self._validate_required_columns(df)
        if not config_col or not exec_col:
            st.error("O arquivo consolidado não contém as colunas de configuração ou execução.")
            return {}
        df[config_col] = df[config_col].astype(str)
        df[exec_col] = df[exec_col].astype(str)
        return df.groupby(config_col)[exec_col].apply(lambda x: sorted(x.unique())).to_dict()

    # ------------------- HEADER -------------------
    def renderHeader(self):
        st.title(f"{self.config.PAGE_TITLE} (Versão Completa)")
        st.markdown("Análise de resultados de otimização com Repopulation-With-Elite-Set.")
        col1, col3 = st.columns([1, 1])
        with col1:
            if st.session_state.df_consolidado is not None:
                st.success(self.config.get_message("success", "system_loaded"))
                if st.button("🔄 Atualizar", key="refresh_btn"):
                    st.rerun()
            else:
                st.warning(self.config.get_message("warning", "system_not_loaded"))
        with col3:
            consolidation_status = self.consolidation_manager.get_consolidation_status()
            if consolidation_status.get('needs_consolidation', False):
                st.warning("⚠️ Consolidação necessária")
                consolidate_text = "🔄 Consolidar Agora"
            else:
                st.success("✅ Consolidação atualizada")
                consolidate_text = "📊 Re-consolidar"
            if st.button(consolidate_text, key="consolidate_btn"):
                with st.spinner("Consolidando resultados..."):
                    try:
                        success = self.consolidation_manager.run_consolidation()
                        if success:
                            st.success(self.config.get_message("success", "consolidation_complete"))
                            st.rerun()
                        else:
                            st.error("❌ Falha na consolidação.")
                    except Exception as e:
                        st.error(f"Erro na consolidação: {e}")
            self.tab_pinning_controller.render_toggle()
        st.markdown("---")

    # ------------------- FOOTER -------------------
    def renderFooter(self):
        st.markdown("---")
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.info("Desenvolvido por Pedro Victor Veras e Rainer Zanghi em um projeto PIBIC pela UFF - 2024/2025")
        with col2:
            if st.button("📥 Exportar Dados", key="export_btn"):
                self.exportData()
        with col3:
            if st.button("🧹 Limpar Cache", key="clear_cache_btn"):
                self.clearCache()
        with col4:
            if st.button("📋 Relatório", key="report_btn"):
                self.generateReport()
        with st.expander("📞 Contato e Suporte", expanded=False):
            st.write("**Email:** pedro.veras@id.uff.br")
            st.write("**Projeto:** Repopulation-With-Elite-Set")
            st.write("**Universidade:** Universidade Federal Fluminense (UFF)")
            st.write("**Programa:** PIBIC - Programa Institucional de Bolsas de Iniciação Científica")

    # ------------------- EXECUTION DETAILS -------------------
    def renderExecutionDetails(self, config_num, exec_num):
        results_data = self.db_controller.get_run_data(config_num, exec_num) or {}
        viz_data_list = self.db_controller.get_visualization_data_for_run(config_num, exec_num)
        df_viz = pd.DataFrame(viz_data_list) if viz_data_list else pd.DataFrame()
        tab_names = self.tab_pinning_controller.get_filtered_tab_names()
        tab_keys = self.tab_pinning_controller.get_filtered_tab_keys()
        tabs = st.tabs(tab_names)
        tab_map = {key: tab for key, tab in zip(tab_keys, tabs)}
        if "solution" in tab_map:
            with tab_map["solution"]:
                try:
                    CardSolutions.render(results_data, exec_num)
                    st.markdown("---")
                    AgendamentoRedePage(key_prefix=f"agend_{config_num}_{exec_num}", selected_exec=exec_num, solution_vars=results_data.get("best_variables"))
                except Exception as e:
                    st.error(f"Erro ao renderizar aba de Solução: {e}")
        if "convergence" in tab_map:
            with tab_map["convergence"]:
                st.subheader("📈 Gráfico de Convergência")
                if not df_viz.empty:
                    if 'gen' in df_viz.columns:
                        stats_df = df_viz.rename(columns={'gen': 'Generation', 'avg': 'Média', 'min': 'Mínimo', 'max': 'Máximo'})
                        st.line_chart(stats_df, x='Generation', y=['Média', 'Mínimo', 'Máximo'], height=self.config.CHART_HEIGHT)
                    elif 'Generations' in df_viz.columns:
                        stats_df = df_viz.groupby('Generations')['Fitness'].agg(['mean', 'min', 'max']).reset_index()
                        stats_df = stats_df.rename(columns={'Generations': 'Generation', 'mean': 'Média', 'min': 'Mínimo', 'max': 'Máximo'})
                        st.line_chart(stats_df, x='Generation', y=['Média', 'Mínimo', 'Máximo'], height=self.config.CHART_HEIGHT)
                    else:
                        st.warning("Colunas de geração não encontradas.")
                else:
                    st.warning("Dados de visualização não disponíveis.")
        if "statistics" in tab_map:
            with tab_map["statistics"]:
                st.subheader("📊 Estatísticas")
                if not df_viz.empty:
                    if hasattr(StatisticsTableComponent, "render"):
                        StatisticsTableComponent.render(df_viz)
                    else:
                        st.dataframe(df_viz.describe())
                        st.dataframe(df_viz.head(20))
                else:
                    st.warning("Dados de estatísticas não disponíveis.")
        if "scheduling" in tab_map:
            with tab_map["scheduling"]:
                st.subheader("🎯 Agendamento Final")
                pop_final_path = self.config.POP_FINAL_FILE
                if pop_final_path.exists():
                    try:
                        pop_df = pd.read_excel(pop_final_path)
                        st.success(f"✅ Arquivo de população final encontrado: {len(pop_df)} indivíduos")
                        with st.expander("📋 Visualizar População Final"):
                            st.dataframe(pop_df.head(self.config.MAX_ROWS_IN_TABLE))
                    except Exception as e:
                        st.error(f"Erro ao ler população final: {e}")
                else:
                    st.info("Arquivo de população final não encontrado.")

    # ------------------- MAIN RUN -------------------
    def run(self):
        self.renderHeader()
        executions_map = st.session_state.executions_map
        if not executions_map:
            st.warning("Nenhum resultado consolidado encontrado. Execute a consolidação através do Launcher.")
            st.stop()
        df_consolidado = st.session_state.df_consolidado
        if df_consolidado is not None and not df_consolidado.empty:
            st.subheader("📈 Resultados Consolidados")
            st.dataframe(df_consolidado, use_container_width=True)
        else:
            st.warning("Nenhum resultado consolidado encontrado.")
            st.stop()
        config_keys = sorted(executions_map.keys())
        config_tabs = st.tabs([f"Config {cfg}" for cfg in config_keys])
        for i, tab in enumerate(config_tabs):
            with tab:
                config_num = config_keys[i]
                exec_numbers = executions_map.get(config_num, [])
                exec_tabs = st.tabs([f"Execução {en}" for en in exec_numbers])
                for j, exec_tab in enumerate(exec_tabs):
                    with exec_tab:
                        self.renderExecutionDetails(config_num, exec_numbers[j])
        self.renderFooter()
