# --- Componentes da Interface de Usuário ---
import pickle
import pathlib
import streamlit as st
import os
import pandas as pd
import numpy as np
import sys
import time
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from controllers.Utils import Controller, OPTIONS_JSON
#! TODO SABER PEGAR IMPORT TUDO DE CONTROLLER E UTILS

# Ajuste conforme a estrutura do projeto
def get_folder_path():
    BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent  
    # Queremos apontar para .../src/output
    # BASE_DIR está em .../src/DashboardApp/views, então parent.parent é .../src
    FOLDER_NAME = BASE_DIR.parent.parent / "output"
    return FOLDER_NAME

path_foler_output = get_folder_path()






class ConsolidatedResultsComponent:
    """Componente para exibir os resultados consolidados."""    

    @staticmethod
    def render():
        """Verifica e exibe a seção de resultados consolidados."""

        # Nome base do arquivo
        consolidated_excel_path = rf"{path_foler_output}/results_consolidados.xlsx"

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
                # Converter execution_time com robustez (aceita números, 'x segundos' ou 'y minutos')
                if "execution_time" in df_consolidado.columns:
                    def to_seconds(x):
                        if pd.isna(x):
                            return np.nan
                        if isinstance(x, (int, float)):
                            return float(x)
                        s = str(x).strip().lower()
                        # extrai número (suporta vírgula decimal)
                        num_str = re.sub(r"[^0-9\.,]", "", s).replace(",", ".")
                        try:
                            val = float(num_str) if num_str else np.nan
                        except Exception:
                            return np.nan
                        if "min" in s:  # minutos -> segundos
                            return val * 60.0
                        return val  # já está em segundos
                    df_consolidado["execution_time"] = df_consolidado["execution_time"].apply(to_seconds)

                # Calcula a média da coluna execution_time
                exec_time = df_consolidado["execution_time"]
                time_exec_media = exec_time.mean()
                tempo_total = exec_time.sum()

                 
                
                # Descobrir quantas linhas por configuração
                rep = OPTIONS_JSON['repeticoes_por_config']
                num_rows = len(df_consolidado)
                
                
                # Adicionar as colunas dos parâmetros
                for param in ['CROSSOVER', 'MUTACAO', 'POP_SIZE', 'IND_SIZE']:
                    if param not in OPTIONS_JSON:
                        continue
                    values = OPTIONS_JSON[param]
                    # Normaliza 'values' para uma lista
                    vals = values if isinstance(values, list) else [values]
                    # Repete cada valor 'rep' vezes
                    repeated = [v for v in vals for _ in range(rep)] if len(vals) > 1 or rep > 1 else vals
                    # Ajusta exatamente para o tamanho de num_rows (cicla e/ou corta)
                    if len(repeated) == 0:
                        repeated = [np.nan] * num_rows
                    elif len(repeated) < num_rows:
                        times = (num_rows // len(repeated)) + 1
                        repeated = (repeated * times)[:num_rows]
                    elif len(repeated) > num_rows:
                        repeated = repeated[:num_rows]
                    df_consolidado[param] = repeated

                #if OPTIONS_JSON:
                #    st.write(f"**Parâmetros de Execução Options.json:** {OPTIONS_JSON}")
                
                st.dataframe(df_consolidado)
                
                if time_exec_media <= 60:
                    st.write(f"Média do tempo de cada execução (em segundos) = ",round(time_exec_media,3))
                    
                    if tempo_total <= 60:
                        st.write("Tempo total de execução (em segundos) = ", round(tempo_total,2))
                    else:
                        st.write("Tempo total de execução (em minutos) = ", round(tempo_total/60,2))

                else:
                    st.write(f"Média do tempo de cada execução (em segundos) = ",round(time_exec_media,3))
                    st.write(f"Média do tempo de cada execução (em minutos) = ",round(time_exec_media/60,3))

                # Adiciona o botão de download
                button_save_excel(consolidated_excel_path, "results_consolidados.xlsx")




            except Exception as e:
                st.error(f"Erro ao ler os resultados consolidados: {e}")
        else:
            # Tentativa de construir automaticamente o arquivo consolidado a partir dos .pkl no output
            st.info(f"Arquivo de resultados consolidados ({consolidated_excel_path}) não encontrado. Tentando gerar automaticamente...")
            rows = []
            try:
                for fname in sorted(os.listdir(path_foler_output)):
                    if not (fname.startswith("dashboard_data_config") and fname.endswith(".pkl")):
                        continue
                    # Extrair config e exec do nome do arquivo
                    m = re.match(r"dashboard_data_config(\d+)_exec(\d+)\\.pkl", fname)
                    cfg = execn = None
                    if m:
                        cfg = int(m.group(1))
                        execn = int(m.group(2))
                    fpath = os.path.join(path_foler_output, fname)
                    try:
                        with open(fpath, "rb") as f:
                            data = pickle.load(f)
                        if isinstance(data, dict):
                            row = {
                                "config": cfg,
                                "execution": execn,
                                "best_fitness": data.get("best_fitness", np.nan),
                                "best_gen_idx": data.get("best_gen_idx", np.nan),
                                "best_vars": data.get("best_vars", []),
                            }
                            # tentar pegar execution_time se existir
                            et = data.get("execution_time") or data.get("tempo_execucao")
                            row["execution_time"] = et if et is not None else np.nan
                            rows.append(row)
                    except Exception as e:
                        st.warning(f"Falha ao ler {fname}: {e}")
                if rows:
                    df_built = pd.DataFrame(rows)
                    # normalizar execution_time
                    if "execution_time" in df_built.columns:
                        def to_seconds2(x):
                            if pd.isna(x): return np.nan
                            if isinstance(x, (int, float)): return float(x)
                            s = str(x).strip().lower()
                            num_str = re.sub(r"[^0-9\.,]", "", s).replace(",", ".")
                            try:
                                val = float(num_str) if num_str else np.nan
                            except Exception:
                                return np.nan
                            if "min" in s:
                                return val * 60.0
                            return val
                        df_built["execution_time"] = df_built["execution_time"].apply(to_seconds2)
                    # salvar e exibir
                    try:
                        df_built.to_excel(consolidated_excel_path, index=False)
                        st.success("Arquivo consolidado gerado com sucesso.")
                        st.dataframe(df_built)
                        button_save_excel(consolidated_excel_path, "results_consolidados.xlsx")
                    except Exception as e:
                        st.error(f"Não foi possível salvar o consolidado: {e}")
                else:
                    st.info("Nenhum arquivo de execução (.pkl) encontrado em output para gerar o consolidado.")
            except Exception as e:
                st.error(f"Erro ao gerar o arquivo consolidado automaticamente: {e}")
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

        # Corrigir/limitar melhor geração com base no logbook ou número de gerações
        try:
            max_gen_available = None
            if isinstance(data.get('logbook_data'), dict):
                gens = data['logbook_data'].get('generation')
                if isinstance(gens, (list, tuple)) and len(gens) > 0:
                    max_gen_available = max(gens)
                elif isinstance(gens, (int, float)):
                    max_gen_available = int(gens)
            if max_gen_available is None and isinstance(data.get('num_generations'), (int, float)):
                # num_generations pode ser contagem; índice máximo é num_generations-1
                num_g = int(data['num_generations'])
                max_gen_available = num_g - 1 if num_g > 0 else None

            if isinstance(best_gen_idx, (int, float)) and max_gen_available is not None:
                if best_gen_idx > max_gen_available:
                    best_gen_idx = max_gen_available
        except Exception:
            pass

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
                   
            
        st.markdown(
            f"""
            <div style="
                border: 2px solid #e6e6e6; 
                border-radius: 15px; 
                background-color: #9c9c9c;
                padding: 12px;
                display: flex;
                flex-direction: row;
                justify-content: space-between;
                align-items: flex-start;
            ">
                <div style="width: 52%; border: 1px solid #ccc; border-radius: 8px; padding: 12px;">
                    <h3 style="color: #1f2db4; text-align: left;">Resumo da Melhor Solução</h3>
                    <h4><strong>Melhor Geração:</strong> {best_gen_idx}</h4>
                    <h4><strong>Melhor Fitness:</strong> {best_fitness_str}</h4>
                </div>
                <div style="width: 46%; border: 1px solid #ccc; border-radius: 8px; padding: 8px;">
                    <h4 style="color: #1f2db4; text-align: left;">Variáveis de Decisão</h4>
                    {best_vars_table}
                </div>
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
        df_pop_final = pd.read_excel(arquivo)

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

        

