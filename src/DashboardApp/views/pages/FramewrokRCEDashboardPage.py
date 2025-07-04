

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
            st.experimental_rerun()
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
            dados = self.utils.load_execution_data(active_tab + 1, debug=False)
                    
            # Sempre renderiza a configuração do app e do AG
            self.ConfigWebApp()
            self.Config_AG_Json(dados if dados else {})

            # Cabeçalho
            self.header()

            if dados:
                # Renderiza os resultados consolidados
                ConsolidatedResultsComponent.render()
            else:
                # Renderiza componente default para "sem execução"
                st.info("Nenhum dado encontrado ainda. Execute uma simulação para visualizar os resultados.")
                # Você pode adicionar mais componentes ou instruções aqui se quiser

            #! MEU TEMPLATE USANDO TABS com Seleção de execução com tabs para cada execução controlado pelo UseState
            with st.container():
                st.subheader("🔄 Seleção da Execução")
                
                # Cria abas
                tabs = st.tabs([f"Execução {num}" for num in self.execution_numbers])

                # Renderiza o conteúdo de cada aba
                for i, (tab, exec_num) in enumerate(zip(tabs, self.execution_numbers)):
                    with tab:
                        # Atualiza o estado da aba ativa
                        if UseState.get_state("active_tab") != i:
                            self.handle_tab_change(i, exec_num)

                        # Carrega os dados e o gráfico da execução CORRETOS para cada aba
                        dados_exec = self.utils.load_execution_data(exec_num, debug=False)
                        if dados_exec:
                            try:
                                with st.container():
                                    CardSolutions.render(dados_exec, exec_num, debug=False)
                                with st.container():
                                    GraficoRCEComponent.render(exec_num)
                                with st.container():
                                    StatisticsTableComponent.render(dados_exec)
                                    st.write("Graficos e Tabelas")
                            except Exception as e:
                                st.error(f"Erro ao carregar os dados da execução {exec_num}. {e}")
                        else:
                            st.error("Não foi encontrado nenhum conjunto de dados")

            self.footer()

        except Exception as error:
            st.warning(f"Erro ao carregar pagina: {error}")
    
    

    def Config_AG_Json(self, dados):
            # Expandir para mostrar os parâmetros utilizados
            with st.expander("Parâmetros AG Utilizados em params.json", expanded=False):
                json_data_params = dados.get("params", {})

                if json_data_params:
                    
                    # Separa os campos especiais
                    array_var = json_data_params.get("ARRAY_VAR", [14,15,14,18,15])
                    limite_var = json_data_params.get("LIMITE_VAR", [0, 31])

                    # Remove os campos especiais para edição no data_editor
                    json_table = {k: v for k, v in json_data_params.items() if k not in ["ARRAY_VAR", "LIMITE_VAR"]}
                    #print("json_table", json_table)


                    st.info("Usando Variáveis de Decisão do Problema e Limites de valores inteiros para o problema de agendamento de Redes Elétricas")

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
                    df_params = pd.DataFrame(list(json_table.items()), columns=["Parâmetro", "Valor"])
                    edited_df = st.data_editor(
                        df_params,
                        use_container_width=True,
                        num_rows="dynamic",
                        column_config={
                            "Parâmetro": st.column_config.Column(disabled=True),
                            "Valor": st.column_config.Column(disabled=False)
                        }
                    )

                    # Atualiza json_table com os valores editados
                    if not edited_df.empty:
                        for _, row in edited_df.iterrows():
                            param = row["Parâmetro"]
                            value = row["Valor"]
                            json_table[param] = value

                    st.markdown("---")

                    # Monta o dicionário final para exportação
                    json_atualizados = dict(json_table)
                    json_atualizados["ARRAY_VAR"] = [int(x) for x in array_var_edit]
                    json_atualizados["LIMITE_VAR"] = [int(x) for x in limite_var_edit]

                    # --- TRATAMENTO DE TIPOS ---
                    float_keys = {"MUTACAO", "CROSSOVER", "PORCENTAGEM"}
                    for k, v in json_atualizados.items():
                        if k in float_keys:
                            try:
                                json_atualizados[k] = float(v)
                            except Exception:
                                st.error(f"Valor inválido para {k}. Deve ser um número flutuante.")
                        elif k in {"ARRAY_VAR", "LIMITE_VAR"}:
                            # Garante que sejam listas de inteiros
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
                                st.error(f"Valor inválido para {k}. Deve ser um número inteiro.")  # Salva o arquivo atualizado em dois diretórios anteriores
                    
                    
                    current_dir = pathlib.Path(__file__).parent
                    target_path = current_dir.parent.parent.parent / "params.json"
                    try:
                        with open(target_path, "w", encoding="utf-8") as f:
                            json.dump(json_atualizados, f, indent=4, ensure_ascii=False)
                        st.success(f"Arquivo salvo em: {target_path}")
                    except Exception as e:
                        st.error(f"Erro ao salvar arquivo: {e}")

                    # Exporta os dados atualizados para um arquivo json com um botão de download
                    st.download_button(
                        label="Salvar os Parâmetros AG Atualizados",
                        data=json.dumps(json_atualizados, indent=4),
                        file_name="params.json",
                        mime="application/json"
                    )

    def ConfigWebApp(self):
        
#    !TODO GUI para interação com o usuário

#    1 - 256 conjuntos de parametros (4⁴) 
#    2 - 10 ou 20 numero de execucoes
#    3 - 4 parametros variando [Mutação, Crossover, Var DIFF, DELTA e restante fixo 
#    4 - 4 Caixas de texto fixas para esses parametros variando
#    5 - Criar checkbox para o usuario desabilitar as demais caixas de texto, deixando um valor possivel para aquele parametro 
#    6 - butao Radio para selecionar a tabela a configuração das 256 conjuntos
#    7 - Progress bar para cada geração em tempo de execução 


        st.title("🛠️ Configurador de Execuções do Framework")
        
        with st.expander("Abra para configurar os parâmetros de execução", expanded=False):
            config = st.session_state.user_config

            # --- Seção de Configurações Gerais ---
            st.subheader("Configurações Gerais")
            config['value'] = st.number_input(
                "Número de Execuções por Configuração",
                min_value=1,
                value=config.get('value', 1),
                help="Quantas vezes cada combinação única de parâmetros será executada."
            )
            st.markdown("---")

            # --- Seção de Parâmetros Evolutivos ---
            st.subheader("Parâmetros Evolutivos")

            def render_parameter_widget(param_name, default_value_from_params):
                # --- LÓGICA ROBUSTA PARA ENCONTRAR O PARÂMETRO E SEU ÍNDICE ---
                param_dict = None
                param_index = -1
                for i, p_dict in enumerate(config.get('parametros_opcionais', [])):
                    if param_name in p_dict:
                        param_dict = p_dict
                        param_index = i
                        break
                
                # Se o parâmetro não for encontrado, exibe um erro e interrompe a renderização para este widget
                if param_index == -1:
                    st.error(f"Parâmetro de configuração '{param_name}' não encontrado no estado da sessão.")
                    return
                # --- FIM DA LÓGICA ROBUSTA ---

                current_value = param_dict[param_name]

                # Altera os nomes dos parametros para português e adiciona toggle
                toggle_label = {
                    "NUM_GENERATIONS": "Configurar Número de Gerações?",
                    "POP_SIZE": "Configurar Tamanho da População?",
                    "MUTACAO": "Configurar Taxa de Mutação?",
                    "CROSSOVER": "Configurar Taxa de Crossover?"
                }.get(param_name, f"Configurar {param_name}?")

                if st.toggle(toggle_label, key=f"config_check_{param_index}"):


                    mode = "Variável" if isinstance(current_value, list) and len(current_value) > 1 else "Fixo"
                    choice = st.radio(
                        "Modo:", ("Fixo", "Variável"), index=1 if mode == "Variável" else 0,
                        key=f"radio_{param_index}", horizontal=True, label_visibility="collapsed"
                    )

                    if choice == "Variável":
                        st.write(f"Valores para {param_name}:")
                        cols = st.columns(4)
                        new_values = []
                        existing_values = current_value if mode == "Variável" else [""]*4
                        
                        for j, col in enumerate(cols):
                            with col:
                                val_str = str(existing_values[j]) if j < len(existing_values) else ""
                                user_input = st.text_input(f"V {j+1}", val_str, key=f"input_{param_index}_{j}", label_visibility="collapsed")
                                if user_input:
                                    try:
                                        if param_name in ["NUM_GENERATIONS", "POP_SIZE"]:
                                            new_values.append(int(user_input))
                                        else:
                                            new_values.append(round(float(user_input), 1))
                                    except ValueError:
                                        st.error("Valor inválido", icon="⚠️")
                        
                        if not new_values:
                            st.warning(f"Preencha ao menos um valor para '{param_name}'.")
                        
                        config['parametros_opcionais'][param_index] = {param_name: new_values or [default_value_from_params]}

                    else: # Fixo
                        default_value = current_value[0] if isinstance(current_value, list) else current_value
                        if param_name in ["NUM_GENERATIONS", "POP_SIZE"]:
                            new_val = st.number_input(f"Valor para {param_name}", value=int(default_value), step=1, key=f"s_{param_index}", format="%d")
                        else:
                            new_val = st.number_input(f"Valor para {param_name}", value=float(default_value), step=0.1, key=f"s_{param_index}", format="%.1f")
                        config['parametros_opcionais'][param_index] = {param_name: [new_val]}


                        
                st.markdown("---")

            col1, col2 = st.columns(2)
            with col1:
                render_parameter_widget("MUTACAO", PARAMETROS_JSON["MUTACAO"])
                render_parameter_widget("CROSSOVER", PARAMETROS_JSON["CROSSOVER"])
            with col2:
                render_parameter_widget("NUM_GENERATIONS", PARAMETROS_JSON["NUM_GENERATIONS"])
                render_parameter_widget("POP_SIZE", PARAMETROS_JSON["POP_SIZE"])

            # --- Seção de Resumo ---
            st.subheader("Quantidade de Execuções Configuradas")
            num_variations = [len(v) for p in config['parametros_opcionais'] for k,v in p.items() if isinstance(v, list) and len(v) > 1 and v]
            total_combinations = reduce(operator.mul, num_variations, 1) if num_variations else 1
            total_execucoes = total_combinations * config.get('value', 1)

            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric("Configurações Únicas", total_combinations, help="Número de combinações diferentes de parâmetros.")
            with metric_col2:
                st.metric("Total de Execuções", total_execucoes)

                        # --- Botão para Salvar ---
            if st.button("Salvar e Executar", type="primary"):
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
                            arquivos_atual = set(self.utils.get_html_content_from_folder(FOLDER_NAME))
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
        st.subheader("Version 11.1.5 - 24/06/2025")
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
