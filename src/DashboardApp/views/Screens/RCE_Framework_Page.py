import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import numpy as np
import datetime
from streamlit_timeline import st_timeline
import ast

from .components.dash_rce_components import (
    CardSolutions,
    StatisticsTableComponent
)
# Removido AgendamentoRedePage para simplificar e focar na timeline
# from .components.AgendamentoRedePage import AgendamentoRedePage
from .components.dashboard_config import get_config

# --- Adiciona o diretório raiz ao path para encontrar os módulos ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

print(BASE_DIR)

from database_controller import DatabaseController, ConsolidationManager
print(f"Dashboard importing database_controller from: {DatabaseController.__module__}")

import streamlit.components.v1 as components
import os



def rede_template_view(html_path: str | None = None, height: int = 1200):
    """Renderiza o template HTML da rede IEEE dentro do Streamlit.

    Args:
        html_path: Caminho absoluto/relativo para o arquivo HTML. Se None, usa o arquivo padrão ao lado desta tela.
        height: Altura do iframe em pixels.
    """
    if html_path is None:
        html_path = BASE_DIR / "resultados - Artigo PIBIC" / "plot_rede_IEEE_template_dashboard.html"
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
    def __init__(self):
        pass

    def render_toggle(self, key):
        """Renderiza o toggle e retorna seu estado."""
        if key not in st.session_state:
            st.session_state[key] = False
        
        st.toggle(
            "📌 Fixar Aba",
            key=key,
            help="Ative para selecionar e fixar a visualização de uma única aba."
        )
        
        return st.session_state[key]

    def render_selection_box(self, tab_options, key):
        """Renderiza a caixa de seleção para escolher uma aba."""
        return st.selectbox(
            "Selecione a aba para fixar:",
            options=tab_options,
            key=key
        )


class FrameworkRCEDashboard:
    """Dashboard principal, com a timeline integrada na aba Solução."""

    def __init__(self):
        self.db_controller = DatabaseController(base_dir=BASE_DIR)
        self.consolidation_manager = ConsolidationManager(base_dir=BASE_DIR)
        self.config = get_config()
        self.tab_pinning_controller = TabPinningController()
        self._init_state()
        self.MenuLateral()
        
    def MenuLateral(self):
        st.sidebar.title("🧭 Menu Dashboard")
        st.sidebar.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRHVsZ1z9B-HIP8Ddsks0mP3aETeG1CkYixtA&s", use_container_width=True)
        st.sidebar.markdown("---")
        st.info("EM DESENVOLVIMENTO")

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

    def renderHeader(self):
        st.title(f"{self.config.PAGE_TITLE} (Versão Completa)")
        st.markdown("Análise de resultados de otimização com Repopulation-With-Elite-Set.")
        st.markdown("---")
        
        if st.session_state.df_consolidado is not None:
            df = st.session_state.df_consolidado
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📁 Total de Execuções", len(df))
            with col2:
                config_col, _ = self._validate_required_columns(df)
                st.metric("⚙️ Configurações", df[config_col].nunique() if config_col else "N/A")
            with col3:
                st.metric("📊 Arquivos de Saída", len(st.session_state.executions_map))
            with col4:
                st.metric("📌 Config Fixada", st.session_state.locked_config or "Nenhuma")
        
        st.markdown("---")

    def renderFooter(self):
        st.markdown("---")
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.info("Desenvolvido por Pedro Victor Veras e Rainer Zanghi em um projeto PIBIC pela UFF - 2024/2025")
        with col2:
            if st.button("📥 Exportar Dados", key="export_btn"): self.exportData()
        with col3:
            if st.button("🧹 Limpar Cache", key="clear_cache_btn"): self.clearCache()
        with col4:
            if st.button("📋 Relatório", key="report_btn"): self.generateReport()
        st.markdown("---")
        
        with st.expander("📞 Contato e Suporte", expanded=True):
            st.write(f"**Versão:** {self.config.PAGE_TITLE} v17.0")
            st.write("**Desenvolvedores:** Pedro Victor Veras e Rainer Zanghi")
        self.showSystemInfo()

    def exportData(self):
        st.info("Acesse os resultados em: `src/output/resultados_consolidados.xlsx`")

    def clearCache(self):
        try:
            for key in ["df_consolidado", "executions_map"]:
                if key in st.session_state: del st.session_state[key]
            st.success(self.config.get_message("success", "cache_cleared"))
            st.rerun()
        except Exception as e:
            st.error(f"{self.config.get_message('error', 'cache_error')}: {e}")

    def generateReport(self):
        st.info("Para um resumo, consulte a seção 'Informações do Sistema'.")

    def renderExecutionDetails(self, config_num, exec_num, pinned_tab_name=None):
        results_data = self.db_controller.get_run_data(config_num, exec_num) or {}
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
                results_data['best_variables'] = [results_data[k] for k in var_keys]

        viz_data_list = self.db_controller.get_visualization_data_for_run(config_num, exec_num)
        df_viz = pd.DataFrame(viz_data_list) if viz_data_list else pd.DataFrame()

        def render_solucao_tab():
            try:
                CardSolutions.render(results_data, exec_num)
                st.markdown("---")
                st.subheader("🗓️ Linha do Tempo Interativa do Agendamento")
                
                # Garante que as variáveis são numéricas antes de ordenar
                solution_variables = sorted([v for v in results_data.get("best_variables", []) if isinstance(v, (int, float))])

                if not solution_variables:
                    st.warning("Variáveis da solução não encontradas ou em formato inválido para gerar a linha do tempo.")
                    return
                
                items = []
                base_date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                
                for i in range(len(solution_variables) - 1):
                    start_hour, end_hour = solution_variables[i], solution_variables[i+1]
                    duration = end_hour - start_hour
                    items.append({
                        "id": i, 
                        "content": f"Intervalo {i+1} ({duration:.1f}h)",
                        "start": (base_date + datetime.timedelta(hours=start_hour)).isoformat(),
                        "end": (base_date + datetime.timedelta(hours=end_hour)).isoformat(),
                        "title": f"Das {start_hour:.1f}h às {end_hour:.1f}h"
                    })
                
                selected_item = st_timeline(items, groups=[], options={"height": 200}, key=f"timeline_{config_num}_{exec_num}")

                # Lógica de interatividade: mostra detalhes ao clicar
                if selected_item:
                    st.markdown("---")
                    st.subheader(f"⚙️ Detalhes do Intervalo {selected_item['id'] + 1}")
                    
                    # Tenta carregar os detalhes de ramos e contingências
                    details_str = results_data.get('ramos_contingencias', '{}')
                    try:
                        # ast.literal_eval é mais seguro que eval()
                        details_dict = ast.literal_eval(details_str) if isinstance(details_str, str) else details_str
                        
                        if isinstance(details_dict, dict) and 'ramos' in details_dict and 'contingencia' in details_dict:
                            ramos_df = pd.DataFrame(details_dict['ramos'], columns=['De', 'Para'])
                            contingencia_df = pd.DataFrame(pd.Series(details_dict['contingencia']), columns=['ID Contingência'])
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write("📌 **Ramos para Operação**")
                                st.dataframe(ramos_df, use_container_width=True)
                            with col2:
                                st.write("⚠️ **Contingências Consideradas**")
                                st.dataframe(contingencia_df, use_container_width=True)
                        else:
                            st.info("Detalhes de ramos e contingências não encontrados na estrutura esperada.")
                    
                    except (ValueError, SyntaxError) as e:
                        st.error(f"Não foi possível processar os detalhes de ramos/contingências. Verifique o formato dos dados. Erro: {e}")

            except Exception as e:
                st.error(f"Erro ao renderizar a aba de Solução: {e}")

        def render_graficos_tab():
            st.subheader("Gráfico de Convergência (Estatísticas)")
            if not df_viz.empty:
                try:
                    if 'gen' in df_viz.columns:
                        stats_df = df_viz.rename(columns={'gen': 'Generation', 'avg': 'Média', 'min': 'Mínimo', 'max': 'Máximo'})
                        st.line_chart(stats_df, x='Generation', y=['Média', 'Mínimo', 'Máximo'], height=self.config.CHART_HEIGHT)
                    elif 'Generations' in df_viz.columns:
                        stats_df = df_viz.groupby('Generations')['Fitness'].agg(['mean', 'min', 'max']).reset_index()
                        stats_df = stats_df.rename(columns={'Generations': 'Generation', 'mean': 'Média', 'min': 'Mínimo', 'max': 'Máximo'})
                        st.line_chart(stats_df, x='Generation', y=['Média', 'Mínimo', 'Máximo'], height=self.config.CHART_HEIGHT)
                    else:
                        st.warning("Colunas 'gen' ou 'Generations' não encontradas para o gráfico de convergência.")
                except Exception as e:
                    st.error(f"Erro ao renderizar gráfico: {e}")
                    st.info(self.config.get_message("info", "try_reload"))
            else:
                st.warning("Dados de visualização não disponíveis para o gráfico de estatísticas.")

            # st.markdown("---")
            # st.subheader("Gráfico de Convergência (Interativo)")
            # try:
            #     html_path = self.db_controller.output_dir / f"grafico_execucao_config{config_num}_exec{exec_num}.html"
            #     if not html_path.exists():
            #          html_path = "/home/pedrov12/Documentos/GitHub/Repopulation-With-Elite-Set/src/output/grafico_execucao_config1_exec1.html"

            #     with open(html_path, "r", encoding="utf-8") as f:
            #         html_content = f.read()
            #     components.html(html_content, height=self.config.CHART_HEIGHT + 100, scrolling=True)
            # except FileNotFoundError:
            #     st.error(f"Arquivo HTML do gráfico não encontrado em: {html_path}")
            # except Exception as e:
            #     st.error(f"Erro ao renderizar o gráfico interativo: {e}")

        def render_pop_final_tab():
            st.subheader("Análise da População Final")
            pop_final_path = self.config.POP_FINAL_FILE
            if pop_final_path.exists():
                try:
                    pop_df = pd.read_excel(pop_final_path)
                    st.dataframe(pop_df.head(self.config.MAX_ROWS_IN_TABLE))
                except Exception as e:
                    st.error(f"Erro ao ler população final: {e}")
            else:
                st.info("Arquivo de população final não encontrado.")

        def render_dashboard_tab():
            rede_template_view()

        tab_definitions = {
            "Solução": render_solucao_tab,
            "Gráficos de Convergência": render_graficos_tab,
            "População Final": render_pop_final_tab,
            "Dashboard Sistema Elétrico": render_dashboard_tab
        }

        if pinned_tab_name:
            if render_function := tab_definitions.get(pinned_tab_name):
                render_function()
        else:
            tabs = st.tabs(list(tab_definitions.keys()))
            for tab, render_func in zip(tabs, tab_definitions.values()):
                with tab:
                    render_func()
                    
    def showSystemInfo(self):
        with st.expander("ℹ️ Informações do Sistema", expanded=False):
            st.write(f"**Debug Mode:** {self.config.DEBUG_MODE}")
            if st.session_state.df_consolidado is not None:
                st.write(f"**Total de Execuções:** {len(st.session_state.df_consolidado)}")
            
            summary = self.db_controller.get_execution_summary()
            st.write(f"**Execuções Detectadas:** {summary.get('total_runs')}")
            
            status = self.consolidation_manager.get_consolidation_status()
            st.write(f"**Arquivo Consolidado:** {'✅ Sim' if status.get('consolidated_file_exists') else '❌ Não'}")

    def run(self):
        self.renderHeader()
        executions_map = st.session_state.executions_map
        if not executions_map:
            st.warning("Nenhum resultado consolidado encontrado. Execute a consolidação através do Launcher.")
            st.stop()
            
        df_consolidado = st.session_state.df_consolidado
        if df_consolidado is not None and not df_consolidado.empty:
            st.subheader("📈 Resultados Consolidados de Todas as Configurações e Execuções")
            st.dataframe(df_consolidado, use_container_width=True)
        else:
            st.warning("Nenhum resultado consolidado encontrado. Execute a consolidação através do Launcher.")
            st.stop()

        config_keys = sorted(executions_map.keys())
        config_tabs = st.tabs([f"Config {cfg}" for cfg in config_keys])

        # Criação das abas com fixar aba
        for i, config_tab_ui in enumerate(config_tabs):
            with config_tab_ui:
                config_num = config_keys[i]
                
                tab_names = ["Solução", "Gráficos de Convergência", "População Final", "Dashboard Sistema Elétrico"]

                toggle_key = f"pin_toggle_{config_num}"
                select_key = f"pin_select_{config_num}"

                is_pinned = self.tab_pinning_controller.render_toggle(key=toggle_key)
                

                if is_pinned:
                    tab_names = ["Solução", "Gráficos de Convergência", "População Final", "Dashboard Sistema Elétrico"]
                    selected_tab_name = self.tab_pinning_controller.render_selection_box(tab_names, key=select_key)

                    exec_numbers = executions_map.get(config_num, [])

                    # selected_exec = st.selectbox(
                    #     "Selecione a Execução:",
                    #     options=exec_numbers,
                    #     key=f"exec_select_{config_num}"
                    # )
                    # self.renderExecutionDetails(config_num, selected_exec, pinned_tab_name=selected_tab_name)

                    if not exec_numbers:
                        st.warning("Nenhuma execução encontrada para esta configuração.")
                        continue

                    exec_tabs = st.tabs([f"Execução {en}" for en in exec_numbers])
                    for j, exec_tab_ui in enumerate(exec_tabs):
                        with exec_tab_ui:
                            exec_num = exec_numbers[j]
                            self.renderExecutionDetails(config_num, exec_num, pinned_tab_name=selected_tab_name)
                else:
                    exec_numbers = executions_map.get(config_num, [])
                    if not exec_numbers:
                        st.warning("Nenhuma execução encontrada para esta configuração.")
                        continue

                    exec_tabs = st.tabs([f"Execução {en}" for en in exec_numbers])
                    for j, exec_tab_ui in enumerate(exec_tabs):
                        with exec_tab_ui:
                            self.renderExecutionDetails(config_num, exec_numbers[j])

                                    
                    st.markdown("---")

        self.renderFooter()