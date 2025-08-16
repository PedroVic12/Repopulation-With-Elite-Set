# --- Componentes da Interface de Usuário ---
import pickle
import pathlib
import streamlit as st
import streamlit.components.v1 as components
import os
import pandas as pd
import numpy as np
import sys
import io
import re
from datetime import datetime


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

            # Normaliza estrutura: alguns arquivos podem salvar lista em vez de dict
            if isinstance(exec_data, dict):
                data_dict = exec_data
            elif isinstance(exec_data, list):
                # tenta pegar o primeiro item se for lista de dicts
                data_dict = exec_data[0] if exec_data and isinstance(exec_data[0], dict) else {}
                if not isinstance(data_dict, dict):
                    warnings.append(f"Formato de dados inesperado em {data_file.name} (lista não suportada).")
            else:
                warnings.append(f"Formato de dados inesperado em {data_file.name}: {type(exec_data).__name__}")
                data_dict = {}

            # Usa os parâmetros já carregados pela página principal
            params_data = all_params.get(config_num, {})
            if not params_data:
                 warnings.append(f"Arquivo de parâmetros não encontrado para a Configuração {config_num}")

            # Extrair e montar os dados
            execution_time_str = str(data_dict.get("execution_time", "0"))
            cleaned_time = re.sub(r'[^\d.]', '', execution_time_str)

            all_results.append({
                "Config": config_num,
                "Exec": exec_num,
                "Melhor Fitness": data_dict.get("best_fitness"),
                "Melhor Geração": data_dict.get("best_gen_idx"),
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
    """Componente para exibir o resumo da melhor solução com suporte a dark mode."""

    @staticmethod
    def render(data, exec_num, debug=False):
        """Exibe o resumo da melhor solução com suporte a dark mode."""
        # Verifica se o tema atual é dark
        is_dark = st.get_option('theme.base') == 'dark' if hasattr(st, 'get_option') else False
        
        # Cores baseadas no tema
        bg_color = "#1e1e1e" if is_dark else "#ffffff"
        card_bg = "#2d2d2d" if is_dark else "#f8f9fa"
        text_color = "#ffffff" if is_dark else "#333333"
        border_color = "#444" if is_dark else "#e0e0e0"
        success_color = "#4caf50"
        warning_color = "#ff9800"
        
        # Estilo CSS para o card
        card_style = f"""
        <style>
            .solution-card {{
                background-color: {card_bg};
                border-radius: 10px;
                padding: 20px;
                margin: 10px 0;
                border: 1px solid {border_color};
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .metric-value {{
                font-size: 1.2em;
                font-weight: bold;
                color: {success_color};
            }}
            .metric-label {{
                font-size: 0.9em;
                color: {text_color};
                opacity: 0.8;
            }}
            .var-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
            }}
            .var-table th, .var-table td {{
                border: 1px solid {border_color};
                padding: 8px 12px;
                text-align: left;
            }}
            .var-table th {{
                background-color: {'#3a3a3a' if is_dark else '#f0f0f0'};
            }}
        </style>
        """
        
        # Título da seção
        st.markdown(f"### 📊 Resultados da Execução {exec_num}")
        
        if debug:
            with st.expander("Dados da Execução (Debug)"):
                st.json(data)

        # Obter os dados necessários
        best_gen_idx = data.get('best_gen_idx', 'N/A')
        best_fitness = data.get('best_fitness', float('nan'))
        best_vars = data.get('best_vars', [])
        
        # Formatar fitness
        import math
        if isinstance(best_fitness, (int, float)) and not math.isnan(best_fitness):
            best_fitness_str = f"{best_fitness:.2f}"
            fitness_color = success_color
        else:
            best_fitness_str = "N/A"
            fitness_color = warning_color
            
        # Criar HTML do card
        html_content = f"""
        {card_style}
        <div class="solution-card">
            <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                <div>
                    <div class="metric-label">Melhor Geração</div>
                    <div class="metric-value">{best_gen_idx}</div>
                </div>
                <div style="text-align: right;">
                    <div class="metric-label">Melhor Fitness</div>
                    <div class="metric-value" style="color: {fitness_color};">{best_fitness_str}</div>
                </div>
            </div>
        """

        # !Tabela Card Soluções de Variáveis de Decisão
        # !Tabela Card Soluções de Variáveis de Decisão (modo horizontal)
        vars_html = ""
        if isinstance(best_vars, (list, tuple)) and best_vars:
            vars_html += "<h4 style='margin-top: 20px;'>Variáveis de Decisão</h4>"
            vars_html += "<div style='overflow-x: auto;'>"
            vars_html += "<table class='var-table' style='width: 100%; border-collapse: collapse;'>"

            # Cabeçalho com VAR 1, VAR 2, ...
            vars_html += "<thead><tr>"
            for i in range(1, len(best_vars) + 1):
                vars_html += f"<th style='padding: 10px; text-align: center; border-bottom: 1px solid {border_color};'>VAR {i}</th>"
            vars_html += "</tr></thead>"

            # Linha com os valores
            vars_html += "<tbody><tr>"
            for var in best_vars:
                var_style = f"color: {success_color}; font-weight: 500;" if var != 0 else "color: #888;"
                try:
                    var_val = f"{float(var):.2f}"
                except Exception:
                    var_val = str(var)
                vars_html += f"<td style='padding: 8px 12px; text-align: center; {var_style}'>{var_val}</td>"
            vars_html += "</tr></tbody>"

            vars_html += "</table></div>"
        else:
            vars_html = "<p style='color: #888; text-align: center;'>Nenhuma variável encontrada</p>"


        # HTML para o card principal
        card_html = f"""
        <style>
            .card {{
                border-radius: 12px;
                background-color: {card_bg};
                border: 1px solid {border_color};
                padding: 16px;
                margin-bottom: 16px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                color: {text_color};
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            .card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }}
            .card-header {{
                font-size: 1.2em;
                font-weight: 600;
                margin-bottom: 16px;
                color: #4a90e2;
                border-bottom: 1px solid {border_color};
                padding-bottom: 8px;
            }}
            .metric-card {{
                background: {card_bg};
                border-radius: 10px;
                padding: 16px;
                text-align: center;
                border: 1px solid {border_color};
            }}
            .metric-label {{
                font-size: 0.9em;
                color: {text_color};
                opacity: 0.8;
                margin-bottom: 6px;
            }}
            .metric-value {{
                font-size: 1.8em;
                font-weight: 700;
                color: {success_color};
            }}
            .execution-info {{
                font-size: 0.9em;
                color: {text_color};
                opacity: 0.8;
                margin-top: 12px;
                padding-top: 12px;
                border-top: 1px dashed {border_color};
            }}
        </style>

        <div class="card">
            <div class="card-header">📊 Resumo da Melhor Solução</div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 16px;">
                
                
                
                <div class="metric-card">
                    <div class="metric-label">Melhor Geração</div>
                    <div class="metric-value" style="color: #4a90e2;">{best_gen_idx}</div>
                </div>

                <div style="margin-top: 16px;">
                    Resultados dos melhores horários de desligamento de linhas em Rede - IEEE 14
                    {vars_html}
                </div>

                <div class="metric-card">
                    <div class="metric-label">Melhor Fitness</div>
                    <div class="metric-value" style="color: {fitness_color};">{best_fitness_str}</div>
                </div>
            </div>  
            

            
            <div class="execution-info">
                Execução realizada em: {exec_num} • {datetime.now().strftime('%d/%m/%Y %H:%M')}
            </div>
        </div>
        """
        
        # Renderiza como HTML bruto para garantir que o card seja exibido corretamente
        approx_height = 320 + (len(best_vars) if isinstance(best_vars, (list, tuple)) else 0) * 28
        approx_height = max(approx_height, 380)
        components.html(card_html, height=approx_height, scrolling=True)
        
        # Adiciona um pequeno espaço entre os cards
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)



        st.markdown("---")

class GraficoPotenciaAtivaReativaComponent:
    """Componente para exibir o gráfico de potência ativa e reativa."""

    @staticmethod
    def render(exec_num, num_configs=1, config_num: int | None = None, debug=False):
        """
        Exibe o gráfico de potência ativa e reativa na página principal.
        
        Args:
            exec_num (int): Número da execução
            num_configs (int): Número total de configurações
            config_num (int, optional): Número da configuração específica
            debug (bool): Se True, mostra informações adicionais para debug
        """
        # Verifica se o tema atual é dark
        is_dark = st.get_option('theme.base') == 'dark' if hasattr(st, 'get_option') else False
        
        # Estilo CSS para o container
        container_style = """
        <style>
            .power-flow-container {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                margin: 15px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .power-flow-title {
                color: #2c3e50;
                margin-bottom: 15px;
                font-size: 1.4em;
                font-weight: 600;
            }
            @media (prefers-color-scheme: dark) {
                .power-flow-container {
                    background-color: #2d2d2d;
                    border: 1px solid #444;
                }
                .power-flow-title {
                    color: #ecf0f1;
                }
            }
        </style>
        """
        
        # Título da seção
        st.markdown(container_style, unsafe_allow_html=True)
        st.markdown(f"<div class='power-flow-title'>🔌 Fluxo de Potência - Execução {exec_num}</div>", unsafe_allow_html=True)
        
        # Caminhos possíveis para os arquivos de potência
        candidates = [
            path_foler_output / f"potencia_exec_{exec_num}.html",
            path_foler_output / f"potencia_{num_configs}_{exec_num}.html",
            path_foler_output / f"potencia_execucao_{num_configs}_{exec_num}.html",
            path_foler_output / f"potencia_caso_{exec_num}.html",
        ]
        
        # Adiciona padrões específicos se config_num for fornecido
        if config_num is not None:
            candidates[:0] = [
                path_foler_output / f"potencia_config{config_num}_exec{exec_num}.html",
                path_foler_output / f"potencia_caso_config{config_num}_exec{exec_num}.html",
                path_foler_output / f"fluxo_potencia_config{config_num}_exec{exec_num}.html",
            ]
        
        # Tenta encontrar o arquivo de potência
        html_file = next((p for p in candidates if p and p.exists()), None)
        
        # Fallback: busca por padrão genérico se não encontrar nos candidatos
        if html_file is None:
            pattern = f"*config{config_num}*exec{exec_num}*.html" if config_num is not None else f"*{exec_num}*.html"
            matches = sorted(
                path_foler_output.glob(pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            # Prioriza arquivos que contenham 'potencia' ou 'fluxo' no nome
            potencia_matches = [p for p in matches if any(termo in p.stem.lower() for termo in ['potencia', 'fluxo', 'power'])]
            html_file = potencia_matches[0] if potencia_matches else (matches[0] if matches else None)
        
        # Exibe o gráfico se o arquivo for encontrado
        if html_file and html_file.exists():
            try:
                with st.spinner(f"Carregando fluxo de potência da execução {exec_num}..."):
                    with open(html_file, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                        
                        # Adiciona estilos personalizados ao HTML se necessário
                        if '<style>' not in html_content:
                            html_content = f"""
                            <style>
                                body {{ 
                                    font-family: Arial, sans-serif;
                                    margin: 15px;
                                    background-color: transparent !important;
                                }}
                                .header {{
                                    font-size: 16px;
                                    font-weight: bold;
                                    margin-bottom: 10px;
                                    color: #2c3e50;
                                }}
                                @media (prefers-color-scheme: dark) {{
                                    body {{ 
                                        background-color: #2d2d2d !important;
                                        color: #ecf0f1 !important;
                                    }}
                                    .header {{
                                        color: #ecf0f1 !important;
                                    }}
                                }}
                            </style>
                            <div class='header'>Fluxo de Potência - Execução {exec_num}</div>
                            """ + html_content
                        
                        # Exibe o conteúdo HTML
                        st.components.v1.html(
                            html_content, 
                            height=600, 
                            scrolling=True
                        )
                        
                        # Mostra informações de debug se necessário
                        if debug:
                            with st.expander("Informações de Debug"):
                                st.write(f"Arquivo carregado: {html_file.name}")
                                st.write(f"Tamanho: {html_file.stat().st_size / 1024:.2f} KB")
                                st.write(f"Última modificação: {datetime.fromtimestamp(html_file.stat().st_mtime).strftime('%d/%m/%Y %H:%M:%S')}")
            
            except Exception as e:
                st.error(f"Erro ao carregar o gráfico de potência: {str(e)}")
                if debug:
                    st.exception("Detalhes do erro:")
        else:
            # Mensagem mais informativa quando o arquivo não é encontrado
            st.warning(
                f"""
                **Gráfico de potência não encontrado para a Execução {exec_num}**
                
                O sistema procurou nos seguintes locais:
                - {path_foler_output}/potencia_exec_{exec_num}.html
                - {path_foler_output}/potencia_*_{exec_num}.html
                - {path_foler_output}/*config{config_num}*exec{exec_num}*.html
                
                Verifique se a execução foi concluída corretamente e se os arquivos de saída foram gerados.
                Gere o HTML correspondente em src/output ou finalize a implementação desta etapa.
                """
            )
            
            # Botão para recarregar
            if st.button("🔄 Tentar novamente", key=f"reload_power_flow_{exec_num}"):
                st.rerun()

class GraficoRCEComponent:
    """Componente para exibir o gráfico de convergência."""
    
    @staticmethod
    def render(exec_num, num_configs = 1, config_num: int | None = None):
        """Exibe os gráficos de convergência na página principal."""
        st.header(f"📉 Gráfico RCE: F(x,y) = Generations x Fitness (Execução {exec_num})")
        
        # Procura arquivos em src/output com padrões conhecidos
        candidates = [
            path_foler_output / f"grafico_execucao_{num_configs}_{exec_num}.html",
            path_foler_output / f"grafico_execucao_{exec_num}.html",
            path_foler_output / f"grafico_{num_configs}_{exec_num}.html",
            path_foler_output / f"grafico_exec_{exec_num}.html",
        ]
        if config_num is not None:
            candidates[:0] = [
                path_foler_output / f"grafico_execucao_config{config_num}_exec{exec_num}.html",
                path_foler_output / f"grafico_config{config_num}_exec{exec_num}.html",
            ]
        html_file = next((p for p in candidates if p.exists()), None)
        if html_file is None:
            # fallback: qualquer html que contenha o número da execução
            pattern = f"*config{config_num}*exec{exec_num}*.html" if config_num is not None else f"*{exec_num}*.html"
            matches = sorted(
                path_foler_output.glob(pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            # prioriza arquivos que contenham 'grafico' no nome
            graf_matches = [p for p in matches if 'grafico' in p.stem.lower()]
            html_file = graf_matches[0] if graf_matches else (matches[0] if matches else None)
        
        if html_file and html_file.exists(): 
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                    st.components.v1.html(html_content, height=500, scrolling=True)
                    st.caption(f"Arquivo: {html_file.name}")
                    
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

        

