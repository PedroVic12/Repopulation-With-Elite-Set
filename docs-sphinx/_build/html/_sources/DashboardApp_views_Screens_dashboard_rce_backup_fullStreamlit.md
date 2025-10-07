# dashboard_rce_backup_fullStreamlit.py

```python
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import numpy as np
import json
import os
from functools import reduce
import operator
import streamlit.components.v1 as components

# Assuming these components are in the same directory or accessible via sys.path
# Adjust imports if components are in different subdirectories
from components.dash_rce_components import CardSolutions, StatisticsTableComponent
from components.AgendamentoRedePage import AgendamentoRedePage


# --- Add root directory to path to find modules ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
print(BASE_DIR)

# --- Import Controllers and Components ---
from database_controller import DatabaseController
from controllers.Utils import Controller, FOLDER_NAME, Utils, PARAMETROS_JSON
from controllers.ConfigRepository import ConfigRepository


# --- Helper for Streamlit State Management ---
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

# --- IEEE Network Visualization Helper ---
CURRENT_DIR = os.path.dirname(__file__)
def rede_template_view(html_path: str | None = None, height: int = 1200):
    if html_path is None:
        html_path = os.path.join(CURRENT_DIR, "plot_rede_IEEE_template_dashboard.html") # Assuming this file exists

    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    except FileNotFoundError:
        st.error(f"HTML file not found: {os.path.abspath(html_path)}")
        st.info("Please create the file or provide a valid path.")
        return
    except Exception as e:
        st.error(f"Error reading HTML file: {e}")
        return
    components.html(html_content, height=height, scrolling=True)

# --- Unified Dashboard Class ---
class UnifiedDashboard:
    def __init__(self):
        st.set_page_config(page_title="Unified RCE Framework Dashboard", page_icon="⚡", layout="wide")
        self.db_controller = DatabaseController(base_dir=BASE_DIR)
        self.utils = Utils() # From controllers.Utils
        self._init_state()

    def _init_state(self):
        UseState.initialize_state("df_consolidado", self.db_controller.get_consolidated_data())
        UseState.initialize_state("executions_map", self._get_executions_map())
        UseState.initialize_state("locked_config", None)
        UseState.initialize_state("selected_config", None)
        UseState.initialize_state("selected_exec", None)
        UseState.initialize_state("selected_pair", None) # For UI_Gradiente_RCE_SCREEN style tabs

        # Validate and set config/exec columns if df_consolidado exists
        df = UseState.get_state("df_consolidado")
        if df is not None and not df.empty:
            config_col, exec_col = self._validate_required_columns(df)
            UseState.set_state("config_col", config_col)
            UseState.set_state("exec_col", exec_col)
        else:
            UseState.set_state("config_col", None)
            UseState.set_state("exec_col", None)

        # Set initial selected pair if available
        if UseState.get_state("selected_pair") is None:
            first_pair = None
            executions_map = UseState.get_state("executions_map")
            for cfg, execs in executions_map.items():
                if execs:
                    first_pair = (cfg, execs[0])
                    break
            if first_pair is not None:
                UseState.set_state("selected_pair", first_pair)

    def _get_column_name_insensitive(self, df, possible_names):
        df_columns = [str(col).lower().strip() for col in df.columns]
        for name in possible_names:
            if name.lower() in df_columns:
                return df.columns[df_columns.index(name.lower())]
        return None

    def _validate_required_columns(self, df):
        config_col_names = ['config_num', 'config', 'configuration', 'configuracao', 'configuração']
        exec_col_names = ['exec_num', 'exec', 'execution', 'run', 'execucao', 'execução']
        config_col = self._get_column_name_insensitive(df, config_col_names)
        exec_col = self._get_column_name_insensitive(df, exec_col_names)
        return config_col, exec_col

    def _get_executions_map(self) -> dict:
        df = UseState.get_state("df_consolidado")
        if df is None or df.empty: return {}
        config_col, exec_col = self._validate_required_columns(df)
        if not config_col or not exec_col:
            st.error("The consolidated file does not contain the configuration or execution columns.")
            return {}

        df[config_col] = df[config_col].astype(str)
        df[exec_col] = df[exec_col].astype(str)
        return df.groupby(config_col)[exec_col].apply(lambda x: sorted(x.unique())).to_dict()

    def render_header(self):
        st.title("⚡ Unified RCE Framework Dashboard ⚡")
        st.markdown("Explore the results of the evolutionary algorithm executions.")

    def render_footer(self):
        st.markdown("---")
        st.info("Developed by Pedro Victor Veras and Rainer Zanghi in a PIBIC project by UFF - 2024/2025")
        st.link_button(
            url="https://github.com/PedroVic12/Repopulation-With-Elite-Set",
            label="Visit the Project Documentation",
            type="primary",
            icon="📖",
        )
        st.markdown("---")

    def render_execution_details(self, config_num, exec_num):
        results_data = self.db_controller.get_run_data(config_num, exec_num) or {}
        viz_data = self.db_controller.get_visualization_data(config_num, exec_num)
        df_consolidado = UseState.get_state("df_consolidado")

        if df_consolidado is not None:
            config_col = UseState.get_state("config_col")
            exec_col = UseState.get_state("exec_col")
            if config_col and exec_col:
                row = df_consolidado[(df_consolidado[config_col].astype(str) == str(config_num)) & (df_consolidado[exec_col].astype(str) == str(exec_num))]
                if not row.empty:
                    results_data.update(row.iloc[0].to_dict())

        if not results_data.get('best_variables') and results_data:
            var_keys = sorted([k for k in results_data if str(k).startswith('best_var_')], key=lambda x: int(str(x).split('_')[-1]))
            if var_keys:
                best_vars_list = [results_data[k] for k in var_keys]
                results_data['best_variables'] = best_vars_list
                results_data['decision_vars'] = {f'VAR {i+1}': v for i, v in enumerate(best_vars_list)}

        tab1, tab2, tab3, tab4 = st.tabs(["Solution", "Convergence Graph", "Statistics", "Scheduling"])

        with tab1:
            st.subheader("Solution Details")
            CardSolutions.render(results_data, exec_num)
            st.markdown("---")
            st.subheader("Electrical Network Scheduling")
            AgendamentoRedePage(key_prefix=f"agend_{config_num}_{exec_num}", selected_exec=exec_num, solution_vars=results_data.get('best_variables'))

        with tab2:
            st.subheader("Convergence Graph")
            if viz_data:
                try:
                    df_viz = pd.DataFrame(viz_data)
                    if 'gen' in df_viz.columns:
                        stats_df = df_viz.rename(columns={'gen': 'Generation', 'avg': 'Average', 'min': 'Min', 'max': 'Max'})
                        st.line_chart(stats_df, x='Generation', y=['Average', 'Min', 'Max'])
                    elif 'Generations' in df_viz.columns:
                        stats_df = df_viz.groupby('Generations')['Fitness'].agg(['mean', 'min', 'max']).reset_index()
                        stats_df = stats_df.rename(columns={'Generations': 'Generation', 'mean': 'Average', 'min': 'Min', 'max': 'Max'})
                        st.line_chart(stats_df, x='Generation', y=['Average', 'Min', 'Max'])
                except Exception as e:
                    st.error(f"Error rendering graph: {e}")
            else:
                st.warning("Visualization data not available.")

        with tab3:
            st.subheader("Statistics Table")
            StatisticsTableComponent.render(viz_data)

        with tab4:
            st.warning("Final Population not implemented in this visualization.")

    def run(self):
        self.render_header()

        executions_map = UseState.get_state("executions_map")
        if not executions_map:
            st.warning("No consolidated results found. Please run the consolidation via the Launcher.")
            self.render_footer()
            return

        # --- Tab management inspired by RCE_Framework_Page and UI_Gradiente_RCE_SCREEN ---
        # This section combines the "locked config" and nested tab logic.

        # Option to lock a configuration view
        locked_config = UseState.get_state("locked_config")
        if locked_config:
            if st.button(f"🔓 Unlock Configuration {locked_config}"):
                UseState.set_state("locked_config", None)
                st.rerun()

            st.header(f"Configuration {locked_config} (Locked)")
            exec_numbers = executions_map.get(locked_config, [])
            exec_tabs = st.tabs([f"Execution {en}" for en in exec_numbers])
            for j, exec_tab in enumerate(exec_tabs):
                with exec_tab:
                    self.render_execution_details(locked_config, exec_numbers[j])
        else:
            config_keys = sorted(executions_map.keys())
            config_tabs = st.tabs([f"Config {cfg}" for cfg in config_keys])

            for i, tab in enumerate(config_tabs):
                with tab:
                    config_num = config_keys[i]
                    if st.button(f"📌 Lock Configuration {config_num}", key=f"pin_{config_num}"):
                        UseState.set_state("locked_config", config_num)
                        st.rerun()

                    exec_numbers = executions_map.get(config_num, [])
                    exec_tabs = st.tabs([f"Execution {en}" for en in exec_numbers])
                    for j, exec_tab in enumerate(exec_tabs):
                        with exec_tab:
                            self.render_execution_details(config_num, exec_numbers[j])

        # --- Consolidated Results Table ---
        with st.expander("View Consolidated Results Table", expanded=False):
            df_consolidado = UseState.get_state("df_consolidado")
            if df_consolidado is not None and not df_consolidado.empty:
                st.dataframe(df_consolidado)
            else:
                st.warning("Consolidated results file not found.")

        # --- IEEE Network Visualization ---
        st.markdown("---")
        st.subheader("🕸️ IEEE Network Visualization (Embedded HTML)")
        rede_template_view() # Renders the HTML file

        self.render_footer()

if __name__ == "__main__":
    page = UnifiedDashboard()
    page.run()

```