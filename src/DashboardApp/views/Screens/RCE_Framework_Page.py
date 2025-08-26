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
from dashboard_config import get_config
from consolidation_manager import ConsolidationManager


import streamlit.components.v1 as components
import os



def load_data_excel():
    df = pd.read_excel("/home/pedrov12/Documentos/GitHub/Repopulation-With-Elite-Set/src/output/resultados_consolidados.xlsx")
    return df

def rede_template_view(html_path: str | None = None, height: int = 1200):
    """Renderiza o template HTML da rede IEEE dentro do Streamlit.

    Args:
        html_path: Caminho absoluto/relativo para o arquivo HTML. Se None, usa o arquivo padrão ao lado desta tela.
        height: Altura do iframe em pixels.
    """
    # Caminho padrão: src/DashboardApp/plot_rede_IEEE_template_dashboard.html
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

    # Renderiza o HTML completo (com Plotly CDN incluído no próprio arquivo)
    components.html(html_content, height=height, scrolling=True)


class FrameworkRCEDashboard:
    """Dashboard principal, restaurado e corrigido para incluigr todas as funcionalidades solicitadas."""

    def __init__(self):
        self.db_controller = DatabaseController(base_dir=BASE_DIR)
        self.consolidation_manager = ConsolidationManager(base_dir=BASE_DIR)  # Gerenciador de consolidação
        self.config = get_config()  # Carrega configurações
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

    def render_footer(self):
        st.markdown("---")
        
        # Funcionalidades de exportação e utilitários
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            st.info("Desenvolvido por Pedro Victor Veras e Rainer Zanghi em um projeto PIBIC pela UFF - 2024/2025")
        
        with col2:
            if st.button("📥 Exportar Dados", key="export_btn"):
                self._export_data()
        
        with col3:
            if st.button("🧹 Limpar Cache", key="clear_cache_btn"):
                self._clear_cache()
        
        with col4:
            if st.button("📋 Relatório", key="report_btn"):
                self._generate_report()
        
        # Informações de contato e suporte
        with st.expander("📞 Contato e Suporte", expanded=False):
            st.write("**Email:** pedro.veras@id.uff.br")
            st.write("**Projeto:** Repopulation-With-Elite-Set")
            st.write("**Universidade:** Universidade Federal Fluminense (UFF)")
            st.write("**Programa:** PIBIC - Programa Institucional de Bolsas de Iniciação Científica")

    def _export_data(self):
        """Exporta dados do dashboard usando o orquestrador."""
        try:
            with st.spinner("Exportando dados..."):
                # Cria relatório de saída
                if self.db_controller.create_output_report():
                    st.success(self.config.get_message("success", "export_complete"))
                else:
                    st.error(self.config.get_message("error", "export_error"))
        except Exception as e:
            st.error(f"{self.config.get_message('error', 'export_error')}: {e}")

    def _clear_cache(self):
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

    def _generate_report(self):
        """Gera relatório detalhado do sistema."""
        try:
            with st.spinner("Gerando relatório..."):
                # Usa o orquestrador para criar relatório
                if self.db_controller.create_output_report():
                    st.success("✅ Relatório gerado com sucesso!")
                    
                    # Exibe informações do sistema
                    st.write("**Relatório do Sistema:**")
                    st.write(f"  • Data/Hora: {pd.Timestamp.now()}")
                    st.write(f"  • Total de Execuções: {len(st.session_state.df_consolidado) if st.session_state.df_consolidado is not None else 0}")
                    st.write(f"  • Configurações: {len(st.session_state.executions_map)}")
                    
                    # Informações do orquestrador
                    try:
                        summary = self.db_controller.get_execution_summary()
                        st.write(f"  • Execuções Detectadas: {summary['total_runs']}")
                        st.write(f"  • Total de Arquivos: {sum(summary['file_counts'].values())}")
                    except Exception as e:
                        st.write(f"  • Erro ao obter resumo: {e}")
                        
                else:
                    st.error("❌ Erro ao gerar relatório")
                    
        except Exception as e:
            st.error(f"❌ Erro ao gerar relatório: {e}")

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
                results_data['best_vars'] = best_vars_list
                results_data['decision_vars'] = {f'VAR {i+1}': v for i, v in enumerate(best_vars_list)}

        # Usa nomes de tabs das configurações
        tab_names = [
            self.config.TAB_NAMES["solution"],
            self.config.TAB_NAMES["convergence"],
            self.config.TAB_NAMES["statistics"],
            self.config.TAB_NAMES["scheduling"]
        ]
        tab1, tab2, tab3, tab4 = st.tabs(tab_names)

        with tab1:
            try:
                CardSolutions.render(results_data, exec_num)
                st.markdown("---")
                AgendamentoRedePage(key_prefix=f"agend_{config_num}_{exec_num}", selected_exec=exec_num, solution_vars=results_data.get('best_variables'))
            except Exception as e:
                st.error(f"Erro ao renderizar aba de Solução: {e}")
                st.info("Tente recarregar a página ou verificar se todos os componentes estão disponíveis.")

        with tab2:
            st.subheader("Gráfico de Convergência")
            df_viz = self.db_controller.get_visualization_data(config_num, exec_num)
            st.write(df_viz)
            if df_viz:

                st.write("**Dados de Visualização:**")
                st.dataframe(df_viz.head(self.config.MAX_ROWS_IN_TABLE), use_container_width=True)
                try:

                    if 'gen' in df_viz.columns:
                        stats_df = df_viz.rename(columns={'gen': 'Generation', 'avg': 'Média', 'min': 'Mínimo', 'max': 'Máximo'})
                        st.line_chart(stats_df, x='Generation', y=['Média', 'Mínimo', 'Máximo'], height=self.config.CHART_HEIGHT)
                    elif 'Generations' in df_viz.columns:
                        stats_df = df_viz.groupby('Generations')['Fitness'].agg(['mean', 'min', 'max']).reset_index()
                        stats_df = stats_df.rename(columns={'Generations': 'Generation', 'mean': 'Média', 'min': 'Mínimo', 'max': 'Máximo'})
                        st.line_chart(stats_df, x='Generation', y=['Média', 'Mínimo', 'Máximo'], height=self.config.CHART_HEIGHT)
                except Exception as e:
                    st.error(f"Erro ao renderizar gráfico: {e}")
                    st.info(self.config.get_message("info", "try_reload"))
            else:
                st.warning("Dados de visualização não disponíveis.")
        
        with tab3:
            st.subheader("Tabela de Estatísticas")
            try:
                # Verifica se o componente está habilitado nas configurações
                if self.config.is_component_enabled("StatisticsTableComponent"):
                    StatisticsTableComponent.render(viz_data)
                else:
                    st.warning("Componente de estatísticas desabilitado nas configurações.")
            except Exception as e:
                st.error(f"Erro ao renderizar estatísticas: {e}")
                st.info(self.config.get_message("info", "check_components"))

        with tab4:
            st.warning("População Final não implementada nesta visualização.")
            st.info("Esta funcionalidade será implementada em versões futuras.")
            
            # Adiciona informações sobre população final se o arquivo existir
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
            
            # Adiciona informações do orquestrador
            with st.expander("🔍 Informações do Orquestrador", expanded=False):
                try:
                    summary = self.db_controller.get_execution_summary()
                    st.write("**Resumo das Execuções:**")
                    st.write(f"  • Total de execuções: {summary['total_runs']}")
                    st.write(f"  • Total de arquivos: {sum(summary['file_counts'].values())}")
                    
                    # Lista arquivos por tipo
                    st.write("**Arquivos por Tipo:**")
                    for file_type, count in summary['file_counts'].items():
                        st.write(f"  • {file_type.upper()}: {count}")
                        
                except Exception as e:
                    st.write(f"Erro ao obter informações do orquestrador: {e}")
                    
    def _show_system_info(self):
        """Mostra informações detalhadas do sistema usando configurações."""
        with st.expander("ℹ️ Informações do Sistema", expanded=True):
            st.write(f"**Versão:** {self.config.PAGE_TITLE} v2.0")
            st.write("**Desenvolvedores:** Pedro Victor Veras e Rainer Zanghi")
            st.write("**Projeto:** PIBIC UFF 2024/2025")
            st.write("**Framework:** Repopulation-With-Elite-Set")
            
            # Informações técnicas
            st.write("**Informações Técnicas:**")
            st.write(f"  • Base Directory: {self.config.BASE_DIR}")
            st.write(f"  • Output Directory: {self.config.OUTPUT_DIR}")
            st.write(f"  • Debug Mode: {self.config.DEBUG_MODE}")
            st.write(f"  • Log Level: {self.config.LOG_LEVEL}")
            
            # Status dos componentes
            st.write("**Status dos Componentes:**")
            for component_name, config in self.config.COMPONENTS.items():
                status = "✅ Habilitado" if config.get("enabled", True) else "❌ Desabilitado"
                st.write(f"  {status} {component_name}")
            
            # Informações do sistema
            st.write("**Informações do Sistema:**")
            if st.session_state.df_consolidado is not None:
                df = st.session_state.df_consolidado
                st.write(f"  • Total de Execuções: {len(df)}")
                st.write(f"  • Colunas Disponíveis: {list(df.columns)}")
            
            # Funcionalidades do orquestrador
            st.write("**Funcionalidades do Orquestrador:**")
            try:
                summary = self.db_controller.get_execution_summary()
                st.write(f"  • Total de Execuções: {summary['total_runs']}")
                st.write(f"  • Total de Arquivos: {sum(summary['file_counts'].values())}")
            except Exception as e:
                st.write(f"  • Erro ao obter resumo: {e}")
            
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
        self.render_header()

        executions_map = st.session_state.executions_map
        if not executions_map:
            st.warning("Nenhum resultado consolidado encontrado. Execute a consolidação através do Launcher.")
            st.stop()
            
        # Ensure df_consolidado and executions_map are initialized in _init_state
        # and are available in st.session_state
        df_consolidado = st.session_state.df_consolidado
        executions_map = st.session_state.executions_map

        if df_consolidado is not None and not df_consolidado.empty:
            st.subheader("📈 Resultados Consolidados de Todas as Configurações e Execuções")
            st.dataframe(df_consolidado, use_container_width=True)
        else:
            st.warning("Nenhum resultado consolidado encontrado. Execute a consolidação através do Launcher.")
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

