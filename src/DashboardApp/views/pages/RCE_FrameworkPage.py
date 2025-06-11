# --- Componentes da Interface de Usuário ---
from functools import reduce
import json
import operator
from ..components.dash_rce_components import ConsolidatedResultsComponent, CardSolutions, StatisticsTableComponent, GraficoRCEComponent, TabExamplePage

# Backend
from controllers.Utils import Controller, FOLDER_NAME, Utils, PARAMETROS_JSON
import os

# Frontend
import streamlit as st
import time
from pathlib import Path
import threading
import queue

# --- Classe de Gerenciamento de Estado ---
class UseState:
    @staticmethod
    def initialize_state(key, default_value):
        if key not in st.session_state:
            st.session_state[key] = default_value

    @staticmethod
    def get_state(key, default_value=None):
        return st.session_state.get(key, default_value)

    @staticmethod
    def set_state(key, value):
        st.session_state[key] = value

# --- Classe Principal do Aplicativo ---
class FrameworkRCEDashboard:
    def __init__(self, options=None):
        self.controller = Controller()
        self.utils = Utils()
        self.execution_numbers = self.controller.execution_numbers
        #self.menu_lateral = DrawerSideBar()
        self.options = options
        self.init_css()

        UseState.initialize_state("selected_execution", None)
        UseState.initialize_state("active_tab", 0)

        # Inicializa a configuração do usuário, respeitando o parâmetro 'options'
        if 'user_config' not in st.session_state:
            if self.options:
                st.session_state.user_config = self.options
            else:
                # Fallback para configuração padrão se 'options' não for fornecido
                st.session_state.user_config = {
                    "key": True, "value": 10,
                    "parametros_opcionais": [
                        {"MUTACAO": [PARAMETROS_JSON.get('MUTACAO', 0.5)]},
                        {"CROSSOVER": [PARAMETROS_JSON.get('CROSSOVER', 0.9)]},
                        {'NUM_GENERATIONS': [PARAMETROS_JSON.get('NUM_GENERATIONS', 10)]},
                        {'POP_SIZE': [PARAMETROS_JSON.get('POP_SIZE', 10)]},
                    ]
                }

    def init_css(self):
        st.markdown("""
        <style>
            div.stCheckbox > label > div.st-bk { transform: scale(1.5); }
        </style>
        """, unsafe_allow_html=True)

    def _render_parameter_widget(self, param_name, default_value_from_params):
        config = st.session_state.user_config
        param_dict = next((p for p in config.get('parametros_opcionais', []) if param_name in p), None)
        
        if not param_dict:
            st.error(f"Parâmetro '{param_name}' não encontrado na configuração.")
            return

        param_index = config['parametros_opcionais'].index(param_dict)
        current_value = param_dict[param_name]
        
        if st.checkbox(f"Configurar {param_name}?", key=f"config_check_{param_index}"):
            mode = "Variável" if isinstance(current_value, list) and len(current_value) > 1 else "Fixo"
            choice = st.radio("Modo:", ("Fixo", "Variável"), index=1 if mode == "Variável" else 0, key=f"radio_{param_index}", horizontal=True, label_visibility="collapsed")

            if choice == "Variável":
                cols = st.columns(4)
                new_values = []
                existing_values = current_value if mode == "Variável" else [""] * 4
                for j, col in enumerate(cols):
                    with col:
                        val_str = str(existing_values[j]) if j < len(existing_values) else ""
                        user_input = st.text_input(f"V{j+1}", val_str, key=f"input_{param_index}_{j}", label_visibility="collapsed")
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

            else:  # Modo Fixo
                val = current_value[0] if isinstance(current_value, list) else current_value
                if param_name in ["NUM_GENERATIONS", "POP_SIZE"]:
                    new_val = st.number_input("Valor", value=int(val), step=1, key=f"s_{param_index}", format="%d")
                else:
                    new_val = st.number_input("Valor", value=float(val), step=0.1, key=f"s_{param_index}", format="%.1f")
                config['parametros_opcionais'][param_index] = {param_name: [new_val]}
        st.markdown("---")

    def ConfigWebApp(self):
        st.title("🛠️ Configurador de Execuções do Framework")
        with st.expander("Abra para configurar os parâmetros de execução", expanded=True):
            config = st.session_state.user_config
            st.subheader("Configurações Gerais")
            config['value'] = st.number_input("Número de Execuções por Configuração", min_value=1, value=config.get('value', 1))
            st.markdown("---")
            st.subheader("Parâmetros Evolutivos")
            col1, col2 = st.columns(2)
            with col1:
                self._render_parameter_widget("MUTACAO", PARAMETROS_JSON.get("MUTACAO", 0.5))
                self._render_parameter_widget("CROSSOVER", PARAMETROS_JSON.get("CROSSOVER", 0.9))
            with col2:
                self._render_parameter_widget("NUM_GENERATIONS", PARAMETROS_JSON.get("NUM_GENERATIONS", 10))
                self._render_parameter_widget("POP_SIZE", PARAMETROS_JSON.get("POP_SIZE", 10))
            st.subheader("Quantidade de Execuções Configuradas")
            num_variations = [len(v) for p in config['parametros_opcionais'] for k, v in p.items() if isinstance(v, list) and len(v) > 1 and v]
            total_combinations = reduce(operator.mul, num_variations, 1) if num_variations else 1
            total_execucoes = total_combinations * config.get('value', 1)
            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric("Configurações Únicas", total_combinations)
            with metric_col2:
                st.metric("Total de Execuções", total_execucoes)
            if st.button("Salvar e Executar", type="primary"):
                self.save_and_run_framework()

    def save_and_run_framework(self):
        try:
            final_config = {**PARAMETROS_JSON}
            user_config = st.session_state.user_config
            optional_params = {k: v for d in user_config.get('parametros_opcionais', []) for k, v in d.items()}
            final_config.update(optional_params)
            final_config['repeticoes_por_config'] = user_config.get('value')
            
            # Gera o ficheiro de configuração .txt
            config_path = FOLDER_NAME.parent / "configuracao_usada.txt"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(final_config, f, indent=4)
            
            st.success(f"Configuração salva em **{config_path.name}**!")
            
            script_path = FOLDER_NAME.parent / "run_framework.py"
            self.run_script(script_path)
        except Exception as e:
            st.error(f"Ocorreu um erro ao salvar a configuração: {e}")

    def run_script(self, script_path):
        """Executa o script em uma thread com GIF e barra de progresso."""
        dialog_placeholder = st.empty()
        progress_placeholder = st.empty()
        
        try:
            img_gif_loading = FOLDER_NAME.parent / "assets" / "humans_evolution.gif"
            
            with dialog_placeholder.container():
                if img_gif_loading.exists():
                    st.image(str(img_gif_loading))
                st.subheader("Executando o programa principal... Por favor, aguarde.")

                def run_command_in_thread():
                    command = f'python -u "{script_path}"'
                    self._return_code = os.system(command) # os.system é bloqueante, mas está na thread
                
                self._return_code = None
                thread = threading.Thread(target=run_command_in_thread)
                thread.start()

                # Simula uma barra de progresso enquanto a thread está viva
                progress_bar = progress_placeholder.progress(0)
                while thread.is_alive():
                    # Este loop apenas atualiza a UI e não reflete o progresso real do script
                    for i in range(100):
                        if not thread.is_alive():
                            break
                        progress_bar.progress(i + 1)
                        time.sleep(0.1) # Ajuste o tempo para a velocidade da barra
                    progress_bar.progress(100)
                
                thread.join()
                return_code = self._return_code

            dialog_placeholder.empty()
            progress_placeholder.empty()

            if return_code == 0:
                st.success("Script executado com sucesso! Atualizando a página...")
            else:
                st.error(f"O script falhou com o código de retorno {return_code}.")
            
            time.sleep(2)
            st.rerun()

        except Exception as e:
            dialog_placeholder.empty()
            progress_placeholder.empty()
            st.error(f"Erro ao executar o script: {e}")
            
    def run(self):
        self.ConfigWebApp()
        self.header()
        
        if not self.execution_numbers:
            st.info("Nenhuma execução encontrada. Configure e execute o framework para ver os resultados.")
        else:
            self.display_results_tabs()
            
        self.footer()

    def display_results_tabs(self):
        st.subheader("🔄 Análise por Execução")
        
        active_tab_index = UseState.get_state("active_tab", 0)
        if active_tab_index >= len(self.execution_numbers):
            active_tab_index = 0
            UseState.set_state("active_tab", 0)

        tabs = st.tabs([f"Execução {num}" for num in self.execution_numbers])

        for i, tab in enumerate(tabs):
            with tab:
                if i == active_tab_index:
                    exec_num = self.execution_numbers[i]
                    with st.spinner(f"Carregando dados da Execução {exec_num}..."):
                        dados = self.utils.load_execution_data(exec_num, debug=False)
                    if dados:
                        CardSolutions.render(dados, exec_num)
                        GraficoRCEComponent.render(exec_num)
                        StatisticsTableComponent.render(dados)
                    else:
                        st.warning(f"Não foram encontrados dados para a Execução {exec_num}.")
                else:
                    if st.button(f"Carregar Execução {self.execution_numbers[i]}", key=f"btn_{i}"):
                        UseState.set_state("active_tab", i)
                        st.rerun()

    def header(self):
        st.markdown("<hr>", unsafe_allow_html=True)
        st.title("⚡ Framework Repopulation-With-Elite-Set RCE ⚡")

    def footer(self):
        st.markdown("<hr>", unsafe_allow_html=True)
        st.info("Desenvolvido por Pedro Victor Veras e Rainer Zanghi em um projeto PIBIC pela UFF - 2024/2025")


def main():
    app = FrameworkRCEDashboard()
    app.run()


if __name__ == "__main__":
    main()

