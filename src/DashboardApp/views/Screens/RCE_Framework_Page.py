

# --- Componentes da Interface de Usuário ---
from ..components.dash_rce_components import ConsolidatedResultsComponent, CardSolutions, GraficoPotenciaAtivaReativaComponent, StatisticsTableComponent, GraficoRCEComponent
from ..components.side_bar_widget import load_execution_data
from .AgendamentoRedePage import AgendamentoRedePage

#backend
from controllers.Utils import Controller, Utils, ConfigController

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
    def __init__(self, options=None):
        self.controller = Controller()
        self.utils = Utils()
        
        # Get available executions (returns dict of {config_num: [exec_nums]}, warnings)
        self.executions, self.warnings = self.utils.find_available_executions()
        self.menu_lateral = DrawerSideBar(self.warnings)
        
        # Store the first config and its first execution as default
        self.current_config = next(iter(self.executions.keys()), None) if self.executions else None
        self.current_execution = self.executions[self.current_config][0] if self.current_config and self.executions[self.current_config] else None
        
        self.options = options 
        self.init_css()

        UseState.initialize_state("saved_configurations", {})
        if 'user_config' not in st.session_state:
            st.session_state.user_config = self.options

        if "dados" not in st.session_state:
            st.session_state.dados = None

        if "resultados_AG" not in st.session_state:
            st.session_state.resultados_AG = None
            
        # Store execution data in session state
        if 'execution_data' not in st.session_state and self.current_config and self.current_execution:
            try:
                st.session_state.execution_data = self.utils.load_execution_data(
                    self.current_config, 
                    self.current_execution
                )
            except Exception as e:
                st.error(f"Erro ao carregar dados da execução: {str(e)}")




    def init_css(self):
        st.markdown("""...""", unsafe_allow_html=True) # CSS omitido para brevidade

    def _create_timeline(self, execution_data):
        """Create an interactive timeline of solutions with branch disconnections."""
        if not execution_data or 'solutions' not in execution_data:
            return None
            
        timeline_data = []
        for sol in execution_data['solutions']:
            if not sol.get('disconnected_branches'):
                continue
                
            for branch in sol['disconnected_branches']:
                timeline_data.append({
                    'time': sol.get('timestamp', 0),
                    'branch': f"Ramo {branch}",
                    'status': 'Desligado',
                    'fitness': sol.get('fitness', 0)
                })
        
        if not timeline_data:
            return None
            
        return pd.DataFrame(timeline_data)

    def _display_timeline_filter(self, df):
        """Display interactive timeline with filtering options."""
        st.sidebar.subheader("Filtros")
        
        # Time range filter
        min_time = int(df['time'].min())
        max_time = int(df['time'].max())
        time_range = st.sidebar.slider(
            "Intervalo de Tempo",
            min_value=min_time,
            max_value=max_time,
            value=(min_time, max_time)
        )
        
        # Branch filter
        all_branches = sorted(df['branch'].unique())
        selected_branches = st.sidebar.multiselect(
            "Ramos",
            options=all_branches,
            default=all_branches
        )
        
        # Apply filters
        filtered_df = df[
            (df['time'] >= time_range[0]) & 
            (df['time'] <= time_range[1]) &
            (df['branch'].isin(selected_branches))
        ]
        
        return filtered_df

    def run(self):
        try:
            self.menu_lateral.render()
            self.header()

            if not self.executions:
                st.info("Nenhuma execução encontrada. Execute o framework para gerar resultados.")
                st.stop()

            config_controller = ConfigController()
            all_params = config_controller.repository.get_all_configs()
            
            # Show configuration and execution selectors
            with st.sidebar.expander("🔧 Configuração e Execução", expanded=True):
                # Configuration selector
                config_options = list(self.executions.keys())
                selected_config = st.selectbox(
                    "Selecione a configuração:",
                    config_options,
                    index=0,
                    format_func=lambda x: f"Configuração {x}"
                )
                
                # Execution selector for the selected configuration
                if selected_config in self.executions and self.executions[selected_config]:
                    exec_options = self.executions[selected_config]
                    selected_exec = st.selectbox(
                        "Selecione a execução:",
                        exec_options,
                        index=0,
                        format_func=lambda x: f"Execução {x}"
                    )
                    
                    # Load button
                    if st.button("Carregar Dados"):
                        with st.spinner("Carregando dados da execução..."):
                            try:
                                data, fig = self.utils.load_execution_data(selected_config, selected_exec)
                                st.session_state.execution_data = data
                                if fig is not None:
                                    st.session_state.execution_figure = fig
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao carregar execução: {str(e)}")
                else:
                    st.warning("Nenhuma execução disponível para esta configuração.")
            
            # Display execution data if available
            if 'execution_data' in st.session_state and st.session_state.execution_data:
                # Create and display timeline if data is available
                timeline_df = self._create_timeline(st.session_state.execution_data)
                if timeline_df is not None:
                    st.subheader("Linha do Tempo de Soluções")
                    filtered_timeline = self._display_timeline_filter(timeline_df)
                    
                    # Display timeline
                    if not filtered_timeline.empty:
                        st.vega_lite_chart(filtered_timeline, {
                            'mark': {'type': 'circle', 'tooltip': True},
                            'encoding': {
                                'x': {'field': 'time', 'type': 'quantitative', 'title': 'Tempo'},
                                'y': {'field': 'branch', 'type': 'nominal', 'title': 'Ramo'},
                                'size': {'field': 'fitness', 'type': 'quantitative', 'title': 'Fitness'},
                            'color': {'field': 'status', 'type': 'nominal', 'title': 'Status'}
                        }
                    })
                    
                    # Show selected point details
                    if st.checkbox("Mostrar detalhes da solução"):
                        selected_time = st.slider(
                            "Selecione um ponto no tempo",
                            min_value=int(filtered_timeline['time'].min()),
                            max_value=int(filtered_timeline['time'].max()),
                            value=int(filtered_timeline['time'].iloc[0])
                        )
                        
                        selected_solution = filtered_timeline[
                            filtered_timeline['time'] == selected_time
                        ]
                        st.dataframe(selected_solution)

            # Consolida resultados e exibe, passando all_params exigido pelo componente
            df_consolidado, cons_warnings = ConsolidatedResultsComponent.render(all_params)
            if cons_warnings:
                for w in cons_warnings:
                    st.warning(w)
            if df_consolidado is not None:
                # guarda no estado os execs realmente disponíveis por configuração
                try:
                    available_execs = {}
                    for cfg in sorted(df_consolidado['Config'].unique()):
                        execs_list = sorted(df_consolidado[df_consolidado['Config'] == cfg]['Exec'].unique().tolist())
                        # guarda com múltiplas chaves para evitar mismatch de tipos (int/str)
                        available_execs[cfg] = execs_list
                        try:
                            available_execs[int(cfg)] = execs_list
                        except Exception:
                            st.error(f"Erro ao converter config {cfg} para int.")
                        try:
                            available_execs[str(cfg)] = execs_list
                        except Exception:
                            st.error(f"Erro ao converter config {cfg} para str.")
                    st.session_state['available_execs_by_config'] = available_execs
                    st.session_state['df_consolidado'] = df_consolidado
                except Exception as e:
                    st.error(f"Erro ao processar resultados consolidados: {e}")
                ConsolidatedResultsComponent.display_and_download(df_consolidado)

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
        # Controle global acima das tabs
        UseState.initialize_state("lock_all_configs", False)
        top_cols = st.columns([0.8, 0.2])
        with top_cols[1]:
            is_locked_global = st.toggle(
                "🔒 Fixar Aba",
                key="toggle_all_configs",
                value=UseState.get_state("lock_all_configs"),
                help="Fixar a visualização e escolher componente/execução via select boxes."
            )
            UseState.set_state("lock_all_configs", is_locked_global)

        #st.markdown("---")

        config_keys = list(self.executions.keys())
        config_tabs = st.tabs([f"Config {key}" for key in config_keys])

        for i, config_tab in enumerate(config_tabs):
            with config_tab:
                config_num = config_keys[i]
                # Se existir um conjunto de execs consolidado para essa config, usa ele para evitar inconsistências
                available_map = st.session_state.get('available_execs_by_config', {})
                exec_numbers = (
                    available_map.get(config_num)
                    or available_map.get(str(config_num))
                    or available_map.get(int(config_num) if isinstance(config_num, (str, bytes)) and str(config_num).isdigit() else None)
                    or self.executions[config_num]
                )
                if not exec_numbers:
                    st.info("Nenhuma execução consolidada disponível para esta configuração.")
                    continue
                
                if is_locked_global:
                    self.render_locked_view(config_num, exec_numbers)
                else:
                    self.render_dynamic_view(config_num, exec_numbers)

    def render_locked_view(self, config_num, exec_numbers):
        component_options = ["Soluções", "Gráfico", "Estatísticas"]
        locked_component_key = f"locked_component_{config_num}"
        locked_exec_key = f"locked_exec_{config_num}"
        
        UseState.initialize_state(locked_component_key, component_options[0])
        UseState.initialize_state(locked_exec_key, exec_numbers[0])
        # Se o estado persistido tiver uma execução indisponível, ajusta para a primeira disponível
        try:
            if UseState.get_state(locked_exec_key) not in exec_numbers:
                UseState.set_state(locked_exec_key, exec_numbers[0])
        except Exception:
            UseState.set_state(locked_exec_key, exec_numbers[0])

        col1, col2 = st.columns(2)
        with col1:
            selected_component = st.selectbox("Selecione o Componente", component_options, 
                index=component_options.index(UseState.get_state(locked_component_key)),
                key=f"select_comp_{config_num}")
            UseState.set_state(locked_component_key, selected_component)
        with col2:
            # Garante que o índice exista; se não, usa 0
            try:
                idx_exec = exec_numbers.index(UseState.get_state(locked_exec_key))
            except ValueError:
                idx_exec = 0
            selected_exec = st.selectbox("Selecione a Execução", exec_numbers,
                index=idx_exec,
                key=f"select_exec_{config_num}")
            UseState.set_state(locked_exec_key, selected_exec)
            
        #st.markdown("---")
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
                # Check if data is the correct structure for CardSolutions
                if isinstance(data, list) and len(data) > 0:
                    # If data is a list, use the first element (assuming it contains the solution data)
                    solution_data = data[0] if isinstance(data[0], dict) else {}
                elif isinstance(data, dict):
                    solution_data = data
                else:
                    solution_data = {}
                    st.warning(f"Estrutura de dados inesperada para Config {config_num}/Exec {exec_num}. Dados: {type(data)}")
                
                CardSolutions.render(solution_data, exec_num, debug=False)
                # Renderizar Agendamento diretamente para esta aba de execução
                AgendamentoRedePage(
                    key_prefix=f"cfg{config_num}_exec{exec_num}",
                    selected_exec=exec_num,
                    solution_vars=solution_data.get('best_vars') if isinstance(solution_data, dict) else None,
                )
                
            elif component_name == "Gráfico":
                # Verifica se a execução selecionada existe no consolidado
                available_map = st.session_state.get('available_execs_by_config', {})
                available_execs = (
                    available_map.get(config_num)
                    or available_map.get(str(config_num))
                    or available_map.get(int(config_num) if isinstance(config_num, (str, bytes)) and str(config_num).isdigit() else None)
                    or []
                )
                if available_execs and exec_num not in available_execs:
                    st.warning(f"Gráficos não disponíveis para a Execução {exec_num}. Disponíveis: {available_execs}")
                    return
                GraficoRCEComponent.render(exec_num, config_num=config_num)
                GraficoPotenciaAtivaReativaComponent.render(exec_num, 1, config_num=config_num)
                
            elif component_name == "Estatísticas":
                StatisticsTableComponent.render(data)
                
        except Exception as e:
            st.error(f"Erro ao renderizar '{component_name}' para Config {config_num}/Exec {exec_num}: {e}")

    def header(self):
        st.markdown("---")
        st.title("⚡ Dashboard Repopulation-With-Elite-Set RCE ⚡")
        st.subheader("Version 15.7.5 - 16/08/2025")
        st.subheader("Artigo Cientifico PIBIC - 28/08/2025")
        st.subheader("Desenvolvido por Pedro Victor Veras e Rainer Zanghi em um projeto PIBIC pela UFF - 2024/2025")
        st.subheader("Apresentação e Resumo UFF - 06/09/2025")
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