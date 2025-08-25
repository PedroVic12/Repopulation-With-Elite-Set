import streamlit as st
import pandas as pd

class CardSolutions:
    """Componente moderno para exibir o resumo da melhor solução."""

    @staticmethod
    def _get_progress_color(progress):
        if progress < 0.3:
            return "#ff4b4b"
        elif progress < 0.7:
            return "#f4c430"
        return "#2ecc71"

    @staticmethod
    def create_metric_card(title, value, icon, color, progress=None):
        if progress is not None:
            progress_color = CardSolutions._get_progress_color(progress)
            progress_bar = f'''
            <div style="background: #e0e0e0; border-radius: 5px; height: 6px; margin-top: 8px;">
                <div style="background: {progress_color}; width: {progress*100}%; height: 100%; border-radius: 5px;"></div>
            </div>
            '''
        else:
            progress_bar = ""
            
        return f'''
        <div style="
            background: white;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            height: 100%;
        ">
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <div style="background: {color}20; color: {color}; width: 40px; height: 40px; 
                    border-radius: 8px; display: flex; align-items: center; justify-content: center; 
                    margin-right: 12px;">
                    <span style="font-size: 20px;">{icon}</span>
                </div>
                <div>
                    <div style="font-size: 12px; color: #666; font-weight: 500;">{title}</div>
                    <div style="font-size: 18px; font-weight: 600; color: #2c3e50;">{value}</div>
                </div>
            </div>
            {progress_bar}
        </div>
        '''

    @staticmethod
    def render(data, exec_num, debug=False):
        st.markdown("""
        <style>
            .metric-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.1) !important;
            }
            .solution-card {
                background: white;
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 16px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            .var-value {
                font-weight: 600;
                color: #2c3e50;
            }
            .var-label {
                font-size: 0.8rem;
                color: #6c757d;
                margin-bottom: 4px;
            }
        </style>
        """, unsafe_allow_html=True)

        st.markdown(f'''
        <div style="margin-bottom: 24px;">
            <h2 style="margin: 0; color: #2c3e50; font-weight: 700; font-size: 1.5rem;">
                Execução #{exec_num}
            </h2>
            <p style="margin: 0; color: #6c757d; font-size: 0.9rem;">
                Análise detalhada dos resultados
            </p>
        </div>
        ''', unsafe_allow_html=True)

        best_gen_idx = data.get('best_gen_idx', 'N/A')
        best_fitness = data.get('best_fitness', float('nan'))
        num_generations = data.get('params', {}).get('NUM_GENERATIONS', 100)
        
        fitness_value = f"{float(best_fitness):.4f}" if isinstance(best_fitness, (int, float)) and not pd.isna(best_fitness) else "N/A"
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown(CardSolutions.create_metric_card("Melhor Geração", best_gen_idx, "📊", "#3498db"), unsafe_allow_html=True)
            st.markdown(CardSolutions.create_metric_card("Melhor Fitness", fitness_value, "🏆", "#2ecc71"), unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="solution-card" style="height: 100%;">', unsafe_allow_html=True)
            st.markdown("<h6>Variáveis de Decisão</h6>", unsafe_allow_html=True)
            
            vars_to_display = data.get('decision_vars', {})
            if not vars_to_display:
                best_vars_list = data.get('best_variables', [])
                if isinstance(best_vars_list, (list, tuple)) and best_vars_list:
                    vars_to_display = {f"VAR {i+1}": val for i, val in enumerate(best_vars_list)}

            if vars_to_display:
                num_cols = 3
                var_items = list(vars_to_display.items())
                
                for i in range(0, len(var_items), num_cols):
                    cols = st.columns(num_cols)
                    for j in range(num_cols):
                        if i + j < len(var_items):
                            var_name, var_value = var_items[i+j]
                            with cols[j]:
                                formatted_value = f"{float(var_value):.4f}" if isinstance(var_value, (int, float)) else str(var_value)
                                st.markdown(f'''
                                <div class="var-label">{str(var_name).replace('_', ' ').title()}</div>
                                <div class="var-value">{formatted_value}</div>
                                ''', unsafe_allow_html=True)
            else:
                st.info("Nenhuma variável de decisão disponível.")
            
            st.markdown("</div>", unsafe_allow_html=True)
