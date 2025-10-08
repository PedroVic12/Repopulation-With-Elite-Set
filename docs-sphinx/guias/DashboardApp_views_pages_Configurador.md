# Configurador.py

```python
import streamlit as st
import json
from pathlib import Path
from functools import reduce
import operator

# --- PARÂMETROS FIXOS DO FRAMEWORK ---
# Estes valores são a base da configuração e não são editados pela UI.
params = {
    "ARRAY_VAR": [14, 15, 14, 18, 15],
    "LIMITE_VAR": [0, 31],
    "IND_SIZE": 5,
    "RCE_REPOPULATION_GENERATIONS": 20,
    "NUM_VAR_DIFERENTES": 1,
    "PORCENTAGEM": 0.2,
    "DELTA_MIN": 2,
    # Os valores abaixo servem como padrão inicial para a UI
    "NUM_GENERATIONS": 10,
    "CROSSOVER": 0.9,
    "MUTACAO": 0.5,
    "POP_SIZE": 10,
}

# --- PARÂMETROS CONFIGURÁVEIS PELO USUÁRIO ---
# Esta é a configuração padrão para os itens que o usuário pode variar.
configuracoes_execucoes = {
    "key": True,
    "value": 10,  # Este será o número de repetições
    "parametros_opcionais": [
        {"MUTACAO": [params['MUTACAO']]},
        {"CROSSOVER": [params['CROSSOVER']]},
        {'NUM_GENERATIONS': [params['NUM_GENERATIONS']]},
        {'POP_SIZE': [params['POP_SIZE']]},
    ]
}

# --- Classe Principal do Configurador de Experimentos ---
class ConfiguradorDeExperimentos:
    """
    Uma classe para gerenciar a criação e edição de configurações
    de experimentos com um layout dinâmico e em colunas.
    """

    def __init__(self):
        """Inicializa o estado da sessão com base na configuração global."""
        if 'user_config' not in st.session_state:
            # Usa uma cópia da configuração padrão para o estado da sessão
            st.session_state.user_config = json.loads(json.dumps(configuracoes_execucoes))

    def run(self):
        """Renderiza a aplicação inteira, incluindo a UI e a lógica de salvamento."""
        st.set_page_config(layout="wide", page_title="Configurador de Experimentos")

        st.markdown("""
            <style>
                div.stCheckbox > label > div.st-bk { transform: scale(1.5); }
            </style>
        """, unsafe_allow_html=True)

        st.title("🛠️ Configurador de Execuções do Framework")
        
        config = st.session_state.user_config

        # --- Seção de Configurações Gerais ---
        with st.expander("Configurações Gerais"):
            config['value'] = st.number_input(
                "Número de Execuções por Configuração",
                min_value=1,
                value=config.get('value', 1),
                help="Quantas vezes cada combinação única de parâmetros será executada."
            )
            st.markdown("---")

            # --- Seção de Parâmetros Evolutivos ---
            st.subheader("Parâmetros Evolutivos")

            # Função auxiliar interna para renderizar o widget de cada parâmetro
            def render_parameter_widget(param_name, index, default_value_from_params):
                param_dict = config['parametros_opcionais'][index]
                current_value = param_dict[param_name]
                
                # O checkbox principal para ativar a configuração
                if st.checkbox(f"Configurar {param_name}?", key=f"config_check_{index}"):
                    
                    # Determina o modo (Fixo ou Variável) com base nos dados atuais
                    mode = "Variável" if isinstance(current_value, list) and len(current_value) > 1 else "Fixo"
                    
                    # Seletor de modo
                    choice = st.radio(
                        "Modo de Configuração:",
                        ("Fixo", "Variável"),
                        index=1 if mode == "Variável" else 0,
                        key=f"radio_{index}",
                        horizontal=True
                    )

                    if choice == "Variável":
                        st.write(f"Valores para {param_name}:")
                        cols = st.columns(4)
                        new_values = []
                        
                        existing_values = current_value if mode == "Variável" else [""]*4
                        
                        for j, col in enumerate(cols):
                            with col:
                                val_str = str(existing_values[j]) if j < len(existing_values) else ""
                                user_input = st.text_input(
                                    f"Valor {j+1}", val_str,
                                    key=f"input_{index}_{j}", label_visibility="collapsed"
                                )
                                if user_input:
                                    try:
                                        # Validação de tipo: INT para Gerações/População, FLOAT para os demais
                                        if param_name in ["NUM_GENERATIONS", "POP_SIZE"]:
                                            value = int(user_input)
                                            new_values.append(value)
                                        else:
                                            value = float(user_input)
                                            new_values.append(round(value, 1)) # Arredonda para 1 casa decimal
                                    except ValueError:
                                        expected_type = "inteiro" if param_name in ["NUM_GENERATIONS", "POP_SIZE"] else "decimal"
                                        st.error(f"'{user_input}' não é um número {expected_type} válido.", icon="⚠️")
                        
                        if not new_values:
                            st.warning(f"Preencha pelo menos um valor para '{param_name}' quando o modo 'Variável' está selecionado.")
                        
                        config['parametros_opcionais'][index] = {param_name: new_values or [default_value_from_params]}

                    else: # choice == "Fixo"
                        default_value = current_value[0] if isinstance(current_value, list) else current_value
                        
                        if param_name in ["NUM_GENERATIONS", "POP_SIZE"]:
                            new_single_value = st.number_input(
                                f"Valor para {param_name}",
                                value=int(default_value), step=1, key=f"single_input_{index}", format="%d"
                            )
                        else:
                            new_single_value = st.number_input(
                                f"Valor para {param_name}",
                                value=float(default_value), step=0.1, key=f"single_input_{index}", format="%.1f"
                            )
                        config['parametros_opcionais'][index] = {param_name: [new_single_value]}
                
                st.markdown("---")

            col1, col2 = st.columns(2)
            with col1:
                render_parameter_widget("MUTACAO", 0, params["MUTACAO"])
                render_parameter_widget("CROSSOVER", 1, params["CROSSOVER"])
            with col2:
                render_parameter_widget("NUM_GENERATIONS", 2, params["NUM_GENERATIONS"])
                render_parameter_widget("POP_SIZE", 3, params["POP_SIZE"])

            # --- Seção de Resumo ---
            st.subheader("Quantidade de Execuções Configuradas")
            num_variations = [len(v) for p in config['parametros_opcionais'] for k, v in p.items() if isinstance(v, list) and len(v) > 1 and v]
            total_combinations = reduce(operator.mul, num_variations, 1) if num_variations else 1
            total_execucoes = total_combinations * config.get('value', 1)

            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric(
                    label="Configurações Únicas", value=total_combinations,
                    help="O número total de combinações diferentes de parâmetros que serão testadas."
                )
            with metric_col2:
                st.metric(label="Total de Execuções", value=total_execucoes)

            # --- Botão para Salvar ---
            if st.button("Salvar Configuração em Arquivo", type="primary"):
                try:
                    final_config = {**params, **st.session_state.user_config}
                    optional_params_dict = {k: v for d in final_config.pop('parametros_opcionais') for k, v in d.items()}
                    final_config.update(optional_params_dict)

                    if 'value' in final_config:
                        final_config['repeticoes_por_config'] = final_config.pop('value')
                    
                    final_config.pop('key', None)

                    config_str = json.dumps(final_config, indent=4)
                    Path("params.json").write_text(config_str, encoding="utf-8")
                    
                    st.success("Configuração salva com sucesso em **params.json**!")
                    st.code(config_str, language="json")
                except Exception as e:
                    st.error(f"Ocorreu um erro ao salvar o arquivo: {e}")

# --- Ponto de Entrada da Aplicação ---
if __name__ == "__main__":
    app = ConfiguradorDeExperimentos()
    app.run()

```