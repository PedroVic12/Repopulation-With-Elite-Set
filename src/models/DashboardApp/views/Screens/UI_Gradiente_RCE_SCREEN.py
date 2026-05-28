

# --- Componentes da Interface de Usuário ---
from functools import reduce
import json
import operator
import sys
import os




# Ajusta o path para permitir execução isolada via `streamlit run` deste arquivo
CURRENT_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '.'))

from components.dash_components import (
        CardSolutions,
    StatisticsTableComponent,
    GraficoRCEComponent,
)
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)




#backend
from controllers.Utils import Controller, FOLDER_NAME, Utils, PARAMETROS_JSON
from controllers.ConfigRepository import ConfigRepository

# Frontend
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import time
import threading
import pathlib


def load_data_excel():
    # Caminho relativo para o arquivo consolidado
    output_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "output"
    path = output_dir / "resultados_consolidados.xlsx"
    df = pd.read_excel(path)
    return df


def rede_template_view(html_path: str | None = None, height: int = 1200):
    """Renderiza o template HTML da rede IEEE dentro do Streamlit.

    Args:
        html_path: Caminho absoluto/relativo para o arquivo HTML. Se None, usa o arquivo padrão ao lado desta tela.
        height: Altura do iframe em pixels.
    """
    # Caminho padrão
    if html_path is None:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
        html_path = base_dir / "resultados - Artigo PIBIC" / "plot_rede_IEEE_template_dashboard.html"
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


# Configuração da barra lateral
class DrawerSideBar:
    """Classe para gerenciar a barra lateral do aplicativo."""

    def __init__(self):
        """Inicializa a barra lateral."""
        self.st = st

    def render(self):
        """Renderiza a barra lateral."""
        self.st.sidebar.title("Seleção da Execução com Algoritmo Evolutivo")
        if st.button("Atualizar Estado"):
            st.session_state["selected_execution"] = None
            st.rerun()
        self.st.sidebar.markdown("---")  # Separador visual
        self.filtro()
        
    def filtro(self):
        """Adiciona filtros à barra lateral."""
        self.st.sidebar.header("🔍 Filtros")
        data = load_data_excel()
        
        item_selecionado = st.sidebar.multiselect(
            "Selecione o número da execução para visualizar os dados:",
            options=data["configuracao"].unique().tolist(),
        )
        





## Controlador de Gerenciamento de Estado
class UseState:
    """Classe para gerenciar o estado do Streamlit."""

    @staticmethod
    def initialize_state(key, default_value):
        """Inicializa uma chave no session_state com um valor padrão."""
        if key not in st.session_state:
            st.session_state[key] = default_value

    @staticmethod
    def get_state(key, default_value=None):
        """Obtém o valor de uma chave no session_state."""
        return st.session_state.get(key, default_value)

    @staticmethod
    def set_state(key, value):
        """Define o valor de uma chave no session_state."""
        st.session_state[key] = value
        #print("State atualizado:", key, "=", value)  


# --- Classe Principal do Aplicativo ---
class FrameworkRCEDashboard:
    def __init__(self, options = None):
        self.controller = Controller()
        self.utils = Utils()
        # Mapa de execuções: {config_num: [exec_nums]}
        try:
            executions_map, _warnings = self.utils.find_available_executions()
        except Exception:
            executions_map = {}
        self.executions_map = executions_map
        self.menu_lateral = DrawerSideBar().render()
        
  
        # Initialize options from parameter or use default
        self.options = options 
        self.init_css()


        # Inicializa os estados necessários
        UseState.initialize_state("selected_execution", None)
        # Guarda o par selecionado (config, exec)
        UseState.initialize_state("selected_pair", None)
        UseState.initialize_state("saved_configurations", {})
        if 'user_config' not in st.session_state:
            # Usa uma cópia da configuração padrão para o estado da sessão
            st.session_state.user_config = self.options


    def handle_tab_change(self, run_config_key: str, exec_num: int):
        """Atualiza o par (run_config_key, exec_num) selecionado."""
        UseState.set_state("selected_pair", (run_config_key, exec_num))


    def init_css(self):
        st.markdown("""
        <style>
            /* Hide Streamlit elements */
            .st-emotion-cache-j7qwjs.e1c29vlm3 {
                display: none;
            }
            
            .st-emotion-cache-vz9k5h.e1c29vlm19 {
                display: none;
            }
            
            .st-emotion-cache-1s1exd7.e1c29vlm19 {
                display: none;
            }
            
            .st-emotion-cache-14lrqrc.e1c29vlm19 {
                display: none;
            }
            
            .st-emotion-cache-1tuwfdi.e1c29vlm19 {
                display: none;
            }
            
            .st-emotion-cache-1gczx66.edtmxes2 {
                display: none;
            }
            
            .st-emotion-cache-1s1exd7.edtmxes19 {
                display: none;
            }
            
            /* Custom UI Improvements */
            .main .block-container {
                padding-top: 1rem;
                padding-bottom: 1rem;
            }
            
            /* Improved buttons */
            .stButton > button {
                border-radius: 8px;
                border: none;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .stButton > button[kind="primary"] {
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                color: white;
                font-size: 1.1rem;
                padding: 0.75rem 2rem;
            }
            
            .stButton > button[kind="primary"]:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            }
            
            /* Enhanced expander */
            .streamlit-expanderHeader {
                background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
                border-radius: 8px;
                font-weight: 600;
            }
            
            /* Number input improvements */
            .stNumberInput > div > div > input {
                border-radius: 6px;
                border: 2px solid #e9ecef;
                padding: 0.5rem;
                transition: border-color 0.3s ease;
            }
            
            .stNumberInput > div > div > input:focus {
                border-color: #667eea;
                box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
            }
            
            /* Text input improvements */
            .stTextInput > div > div > input {
                border-radius: 6px;
                border: 2px solid #e9ecef;
                padding: 0.5rem;
                transition: border-color 0.3s ease;
            }
            
            .stTextInput > div > div > input:focus {
                border-color: #667eea;
                box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
            }
            
            /* Toggle improvements */
            .stToggle > div {
                background: #f8f9fa;
                border-radius: 8px;
                padding: 0.5rem;
            }
            
            /* Radio button improvements */
            .stRadio > div {
                background: #f8f9fa;
                border-radius: 8px;
                padding: 0.5rem;
            }
            
            /* Success/Warning/Error message improvements */
            .stSuccess, .stWarning, .stError {
                border-radius: 8px;
                border-left: 4px solid;
                padding: 1rem;
                margin: 0.5rem 0;
            }
            
            .stSuccess {
                border-left-color: #28a745;
                background: #d4edda;
            }
            
            .stWarning {
                border-left-color: #ffc107;
                background: #fff3cd;
            }
            
            .stError {
                border-left-color: #dc3545;
                background: #f8d7da;
            }
        </style>
    """, unsafe_allow_html=True)

    

    def run(self):
        try:
            # Define um par padrão (config, exec) se houver execuções disponíveis
            selected_pair = UseState.get_state("selected_pair")
            if selected_pair is None:
                first_pair = None
                for cfg, execs in self.executions_map.items():
                    if execs:
                        first_pair = (cfg, execs[0])
                        break
                if first_pair is not None:
                    UseState.set_state("selected_pair", first_pair)
                    selected_pair = first_pair

            # Carrega os dados do par selecionado
            if selected_pair is not None:
                cfg_num, exec_num = selected_pair
                dados = self.utils.load_execution_data(cfg_num, exec_num, debug=False)
                _saved_config = UseState.get_state("saved_configurations", {})
            else:
                dados = None


            # Cabeçalho
            self.header()

            if dados:
                # Renderiza os resultados consolidados
                # Carrega todos os parâmetros por configuração para consolidar
                repo = ConfigRepository(pathlib.Path(FOLDER_NAME))
                all_params = repo.get_all_configs()
                # df_consolidado, warnings = ConsolidatedResultsComponent.render(all_params)
                # if df_consolidado is not None:
                #     ConsolidatedResultsComponent.display_and_download(df_consolidado)
                # for w in (warnings or []):
                #     st.warning(w)
                
                
                df_consolidado = load_data_excel()
                st.subheader("📈 Resultados Consolidados de Todas as Configurações e Execuções")
                if df_consolidado is not None:
                    st.dataframe(df_consolidado, use_container_width=True)
            else:
                # Renderiza componente default para "sem execução"
                st.info("Nenhum dado encontrado ainda. Execute uma simulação para visualizar os resultados.")

            # Renderiza as abas de execução - Por um Container pelo TAB
            exec_tabs_dict = self.get_exec_tabs_dict()
            self.ContainerTabs(exec_tabs_dict)
            
            # Seção extra: exibir o dashboard HTML externo da rede IEEE
            st.markdown("---")
            st.subheader("🕸️ Rede IEEE (HTML embutido)")
            rede_template_view()  # Lê o arquivo plot_rede_IEEE_template_dashboard.html ao lado desta tela
            
        except Exception as e:
            st.error(f"Ocorreu um erro ao carregar os dados da execução: {e}")
            
            # Agrupa os dados das execuções e os lambdas dos componentes em uma função separada
    def get_exec_tabs_dict(self):
        exec_tabs_dict = {}
        # Cria uma aba para cada par (config, exec)
        for cfg_num, exec_list in self.executions_map.items():
            for exec_num in exec_list:
                label = f"Config {cfg_num} - Exec {exec_num}"
                dados_exec = self.utils.load_execution_data(cfg_num, exec_num, debug=False)
                # Normaliza estruturas salvas como lista para um dicionário compatível
                if isinstance(dados_exec, list):
                    if dados_exec and isinstance(dados_exec[0], dict):
                        dados_exec_norm = dados_exec[0]
                    else:
                        dados_exec_norm = {}
                else:
                    dados_exec_norm = dados_exec or {}

                if dados_exec_norm:
                    exec_tabs_dict[label] = {
                        "Soluções": lambda de=dados_exec_norm, en=exec_num: CardSolutions.render(de, en, debug=False),
                        "Gráfico": lambda en=exec_num: GraficoRCEComponent.render(en),
                        "Estatísticas": lambda de=dados_exec_norm: StatisticsTableComponent.render(de),
                    }
                else:
                    exec_tabs_dict[label] = {"Erro": "Não foi encontrado nenhum conjunto de dados"}
        return exec_tabs_dict

    # Função separada para renderizar o container de tabs
    def ContainerTabs(self,exec_tabs_dict):
        with st.container():
            st.subheader("🔄 Seleção da Execução (NEW)")
            main_tabs = st.tabs(list(exec_tabs_dict.keys()))
            for i, (main_tab, main_key) in enumerate(zip(main_tabs, exec_tabs_dict.keys())):
                with main_tab:
                    sub_dict = exec_tabs_dict[main_key]
                    if isinstance(sub_dict, dict):
                        sub_tabs = st.tabs(list(sub_dict.keys()))
                        for j, (sub_tab, sub_key) in enumerate(zip(sub_tabs, sub_dict.keys())):
                            with sub_tab:
                                content = sub_dict[sub_key]
                                if callable(content):
                                    try:
                                        content()
                                    except Exception as e:
                                        st.error(f"Erro ao renderizar '{sub_key}': {e}")
                                else:
                                    st.write(content)
                    else:
                        st.write(sub_dict)
                        self.footer()


    def Config_AG_Json(self):
            # Expandir para mostrar os parâmetros utilizados
            with st.expander("Parâmetros AG - RCE Utilizados em params.json", expanded=False):
                json_data_params = PARAMETROS_JSON
                
                if json_data_params:
                    
                    # Separa os campos especiais
                    array_var = json_data_params.get("ARRAY_VAR", [14,15,14,18,15])
                    limite_var = json_data_params.get("LIMITE_VAR", [0, 31])

                    # Remove os campos especiais para edição no data_editor
                    json_table = {k: v for k, v in json_data_params.items() if k not in ["ARRAY_VAR", "LIMITE_VAR"]}
                    #print("json_table", json_table)


                    #st.info("Usando Variáveis de Decisão do Problema e Limites de valores inteiros para o problema de agendamento de Redes Elétricas")

                    # Edição simples do ARRAY_VAR
                    try:
                        array_str = st.text_input(
                            "Variáveis de Decisão do Problema (digite 5 valores separados por vírgula)",
                            value=", ".join(str(x) for x in array_var),
                            help="Esses são os horários de agendamento para Rede Elétrica (ex: 14h, 15h, 14h, 18h, 15h)"
                        )
                        array_var_edit = [int(x.strip()) for x in array_str.split(",")][:5]

                        if len(array_var_edit) < 5:
                            array_var_edit += [0] * (5 - len(array_var_edit))

                        # Slider para LIMITE_VAR
                        else:
                            limite_var_value = limite_var
                            limite_var_value = st.slider(
                                "Selecione os limites dos valores da variável de decisão",
                                0, 50, (0, 31), step=1, key="limite_var_slider"
                            )
                            limite_var_edit = list(limite_var_value)

                    except Exception:
                        st.error("ARRAY_VAR inválido. Use 5 números separados por vírgula.")
                        array_var_edit = array_var



                    # Data editor para os demais parâmetros
                    def excel_table(array, colunas_excluir=None, css_inicial=False):
                        """
                        Exibe um DataFrame no estilo Excel, removendo colunas indesejadas e aplicando CSS opcional.
                        :param array: lista de tuplas ou dicionário de parâmetros
                        :param colunas_excluir: lista de nomes de colunas a serem excluídas
                        :param css_inicial: bool, se True aplica CSS customizado
                        :return: DataFrame editado pelo usuário
                        """
                        df = pd.DataFrame(list(array.items()))
                        df.columns = ["Parâmetro", "Valor"]
                        if colunas_excluir:
                            df = df[~df["Parâmetro"].isin(colunas_excluir)]
                        if css_inicial:
                            st.markdown(
                                """
                                <style>
                                .stDataFrame {background-color: #f7f7f7;}
                                </style>
                                """,
                                unsafe_allow_html=True
                            )
                        edited_df = st.data_editor(
                            df,
                            use_container_width=True,
                            num_rows="dynamic",
                            column_config={
                                "Parâmetro": st.column_config.Column(disabled=True),
                                "Valor": st.column_config.Column(disabled=False)
                            },
                            key="params_editor"
                        )
                        return edited_df

                    # Exemplo de uso:
                    colunas_nao_usar = ["CROSSOVER", "MUTACAO", "NUM_GENERATIONS", "POP_SIZE"]  # Exemplo, substitua pelos nomes das colunas que deseja excluir
                    edited_df = excel_table(json_table, colunas_excluir=colunas_nao_usar, css_inicial=True)

                    # Atualiza json_table com os valores editados
                    if not edited_df.empty:
                        for _, row in edited_df.iterrows():
                            param = row["Parâmetro"]
                            value = row["Valor"]
                            json_table[param] = value

                        # Monta o dicionário final para exportação
                        json_atualizados = dict(json_table)
                        json_atualizados["ARRAY_VAR"] = [int(x) for x in array_var_edit]
                        json_atualizados["LIMITE_VAR"] = [int(x) for x in limite_var_edit]

                        # --- TRATAMENTO DE TIPOS de dados para salvar no json---
                        float_keys = {"MUTACAO", "CROSSOVER", "PORCENTAGEM"}
                        for k, v in json_atualizados.items():
                            if k in float_keys:
                                try:
                                    json_atualizados[k] = float(v)
                                except Exception:
                                    st.error(f"Valor inválido para {k}. Deve ser um número flutuante.")
                            elif k in {"ARRAY_VAR", "LIMITE_VAR"}:
                                if isinstance(v, list):
                                    try:
                                        json_atualizados[k] = [int(x) for x in v]
                                    except Exception:
                                        st.error(f"Valor inválido em {k}. Todos os valores devem ser inteiros.")
                                else:
                                    st.error(f"{k} deve ser uma lista de inteiros.")
                            else:
                                try:
                                    json_atualizados[k] = int(v)
                                except Exception:
                                    st.error(f"Valor inválido para {k}. Deve ser um número inteiro.")

                        # Salva o arquivo atualizado automaticamente
                        current_dir = pathlib.Path(__file__).parent
                        target_path = current_dir.parent.parent.parent / "params.json"
                        try:
                            with open(target_path, "w", encoding="utf-8") as f:
                                json.dump(json_atualizados, f, indent=4, ensure_ascii=False)
                            st.success(f"Arquivo salvo automaticamente em: {target_path}")
                        except Exception as e:
                            st.error(f"Erro ao salvar arquivo: {e}")

                    # Exporta os dados atualizados para um arquivo json com um botão de download
                    # st.download_button(
                    #     label="Salvar os Parâmetros AG Atualizados",
                    #     data=json.dumps(json_atualizados, indent=4),
                    #     file_name="params.json",
                    #     mime="application/json"
                    # )

    def ConfigWebApp(self):
        # Header com estilo moderno
        st.markdown("""
        <div style="
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <h1 style="color: white; margin: 0; font-size: 2.5rem;">🛠️ Configurador do Framework RCE</h1>
            <p style="color: #f0f0f0; margin: 0.5rem 0 0 0; font-size: 1.2rem;">Configure parâmetros do Algoritmo Evolutivo</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Card container principal
        st.markdown("""
        <style>
        .config-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
            margin-bottom: 1rem;
        }
        .metric-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 8px;
            color: white;
            text-align: center;
            margin: 0.5rem 0;
        }
        .param-group {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            border: 1px solid #e9ecef;
        }
        .toggle-section {
            background: #e3f2fd;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            border-left: 3px solid #2196f3;
        }
        </style>
        """, unsafe_allow_html=True)
        
        with st.container():
            config = st.session_state.user_config

            # --- Seção de Configurações Gerais ---
            st.markdown('<div class="config-card">', unsafe_allow_html=True)
            st.markdown("### 📊 Configurações Gerais")
            
            col_exec1, col_exec2 = st.columns([2, 1])
            with col_exec1:
                config['value'] = st.number_input(
                    "🔄 Número de Execuções por Configuração",
                    min_value=1,
                    value=config.get('value', 1),
                    help="Quantas vezes cada combinação única de parâmetros será executada."
                )
            with col_exec2:
                st.markdown(f"""
                <div class="metric-container">
                    <h3 style="margin: 0;">{config.get('value', 1)}</h3>
                    <p style="margin: 0; opacity: 0.8;">Execuções</p>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # --- Seção de Parâmetros Evolutivos ---
            st.markdown('<div class="config-card">', unsafe_allow_html=True)
            st.markdown("### 🧬 Parâmetros do Algoritmo Genético")
            st.markdown("Configure os parâmetros que variarão durante a otimização")

            def render_parameter_widget(param_name, default_value_from_params):
                # --- LÓGICA ROBUSTA PARA ENCONTRAR O PARÂMETRO E SEU ÍNDICE ---
                param_dict = None
                param_index = -1
                for i, p_dict in enumerate(config.get('parametros_opcionais', [])):
                    if param_name in p_dict:
                        param_dict = p_dict
                        param_index = i
                        break

                # Corrigido: Verifica se param_dict é None antes de tentar acessar
                if param_dict is None or param_index == -1:
                    st.error(f"Parâmetro de configuração '{param_name}' não encontrado no estado da sessão ou não foi configurado.")
                    return

                current_value = param_dict[param_name]


                # --- FIM DA LÓGICA ROBUSTA ---



                # Altera os nomes dos parametros para português e adiciona toggle
                param_info = {
                    "NUM_GENERATIONS": {"label": "🔄 Configurar Número de Gerações", "icon": "🔄", "desc": "Quantas gerações o algoritmo executará"},
                    "POP_SIZE": {"label": "👥 Configurar Tamanho da População", "icon": "👥", "desc": "Número de indivíduos por geração"},
                    "MUTACAO": {"label": "🧬 Configurar Taxa de Mutação", "icon": "🧬", "desc": "Probabilidade de mutação (0-1)"},
                    "CROSSOVER": {"label": "🔀 Configurar Taxa de Crossover", "icon": "🔀", "desc": "Probabilidade de cruzamento (0-1)"}
                }
                
                param_config = param_info.get(param_name, {"label": f"Configurar {param_name}", "icon": "⚙️", "desc": ""})
                
                st.markdown('<div class="toggle-section">', unsafe_allow_html=True)
                col_toggle, col_info = st.columns([3, 1])
                
                with col_toggle:
                    toggle_active = st.toggle(param_config["label"], key=f"config_check_{param_index}")
                
                with col_info:
                    if param_config["desc"]:
                        st.markdown(f'<small style="color: #666;">{param_config["desc"]}</small>', unsafe_allow_html=True)

                if toggle_active:


                    st.markdown('<div class="param-group">', unsafe_allow_html=True)
                    
                    mode = "Variável" if isinstance(current_value, list) and len(current_value) > 1 else "Fixo"
                    choice = st.radio(
                        "📌 Modo de Configuração:", ("Fixo", "Variável"), 
                        index=1 if mode == "Variável" else 0,
                        key=f"radio_{param_index}", horizontal=True,
                        help="Fixo: um valor constante | Variável: múltiplos valores para teste"
                    )

                    if choice == "Variável":
                        st.markdown(f"**🎯 Valores para {param_config['icon']} {param_name}:**")
                        cols = st.columns(4)
                        new_values = []
                        existing_values = current_value if mode == "Variável" else [""]*4
                        
                        for j, col in enumerate(cols):
                            with col:
                                val_str = str(existing_values[j]) if j < len(existing_values) else ""
                                user_input = st.text_input(
                                    f"Valor {j+1}", val_str, 
                                    key=f"input_{param_index}_{j}",
                                    placeholder=f"V{j+1}"
                                )
                                if user_input:
                                    try:
                                        if param_name in ["NUM_GENERATIONS", "POP_SIZE"]:
                                            new_values.append(int(user_input))
                                        else:
                                            new_values.append(round(float(user_input), 1))
                                    except ValueError:
                                        st.error("⚠️ Valor inválido")
                        
                        if new_values:
                            st.success(f"✅ {len(new_values)} valores configurados")
                        else:
                            st.warning(f"⚠️ Preencha ao menos um valor para '{param_name}'")
                        
                        config['parametros_opcionais'][param_index] = {param_name: new_values or [default_value_from_params]}

                    else: # Fixo
                        default_value = current_value[0] if isinstance(current_value, list) else current_value
                        st.markdown(f"**🎯 Valor fixo para {param_config['icon']} {param_name}:**")
                        
                        if param_name in ["NUM_GENERATIONS", "POP_SIZE"]:
                            new_val = st.number_input(
                                "Valor", value=int(default_value), step=1, 
                                key=f"s_{param_index}", format="%d",
                                label_visibility="collapsed"
                            )
                        else:
                            new_val = st.number_input(
                                "Valor", value=float(default_value), step=0.1, 
                                key=f"s_{param_index}", format="%.1f",
                                label_visibility="collapsed"
                            )
                        config['parametros_opcionais'][param_index] = {param_name: [new_val]}

                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)

            # Layout em grid responsivo
            col1, col2 = st.columns(2, gap="large")
            with col1:
                st.markdown("**📊 Parâmetros de População**")
                render_parameter_widget("MUTACAO", PARAMETROS_JSON["MUTACAO"])
                render_parameter_widget("CROSSOVER", PARAMETROS_JSON["CROSSOVER"])
            with col2:
                st.markdown("**⚙️ Parâmetros de Execução**")
                render_parameter_widget("NUM_GENERATIONS", PARAMETROS_JSON["NUM_GENERATIONS"])
                render_parameter_widget("POP_SIZE", PARAMETROS_JSON["POP_SIZE"])
            
            st.markdown('</div>', unsafe_allow_html=True)

            # --- Seção de Resumo ---
            st.markdown('<div class="config-card">', unsafe_allow_html=True)
            st.markdown("### 📈 Resumo da Configuração")
            
            num_variations = [len(v) for p in config['parametros_opcionais'] for k,v in p.items() if isinstance(v, list) and len(v) > 1 and v]
            total_combinations = reduce(operator.mul, num_variations, 1) if num_variations else 1
            total_execucoes = total_combinations * config.get('value', 1)

            # Cards de métricas com visual aprimorado
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            
            with metric_col1:
                st.markdown(f"""
                <div class="metric-container">
                    <h2 style="margin: 0; font-size: 2rem;">{total_combinations}</h2>
                    <p style="margin: 0; opacity: 0.9;">Configurações Únicas</p>
                    <small style="opacity: 0.7;">Combinações de parâmetros</small>
                </div>
                """, unsafe_allow_html=True)
                
            with metric_col2:
                st.markdown(f"""
                <div class="metric-container">
                    <h2 style="margin: 0; font-size: 2rem;">{total_execucoes}</h2>
                    <p style="margin: 0; opacity: 0.9;">Total de Execuções</p>
                    <small style="opacity: 0.7;">Todas as repetições</small>
                </div>
                """, unsafe_allow_html=True)
                
            with metric_col3:
                tempo_estimado = total_execucoes * 2  # Estimativa de 2 min por execução
                st.markdown(f"""
                <div class="metric-container">
                    <h2 style="margin: 0; font-size: 2rem;">{tempo_estimado}</h2>
                    <p style="margin: 0; opacity: 0.9;">Tempo Estimado (min)</p>
                    <small style="opacity: 0.7;">Aproximadamente</small>
                </div>
                """, unsafe_allow_html=True)
            
            # Barra de progresso visual para mostrar complexidade
            complexity_level = min(total_combinations / 10, 1.0)  # Normaliza para 0-1
            st.markdown(f"""
            <div style="background: #e0e0e0; border-radius: 10px; height: 8px; margin: 1rem 0;">
                <div style="background: linear-gradient(90deg, #4CAF50, #FF9800, #F44336); width: {complexity_level*100}%; height: 8px; border-radius: 10px; transition: width 0.3s ease;"></div>
            </div>
            <p style="text-align: center; color: #666; font-size: 0.9rem;">Complexidade: {"Baixa" if complexity_level < 0.3 else "Média" if complexity_level < 0.7 else "Alta"}</p>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

            # --- Botão para Salvar ---
            st.markdown('<div class="config-card">', unsafe_allow_html=True)
            
            # Botão estilizado
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                execute_btn = st.button(
                    "🚀 Salvar Configuração e Executar", 
                    type="primary",
                    use_container_width=True,
                    help="Salva a configuração em options.json e inicia a execução do algoritmo evolutivo"
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            if execute_btn:
                try:
                    self.utils.apagar_arquivos()

                    final_config = {**PARAMETROS_JSON}
                    user_config = st.session_state.user_config

                    # Pega os dados atualizados do usuario na tela
                    optional_params_dict = {k: v for d in user_config.get('parametros_opcionais', []) for k, v in d.items()}
                    final_config.update(optional_params_dict)
                    final_config['repeticoes_por_config'] = user_config.get('value')
                    final_config.update(user_config)

                    # --- TRATAMENTO DE TIPOS ---
                    for k in ["NUM_GENERATIONS", "POP_SIZE"]:
                        if isinstance(final_config[k], list):
                            final_config[k] = [int(x) for x in final_config[k]]
                        else:
                            final_config[k] = int(final_config[k])
                    for k in ["MUTACAO", "CROSSOVER"]:
                        if isinstance(final_config[k], list):
                            final_config[k] = [float(x) for x in final_config[k]]
                        else:
                            final_config[k] = float(final_config[k])
                            
                    # remove os campos desnecessários
                    del final_config['parametros_opcionais']
                    del final_config['value']
                    # -------------------------
                    

                    with open("../options.json", "w", encoding="utf-8") as f:
                            json.dump(final_config, f, indent=4, ensure_ascii=False)
                    st.success(f"Configuração salva em **options.json**!")

                    # Executa o script principal
                    script_path = FOLDER_NAME.parent / "run_framework.py"
                    print("Configurações o Usuario escolhida", final_config)
                    self.run_script(script_path)
                    st.rerun()

                except Exception as e:
                    st.error(f"Ocorreu um erro ao salvar os options.json ou executar o script run_framework.py : {e}")

    def atualizar_pagina(self):
        """Atualiza a página."""
        print("Atualizando a página...")
        st.rerun()

    def run_script(self, script_path):
            """Executa um script Python com barra de progresso baseado no número total de execuções configuradas."""
            dialog_placeholder = st.empty()
            progress_placeholder = st.empty()

            try:
                img_gif_loading = FOLDER_NAME.parent / "assets" / "humans_evolution.gif"

                # Obtém o total de steps a partir da configuração do usuário
                config = st.session_state.user_config
                total_steps = config.get('value', 1)

                if img_gif_loading.exists():
                    with dialog_placeholder.container():
                        st.image(str(img_gif_loading), width=800)
                        st.subheader("Executando o programa principal com Algoritmo Evolutivo RCE no mesmo terminal, por favor aguarde...")

                        # Executa o script em thread separada para não travar a UI
                        def run_command():
                            command = f'python "{script_path}"'
                            self._return_code = os.system(command)

                        self._return_code = None
                        thread = threading.Thread(target=run_command)
                        thread.start()

                        while thread.is_alive():
                            arquivos_atual = set(self.utils.get_html_content_from_folder(str(FOLDER_NAME)))
                            progresso = len(arquivos_atual)
                            percent = int((progresso / total_steps) * 100) if total_steps > 0 else 0
                            percent = min(percent, 100)  # Garante que não passe de 100%

                            bar_html = f"""
                            <div style="background-color:#e0e0e0; border-radius:10px; width:100%; height:30px;">
                                <div style="background-color:#008000; width:{percent}%; height:30px; border-radius:10px;"></div>
                            </div>
                            <p style="text-align:center;">{percent}%</p>
                            """
                            progress_placeholder.markdown(bar_html, unsafe_allow_html=True)
                            time.sleep(3.0)  # Atualiza a cada 2 segundos

                        # Garante 100% ao finalizar
                        bar_html = f"""
                        <div style="background-color:#e0e0e0; border-radius:10px; width:100%; height:30px;">
                            <div style="background-color:#008000; width:100%; height:30px; border-radius:10px;"></div>
                        </div>
                        <p style="text-align:center;">100%</p>
                        """
                        progress_placeholder.markdown(bar_html, unsafe_allow_html=True)
                        time.sleep(1.0)  # Espera um segundo para mostrar 100%
                        st.success("Script executado com sucesso!")

                        thread.join()
                        return_code = self._return_code



                dialog_placeholder.empty()
                progress_placeholder.empty()

                if return_code == 0:
                    st.rerun()

            except Exception as e:
                dialog_placeholder.empty()
                st.error(f"Erro ao executar o script. Código de retorno: {locals().get('return_code', 'N/A')} e Erro: {e}")

            if not self.execution_numbers:
                st.error("Nenhum arquivo de resultado encontrado.")
                st.stop()


    def header(self):
        """Cabeçalho do aplicativo."""
        st.markdown("---")
        st.title("⚡ Framework Repopulation-With-Elite-Set RCE ⚡")
        st.subheader("Version 14.3.2 - 17/07/2025")
        st.markdown("---")

        # Adiciona CSS personalizado para estilizar o botão
        st.markdown(
            """
            <style>
            div.stButton > button {
                background-color: #008000; /* Verde */
                color: white; /* Cor do texto */
                padding: 12px 20px;
                text-align: center;
                display: inline-block;
                font-size: 25px;
                margin: 2px 2px;
                cursor: pointer;
                border-radius: 8px;
            }
            div.stButton > button:hover {
                background-color: #45a049; /* Verde mais escuro ao passar o mouse */
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Adiciona CSS personalizado para estilizar as abas
        st.markdown(
            """
            <style>
            /* Estiliza as abas */
            div.streamlit-tabs div[data-baseweb="tab"] {
                font-size: 25px; /* Aumenta o tamanho da fonte */
                padding: 10px 10px; /* Aumenta o espaçamento interno */
            }
            </style>
            """,
            unsafe_allow_html=True,
        )



    def footer(self):
        """Rodapé do aplicativo."""
        st.markdown("---")
        st.info("Desenvolvido por Pedro Victor Veras e Rainer Zanghi em um projeto PIBIC pela UFF - 2024/2025")
        st.link_button(
            url="https://github.com/PedroVic12/Repopulation-With-Elite-Set",
            label="Visite a Documentação do Projeto nesse link",
            type="primary",
            icon="📖",
        )
        st.markdown("---")



if __name__ == "__main__":
    # Configuração básica da página quando executado isoladamente
    st.set_page_config(
        page_title="RCE - Tela Isolada",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Inicializa e executa a tela
    try:
        app = FrameworkRCEDashboard(options=PARAMETROS_JSON)
        app.run()
    except Exception as e:
        st.exception(e)
