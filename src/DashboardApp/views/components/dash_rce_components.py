# --- Componentes da Interface de Usuário ---

import pathlib
import streamlit as st
import os
import pandas as pd

#! TODO SABER PEGAR IMPORT TUDO DE CONTROLLER E UTILS

# Ajuste conforme a estrutura do projeto
def get_folder_path():
    BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent  
    # Define o caminho relativo para a pasta "output" dentro do projeto
    FOLDER_NAME = BASE_DIR.parent.parent / "src" / "output"
    return FOLDER_NAME

path_foler_output = get_folder_path()


        


class ConsolidatedResultsComponent:
    """Componente para exibir os resultados consolidados."""    

    @staticmethod
    def render():
        """Verifica e exibe a seção de resultados consolidados."""

        # Nome base do arquivo
        consolidated_excel_filename = rf"{path_foler_output}/results_consolidados.xlsx"
        
        # Caminho completo para o arquivo
        consolidated_excel_path = consolidated_excel_filename

        def button_save_excel(arquivo, nome_arquivo):
            # Abre o arquivo usando o caminho completo para o botão de download
            with open(arquivo, "rb") as fp:
                        st.download_button(
                            label="Baixar Resultados Consolidados (Excel)",
                            data=fp,
                            # Usa o nome base do arquivo para o download
                            file_name=nome_arquivo,
                            mime="application/vnd.ms-excel"
                        )

        # Verifica a existência usando o caminho completo
        if os.path.exists(consolidated_excel_path):
            st.header("✅ Resultados Consolidados Gerais de todas as execuções")
            try:
                # Lê o excel usando o caminho completo
                df_consolidado = pd.read_excel(consolidated_excel_path)
                df_consolidado["execution_time"] = df_consolidado["execution_time"].str.replace(" segundos", "").astype(float)

                # Calcula a média da coluna execution_time
                exec_time = df_consolidado["execution_time"]
                time_exec_media = exec_time.mean()
                tempo_total = exec_time.sum()
                
                st.dataframe(df_consolidado)
                st.write(f"Média do tempo de Execução (em segundos) = ",round(time_exec_media,3))
                st.write("Tempo total de execução (em segundos) = ", round(tempo_total,2))

                # Adiciona o botão de download
                button_save_excel(consolidated_excel_path, "results_consolidados.xlsx")


    
                

            except Exception as e:
                st.error(f"Erro ao ler o arquivo consolidado {consolidated_excel_path}: {e}")
        else:
            st.info(f"Arquivo de resultados consolidados ({consolidated_excel_path}) não encontrado.")
        st.markdown("---")


class CardSolutions:
    """Componente para exibir o resumo da melhor solução."""

    @staticmethod
    def render(data, exec_num, debug=False):
        """Exibe o cabeçalho e o resumo da melhor solução."""
        st.subheader(f"Resultados da Execução: {exec_num}")

        if debug:
            st.write(data)

        # Obter os dados necessários
        best_gen_idx = data.get('best_gen_idx', 'N/A')
        best_fitness = data.get('best_fitness', float('nan'))
        best_vars = data.get('best_vars', [])

        # Criar tabela de variáveis de decisão
        if isinstance(best_vars, (list, tuple)) and len(best_vars) > 0:
            best_vars_table = pd.DataFrame(
                {"Valor": best_vars},
                index=[f"VAR {i+1}" for i in range(len(best_vars))]
            ).to_html(classes='dataframe', border=1, justify='center', index_names=True, index=True)
        else:
            best_vars_table = "<p>Nenhuma variável encontrada.</p>"

        # Criar layout com duas colunas
        col1, col2 = st.columns(2)

        # Card 1: Resumo da Melhor Solução
        with col1:
            # Safely format best_fitness
            import math
            if isinstance(best_fitness, (int, float)) and not math.isnan(best_fitness):
                best_fitness_str = f"{best_fitness:.6f}"
            else:
                best_fitness_str = str(best_fitness)
            st.markdown(
                f"""
                <div style="
                    border: 2px solid #e6e6e6; 
                    border-radius: 15px; 
                    padding:40px;
                    background-color: #c4c4c4;
                    height: 400px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                ">
                    <hr style="border: 2px solid blue; width: 80%;">
                    <h2 style="color: #1f2db4; text-align: center;">Resumo da Melhor Solução</h2>
                    <hr style="border: 2px solid blue; width: 80%;">
                    <h2><strong>Melhor Geração:</strong> {best_gen_idx}</h2>
                    <h2><strong>Melhor Fitness:</strong> {best_fitness_str}</h2>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Card 2: Melhores Variáveis de Decisão
        with col2:
            st.markdown(
                f"""
                <div style="
                    border: 2px solid #e6e6e6; 
                    border-radius: 15px; 
                    padding: 20px; 
                    background-color: #c4c4c4;
                    margin-bottom: 20px;
                    height: 100%;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                ">                    
                    <hr style="border: 2px solid blue; width: 80%;">
                    <h2 style="color: #1f2db4; text-align: center;">Melhores Variáveis de Decisão</h2>
                    <hr style="border: 2px solid blue; width: 80%;">
                    {best_vars_table}
                </div>
                """,
                unsafe_allow_html=True
            )

        # Expandir para mostrar os parâmetros utilizados
        with st.expander("Parâmetros Utilizados nesta Execução", expanded=False):
            st.json(data.get('params', {}))

        st.markdown("---")


class GraficoRCEComponent:
    """Componente para exibir o gráfico de convergência."""
    
    @staticmethod
    def render(exec_num):
        """Exibe os gráficos de convergência na página principal."""
        st.header(f"📉 Gráfico RCE - Generations x Fitness (Execução {exec_num})")
        
        # Caminho do arquivo HTML
        html_file = path_foler_output / f"grafico_execucao_{exec_num}.html"
        
        if html_file.exists():
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                    st.components.v1.html(html_content, height=500, scrolling=True)
                    
                # st.link_button(
                #                     label="Baixar Gráfico",
                #                     url=html_file,
                #                     help="Baixar o gráfico gerado para a execução atual.",
                #                     icon="📥",)      


            except Exception as error:
                st.warning("Erro ao renderizar o grafico", error)
        else:
            st.warning(f"Arquivo HTML não encontrado para a execução {exec_num}.")

        # Adiciona o botão de download
            
        
class StatisticsTableComponent:
    """Componente para exibir a tabela de estatísticas por geração."""

    def button_save_excel(arquivo, nome_arquivo):
            # Abre o arquivo usando o caminho completo para o botão de download
            with open(arquivo, "rb") as fp:
                        st.download_button(
                            label="Baixar Resultados Consolidados (Excel)",
                            data=fp,
                            # Usa o nome base do arquivo para o download
                            file_name=nome_arquivo,
                            mime="application/vnd.ms-excel"
                        )
    
    @staticmethod
    def render(data):
        """Exibe a tabela de estatísticas por geração, se disponível."""

        st.markdown("---")

        def get_logbook_deap_info():
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
                            #button_save_excel(f"{path_foler_output}/statics_by_generation.xlsx", "statics_by_generation.xlsx")
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

        get_logbook_deap_info()

        # Renderizar Tabela de população final com formato Tabela x Grafico
        #! TODO alterar para gerar arquivo pop_final.xlsx sempre
        #print("\n\nDEBUG ARQUIVO POP FINAL",excel_file)
        arquivo = f"{path_foler_output}/pop_final.xlsx"
        df_pop_final = pd.read_excel(arquivo)

        if df_pop_final is not None:
            st.markdown("---")
            st.subheader("Tabela de População Final")
            df_pop_final = df_pop_final.drop(columns=["Unnamed: 0", "index", "Generations"], errors='ignore')
            st.dataframe(df_pop_final, use_container_width=True)


            # Abre o arquivo usando o caminho completo para o botão de download
            
            
        else:
            st.warning("Tabela de população final não encontrada.")

        

