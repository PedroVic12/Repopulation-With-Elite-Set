# --- Componentes da Interface de Usuário ---
import pickle
import pathlib
import streamlit as st
import os
import pandas as pd
import numpy as np
import sys
import time
import io
import json
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from DashboardApp.controllers.Utils import Controller, OPTIONS_JSON
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
    def render(all_params: dict):
        """Coleta, consolida e exibe os resultados de todas as execuções."""
        st.header("✅ Resultados Consolidados Gerais")

        output_path = get_folder_path()
        all_results = []
        warnings = []

        # 1. Encontrar todos os arquivos de dados .pkl
        data_files = sorted(output_path.glob("dashboard_data_config*_exec*.pkl"))

        if not data_files:
            st.info("Nenhum arquivo de resultado de execução (.pkl) foi encontrado.")
            return None, []

        # 2. Iterar sobre cada arquivo de resultado
        for data_file in data_files:
            match = re.search(r"config(\d+)_exec(\d+)", data_file.stem)
            if not match:
                warnings.append(f"Nome de arquivo inválido, não foi possível processar: {data_file.name}")
                continue

            config_num = int(match.group(1))
            exec_num = int(match.group(2))

            # Carregar dados da execução
            try:
                with open(data_file, "rb") as f:
                    exec_data = pickle.load(f)
            except Exception as e:
                warnings.append(f"Erro ao ler o arquivo de dados {data_file.name}: {e}")
                continue

            # Usa os parâmetros já carregados pela página principal
            params_data = all_params.get(config_num, {})
            if not params_data:
                 warnings.append(f"Arquivo de parâmetros não encontrado para a Configuração {config_num}")

            # Extrair e montar os dados
            execution_time_str = str(exec_data.get("execution_time", "0"))
            cleaned_time = re.sub(r'[^\d.]', '', execution_time_str)

            all_results.append({
                "Config": config_num,
                "Exec": exec_num,
                "Melhor Fitness": exec_data.get("best_fitness"),
                "Melhor Geração": exec_data.get("best_gen_idx"),
                "Tempo de Execução (s)": float(cleaned_time) if cleaned_time else 0.0,
                "Caso IEEE": params_data.get("ieee_case", "N/A"),
                "MUTACAO": params_data.get("MUTACAO"),
                "CROSSOVER": params_data.get("CROSSOVER"),
                "NUM_GENERATIONS": params_data.get("NUM_GENERATIONS"),
                "POP_SIZE": params_data.get("POP_SIZE"),
            })

        if not all_results:
            st.warning("Nenhum dado de execução pôde ser consolidado.")
            return

        # 3. Criar e ordenar o DataFrame
        df_consolidado = pd.DataFrame(all_results)
        
        # Devolve o DataFrame e os avisos para a página principal renderizar
        return df_consolidado, warnings

    @staticmethod
    def display_and_download(df_consolidado):
        """Exibe o DataFrame e o botão de download."""
        
        # Define e aplica a ordem correta das colunas
        column_order = [
            "Config", "Exec", "MUTACAO", "CROSSOVER", 
            "NUM_GENERATIONS", "POP_SIZE", "Melhor Fitness", "Melhor Geração", 
            "Tempo de Execução (s)"
        ]
        existing_columns = [col for col in column_order if col in df_consolidado.columns]
        df_display = df_consolidado[existing_columns]
        
        st.dataframe(df_display)

        # 4. Calcular e exibir métricas
        if "Tempo de Execução (s)" in df_display.columns:
            total_time = df_display["Tempo de Execução (s)"].sum()
            mean_time = df_display["Tempo de Execução (s)"].mean()
            
            col1, col2 = st.columns(2)
            col1.metric("Tempo Total de Execução", f"{total_time:.2f} s")
            col2.metric("Tempo Médio por Execução", f"{mean_time:.2f} s")

        # 5. Botão de download para XLSX
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_display.to_excel(writer, index=False, sheet_name='Resultados Consolidados')
        
        st.download_button(
            label="📥 Baixar Resultados Consolidados (XLSX)",
            data=output.getvalue(),
            file_name="resultados_consolidados_geral.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.markdown("---")


class CardSolutions:
    """Componente para exibir o resumo da melhor solução."""

    @staticmethod
    def render(data, exec_num, debug=False):
        """Exibe o cabeçalho e o resumo da melhor solução."""
        st.subheader(f"Resultados da Execução: {exec_num}")
        #st.warning("Resultados da melhor geração da solução encontrada esta acumulando ao longo das execuções. Para ver os resultados de cada execução, acesse a a planilha em 'outpout/resultados_consolidados.xlsx'.")

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
            ).T.to_html(classes='dataframe', border=2, justify='center', index_names=True, index=True)
        else:
            best_vars_table = "<p>Nenhuma variável encontrada.</p>"

      

        # Safely format best_fitness
        import math
        if isinstance(best_fitness, (int, float)) and not math.isnan(best_fitness):
            best_fitness_str = f"{best_fitness:.2f}"
        else:
            best_fitness_str = str(best_fitness)
            
            
                            # Monta uma tabela HTML com as informações em uma única linha
        card_html_table = f"""
            <div style="
            border: 2px solid #e6e6e6; 
            border-radius: 15px; 
            background-color: #9c9c9c;
            padding: 16px;
            margin-bottom: 10px;
            display: flex;
            flex-direction: column;
            align-items: center;
            ">
            <h3 style="color: #1f2db4; text-align: center;">Resumo da Melhor Solução</h3>
            <table style="width: 100%; border-collapse: collapse; background: #f7f7f7;">
                <tr>
                <th style="padding: 8px; border: 1px solid #ccc;">Melhor Geração</th>
                <th style="padding: 8px; border: 1px solid #ccc;">Melhor Fitness</th>
                <th style="padding: 8px; border: 1px solid #ccc;">Variáveis de Decisão</th>
                </tr>
                <tr>
                <td style="padding: 8px; border: 1px solid #ccc; text-align: center;">{best_gen_idx}</td>
                <td style="padding: 8px; border: 1px solid #ccc; text-align: center;">{best_fitness_str}</td>
                <td style="padding: 8px; border: 1px solid #ccc;">{best_vars_table}</td>
                </tr>
            </table>
            </div>
            """
    
            
            
            
        st.markdown(
            f"""
            <div style="
                border: 2px solid #e6e6e6; 
                border-radius: 15px; 
                background-color: #9c9c9c;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
            ">
                <h3 style="color: #1f2db4; text-align: center;">Resumo da Melhor Solução</h2>
                <h4><strong>Melhor Geração:</strong> {best_gen_idx}</h2>
                <h4><strong>Melhor Fitness:</strong> {best_fitness_str}</h2>
                <h3 style="color: #1f2db4; text-align: center;">Melhores Variáveis de Decisão</h2>
                {best_vars_table}
            </div>
            """,
            unsafe_allow_html=True
        )



        st.markdown("---")

class GraficoPotenciaAtivaReativaComponent:
    """Componente para exibir o gráfico de potência ativa e reativa."""

    @staticmethod
    def render(exec_num, num_configs = 1):
        """Exibe o gráfico de potência ativa e reativa na página principal."""
        st.header(f"📊 Gráfico Potência Ativa e Reativa (Execução {exec_num})")
        
        #! Debug aqui Caminho do arquivo HTML
        html_file = path_foler_output / f"potencia_caso_.html"
        
        if html_file.exists(): 
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                    st.components.v1.html(html_content, height=500, scrolling=True)
                    
            except Exception as error:
                st.warning("Erro ao renderizar o grafico", error)
        else:
            st.warning(f"Arquivo HTML não encontrado para a execução {exec_num}.")

class GraficoRCEComponent:
    """Componente para exibir o gráfico de convergência."""
    
    @staticmethod
    def render(exec_num, num_configs = 1):
        """Exibe os gráficos de convergência na página principal."""
        st.header(f"📉 Gráfico RCE: F(x,y) = Generations x Fitness (Execução {exec_num})")
        
        #! Debug aqui Caminho do arquivo HTML
        html_file = path_foler_output / f"grafico_execucao_{num_configs}_{exec_num}.html"
        
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
def TabExamplePage():
    st.write("Tabs allow organizing content within a single page.")

    tab1, tab2, tab3 = st.tabs(["📈 Grafico Barras, Linhas e Trafos", "Potencia e Energia armazenada", "Analise de dados"])

    with tab1:
        st.subheader("A Cool Chart")
        st.line_chart(pd.DataFrame(np.random.randn(20, 3), columns=['a', 'b', 'c']))
        st.write("This tab shows a line chart with random data.")

    with tab2:
        st.subheader("Some Data")
        df = pd.DataFrame({
            'col1': [1, 2, 3, 4],
            'col2': [10, 20, 15, 25],
            'col3': ['A', 'B', 'A', 'C']
        })
        st.dataframe(df, use_container_width=True)
        st.write("This tab displays a sample DataFrame.")

    with tab3:
        st.write("Texto explicativo")
        
class StatisticsTableComponent:
    """Componente para exibir a tabela de estatísticas por geração."""

    
    @staticmethod
    def render(data):
        """Exibe a tabela de estatísticas por geração, se disponível."""


        def get_logbook_deap_info():
            st.markdown("---")

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

        #get_logbook_deap_info()

        # Renderizar Tabela de população final com formato Tabela x Grafico
        #! TODO alterar para gerar arquivo pop_final.xlsx sempre
        #print("\n\nDEBUG ARQUIVO POP FINAL",excel_file)
        arquivo = rf"{path_foler_output}/pop_final.xlsx"
        if os.path.exists(arquivo):
            df_pop_final = pd.read_excel(arquivo)
        else:
            df_pop_final = None

        if df_pop_final is not None:
            st.markdown("---")
            st.subheader("Tabela de População Final")
            df_pop_final = df_pop_final.drop(columns=["Unnamed: 0", "index", "Generations"], errors='ignore')
            st.dataframe(df_pop_final, use_container_width=True)

            df_pop_final["Parentesco"] = df_pop_final["Diversidade"].apply(

                lambda x: "Baixo" if x > 0 and x < 50 else "Médio" if x < 70 else "Alto"
            )

            # Abre o arquivo usando o caminho completo para o botão de download
            
            
        else:
            st.warning("Tabela de população final não encontrada.")

        

