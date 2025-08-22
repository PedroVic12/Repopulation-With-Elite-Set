import streamlit as st
import sys
import os
import pandas as pd
import json
from pathlib import Path

# Adiciona o diretório raiz do projeto ao sys.path para encontrar o database_controller
# Isso assume que RCE_Framework_Page.py está em src/DashboardApp/views/Screens
try:
    from src.database_controller import DatabaseController
except ImportError:
    # Fallback para o caso de a estrutura de pastas mudar ou o script ser chamado de outro lugar
    sys.path.append(str(Path(__file__).resolve().parents[3]))
    from src.database_controller import DatabaseController

# --- Componentes da UI (mantidos do código original) ---
from .components.dash_rce_components import CardSolutions
from streamlit_timeline import st_timeline

# --- Funções de Carregamento de Dados (Refatoradas) ---

@st.cache_data(ttl=60) # Adiciona cache para performance
def load_consolidated_data(_db_controller: DatabaseController):
    """Carrega os dados do arquivo Excel consolidado."""
    if not _db_controller.consolidated_results_file.exists():
        st.warning(f"Arquivo de resultados consolidados não encontrado em: {_db_controller.consolidated_results_file}")
        st.info("Por favor, execute a consolidação no Launcher para gerar o relatório.")
        return None
    try:
        return pd.read_excel(_db_controller.consolidated_results_file)
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo de resultados consolidados: {e}")
        return None

@st.cache_data(ttl=60)
def load_individual_run_data(_db_controller: DatabaseController, config_num, exec_num, data_type):
    """Carrega dados de um arquivo JSON individual (results ou visualization)."""
    if data_type == "results":
        filename = f"config_{config_num}_exec_{exec_num}_results.json"
    elif data_type == "visualization":
        filename = f"config_{config_num}_exec_{exec_num}_visualization.json"
    else:
        return None

    file_path = _db_controller.output_dir / filename
    if not file_path.exists():
        # Não mostra warning para não poluir a tela, apenas retorna None
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo {file_path}: {e}")
        return None

# --- Classe Principal do Dashboard (Refatorada) ---

class FrameworkRCEDashboard:
    def __init__(self):
        self.db_controller = DatabaseController()

    def run(self):
        st.set_page_config(layout="wide")
        st.title("⚡ Dashboard RCE Framework ⚡")
        st.markdown("--- ")

        df_consolidado = load_consolidated_data(self.db_controller)

        if df_consolidado is None:
            st.stop()

        st.header("✅ Resultados Consolidados")
        st.dataframe(df_consolidado)
        
        available_configs = sorted(df_consolidado['config_num'].unique())
        
        if not available_configs:
            st.info("Nenhuma configuração encontrada nos resultados consolidados.")
            st.stop()

        config_tabs = st.tabs([f"Config {key}" for key in available_configs])

        for i, config_tab in enumerate(config_tabs):
            with config_tab:
                config_num = available_configs[i]
                exec_numbers = sorted(df_consolidado[df_consolidado['config_num'] == config_num]['exec_num'].unique())
                
                if not exec_numbers:
                    st.info("Nenhuma execução encontrada para esta configuração.")
                    continue

                exec_tabs = st.tabs([f"Execução {num}" for num in exec_numbers])
                for j, exec_tab in enumerate(exec_tabs):
                    with exec_tab:
                        exec_num = exec_numbers[j]
                        self.render_execution_details(config_num, exec_num)

    def render_execution_details(self, config_num, exec_num):
        """Renderiza os detalhes (Soluções, Gráfico, etc.) para uma execução específica."""
        results_data = load_individual_run_data(self.db_controller, config_num, exec_num, "results")
        viz_data = load_individual_run_data(self.db_controller, config_num, exec_num, "visualization")

        component_tabs = st.tabs(["Soluções", "Gráfico de Convergência", "Parâmetros"])
        
        with component_tabs[0]:
            if results_data:
                CardSolutions.render(results_data, exec_num, debug=False)
            else:
                st.warning("Dados de solução (results.json) não encontrados.")

        with component_tabs[1]:
            st.subheader("Gráfico de Convergência")
            if viz_data:
                df_viz = pd.DataFrame(viz_data)
                # DEAP logbook keys: gen, nevals, avg, std, min, max
                rename_map = {
                    'gen': 'Generation',
                    'avg': 'Average Fitness',
                    'std': 'Std Deviation',
                    'min': 'Min Fitness (Best)',
                    'max': 'Max Fitness'
                }
                df_viz.rename(columns=rename_map, inplace=True)
                
                chart_cols = [col for col in rename_map.values() if col in df_viz.columns]
                if "Generation" in df_viz.columns and chart_cols:
                    st.line_chart(df_viz, x="Generation", y=chart_cols)
                else:
                    st.warning("Colunas necessárias para o gráfico não encontradas nos dados de visualização.")
            else:
                st.warning("Dados de visualização (visualization.json) não encontrados.")

        with component_tabs[2]:
            st.subheader("Parâmetros Utilizados")
            if results_data and 'params' in results_data:
                st.json(results_data['params'], expanded=False)
            else:
                st.warning("Dados de parâmetros não encontrados.")

# --- Ponto de Entrada ---
# Este arquivo é uma "página" e deve ser chamado por um app Streamlit principal.
# Para testar isoladamente, você pode adicionar:
# if __name__ == "__main__":
#     dashboard = FrameworkRCEDashboard()
#     dashboard.run()