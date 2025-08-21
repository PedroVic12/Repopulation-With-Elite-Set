import streamlit as st

# --- Componentes da Interface de Usuário ---
import sys

# Frontend
import os
import re
import pandas as pd
import io
import json

from dash_rce_components import CardSolutions, GraficoPotenciaAtivaReativaComponent, StatisticsTableComponent, GraficoRCEComponent
from .AgendamentoRedePage import AgendamentoRedePage

#backend
from controllers.Utils import Controller, Utils, ConfigController


def find_available_executions_replacement(output_dir):
    executions = {}
    warnings = []
    
    output_path = os.path.abspath(output_dir)

    if not os.path.isdir(output_path):
        warnings.append(f"Diretório de output não encontrado: {output_path}")
        return executions, warnings

    for run_dir in os.listdir(output_path):
        run_path = os.path.join(output_path, run_dir)
        if os.path.isdir(run_path) and run_dir.startswith("run_"):
            for config_dir in os.listdir(run_path):
                config_path = os.path.join(run_path, config_dir)
                if os.path.isdir(config_path) and config_dir.startswith("config_"):
                    config_num_match = re.search(r'config_(\d+)', config_dir)
                    if not config_num_match:
                        continue
                    config_num = int(config_num_match.group(1))
                    
                    if config_num not in executions:
                        executions[config_num] = []

                    for result_file in os.listdir(config_path):
                        if result_file.endswith("_results.json"):
                            exec_num_match = re.search(r'exec_(\d+)_results.json', result_file)
                            if exec_num_match:
                                exec_num = int(exec_num_match.group(1))
                                if exec_num not in executions[config_num]:
                                    executions[config_num].append(exec_num)
    for config_num in executions:
        executions[config_num].sort()
        
    return executions, warnings

def load_data_for_component(config_num, exec_num, data_type):
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'output'))
    
    run_dirs = [d for d in os.listdir(output_path) if d.startswith("run_") and os.path.isdir(os.path.join(output_path, d))]
    run_dirs.sort(reverse=True)

    if not run_dirs:
        return None, None

    file_suffix = "results.json" if data_type == "results" else "visualization.json"

    for run_dir in run_dirs:
        file_path = os.path.join(run_dir, f"config_{config_num}", f"config_{config_num}_exec_{exec_num}_{file_suffix}")
        full_path = os.path.join(output_path, file_path)
        
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r') as f:
                    data = json.load(f)
                return data, None
            except Exception as e:
                st.error(f"Erro ao carregar o arquivo de dados {full_path}: {e}")
                return None, None
    
    return None, None

class ConsolidatedResultsComponent:
    """Componente para exibir os resultados consolidados."""
    
    @staticmethod
    def render(all_params: dict):
        """Coleta, consolida e exibe os resultados de todas as execuções."""
        st.header("✅ Resultados Consolidados Gerais")

        output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'output'))
        all_results = []
        warnings = []

        run_dirs = [d for d in os.listdir(output_path) if d.startswith("run_") and os.path.isdir(os.path.join(output_path, d))]

        if not run_dirs:
            st.info("Nenhum diretório de execução (run_*) foi encontrado.")
            return None, []

        for run_dir in run_dirs:
            run_path = os.path.join(output_path, run_dir)
            for config_dir in os.listdir(run_path):
                if config_dir.startswith("config_"):
                    config_path = os.path.join(run_path, config_dir)
                    for result_file in os.listdir(config_path):
                        if result_file.endswith("_results.json"):
                            match = re.search(r"config_(\d+)_exec_(\d+)_results.json", result_file)
                            if not match:
                                warnings.append(f"Nome de arquivo inválido, não foi possível processar: {result_file}")
                                continue
                            
                            config_num = int(match.group(1))
                            exec_num = int(match.group(2))

                            try:
                                with open(os.path.join(config_path, result_file), "r") as f:
                                    exec_data = json.load(f)
                                
                                params_data = all_params.get(config_num, {})
                                
                                all_results.append({
                                    "Config": config_num,
                                    "Exec": exec_num,
                                    "Melhor Fitness": exec_data.get("best_fitness"),
                                    "Melhor Geração": exec_data.get("best_gen_idx"),
                                    "Tempo de Execução (s)": exec_data.get("execution_time", 0.0),
                                    "Caso IEEE": params_data.get("ieee_case", "N/A"),
                                    "MUTACAO": params_data.get("MUTACAO"),
                                    "CROSSOVER": params_data.get("CROSSOVER"),
                                    "NUM_GENERATIONS": params_data.get("NUM_GENERATIONS"),
                                    "POP_SIZE": params_data.get("POP_SIZE"),
                                })
                            except Exception as e:
                                warnings.append(f"Erro ao ler o arquivo de dados {result_file}: {e}")
                                continue
        
        if not all_results:
            st.warning("Nenhum dado de execução pôde ser consolidado.")
            return None, warnings

        df_consolidado = pd.DataFrame(all_results)
        return df_consolidado, warnings

    @staticmethod
    def display_and_download(df_consolidado):
        """Exibe o DataFrame e o botão de download."""
        
        column_order = [
            "Config", "Exec", "MUTACAO", "CROSSOVER", 
            "NUM_GENERATIONS", "POP_SIZE", "Melhor Fitness", "Melhor Geração", 
            "Tempo de Execução (s)"
        ]
        existing_columns = [col for col in column_order if col in df_consolidado.columns]
        df_display = df_consolidado[existing_columns]
        
        st.dataframe(df_display)

        if "Tempo de Execução (s)" in df_display.columns and df_display["Tempo de Execução (s)"].sum() > 0:
            total_time = df_display["Tempo de Execução (s)"].sum()
            mean_time = df_display["Tempo de Execução (s)"].mean()
            
            col1, col2 = st.columns(2)
            col1.metric("Tempo Total de Execução", f"{total_time:.2f} s")
            col2.metric("Tempo Médio por Execução", f"{mean_time:.2f} s")

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
        if st.sidebar.button("Atualizar a tela"):
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
        
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'output')
        self.executions, self.warnings = find_available_executions_replacement(output_path)
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

            self.show_config_parameters()

            if not self.executions:
                st.info("Nenhuma execução encontrada. Execute o framework para gerar resultados.")
                st.stop()

            config_controller = ConfigController()
            all_params = config_controller.repository.get_all_configs()
            
            df_consolidado, cons_warnings = ConsolidatedResultsComponent.render(all_params)
            if cons_warnings:
                for w in cons_warnings:
                    st.warning(w)
            if df_consolidado is not None:
                st.session_state['df_consolidado'] = df_consolidado
                ConsolidatedResultsComponent.display_and_download(df_consolidado)

                try:
                    available_execs = {}
                    for cfg in sorted(df_consolidado['Config'].unique()):
                        execs_list = sorted(df_consolidado[df_consolidado['Config'] == cfg]['Exec'].unique().tolist())
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
                except Exception as e:
                    st.error(f"Erro ao processar resultados consolidados: {e}")

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

        config_keys = list(self.executions.keys())
        config_tabs = st.tabs([f"Config {key}" for key in config_keys])

        for i, config_tab in enumerate(config_tabs):
            with config_tab:
                config_num = config_keys[i]
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
        component_options = ["Soluções", "Gráfico de Convergência", "Estatísticas"]
        locked_component_key = f"locked_component_{config_num}"
        locked_exec_key = f"locked_exec_{config_num}"
        
        UseState.initialize_state(locked_component_key, component_options[0])
        UseState.initialize_state(locked_exec_key, exec_numbers[0])
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
            try:
                idx_exec = exec_numbers.index(UseState.get_state(locked_exec_key))
            except ValueError:
                idx_exec = 0
            selected_exec = st.selectbox("Selecione a Execução", exec_numbers,
                index=idx_exec,
                key=f"select_exec_{config_num}")
            UseState.set_state(locked_exec_key, selected_exec)
            
        st.info(f"Mostrando **{selected_component}** para a **Execução {selected_exec}** da **Configuração {config_num}**")

        results_data, _ = load_data_for_component(config_num, selected_exec, "results")
        viz_data, _ = load_data_for_component(config_num, selected_exec, "visualization")

        if selected_component == "Soluções":
            self.render_component("Soluções", results_data, config_num, selected_exec)
        elif selected_component == "Gráfico de Convergência":
            self.render_component("Gráfico", viz_data, config_num, selected_exec)
        elif selected_component == "Estatísticas":
            self.render_component("Estatísticas", viz_data, config_num, selected_exec)

    def render_dynamic_view(self, config_num, exec_numbers):
        exec_tabs = st.tabs([f"Execução {num}" for num in exec_numbers])
        for j, exec_tab in enumerate(exec_tabs):
            with exec_tab:
                exec_num = exec_numbers[j]
                
                component_tabs = st.tabs(["Soluções", "Gráfico de Convergência", "Estatísticas"])
                with component_tabs[0]:
                    results_data, _ = load_data_for_component(config_num, exec_num, "results")
                    self.render_component("Soluções", results_data, config_num, exec_num)

                with component_tabs[1]:
                    viz_data, _ = load_data_for_component(config_num, exec_num, "visualization")
                    self.render_component("Gráfico", viz_data, config_num, exec_num)

                with component_tabs[2]:
                    viz_data, _ = load_data_for_component(config_num, exec_num, "visualization")
                    self.render_component("Estatísticas", viz_data, config_num, exec_num)

    def render_component(self, component_name, data, config_num, exec_num):
        try:
            if component_name == "Soluções":
                if data:
                    st.subheader(f"Melhor Solução Encontrada - Config {config_num} / Exec {exec_num}")
                    CardSolutions.render(data, exec_num, debug=False)
                else:
                    st.warning(f"Dados de solução não encontrados para Config {config_num} / Exec {exec_num}.")
                
            elif component_name == "Gráfico":
                st.subheader(f"Gráfico de Convergência - Config {config_num} / Exec {exec_num}")
                if data:
                    df = pd.DataFrame(data)
                    if not df.empty:
                        chart_data = df.rename(columns={'Media': 'Média', 'Desvio Padrao': 'Desvio Padrão'})
                        
                        colors = {
                            'Fitness': '#1f77b4',  # Azul
                            'Média': '#ff7f0e',    # Laranja
                            'Desvio Padrão': '#2ca02c' # Verde
                        }
                        
                        st.line_chart(chart_data, x="Generations", y=["Fitness", "Média", "Desvio Padrão"], color=[colors[col] for col in ["Fitness", "Média", "Desvio Padrão"]])
                    else:
                        st.warning("Dados de visualização vazios.")
                else:
                    st.warning("Dados de visualização não encontrados.")
                
            elif component_name == "Estatísticas":
                st.subheader(f"Estatísticas por Geração - Config {config_num} / Exec {exec_num}")
                if data:
                    st.dataframe(pd.DataFrame(data))
                else:
                    st.warning("Dados de estatísticas não encontrados.")
                
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