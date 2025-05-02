# --- Componentes da Interface de Usuário ---

import streamlit as st
import os
import pandas as pd

class SummaryComponent:
    """Componente para exibir o resumo da melhor solução."""
    
    @staticmethod
    def render(data, exec_num):
        """Exibe o cabeçalho e o resumo da melhor solução."""
        st.header(f"Resultados da Execução: {exec_num}")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f"""
                <div style="border: 2px solid #e6e6e6; border-radius: 5px; padding: 30px; margin: 10px 0; background-color: #d5d5d5;">
                <h3 style="color: #1f77b4;">Resumo da Melhor Solução</h3>
                <h4><strong>Melhor Fitness:</strong> {data.get('best_fitness', 'N/A'):.6f}</h4>
                <h4><strong>Melhor Geração (Índice):</strong> {data.get('best_gen_idx', 'N/A')}</h4>
                </div>
                """, unsafe_allow_html=True)
        with col2:
            st.subheader("BEST DECISION VARIABLES")
            st.write(data.get('best_vars', 'N/A'))

        with st.expander("Parâmetros Utilizados nesta Execução"):
            st.json(data.get('params', {}))


class StatisticsTableComponent:
    """Componente para exibir a tabela de estatísticas por geração."""
    
    @staticmethod
    def render(data):
        """Exibe a tabela de estatísticas por geração, se disponível."""
        if 'logbook_data' in data and isinstance(data['logbook_data'], dict):
            st.subheader("Estatísticas por Geração")
            try:
                log_data = data['logbook_data']
                statics = log_data.get('statics', {})
                stats_data = {
                    "Geração": log_data.get('generation', []),
                    "Min Fitness": statics.get('min_fitness', []),
                    "Média Fitness": statics.get('avg_fitness', []),
                    "Max Fitness": statics.get('max_fitness', []),
                    "Std Dev Fitness": statics.get('std_fitness', [])
                }
                lengths = {key: len(value) for key, value in stats_data.items()}
                if len(set(lengths.values())) <= 1:
                    if lengths and list(lengths.values())[0] > 0:
                        stats_df = pd.DataFrame(stats_data)
                        st.dataframe(stats_df, use_container_width=True)
                    else:
                        st.info("Não há dados de estatísticas por geração para exibir.")
                else:
                    st.warning("Dados de estatísticas por geração têm tamanhos inconsistentes.")
                    st.json(lengths)

            except Exception as e:
                st.warning(f"Não foi possível exibir tabela de estatísticas: {e}")
                st.write("Dados do logbook encontrados:")
                st.json(data.get('logbook_data', {}))
        else:
            st.info("Dados do logbook não encontrados ou em formato inválido no arquivo .pkl.")


class ConvergenceGraphComponent:
    """Componente para exibir o gráfico de convergência."""
    
    @staticmethod
    def render(fig, exec_num):
        """Exibe o gráfico de convergência na página principal."""
        st.header(f"Gráfico de Convergência (Execução {exec_num})")
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Figura não disponível para exibição.")


class ConsolidatedResultsComponent:
    """Componente para exibir os resultados consolidados."""
    
    @staticmethod
    def render():
        """Verifica e exibe a seção de resultados consolidados."""
        # Nome base do arquivo
        consolidated_excel_filename = "results_consolidados.xlsx"
        # Caminho completo para o arquivo
        consolidated_excel_path = consolidated_excel_filename

        # Verifica a existência usando o caminho completo
        if os.path.exists(consolidated_excel_path):
            st.markdown("---")
            st.header("Resultados Consolidados Gerais de todas as execuções")
            try:
                # Lê o excel usando o caminho completo
                df_consolidado = pd.read_excel(consolidated_excel_path)
                st.dataframe(df_consolidado)
                # Abre o arquivo usando o caminho completo para o botão de download
                with open(consolidated_excel_path, "rb") as fp:
                    st.download_button(
                        label="Baixar Resultados Consolidados (Excel)",
                        data=fp,
                        # Usa o nome base do arquivo para o download
                        file_name=consolidated_excel_filename,
                        mime="application/vnd.ms-excel"
                    )
                
                st.title("Tempo de Execução")
                st.write(df_consolidado[""])
            except Exception as e:
                st.error(f"Erro ao ler o arquivo consolidado {consolidated_excel_path}: {e}")
        else:
            st.info(f"Arquivo de resultados consolidados ({consolidated_excel_path}) não encontrado.")


