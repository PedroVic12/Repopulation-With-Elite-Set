

# --- Componentes da Interface de Usuário ---
from functools import reduce
import json
import operator
from ..components.dash_rce_components import ConsolidatedResultsComponent, CardSolutions, StatisticsTableComponent, GraficoRCEComponent


#backend
from controllers.Utils import Controller,FOLDER_NAME, Utils, PARAMETROS_JSON
import os

# Frontend
import streamlit as st
import pandas as pd
import json
import time
import threading
import pathlib



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
        self.execution_numbers = self.controller.execution_numbers
        self.menu_lateral = DrawerSideBar()
  
        # Initialize options from parameter or use default
        self.options = options 
        self.init_css()


        # Inicializa os estados necessários
        UseState.initialize_state("selected_execution", None)
        UseState.initialize_state("active_tab", 0)
        UseState.initialize_state("saved_configurations", {})
        if 'user_config' not in st.session_state:
            # Usa uma cópia da configuração padrão para o estado da sessão
            st.session_state.user_config = self.options


    def handle_tab_change(self, tab_index: int, execution_number: int):
        """Gerencia mudanças de aba e atualiza o estado."""
        UseState.set_state("active_tab", tab_index)
        UseState.set_state("selected_execution", execution_number)


    def init_css(self):
        st.markdown("""
        <style>
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
            
            .st-emotion-cache-1gczx66.edtmxes2 {
                display: none;
            }
            .st-emotion-cache-1s1exd7.edtmxes19 {
                display: none;
            }

            .st-emotion-cache-1s1exd7.edtmxes19 {
                display: none;
            }
            
            .st-emotion-cache-1gczx66.edtmxes2 {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)

    

    def run(self):
        try:
            # Carrega os dados da execução ativa
            active_tab = UseState.get_state("active_tab")
            if active_tab is not None:
                dados = self.utils.load_execution_data(active_tab + 1, debug=False)
                saved_config = UseState.get_state("saved_configurations", {})

            else:
                dados = None
                    
            # Sempre renderiza a configuração do app e do AG 
            self.ConfigWebApp()
            # Optiins e params em json separados mas talves ter as configuracoes em array de dicts
            self.Config_AG_Json()

            # Cabeçalho
            self.header()

            if dados:
                # Renderiza os resultados consolidados
                ConsolidatedResultsComponent.render()
            else:
                # Renderiza componente default para "sem execução"
                st.info("Nenhum dado encontrado ainda. Execute uma simulação para visualizar os resultados.")

            # Renderiza as abas de execução - Por um Container pelo TAB
            exec_tabs_dict = self.get_exec_tabs_dict()
            self.ContainerTabs(exec_tabs_dict)
            
        except Exception as e:
            st.error(f"Ocorreu um erro ao carregar os dados da execução: {e}")
            
            # Agrupa os dados das execuções e os lambdas dos componentes em uma função separada
    def get_exec_tabs_dict(self):
        exec_tabs_dict = {}
        for exec_num in self.execution_numbers:
            dados_exec = self.utils.load_execution_data(exec_num, debug=False)
            if dados_exec:
                exec_tabs_dict[f"Execução {exec_num}"] = {
                    "Soluções": lambda de=dados_exec, en=exec_num: CardSolutions.render(de, en, debug=False),
                    "Gráfico": lambda en=exec_num: GraficoRCEComponent.render(en),
                    "Estatísticas": lambda de=dados_exec: StatisticsTableComponent.render(de)
                }
            else:
                exec_tabs_dict[f"Execução {exec_num}"] = {"Erro": "Não foi encontrado nenhum conjunto de dados"}
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
        # CSS customizado para melhorar a aparência
        st.markdown("""
        <style>
        .config-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin: 1rem 0;
        }
        .param-card {
            background: rgba(255,255,255,0.95);
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin: 1rem 0;
            border-left: 4px solid #4CAF50;
        }
        .metric-card {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            color: white;
            box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
        }
        .section-header {
            color: #2E3B4E;
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 1rem;
            text-align: center;
            background: linear-gradient(45deg, #4CAF50, #2196F3);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .toggle-container {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            border: 2px solid #e9ecef;
            margin: 0.5rem 0;
        }
        .stButton > button {
            background: linear-gradient(45deg, #4CAF50, #45a049) !important;
            color: white !important;
            border: none !important;
            padding: 0.75rem 2rem !important;
            border-radius: 25px !important;
            font-weight: 600 !important;
            font-size: 1.1rem !important;
            box-shadow: 0 4px 15px rgba(76, 175, 80, 0.4) !important;
            transition: all 0.3s ease !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(76, 175, 80, 0.6) !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # Cabeçalho principal com design aprimorado
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="background: linear-gradient(45deg, #667eea, #764ba2); 
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                       font-size: 3rem; font-weight: 800; margin-bottom: 0.5rem;">
                🛠️ Configurador do Framework
            </h1>
            <p style="color: #6c757d; font-size: 1.2rem; margin-top: 0;">
                Configure os parâmetros do Algoritmo Evolutivo RCE de forma intuitiva
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("⚙️ Configuração de Execução em options.json", expanded=False):
            config = st.session_state.user_config

            # --- Seção de Configurações Gerais ---
            st.markdown('<div class="section-header">📊 Configurações Gerais</div>', unsafe_allow_html=True)
            
            with st.container():
                st.markdown('<div class="param-card">', unsafe_allow_html=True)
                
                col_input, col_info = st.columns([2, 1])
                with col_input:
                    config['value'] = st.number_input(
                        "🔄 Número de Execuções por Configuração",
                        min_value=1,
                        max_value=100,
                        value=config.get('value', 1),
                        help="Quantas vezes cada combinação única de parâmetros será executada."
                    )
                
                with col_info:
                    st.info("💡 Mais execuções = resultados mais confiáveis")
                
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("---")

            # --- Seção de Parâmetros Evolutivos ---
            st.markdown('<div class="section-header">🧬 Parâmetros do Algoritmo Genético</div>', unsafe_allow_html=True)

            def render_parameter_widget(param_name, default_value_from_params, icon, description):
                # --- LÓGICA ROBUSTA PARA ENCONTRAR O PARÂMETRO E SEU ÍNDICE ---
                param_dict = None
                param_index = -1
                for i, p_dict in enumerate(config.get('parametros_opcionais', [])):
                    if param_name in p_dict:
                        param_dict = p_dict
                        param_index = i
                        break

                if param_dict is None or param_index == -1:
                    st.error(f"⚠️ Parâmetro '{param_name}' não encontrado na configuração.")
                    return

                current_value = param_dict[param_name]

                # Container do parâmetro com design melhorado
                st.markdown('<div class="param-card">', unsafe_allow_html=True)
                
                # Altera os nomes dos parametros para português e adiciona toggle
                toggle_labels = {
                    "NUM_GENERATIONS": f"{icon} Configurar Número de Gerações",
                    "POP_SIZE": f"{icon} Configurar Tamanho da População",
                    "MUTACAO": f"{icon} Configurar Taxa de Mutação",
                    "CROSSOVER": f"{icon} Configurar Taxa de Crossover"
                }
                
                toggle_label = toggle_labels.get(param_name, f"{icon} Configurar {param_name}")
                
                st.markdown(f"**{toggle_label}**")
                st.caption(description)
                
                st.markdown('<div class="toggle-container">', unsafe_allow_html=True)
                
                toggle_state = st.toggle(
                    f"Ativar configuração personalizada",
                    key=f"config_check_{param_index}",
                    help=f"Ative para personalizar os valores de {param_name}"
                )
                
                if toggle_state:
                    mode = "Variável" if isinstance(current_value, list) and len(current_value) > 1 else "Fixo"
                    
                    choice = st.radio(
                        "🎛️ Modo de Configuração:",
                        ("🔒 Fixo", "📊 Variável"),
                        index=1 if mode == "Variável" else 0,
                        key=f"radio_{param_index}",
                        horizontal=True,
                        help="Fixo: um valor único | Variável: múltiplos valores para teste"
                    )

                    if choice == "📊 Variável":
                        st.markdown(f"**Valores para {param_name}:**")
                        cols = st.columns(4)
                        new_values = []
                        existing_values = current_value if mode == "Variável" else [""]*4
                        
                        for j, col in enumerate(cols):
                            with col:
                                val_str = str(existing_values[j]) if j < len(existing_values) else ""
                                user_input = st.text_input(
                                    f"Valor {j+1}",
                                    val_str,
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
                                        st.error("⚠️ Valor inválido", icon="❌")
                        
                        if not new_values:
                            st.warning(f"⚠️ Preencha ao menos um valor para '{param_name}'.")
                        
                        config['parametros_opcionais'][param_index] = {param_name: new_values or [default_value_from_params]}

                    else:  # Fixo
                        default_value = current_value[0] if isinstance(current_value, list) else current_value
                        if param_name in ["NUM_GENERATIONS", "POP_SIZE"]:
                            new_val = st.number_input(
                                f"Valor para {param_name}",
                                value=int(default_value),
                                step=1,
                                key=f"s_{param_index}",
                                format="%d",
                                min_value=1
                            )
                        else:
                            new_val = st.number_input(
                                f"Valor para {param_name}",
                                value=float(default_value),
                                step=0.1,
                                key=f"s_{param_index}",
                                format="%.1f",
                                min_value=0.0,
                                max_value=1.0
                            )
                        config['parametros_opcionais'][param_index] = {param_name: [new_val]}

                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # Renderiza os parâmetros em layout de duas colunas
            col1, col2 = st.columns(2)
            
            with col1:
                render_parameter_widget(
                    "MUTACAO",
                    PARAMETROS_JSON["MUTACAO"],
                    "🧬",
                    "Taxa de mutação: probabilidade de alteração dos genes"
                )
                render_parameter_widget(
                    "CROSSOVER",
                    PARAMETROS_JSON["CROSSOVER"],
                    "🔄",
                    "Taxa de crossover: probabilidade de reprodução entre indivíduos"
                )
            
            with col2:
                render_parameter_widget(
                    "NUM_GENERATIONS",
                    PARAMETROS_JSON["NUM_GENERATIONS"],
                    "⏳",
                    "Número de gerações: quantas iterações o algoritmo executará"
                )
                render_parameter_widget(
                    "POP_SIZE",
                    PARAMETROS_JSON["POP_SIZE"],
                    "👥",
                    "Tamanho da população: número de indivíduos por geração"
                )

            # --- Seção de Resumo com Cards Melhorados ---
            st.markdown("---")
            st.markdown('<div class="section-header">📈 Resumo da Configuração</div>', unsafe_allow_html=True)
            
            num_variations = [len(v) for p in config['parametros_opcionais'] for k,v in p.items() if isinstance(v, list) and len(v) > 1 and v]
            total_combinations = reduce(operator.mul, num_variations, 1) if num_variations else 1
            total_execucoes = total_combinations * config.get('value', 1)

            metric_col1, metric_col2, metric_col3 = st.columns(3)
            
            with metric_col1:
                st.markdown("""
                <div class="metric-card">
                    <h3 style="margin: 0; font-size: 2rem;">⚙️</h3>
                    <h2 style="margin: 0.5rem 0;">{}</h2>
                    <p style="margin: 0; opacity: 0.9;">Configurações Únicas</p>
                </div>
                """.format(total_combinations), unsafe_allow_html=True)
            
            with metric_col2:
                st.markdown("""
                <div class="metric-card">
                    <h3 style="margin: 0; font-size: 2rem;">🚀</h3>
                    <h2 style="margin: 0.5rem 0;">{}</h2>
                    <p style="margin: 0; opacity: 0.9;">Total de Execuções</p>
                </div>
                """.format(total_execucoes), unsafe_allow_html=True)
            
            with metric_col3:
                tempo_estimado = total_execucoes * 2  # Estimativa de 2 min por execução
                st.markdown("""
                <div class="metric-card">
                    <h3 style="margin: 0; font-size: 2rem;">⏱️</h3>
                    <h2 style="margin: 0.5rem 0;">~{} min</h2>
                    <p style="margin: 0; opacity: 0.9;">Tempo Estimado</p>
                </div>
                """.format(tempo_estimado), unsafe_allow_html=True)

            st.markdown("---")

            # --- Botão para Salvar com Design Aprimorado ---
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            
            with col_btn2:
                if st.button("🚀 Salvar e Executar Framework", type="primary", use_container_width=True):
                    try:
                        with st.spinner("🔄 Preparando configurações..."):
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

                            with open("../options.json", "w", encoding="utf-8") as f:
                                json.dump(final_config, f, indent=4, ensure_ascii=False)
                            
                            st.success("✅ Configuração salva em **options.json**!")

                            # Executa o script principal
                            script_path = FOLDER_NAME.parent / "run_framework.py"
                            print("Configurações do usuário escolhida:", final_config)
                            self.run_script(script_path)
                            st.rerun()

                    except Exception as e:
                        st.error(f"❌ Erro ao salvar ou executar: {e}")

            # Informações adicionais
            with st.expander("ℹ️ Informações Adicionais", expanded=False):
                st.markdown("""
                ### 📚 Guia Rápido de Parâmetros
                
                - **🧬 Taxa de Mutação (0.0-1.0)**: Controla a diversidade genética
                - **🔄 Taxa de Crossover (0.0-1.0)**: Controla a reprodução entre soluções
                - **⏳ Número de Gerações**: Quantas iterações o algoritmo executará
                - **👥 Tamanho da População**: Número de soluções por geração
                
                ### 💡 Dicas de Configuração
                - Para problemas complexos, use mais gerações e população maior
                - Taxa de mutação alta (0.3-0.5) para exploração
                - Taxa de mutação baixa (0.1-0.2) para refinamento
                - Use modo "Variável" para testar diferentes combinações
                """)

        st.markdown("---")

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


