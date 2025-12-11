import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go
from streamlit_timeline import st_timeline

# ==============================================================================
# 1. SIMULAÇÃO DE DADOS (Substituindo o DatabaseController)
# ==============================================================================

def get_scheduling_data():
    """Fornece dados de exemplo para agendamentos."""
    return pd.DataFrame([
        {"ramo": "[1, 4]", "inicio": "14:00", "duracao": 6, "prioridade": 4},
        {"ramo": "[1, 3]", "inicio": "15:00", "duracao": 5, "prioridade": 1},
        {"ramo": "[3, 6]", "inicio": "14:00", "duracao": 6, "prioridade": 1},
        {"ramo": "[11, 12]", "inicio": "18:00", "duracao": 6, "prioridade": 1},
        {"ramo": "[9, 10]", "inicio": "15:00", "duracao": 4, "prioridade": 1}
    ])

def get_contingency_data():
    """Fornece dados de exemplo para contingências."""
    return pd.DataFrame([
        {"contingencia": 1, "from": 2, "to": 3},
        {"contingencia": 2, "from": 5, "to": 12},
        {"contingencia": 3, "from": 12, "to": 13},
    ])

def get_execution_results():
    """Fornece resultados consolidados de exemplo."""
    return pd.DataFrame([
        {"config": 1, "execution": 1, "solution_variables": [3, 11, 1, 18, 31], "best_fitness": 931.71, "best_generations": 1, "execution_time": "15.06s"},
        {"config": 1, "execution": 2, "solution_variables": [30, 1, 14, 30, 9], "best_fitness": 649.91, "best_generations": 6, "execution_time": "6.46s"},
        {"config": 2, "execution": 3, "solution_variables": [30, 17, 30, 30, 9], "best_fitness": 570.33, "best_generations": 11, "execution_time": "5.64s"},
    ])

# ==============================================================================
# 2. COMPONENTES VISUAIS E PÁGINAS
# ==============================================================================

def create_network_diagram():
    """
    Cria uma figura interativa do diagrama de rede usando Plotly.
    
    NOTA: Esta é uma função de exemplo. Você deve substituí-la pela sua
    lógica de geração de gráficos com `pandapower` e `plotly`.
    O importante é que a função retorne um objeto `go.Figure`.
    """
    fig = go.Figure()

    # Posições dos nós (exemplo)
    nodes_x = [0, 1, 1, 2, 2, 3]
    nodes_y = [0, 1, -1, 1, -1, 0]
    node_names = ["Barra 1", "Barra 2", "Barra 3", "Barra 4", "Barra 5", "Barra 6"]

    # Adiciona as linhas de transmissão (arestas)
    edges = [(0, 1), (0, 2), (1, 3), (2, 4), (3, 5), (4, 5)]
    for edge in edges:
        fig.add_trace(go.Scatter(
            x=[nodes_x[edge[0]], nodes_x[edge[1]]],
            y=[nodes_y[edge[0]], nodes_y[edge[1]]],
            mode='lines',
            line=dict(color='gray', width=1),
            hoverinfo='none'
        ))

    # Adiciona os nós (barras)
    fig.add_trace(go.Scatter(
        x=nodes_x,
        y=nodes_y,
        mode='markers+text',
        marker=dict(size=20, color='skyblue', symbol='circle'),
        text=node_names,
        textposition="bottom center",
        hoverinfo="text",
        hovertext=[f"<b>{name}</b><br>Tensão: 1.05 pu" for name in node_names]
    ))

    fig.update_layout(
        title="🔌 Diagrama Unifilar do Sistema (Exemplo)",
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        plot_bgcolor='white',
        margin=dict(l=10, r=10, t=40, b=10)
    )
    return fig

def AgendamentoRedePage(agendamento_df, contingencia_df, exec_data):
    """
    Página que exibe a timeline de agendamento e o diagrama de rede.
    """
    st.header("Análise do Agendamento e da Rede")

    tab1, tab2 = st.tabs(["🗓️ Timeline de Agendamento", "🔌 Diagrama da Rede"])

    with tab1:
        # Lógica da Timeline (código anterior)
        solution_variables = sorted(exec_data["solution_variables"])
        items = []
        base_date = datetime.datetime(2025, 6, 18)

        for j in range(len(solution_variables) - 1):
            start_hour_total = solution_variables[j]
            end_hour_total = solution_variables[j + 1]
            duration = end_hour_total - start_hour_total
            start_datetime = base_date + datetime.timedelta(hours=start_hour_total)
            end_datetime = base_date + datetime.timedelta(hours=end_hour_total)
            start_hour_of_day = start_hour_total % 24
            end_hour_of_day = end_hour_total % 24

            agendamentos_no_intervalo = agendamento_df[
                (agendamento_df["inicio"].apply(lambda x: int(x.split(":")[0])) <= start_hour_of_day) &
                ((agendamento_df["inicio"].apply(lambda x: int(x.split(":")[0])) + agendamento_df["duracao"]) >= end_hour_of_day)
            ]
            ramos_afetados = ", ".join(agendamentos_no_intervalo['ramo'].tolist()) if not agendamentos_no_intervalo.empty else "Nenhum"

            items.append({
                "id": f"{exec_data['execution']}-{j}",
                "content": f"<b>{start_hour_of_day:02d}h - {end_hour_of_day:02d}h</b><br>Ramos: {ramos_afetados}",
                "start": start_datetime.isoformat(),
                "end": end_datetime.isoformat(),
                "title": f"Ramos: {ramos_afetados}"
            })
        
        st_timeline(items, groups=[], options={"height": 300, "stack": False}, key=f"timeline_{exec_data['execution']}")

    with tab2:
        st.subheader("Visualização Interativa da Rede Elétrica")
        st.info("Este é um exemplo. Substitua `create_network_diagram()` pela sua função que usa Pandapower.")
        
        # AQUI: Geramos e exibimos o gráfico Plotly
        figura_rede = create_network_diagram()
        st.plotly_chart(figura_rede, use_container_width=True, key = "diagrama")


# ==============================================================================
# 3. APLICAÇÃO PRINCIPAL
# ==============================================================================

def main():
    st.set_page_config(page_title="Dashboard RCE", layout="wide")
    st.title("Dashboard de Análise de Otimização")

    # Carregar dados (simulados)
    df_consolidado = get_execution_results()
    agendamento_df = get_scheduling_data()
    contingencia_df = get_contingency_data()

    if df_consolidado.empty:
        st.warning("Nenhum resultado encontrado para exibir.")
        return

    # Mapear execuções por configuração
    executions_map = df_consolidado.groupby('config')['execution'].apply(list).to_dict()
    config_keys = sorted(executions_map.keys())
    
    # Criar abas para cada configuração
    config_tabs = st.tabs([f"Configuração {cfg}" for cfg in config_keys])

    for i, tab in enumerate(config_tabs):
        with tab:
            config_num = config_keys[i]
            exec_numbers = executions_map.get(config_num, [])
            
            # Criar abas para cada execução dentro da configuração
            exec_tabs = st.tabs([f"Execução {en}" for en in exec_numbers])
            for j, exec_tab in enumerate(exec_tabs):
                with exec_tab:
                    exec_num = exec_numbers[j]
                    
                    # Filtrar os dados para a execução específica
                    exec_data = df_consolidado[
                        (df_consolidado['config'] == config_num) & 
                        (df_consolidado['execution'] == exec_num)
                    ].iloc[0]
                    
                    st.subheader(f"Detalhes da Execução {exec_num}")
                    cols = st.columns(3)
                    cols[0].metric("Melhor Fitness", f"{exec_data['best_fitness']:.2f}")
                    cols[1].metric("Gerações", exec_data['best_generations'])
                    cols[2].metric("Tempo de Execução", exec_data['execution_time'])
                    
                    st.markdown("---")
                    
                    # Chamar a página/componente de agendamento
                    AgendamentoRedePage(agendamento_df, contingencia_df, exec_data)

if __name__ == "__main__":
    main()
