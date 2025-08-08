# --- Componentes da Interface de Usuário ---
from ..components.dash_rce_components import ConsolidatedResultsComponent, CardSolutions, GraficoPotenciaAtivaReativaComponent, StatisticsTableComponent, GraficoRCEComponent
from .AgendamentoRedePage import AgendamentoRedePage

#backend
from controllers.Utils import Controller,FOLDER_NAME, Utils, PARAMETROS_JSON, ConfigController

# Frontend
import streamlit as st




# Configuração da barra lateral
class DrawerSideBar:
    """Classe para gerenciar a barra lateral do aplicativo."""

    def __init__(self, warnings=None):
        """Inicializa a barra lateral."""
        self.st = st
        self.warnings = warnings or []

    def render(self):
        """Renderiza a barra lateral."""
        self.st.sidebar.title("Painel de Controle")
        if st.sidebar.button("Atualizar Estado"):
            st.session_state.clear()
            st.rerun()
        
        if self.warnings:
            with st.sidebar.expander("⚠️ Avisos de Execução", expanded=True):
                for warning in self.warnings:
                    st.warning(warning)

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


# --- Classe Principal do Aplicativo ---
class FrameworkRCEDashboard:
    def __init__(self, options = None):
        self.controller = Controller()
        self.utils = Utils()
        self.executions, self.warnings = self.utils.find_available_executions()
        self.menu_lateral = DrawerSideBar(self.warnings)
  
        self.options = options 
        self.init_css()

        UseState.initialize_state("saved_configurations", {})
        if 'user_config' not in st.session_state:
            st.session_state.user_config = self.options


    def init_css(self):
        st.markdown("""...""", unsafe_allow_html=True) # CSS omitido para brevidade

    def run(self):
        try:
            self.menu_lateral.render()
            self.header()

            if st.sidebar.button("Consultar Parâmetros do AG"):
                self.show_config_parameters()

            if not self.executions:
                st.info("Nenhuma execução encontrada. Execute o framework para gerar resultados.")
                st.stop()

            config_controller = ConfigController()
            all_params = config_controller.repository.get_all_configs()

            df_consolidado, render_warnings = ConsolidatedResultsComponent.render(all_params)
            self.menu_lateral.warnings.extend(render_warnings)
            
            if df_consolidado is not None and not df_consolidado.empty:
                ConsolidatedResultsComponent.display_and_download(df_consolidado)
            else:
                st.info("Não foi possível gerar a tabela de resultados consolidados.")

            self.render_execution_tabs()
            
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado no dashboard: {e}")
            st.exception(e)

    def show_config_parameters(self):
        st.header("Parâmetros de Configuração do AG")
        config_controller = ConfigController()
        formatted_configs = config_controller.get_formatted_configs()

        if not formatted_configs:
            st.warning("Nenhum arquivo de parâmetro de configuração (params_config*.json) foi encontrado.")
            return

        for config_num, df_params in sorted(formatted_configs.items()):
            with st.expander(f"Configuração {config_num}"):
                st.dataframe(df_params)
            
    def render_execution_tabs(self):
        config_keys = list(self.executions.keys())
        config_tabs = st.tabs([f"Config {key}" for key in config_keys])

        for i, config_tab in enumerate(config_tabs):
            with config_tab:
                config_num = config_keys[i]
                exec_numbers = self.executions[config_num]
                
                lock_state_key = f"lock_config_{config_num}"
                UseState.initialize_state(lock_state_key, False)
                
                _, col2 = st.columns([0.8, 0.2])
                with col2:
                    is_locked = st.toggle("🔒 Fixar Aba", key=f"toggle_{config_num}", value=UseState.get_state(lock_state_key))
                    UseState.set_state(lock_state_key, is_locked)

                if is_locked:
                    self.render_locked_view(config_num, exec_numbers)
                else:
                    self.render_dynamic_view(config_num, exec_numbers)

    def render_locked_view(self, config_num, exec_numbers):
        component_options = ["Soluções", "Gráfico", "Estatísticas"]
        locked_component_key = f"locked_component_{config_num}"
        locked_exec_key = f"locked_exec_{config_num}"
        
        UseState.initialize_state(locked_component_key, component_options[0])
        UseState.initialize_state(locked_exec_key, exec_numbers[0])

        col1, col2 = st.columns(2)
        with col1:
            selected_component = st.selectbox("Selecione o Componente", component_options, 
                index=component_options.index(UseState.get_state(locked_component_key)),
                key=f"select_comp_{config_num}")
            UseState.set_state(locked_component_key, selected_component)
        with col2:
            selected_exec = st.selectbox("Selecione a Execução", exec_numbers,
                index=exec_numbers.index(UseState.get_state(locked_exec_key)),
                key=f"select_exec_{config_num}")
            UseState.set_state(locked_exec_key, selected_exec)
            
        st.markdown("---")
        st.info(f"Mostrando **{selected_component}** para a **Execução {selected_exec}** da **Configuração {config_num}**")

        dados = self.utils.load_execution_data(config_num, selected_exec)
        if dados:
            self.render_component(selected_component, dados, config_num, selected_exec)
        else:
            st.warning("Não foi possível carregar os dados para a seleção atual.")

    def render_dynamic_view(self, config_num, exec_numbers):
        exec_tabs = st.tabs([f"Execução {num}" for num in exec_numbers])
        for j, exec_tab in enumerate(exec_tabs):
            with exec_tab:
                exec_num = exec_numbers[j]
                dados = self.utils.load_execution_data(config_num, exec_num)
                
                if dados:
                    component_tabs = st.tabs(["Soluções", "Gráfico", "Estatísticas"])
                    with component_tabs[0]:
                        self.render_component("Soluções", dados, config_num, exec_num)
                    with component_tabs[1]:
                        self.render_component("Gráfico", dados, config_num, exec_num)
                    with component_tabs[2]:
                        self.render_component("Estatísticas", dados, config_num, exec_num)
                else:
                    st.warning(f"Dados para Config {config_num} / Exec {exec_num} não encontrados.")

    def render_component(self, component_name, data, config_num, exec_num):
        try:
            if component_name == "Soluções":
                CardSolutions.render(data, exec_num, debug=False)
                AgendamentoRedePage()
                
            elif component_name == "Gráfico":
                GraficoRCEComponent.render(exec_num)
                GraficoPotenciaAtivaReativaComponent.render(exec_num, 1)
                
            elif component_name == "Estatísticas":
                StatisticsTableComponent.render(data)
                
        except Exception as e:
            st.error(f"Erro ao renderizar '{component_name}' para Config {config_num}/Exec {exec_num}: {e}")

    def header(self):
        st.markdown("---")
        st.title("⚡ Dashboard Repopulation-With-Elite-Set RCE ⚡")
        st.subheader("Version 15.2.5 - 08/08/2025")
        st.markdown("---")

    def footer(self):
        st.markdown("---")
        st.info("Desenvolvido por Pedro Victor Veras e Rainer Zanghi em um projeto PIBIC pela UFF - 2024/2025")
        st.link_button(
            url="https://github.com/PedroVic12/Repopulation-With-Elite-Set",
            label="Visite a Documentação do Projeto nesse link",
            type="primary",
            icon="📖",
        )
        st.markdown("---")