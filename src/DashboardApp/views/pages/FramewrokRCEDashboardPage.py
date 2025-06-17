

# --- Componentes da Interface de Usuário ---
from functools import reduce
import json
import operator
from ..components.dash_rce_components import ConsolidatedResultsComponent, CardSolutions, StatisticsTableComponent, GraficoRCEComponent, TabExamplePage


#backend
from controllers.Utils import Controller,FOLDER_NAME, Utils, PARAMETROS_JSON
import os

# Frontend
import streamlit as st
import time
import threading



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
                    
            # Configuração de parametros do Framework
            self.ConfigWebApp()
       
            # Cabeçalho
            self.header()

            # Renderiza os resultados consolidados
            if dados:
                ConsolidatedResultsComponent.render(dados)
            else:
                st.info("Nenhum dado encontrado ainda. Execute uma simulação para visualizar os resultados.")


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

                        # Carrega os dados e o gráfico da execução
                        if dados:
                            try:
                                with st.container():
                                    CardSolutions.render(dados, exec_num)


                                with st.container():
                                    GraficoRCEComponent.render(exec_num)  # Passa o exec_num para carregar o gráfico correto
                                    
                                with st.container():
                                    StatisticsTableComponent.render(dados)
                                    st.write("Graficos e Tabelas")
                                    TabExamplePage()
                                    
                                    
                                    
                            except Exception as e:
                                st.error(f"Erro ao carregar os dados da execução {exec_num}.",e)

                        else:
                            st.error("Não foi encontrado nenhum conjunto de dados")
        

            self.footer()

        except Exception as error:
            st.warning(f"Erro ao carregar pagina: {error}")


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
                
                if st.toggle(f"Configurar {param_name}?", key=f"config_check_{param_index}"):
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

                    # Pega o ponteiro dos parametros de AG
                    final_config = {**PARAMETROS_JSON}
                    user_config = st.session_state.user_config
                    
                    # Pega os dados atualizados do usuario na tela
                    optional_params_dict = {k: v for d in user_config.get('parametros_opcionais', []) for k, v in d.items()}
                    final_config.update(optional_params_dict)
                    final_config['repeticoes_por_config'] = user_config.get('value')
                    
                    # Salva o arquivo JSON para ser usado pelo script
                    final_config.update(user_config)
                    out_file = open("output.json", "w")
                    json.dump(final_config, out_file)
                    out_file.close()
                    
                    st.success(f"Configuração salva em **output.json**!")
                    
                    # Executa o script principal
                    script_path = FOLDER_NAME.parent / "run_framework.py"
                    print("Configurações o Usuario escolhida", final_config)
                    self.run_script(script_path)
                    st.rerun()


                except Exception as e:
                    st.error(f"Ocorreu um erro ao salvar ou executar: {e}")


    def atualizar_pagina(self):
        """Atualiza a página."""
        print("Atualizando a página...")
        st.rerun()



    
    def run_script(self, script_path):
        """Executa um script Python com barra de progresso única e GIF enquanto roda. usando threading para não travar a UI e progress_placeholder para atualizar a barra de progresso"""
        dialog_placeholder = st.empty()
        progress_placeholder = st.empty()

        try:
            img_gif_loading = FOLDER_NAME.parent / "assets" / "humans_evolution.gif"
            files = self.utils.get_html_content_from_folder(FOLDER_NAME)
            steps = len(files) * 10 if len(files) > 0 else 10

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

                    for i in range(steps + 1):
                        if not thread.is_alive():
                            break
                        progress = i / steps
                        bar_html = f"""
                        <div style="background-color:#e0e0e0; border-radius:10px; width:100%; height:30px;">
                            <div style="background-color:#008000; width:{progress*100}%; height:30px; border-radius:10px;"></div>
                        </div>
                        <p style="text-align:center;">{int(progress*100)}%</p>
                        """
                        progress_placeholder.markdown(bar_html, unsafe_allow_html=True)
                        time.sleep(1.0)

                    # Aguarda thread terminar se ainda não terminou
                    thread.join()
                    return_code = self._return_code
            else:
                # Caso não tenha GIF, só executa o script
                command = f'python "{script_path}"'
                return_code = os.system(command)

            dialog_placeholder.empty()
            progress_placeholder.empty()

            if return_code == 0:
                st.success("Script executado com sucesso!")
                st.rerun()

        except Exception as e:
            dialog_placeholder.empty()
            st.error(f"Erro ao executar o script. Código de retorno: {return_code} e Erro: {e}")

        if not self.execution_numbers:
            st.error("Nenhum arquivo de resultado encontrado.")
            st.stop()
    


    def header(self):
        """Cabeçalho do aplicativo."""
        st.markdown("---")
        st.title("⚡ Framework Repopulation-With-Elite-Set RCE ⚡")
        st.write("V 10.1.5 - 2025/06/04")
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
