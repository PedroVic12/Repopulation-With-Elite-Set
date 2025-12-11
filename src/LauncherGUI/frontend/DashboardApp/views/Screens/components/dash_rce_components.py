# --- Componentes da Interface de Usuário ---
import pickle
import pathlib
import streamlit as st
import os
import pandas as pd
import numpy as np
import re

def reset_path():
    import sys
    import os
    SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    if SRC_PATH not in sys.path:
        sys.path.append(SRC_PATH)

reset_path()
from controllers.Utils import Controller, OPTIONS_JSON

def get_folder_path():
    BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent  
    FOLDER_NAME = BASE_DIR.parent.parent / "output"
    return FOLDER_NAME

path_foler_output = get_folder_path()

class CardSolutions:
    """Componente moderno para exibir o resumo da melhor solução."""

    @staticmethod
    def render(data, exec_num, debug=False):
        st.markdown("""
        <style>
            .metric-card {
                transition: all 0.3s ease;
                margin-bottom: 16px;
                background: white;
                border-radius: 12px;
                padding: 16px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            .metric-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.1) !important;
            }
            .solution-card {
                background: grey;
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 16px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                transition: all 0.3s ease;
            }
            .solution-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.1) !important;
            }
            .var-value {
                font-weight: 600;
                color: #2c3e50;
                font-size: 1rem;

            }
            .var-label {
                font-size: 1rem;
                color: #6c757d;
                margin-bottom: 4px;
            }
        </style>
        """, unsafe_allow_html=True)

        best_gen_idx = data.get('best_gen_idx', 'N/A')
        best_fitness = data.get('best_fitness', float('nan'))
        best_vars = data.get('best_vars', data.get('best_variables', []))
        decision_vars = data.get('decision_vars', {})
        
        fitness_value = f"{float(best_fitness):.2f}" if isinstance(best_fitness, (int, float)) and not pd.isna(best_fitness) else "N/A"
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.metric("🏆 Melhor Fitness", fitness_value)
            st.metric("📊 Melhor Geração", best_gen_idx)

        with col2:
            st.markdown("<h4>Variáveis de Decisão</h4>", unsafe_allow_html=True)
            
            vars_to_display = decision_vars or {}
            if not vars_to_display and isinstance(best_vars, (list, tuple)) and best_vars:
                vars_to_display = {f"VAR {i+1}": val for i, val in enumerate(best_vars)}

            if vars_to_display:
                num_cols = 3
                var_items = list(vars_to_display.items())
                
                for i in range(0, len(var_items), num_cols):
                    cols = st.columns(num_cols)
                    for j in range(num_cols):
                        if i + j < len(var_items):
                            var_name, var_value = var_items[i+j]
                            with cols[j]:
                                formatted_value = f"{float(var_value):.2f}" if isinstance(var_value, (int, float)) else str(var_value)
                                st.markdown(f'''
                                <div class="var-label">{str(var_name).replace('_', ' ').title()}</div>
                                <div class="var-value">{formatted_value}</div>
                                ''', unsafe_allow_html=True)
            else:
                st.info("Nenhuma variável de decisão disponível.")

class StatisticsTableComponent:
    """Componente para exibir a tabela de estatísticas por geração."""
    @staticmethod
    def render(data):
        if data.empty:
            st.info("Não há dados de estatísticas por geração para exibir.")
            return
        try:
            if isinstance(data, pd.DataFrame):
                df = data
            else:
                df = pd.DataFrame(data)
            st.dataframe(df)
        except Exception as e:
            st.error(f"Não foi possível exibir tabela de estatísticas: {e}")