# --- Componentes da Interface de Usuário ---
import pickle
import pathlib
import streamlit as st
import os
import pandas as pd
import numpy as np

import re

def reset_path():
    import sys
    import os

    # Adiciona o diretório 'src' ao sys.path para permitir importações absolutas
    SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    if SRC_PATH not in sys.path:
        sys.path.append(SRC_PATH)

reset_path()
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
    def render(all_params):
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
    """Componente moderno para exibir o resumo da melhor solução."""

    @staticmethod
    def _get_progress_color(progress):
        """Retorna uma cor baseada no valor de progresso (0-1)."""
        if progress < 0.3:
            return "#ff4b4b"  # Vermelho
        elif progress < 0.7:
            return "#f4c430"  # Âmbar
        return "#2ecc71"  # Verde

    @staticmethod
    def create_metric_card(title, value, icon, color, progress=None):
        """Cria um cartão de métrica estilizado."""
        if progress is not None:
            progress_color = CardSolutions._get_progress_color(progress)
            progress_bar = f"""
            <div style="background: #e0e0e0; border-radius: 5px; height: 6px; margin-top: 8px;">
                <div style="background: {progress_color}; width: {progress*100}%; height: 100%; border-radius: 5px;"></div>
            </div>
            """
        else:
            progress_bar = ""
            
        return f"""
        <div style="
            background: white;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            height: 100%;
        ">
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <div style="background: {color}20; color: {color}; width: 40px; height: 40px; 
                    border-radius: 8px; display: flex; align-items: center; justify-content: center; 
                    margin-right: 12px;">
                    <span style="font-size: 20px;">{icon}</span>
                </div>
                <div>
                    <div style="font-size: 12px; color: #666; font-weight: 500;">{title}</div>
                    <div style="font-size: 18px; font-weight: 600; color: #2c3e50;">{value}</div>
                </div>
            </div>
            {progress_bar}
        </div>
        """

    @staticmethod
    def render(data, exec_num, debug=False):
        """Exibe o cabeçalho e o resumo da melhor solução com UI moderna."""
        # Configuração inicial
        st.markdown("""
        <style>
            .metric-card {
                transition: all 0.3s ease;
                margin-bottom: 16px;
                background: white;
                border-radius: 12px;
                padding: 16px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            .metric-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.1) !important;
            }
            .solution-card {
                background: white;
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 16px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                transition: all 0.3s ease;
            }
            .solution-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.1) !important;
            }
            .status-badge {
                display: inline-flex;
                align-items: center;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 0.75rem;
                font-weight: 500;
                background: #e3f2fd;
                color: #1976d2;
            }
            .status-badge::before {
                content: '';
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #1976d2;
                margin-right: 6px;
            }
            .var-value {
                font-weight: 600;
                color: #2c3e50;
            }
            .var-label {
                font-size: 0.8rem;
                color: #6c757d;
                margin-bottom: 4px;
            }
        </style>
        """, unsafe_allow_html=True)

        # Cabeçalho
        st.markdown(f"""
        <div style="margin-bottom: 24px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <h2 style="margin: 0; color: #2c3e50; font-weight: 700; font-size: 1.5rem;">
                    Execução #{exec_num}
                </h2>
                <div class="status-badge">
                    Em execução
                </div>
            </div>
            <p style="margin: 0; color: #6c757d; font-size: 0.9rem;">
                Análise detalhada dos resultados
            </p>
        </div>
        """, unsafe_allow_html=True)

        if debug:
            with st.expander("🔍 Dados brutos (debug)", expanded=False):
                st.json(data)

        # Processar dados
        best_gen_idx = data.get('best_gen_idx', 'N/A')
        best_fitness = data.get('best_fitness', float('nan'))
        best_vars = data.get('best_vars', [])
        decision_vars = data.get('decision_vars', {})
        num_generations = data.get('num_generations', 1)
        
        # Calcular métricas
        try:
            progress = (int(best_gen_idx) / num_generations) if num_generations > 0 else 0
            progress = min(progress, 1.0)  # Garante que não ultrapasse 100%
        except (TypeError, ValueError):
            progress = 0
            
        fitness_value = f"{float(best_fitness):.4f}" if isinstance(best_fitness, (int, float)) and not pd.isna(best_fitness) else "N/A"
        
        # Layout principal em duas colunas
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Métricas na coluna da esquerda
            st.markdown(CardSolutions.create_metric_card(
                "Melhor Geração", 
                best_gen_idx,
                "📊", 
                "#3498db"
            ), unsafe_allow_html=True)
            
            st.markdown(CardSolutions.create_metric_card(
                "Melhor Fitness", 
                fitness_value,
                "🏆", 
                "#2ecc71"
            ), unsafe_allow_html=True)
            
            # Adicionar tempo de execução
            execution_time = data.get('execution_time', 0)
            if isinstance(execution_time, (int, float)) and execution_time > 0:
                if execution_time > 60:
                    exec_time_str = f"{execution_time/60:.1f} min"
                else:
                    exec_time_str = f"{execution_time:.1f} s"
            else:
                exec_time_str = "N/A"
                
            st.markdown(CardSolutions.create_metric_card(
                "Tempo de Execução", 
                exec_time_str,
                "⏱️", 
                "#e67e22"
            ), unsafe_allow_html=True)
        
        with col2:
            # Seção de variáveis de decisão
            st.markdown("""
            <div style="margin-bottom: 16px; padding: 16px; background: white; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <h3 style="margin: 0 0 16px 0; color: #2c3e50; font-size: 1.1rem; font-weight: 600;">
                    Variáveis de Decisão
                </h3>
            """, unsafe_allow_html=True)
            
            if decision_vars and len(decision_vars) > 0:
                # Criar cards para as variáveis de decisão
                num_cols = 3
                var_items = list(decision_vars.items())
                
                # Criar linhas de 3 colunas cada
                for i in range(0, len(var_items), num_cols):
                    cols = st.columns(num_cols)
                    for j in range(num_cols):
                        idx = i + j
                        if idx < len(var_items):
                            var_name, var_value = var_items[idx]
                            with cols[j]:
                                st.markdown(f"""
                                <div class="solution-card">
                                    <div class="var-label">{var_name.replace('_', ' ').title()}</div>
                                    <div class="var-value">{var_value:.4f if isinstance(var_value, (int, float)) else var_value}</div>
                                </div>
                                """, unsafe_allow_html=True)
            elif isinstance(best_vars, (list, tuple)) and len(best_vars) > 0:
                # Fallback para best_vars se decision_vars não estiver disponível
                for i in range(0, len(best_vars), 3):
                    cols = st.columns(3)
                    for j in range(3):
                        idx = i + j
                        if idx < len(best_vars):
                            var = best_vars[idx]
                            with cols[j]:
                                st.markdown(f"""
                                <div class="solution-card">
                                    <div class="var-label">VAR {idx+1}</div>
                                    <div class="var-value">{var:.4f if isinstance(var, (int, float)) else var}</div>
                                </div>
                                """, unsafe_allow_html=True)
            else:
                st.info("Nenhuma variável de decisão disponível.")
            
            st.markdown("</div>", unsafe_allow_html=True)  # Fechar div da seção



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

        

