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

from database_controller import DatabaseController, ConsolidationManager
print(f"Dashboard importing database_controller from: {DatabaseController.__module__}")
from dashboard_config import get_config

import streamlit.components.v1 as components
import os


def run_bare_mode():
    from streamlit_server_state import server
    from streamlit.runtime.scriptrunner.script_run_context import get_script_run_ctx

    # The container can host multiple sessions, so we must make sure to select the correct one!
    session_id = get_script_run_ctx().session_id
    session_info = server.get_current_server()._get_session_info(session_id)
    session_headers = session_info.client.request.headers._dict
    st.write(session_headers)

def rede_template_view(html_path: str | None = None, height: int = 1200):
    """Renderiza o template HTML da rede IEEE dentro do Streamlit.

    Args:
        html_path: Caminho absoluto/relativo para o arquivo HTML. Se None, usa o arquivo padrão ao lado desta tela.
        height: Altura do iframe em pixels.
    """
    # Caminho padrão: src/DashboardApp/plot_rede_IEEE_template_dashboard.html
    #st.write(BASE_DIR)
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

    # Renderiza o HTML completo (com Plotly CDN incluído no próprio arquivo)
    components.html(html_content, height=height, scrolling=True)


class TabPinningController:
    def __init__(self):
        # No state initialization needed here, it will be dynamic based on keys
        pass

    def render_toggle(self, key):
        """Renders the toggle switch and returns its state, using a unique key."""
        # Initialize the state if it doesn't exist
        if key not in st.session_state:
            st.session_state[key] = False
        
        # Render the toggle. It will use st.session_state[key] as its value
        # and update it automatically on interaction.
        st.toggle(
            "📌 Fixar Aba",
            key=key,
            help="Ative para selecionar e fixar a visualização de uma única aba."
        )
        
        # Return the current state.
        return st.session_state[key]

    def render_selection_box(self, tab_options, key):
        """Renders the selection box for choosing a tab, using a unique key."""
        return st.selectbox(
            "Selecione a aba para fixar:",
            options=tab_options,
            key=key
        )


class FrameworkRCEDashboard:
    """Dashboard principal, restaurado e corrigido para incluigr todas as funcionalidades solicitadas."""

    def __init__(self):
        self.db_controller = DatabaseController(base_dir=BASE_DIR)
        self.consolidation_manager = ConsolidationManager(base_dir=BASE_DIR)  # Gerenciador de consolidação
        self.config = get_config()  # Carrega configurações
        self.tab_pinning_controller = TabPinningController()
        self._init_state()
        self.MenuLateral()
        
    def MenuLateral(self):
        
        """Menu lateral único para navegação."""
        st.sidebar.title("🧭 Menu Dashboard")
        
        # logo da UFF
        st.sidebar.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRHVsZ1z9B-HIP8Ddsks0mP3aETeG1CkYixtA&s", width=800)
        st.sidebar.markdown("---")  # Separador visual
        st.info("EM DESENVOLVIMENTO")

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
        st.sidebar.write(config_col, exec_col)
        if not config_col or not exec_col: 
            st.error("O arquivo consolidado não contém as colunas de configuração ou execução.")
            return {}
        
        df[config_col] = df[config_col].astype(str)
        df[exec_col] = df[exec_col].astype(str)
        return df.groupby(config_col)[exec_col].apply(lambda x: sorted(x.unique())).to_dict()

    def renderHeader(self):
        st.title(f"{self.config.PAGE_TITLE} (Versão Completa)")
        st.markdown("Análise de resultados de otimização com Repopulation-With-Elite-Set.")
        
        # Barra de informações e controles usando configurações
        col1,col3 = st.columns([1,  1])
        
        with col1:
            # Status do sistema
            if st.session_state.df_consolidado is not None:
                st.success(self.config.get_message("success", "system_loaded"))
                # Botão de atualização
                if st.button("🔄 Atualizar", key="refresh_btn"):
                    st.rerun()
            else:
                st.warning(self.config.get_message("warning", "system_not_loaded"))
  
        
        with col3:
            # Botão de consolidação com status
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
                            st.error("❌ Falha na consolidação. Verifique os logs.")
                    except Exception as e:
                        st.error(f"{self.config.get_message('error', 'consolidation_error')}: {e}")
            


        # Separador
        st.markdown("---")
        
        # Informações rápidas usando configurações
        if st.session_state.df_consolidado is not None:
            df = st.session_state.df_consolidado
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📁 Total de Execuções", len(df))
            
            with col2:
                config_col, _ = self._validate_required_columns(df)
                if config_col:
                    unique_configs = df[config_col].nunique()
                    st.metric("⚙️ Configurações", unique_configs)
                else:
                    st.metric("⚙️ Configurações", "N/A")
            
            with col3:
                st.metric("📊 Arquivos de Saída", len(st.session_state.executions_map))
            
            with col4:
                if st.session_state.locked_config:
                    st.metric("📌 Config Fixada", st.session_state.locked_config)
                else:
                    st.metric("📌 Config Fixada", "Nenhuma")
        
        st.markdown("---")

    def renderFooter(self):
        st.markdown("---")
        
        # Funcionalidades de exportação e utilitários
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
        
        # Separador
        st.markdown("---")
        
        # Informações de contato e suporte
        with st.expander("📞 Contato e Suporte", expanded=True):
            st.write(f"**Versão:** {self.config.PAGE_TITLE} v17.0")
            st.write("**Desenvolvedores:** Pedro Victor Veras e Rainer Zanghi")
            st.write("**Projeto:** PIBIC UFF 2024/2025")
            st.write("**Framework:** Repopulation-With-Elite-Set")
            st.write("**Email:** pedrovictorveras@id.uff.br")
            st.write("**Universidade:** Universidade Federal Fluminense (UFF)")
            st.write("**Programa:** PIBIC - Programa Institucional de Bolsas de Iniciação Científica")

        self.showSystemInfo()

    def exportData(self):
        """Exporta dados do dashboard. (Funcionalidade simplificada)"""
        st.info("A funcionalidade de exportação de dados completa não está disponível nesta versão simplificada do controlador de banco de dados.")
        st.info("Você pode acessar os resultados consolidados diretamente em: `src/output/resultados_consolidados.xlsx`")

    def clearCache(self):
        """Limpa o cache da sessão."""
        try:
            # Limpa dados da sessão
            if "df_consolidado" in st.session_state:
                del st.session_state.df_consolidado
            if "executions_map" in st.session_state:
                del st.session_state.executions_map
            
            st.success(self.config.get_message("success", "cache_cleared"))
            st.rerun()
        except Exception as e:
            st.error(f"{self.config.get_message('error', 'cache_error')}: {e}")

    def generateReport(self):
        """Gera relatório detalhado do sistema. (Funcionalidade simplificada)"""
        st.info("A funcionalidade de geração de relatório detalhado não está disponível nesta versão simplificada do controlador de banco de dados.")
        st.info("Para um resumo, consulte a seção 'Informações do Sistema'.")
        
        # Exibe informações do sistema
        st.write("**Relatório do Sistema (Resumo):**")
        st.write(f"  • Data/Hora: {pd.Timestamp.now()}")
        st.write(f"  • Total de Execuções Consolidadas: {len(st.session_state.df_consolidado) if st.session_state.df_consolidado is not None else 0}")
        st.write(f"  • Configurações Únicas: {len(st.session_state.executions_map)}")
        
        # Informações do controlador de banco de dados (simplificado)
        try:
            summary = self.db_controller.get_execution_summary()
            st.write(f"  • Execuções Detectadas (via controlador): {summary['total_runs']}")
            st.write(f"  • Total de Arquivos de Saída: {summary['total_files']}")
            st.write("  • Contagem de Arquivos por Tipo:")
            for file_type, count in summary['file_counts'].items():
                st.write(f"    - {file_type.upper()}: {count}")
        except Exception as e:
            st.write(f"  • Erro ao obter resumo do controlador: {e}")

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
                best_vars_list = [results_data[k] for k in var_keys]
                results_data['best_variables'] = best_vars_list
                results_data['best_vars'] = best_vars_list
                results_data['decision_vars'] = {f'VAR {i+1}': v for i, v in enumerate(best_vars_list)}

        viz_data_list = self.db_controller.get_visualization_data_for_run(config_num, exec_num)
        df_viz = pd.DataFrame(viz_data_list) if viz_data_list else pd.DataFrame()

        # --- Define functions for rendering tab content ---
        def render_solucao_tab():
            try:
                CardSolutions.render(results_data, exec_num)
                AgendamentoRedePage(key_prefix=f"agend_{config_num}_{exec_num}", selected_exec=exec_num, solution_vars=results_data.get('best_variables'))
            except Exception as e:
                st.error(f"Erro ao renderizar a aba de Solução: {e}")
                st.info("Tente recarregar a página ou verificar se todos os componentes estão disponíveis.")

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

            st.markdown("---")
            st.subheader("Gráfico de Convergência (Interativo)")
            try:
                html_path = self.db_controller.output_dir / f"grafico_execucao_config{config_num}_exec{exec_num}.html"
                if not html_path.exists():
                     html_path = "/home/pedrov12/Documentos/GitHub/Repopulation-With-Elite-Set/src/output/grafico_execucao_config1_exec1.html"

                with open(html_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                components.html(html_content, height=self.config.CHART_HEIGHT + 100, scrolling=True)
            except FileNotFoundError:
                st.error(f"Arquivo HTML do gráfico não encontrado em: {html_path}")
            except Exception as e:
                st.error(f"Erro ao renderizar o gráfico interativo: {e}")

        def render_pop_final_tab():
            st.subheader("Análise da População Final")
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

        def render_dashboard_tab():
            try:
                rede_template_view()
            except Exception as e:
                st.error(f"Tente recarregar a página ou verificar se o componente está disponível: {e}")

        tab_definitions = {
            "Solução": render_solucao_tab,
            "Gráficos de Convergência": render_graficos_tab,
            "População Final": render_pop_final_tab,
            "Dashboard Sistema Elétrico": render_dashboard_tab
        }

        if pinned_tab_name:
            render_function = tab_definitions.get(pinned_tab_name)
            if render_function:
                render_function()
        else:
            tab_names = list(tab_definitions.keys())
            tabs = st.tabs(tab_names)
            for tab, (name, render_func) in zip(tabs, tab_definitions.items()):
                with tab:
                    render_func()
                    
    def showSystemInfo(self):
        """Mostra informações detalhadas do sistema usando configurações."""
        with st.expander("ℹ️ Informações do Sistema", expanded=False):
            
            # Informações técnicas
            st.write("**Informações Técnicas:**")
            #st.write(f"  • Base Directory: {self.config.BASE_DIR}")
            #st.write(f"  • Output Directory: {self.config.OUTPUT_DIR}")
            st.write(f"  • Debug Mode: {self.config.DEBUG_MODE}")
            st.write(f"  • Log Level: {self.config.LOG_LEVEL}")
            
            # Status dos componentes
            # st.write("**Status dos Componentes:**")
            # for component_name, config in self.config.COMPONENTS.items():
            #     status = "✅ Habilitado" if config.get("enabled", True) else "❌ Desabilitado"
            #     st.write(f"  {status} {component_name}")
            
            # Informações do sistema
            st.write("**Informações do Sistema:**")
            if st.session_state.df_consolidado is not None:
                df = st.session_state.df_consolidado
                st.write(f"  • Total de Execuções: {len(df)}")
                st.write(f"  • Colunas Disponíveis: {list(df.columns)}")
            
            # Funcionalidades do orquestrador
            st.write("**Funcionalidades do Controlador de Dados (Simplificado):**")
            try:
                summary = self.db_controller.get_execution_summary()
                st.write(f"  • Total de Execuções Detectadas: {summary['total_runs']}")
                st.write(f"  • Total de Arquivos de Saída: {summary['total_files']}")
                st.write("  • Contagem de Arquivos por Tipo:")
                for file_type, count in summary['file_counts'].items():
                    st.write(f"    - {file_type.upper()}: {count}")
            except Exception as e:
                st.write(f"  • Erro ao obter resumo do controlador: {e}")
            
            # Status da consolidação
            st.write("**Status da Consolidação:**")
            try:
                consolidation_status = self.consolidation_manager.get_consolidation_status()
                st.write(f"  • Arquivo Consolidado: {'✅ Sim' if consolidation_status['consolidated_file_exists'] else '❌ Não'}")
                if consolidation_status['consolidated_file_exists']:
                    st.write(f"  • Última Consolidação: {consolidation_status['last_consolidation']}")
                    st.write(f"  • Tamanho do Arquivo: {consolidation_status['file_size_mb']} MB")
                    st.write(f"  • Total de Execuções: {consolidation_status['total_executions']}")
                    st.write(f"  • Total de Configurações: {consolidation_status['total_configs']}")
                
                if consolidation_status.get('needs_consolidation', False):
                    st.warning("⚠️ Nova consolidação necessária!")
                else:
                    st.success("✅ Consolidação atualizada")
                    
            except Exception as e:
                st.write(f"  • Erro ao verificar status: {e}")

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

        for i, config_tab_ui in enumerate(config_tabs):
            with config_tab_ui:
                config_num = config_keys[i]
                
                tab_names = ["Solução", "Gráficos de Convergência", "População Final", "Dashboard Sistema Elétrico"]

                toggle_key = f"pin_toggle_{config_num}"
                select_key = f"pin_select_{config_num}"

                is_pinned = self.tab_pinning_controller.render_toggle(key=toggle_key)

                if is_pinned:
                    selected_tab_name = self.tab_pinning_controller.render_selection_box(tab_names, key=select_key)
                    
                    exec_numbers = executions_map.get(config_num, [])
                    if not exec_numbers:
                        st.warning("Nenhuma execução encontrada para esta configuração.")
                        continue

                    selected_exec = st.selectbox(
                        "Selecione a Execução:",
                        options=exec_numbers,
                        key=f"exec_select_{config_num}"
                    )
                    
                    st.markdown("---")
                    self.renderExecutionDetails(config_num, selected_exec, pinned_tab_name=selected_tab_name)

                else:
                    exec_numbers = executions_map.get(config_num, [])
                    if not exec_numbers:
                        st.warning("Nenhuma execução encontrada para esta configuração.")
                        continue
                        
                    exec_tabs = st.tabs([f"Execução {en}" for en in exec_numbers])
                    for j, exec_tab_ui in enumerate(exec_tabs):
                        with exec_tab_ui:
                            self.renderExecutionDetails(config_num, exec_numbers[j])
        
        self.renderFooter()