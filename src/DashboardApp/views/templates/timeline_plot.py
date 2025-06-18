import streamlit as st
from streamlit_timeline import st_timeline
import pandas as pd


# Função para carregar os dados de agendamento e contingência
def entrada_de_dados():
    agendamento_df = pd.DataFrame([
        {"ramo": [1, 4], "inicio": "14:00", "duracao": 6, "prioridade": 4},
        {"ramo": [1, 3], "inicio": "15:00", "duracao": 5, "prioridade": 1},
        {"ramo": [3, 6], "inicio": "14:00", "duracao": 6, "prioridade": 1},
        {"ramo": [11, 12], "inicio": "18:00", "duracao": 6, "prioridade": 1},
        {"ramo": [9, 10], "inicio": "15:00", "duracao": 4, "prioridade": 1}
    ])

    contingencia_df = pd.DataFrame([
        {"contingencia": 1, "from": 2, "to": 3},
        {"contingencia": 2, "from": 5, "to": 12},
        {"contingencia": 3, "from": 12, "to": 13},
    ])

    return agendamento_df, contingencia_df

# Função para carregar os dados de execução
def carregar_dados_execucao():
    return pd.DataFrame([
        {"execution": 1, "solution_variables": [3, 11, 1, 18, 31], "best_fitness": 931.7123616, "best_generations": 1, "execution_time": "15.06 segundos"},
        {"execution": 2, "solution_variables": [30, 1, 14, 30, 9], "best_fitness": 649.9070763, "best_generations": 6, "execution_time": "6.46 segundos"},
        {"execution": 3, "solution_variables": [30, 17, 30, 30, 9], "best_fitness": 570.334047, "best_generations": 11, "execution_time": "5.64 segundos"},
        {"execution": 4, "solution_variables": [30, 25, 30, 30, 9], "best_fitness": 479.358067, "best_generations": 15, "execution_time": "6.23 segundos"},
        {"execution": 5, "solution_variables": [30, 25, 30, 30, 9], "best_fitness": 479.358067, "best_generations": 15, "execution_time": "5.60 segundos"},
        {"execution": 6, "solution_variables": [30, 25, 30, 30, 9], "best_fitness": 479.358067, "best_generations": 15, "execution_time": "5.26 segundos"},
    ])

# Função para exibir a página de agendamento de rede elétrica
def AgendamentoRedePage():

    st.title("Agendamento de Rede Elétrica")
    st.write("Esta página exibe os agendamentos de rede elétrica e suas contingências, além de uma timeline interativa com as sugestões de agendamento.")

    # Carregar dados
    agendamento_df, contingencia_df = entrada_de_dados()
    execution_df = carregar_dados_execucao()

    # Exibir tabelas editáveis
    st.subheader("Tabela de Agendamentos")
    edited_agendamento_df = st.data_editor(agendamento_df, use_container_width=True, num_rows="dynamic")

    st.subheader("Tabela de Contingências")
    edited_contingencia_df = st.data_editor(contingencia_df, use_container_width=True, num_rows="dynamic")

    # Converter dados de execução para o formato de timeline
    timeline_items = []
    for index, row in agendamento_df.iterrows():
        start_time = row["inicio"]
        start_hour, start_minute = map(int, start_time.split(":"))
        end_hour = start_hour + row["duracao"]

        mes = 6  # Mês fixo para o exemplo
        dia = 18  # Dia fixo para o exemplo

        timeline_items.append({
            "id": f"agendamento-{index}",
            "content": f"Ramo: {row['ramo']}<br>Prioridade: {row['prioridade']}",
            "start": f"2025-0{mes}-{dia}T{start_hour:02d}:{start_minute:02d}:00",
            "end": f"2025-0{mes}-{dia}T{end_hour:02d}:{start_minute:02d}:00"
        })

    # Exibir timeline
    st.subheader("Timeline da Sugestão Agendamento de Rede Elétrica")
    st.write("Clique em um item para ver os detalhes da execução selecionada.")
    timeline = st_timeline(
        timeline_items,
        groups=[],
        options={
            "selectable": True,
            "multiselect": True,
            "zoomable": True,
            "verticalScroll": True,
            "stack": True,
            "height": 500,
            "margin": {"axis": 5},
            "groupHeightMode": "auto",
            "orientation": {"axis": "top", "item": "top"}
        },
    )

    # Mostrar dados da execução selecionada
    st.subheader("Dados da Execução Selecionada")
    if timeline:
        selected_id = timeline.get("id", "").split("-")[1]
        selected_agendamento = agendamento_df.iloc[int(selected_id)]
        st.json(selected_agendamento.to_dict())

    # Tabs para cada execução
    tabs = st.tabs([f"Execução {row['execution']}" for _, row in execution_df.iterrows()])
    for i, tab in enumerate(tabs):
        with tab:
            exec_data = execution_df.iloc[i]
            with st.container():
                st.write(f"Execução {exec_data['execution']}")
                
                # Tabs dentro do container
                inner_tabs = st.tabs(["Tabela", "Gráfico de Barras", "Gráfico de Linhas"])
                with inner_tabs[0]:
                    st.write("Tabela de Horários de Agendamento")
                    st.dataframe(pd.DataFrame({"Horários de Agendamento": exec_data["solution_variables"]}))

                with inner_tabs[1]:
                    st.write("Gráfico de Barras")
                    st.bar_chart(pd.DataFrame({"Horários de Agendamento": exec_data["solution_variables"]}))

                with inner_tabs[2]:
                    st.write("Gráfico de Linhas")
                    st.line_chart(pd.DataFrame({"Horários de Agendamento": exec_data["solution_variables"]}))

                # Timeline para a execução selecionada
                st.subheader(f"Timeline de Soluções para a Execução {exec_data['execution']}")
                solution_variables = sorted(exec_data["solution_variables"])  # Ordenar os horários
                st.write(solution_variables)
                solution_timeline_items = []
                for j, hour in enumerate(solution_variables):
                    # Calcular o dia e horário
                    day_offset = hour // 24
                    hour_in_day = hour % 24
                    start_time = f"2025-06-{18 + day_offset}T{hour_in_day:02d}:00:00"
                    end_time = f"2025-06-{18 + day_offset}T{(hour_in_day + 5) % 24:02d}:00:00"

                    # Adicionar item à timeline
                    if hour_in_day < 24:
                        # Adiciona apenas se o horário for válido (0-23)
                        pass
                    
                    st.write(f" Horário: {start_time} (Dia {day_offset + 18}) ")
                    st.write(end_time)

                    solution_timeline_items.append({
                        "id": f"{exec_data['execution']}-{j}",
                        "content": f"Ramo: {exec_data['execution']}<br>Horário: {hour}",
                        "start": start_time,
                        "end": end_time   
                    })

                st_timeline(
                    solution_timeline_items,
                    groups=[],
                    options={
                        "selectable": True,
                        "multiselect": True,
                        "zoomable": True,
                        "verticalScroll": True,
                        "stack": True,
                        "height": 500,
                        "margin": {"axis": 5},
                        "groupHeightMode": "auto",
                        "orientation": {"axis": "top", "item": "top"}
                    },
                    key=f"execution_timeline_{exec_data['execution']}"
                )

# Exibir a página
AgendamentoRedePage()