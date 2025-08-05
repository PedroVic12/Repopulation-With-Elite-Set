import streamlit as st
from streamlit_timeline import st_timeline
import pandas as pd
import pathlib
import numpy as np

output_xlsx_file = pathlib.Path(__file__).resolve().parent.parent.parent.parent /  "output" / "results_consolidados.xlsx" # Importando o caminho do diretório de configuração
pop_final_xlsx_file = pathlib.Path(__file__).resolve().parent.parent.parent.parent /  "output" / "pop_final.xlsx" # Importando o caminho do diretório de configuração


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
    ])
    
    
def time_line_from_solution_variables(agendamento_df,contingencia_df ,exec_data):
    # Timeline para a execução selecionada
    st.subheader(f"Timeline de Soluções para a Execução {exec_data['execution']}")
    solution_variables = sorted(exec_data["solution_variables"])  # Ordenar os horários
    solution_timeline_items = []

    # Calcular os intervalos entre os horários
    for j in range(len(solution_variables)):
        start_hour = solution_variables[j]
        duration = agendamento_df.iloc[j]["duracao"]  # pega a duração do agendamento correspondente
        end_hour = start_hour + duration

        # Calcular o dia e horário
        day_offset_start = start_hour // 24
        hour_in_day_start = start_hour % 24
        day_offset_end = end_hour // 24
        hour_in_day_end = end_hour % 24

        # Ajustar exibição para o dia seguinte, se necessário
        start_label = f"{hour_in_day_start:02d}h"
        end_label = f"{hour_in_day_end:02d}h{'*' if day_offset_end > day_offset_start else ''}"

        start_time = f"2025-06-{18 + day_offset_start}T{hour_in_day_start:02d}:00:00"
        end_time = f"2025-06-{18 + day_offset_end}T{hour_in_day_end:02d}:00:00"

        solution_timeline_items.append({
            "id": f"{exec_data['execution']}-{j}",
            "content": f"Horário: {start_label} - {end_label} ({duration}h)",
            "start": start_time,
            "end": end_time,
            "title": f"Intervalo: {start_label} - {end_label} ({duration}h)"
        })
        
        
    # Adicionar o último horário como um evento único
    last_hour = solution_variables[-1]
    day_offset_last = last_hour // 24
    hour_in_day_last = last_hour % 24
    last_start_time = f"2025-06-{18 + day_offset_last}T{hour_in_day_last:02d}:00:00"
    last_end_time = f"2025-06-{18 + day_offset_last}T{(hour_in_day_last + 1) % 24:02d}:00:00"

    solution_timeline_items.append({
        "id": f"{exec_data['execution']}-last",
        "content": f"Horário: {hour_in_day_last:02d}h",
        "start": last_start_time,
        "end": last_end_time,
        "title": f"Horário: {hour_in_day_last:02d}h"
    })

    timeline = st_timeline(
        solution_timeline_items,
        groups=[],
        options={
            "selectable": True,
            "multiselect": True,
            "zoomable": True,
            "verticalScroll": True,
            "stack": True,
            "height": 300,
            "margin": {"axis": 5},
            "groupHeightMode": "auto",
            "orientation": {"axis": "top", "item": "top"}
        },
        key=f"execution_timeline_{exec_data['execution']}"
    )

    # Mostrar detalhes da execução ao clicar no timeline
    if timeline:
        selected_id = timeline.get("id", "").split("-")[1]  # Obter o ID do item selecionado no timeline
        selected_index = int(selected_id) if selected_id.isdigit() else None

        if selected_index is not None and selected_index < len(solution_variables) - 1:
            # Dados do intervalo selecionado
            start_hour = solution_variables[selected_index]
            end_hour = solution_variables[selected_index + 1]
            duration = end_hour - start_hour

            # Calcular o dia e horário
            day_offset_start = start_hour // 24
            hour_in_day_start = start_hour % 24
            day_offset_end = end_hour // 24
            hour_in_day_end = end_hour % 24

            start_label = f"{hour_in_day_start:02d}h"
            end_label = f"{hour_in_day_end:02d}h{'*' if day_offset_end > day_offset_start else ''}"

            # Dados relacionados ao agendamento
            related_agendamentos = agendamento_df[
                (agendamento_df["inicio"].apply(lambda x: int(x.split(":")[0])) <= hour_in_day_start) &
                ((agendamento_df["inicio"].apply(lambda x: int(x.split(":")[0])) + agendamento_df["duracao"]) >= hour_in_day_end)
            ]

            # Dados relacionados às contingências
            related_contingencies = contingencia_df[
                (contingencia_df["from"] <= start_hour) & (contingencia_df["to"] >= end_hour)
            ]

            # Exibir os detalhes
            st.subheader("Detalhes do Intervalo Selecionado")
            st.json({
                "Intervalo": f"{start_label} - {end_label} ({duration}h)",
                "Agendamentos Relacionados": related_agendamentos.to_dict(orient="records"),
                "Contingências Relacionadas": related_contingencies.to_dict(orient="records")
            })
        else:
            st.warning("Selecione um intervalo válido no timeline.")


# Função para exibir a página de agendamento de rede elétrica
def AgendamentoRedePage():

    st.title("Agendamento de Intervenções de Redes Elétricas")
    st.write("Esta página exibe os agendamentos de rede elétrica e suas contingências, além de uma timeline interativa com as sugestões de agendamento.")

    # Carregar dados
    agendamento_df, contingencia_df = entrada_de_dados()
    
    # Tente carregar do Excel, se falhar, use os dados mockados
    try:
        execution_df = pd.read_excel(output_xlsx_file)
        # Converter a coluna 'solution_variables' de string para lista, se necessário
        if 'solution_variables' in execution_df.columns and isinstance(execution_df['solution_variables'].iloc[0], str):
            import ast
            execution_df['solution_variables'] = execution_df['solution_variables'].apply(ast.literal_eval)
    except Exception as e:
        st.warning(f"Erro ao carregar do Excel: {e}. Usando dados hardcoded com 5 execucões.")
        execution_df = carregar_dados_execucao()

    # Exibir tabelas editáveis
    with st.expander("Editar Agendamentos e Contingências", expanded=True):
        st.subheader("Tabela de Agendamentos")
        edited_agendamento_df = st.data_editor(
            agendamento_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={},
        )
        st.markdown("---")
        st.info("Edite os agendamentos e contingências conforme necessário. As alterações serão salvas automaticamente.")
        st.subheader("Tabela de Contingências")
        edited_contingencia_df = st.data_editor(contingencia_df, use_container_width=True, num_rows="dynamic")

    # st.subheader("Tabela de Agendamentos")
    # edited_agendamento_df = st.data_editor(
    #     agendamento_df,
    #     use_container_width=True,
    #     num_rows="dynamic",
    #     column_config={},
    # )

    #st.subheader("Tabela de Contingências")
    #edited_contingencia_df = st.data_editor(contingencia_df, use_container_width=True, num_rows="dynamic")

    # Converter dados de execução para o formato de timeline
    timeline_items = []
    for index, row in agendamento_df.iterrows():
        start_time = row["inicio"]
        # Corrigir para garantir que start_time seja uma string antes de usar split
        if isinstance(start_time, (list, tuple, pd.Series, np.ndarray)):
            # Se for array, pega o primeiro elemento (ou ajusta conforme necessário)
            start_time = start_time[0]
        start_time = str(start_time)
        try:
            start_hour, start_minute = map(int, start_time.split(":"))
        except Exception:
            # Caso o formato não seja esperado, define valores padrão ou pula
            start_hour, start_minute = 0, 0
        end_hour = start_hour + row["duracao"]

        mes = 6  # Mês fixo para o exemplo
        dia = 18  # Dia fixo para o exemplo

        timeline_items.append({
            "id": f"agendamento-{index}",
            "content": f"Ramo: {row['ramo']}<br>Prioridade: {row['prioridade']}",
            "start": f"2025-0{mes}-{dia}T{start_hour:02d}:{start_minute:02d}:00",
            "end": f"2025-0{mes}-{dia}T{end_hour:02d}:{start_minute:02d}:00"
        })

    #!  Exibir timeline inicial de Proposta de Agendamento
    # st.subheader("Sugestão inicial para o Agendamento de Rede Elétrica")
    # st.write("Clique em um item para ver os detalhes da execução selecionada.")
    # timeline = st_timeline(
    #     timeline_items,
    #     groups=[],
    #     options={
    #         "selectable": True,
    #         "multiselect": True,
    #         "zoomable": True,
    #         "verticalScroll": True,
    #         "stack": True,
    #         "height": 500,
    #         "margin": {"axis": 5},
    #         "groupHeightMode": "auto",
    #         "orientation": {"axis": "top", "item": "top"}
    #     },
    # )

    # # Mostrar dados da execução selecionada
    # if timeline:
    #     selected_id = timeline.get("id", "").split("-")[1]
    #     selected_agendamento = agendamento_df.iloc[int(selected_id)]
    #     st.json(selected_agendamento.to_dict())

    # #! Tabs para cada execução
    # st.subheader("Resultado de todas as Execuções")
    # st.write(execution_df)
    # st.info("Para melhor visualização vou tentar ter um checkbox no data_editor de cada execução e selecionar dentro da tabela (retira o tabs de execução), mas por enquanto vou deixar como está.")
    
    
    
    def tabs_results_redeEletrica():
        st.write("Clique em uma aba para ver os detalhes da execução selecionada.")
        tabs = st.tabs([f"Execução {row['execution']}" for _, row in execution_df.iterrows()])
        for i, tab in enumerate(tabs):
            with tab:
                exec_data = execution_df.iloc[i]
                with st.container():
                    st.write(f"Execução {exec_data['execution']}")
                    st.subheader("Dados da Execução Selecionada")

                    
                    # Tabs dentro do container
                    inner_tabs = st.tabs(["Horários", "Gráfico de Barras", "Gráfico de Linhas", "População Final"])
                    with inner_tabs[0]:
                        st.write("Tabela de Horários de Agendamento")
                        sorted_vars = sorted(exec_data["solution_variables"])
                        st.dataframe(
                            pd.DataFrame([sorted_vars], columns=[f"Horário {i+1}" for i in range(len(sorted_vars))])
                        )

                    with inner_tabs[1]:
                        st.write("Gráfico de Barras")
                        st.bar_chart(pd.DataFrame({"Horários de Agendamento": exec_data["solution_variables"]}))

                    with inner_tabs[2]:
                        st.write("Gráfico de Linhas")
                        st.line_chart(pd.DataFrame({"Horários de Agendamento": exec_data["solution_variables"]}))
                        
                    with inner_tabs[3]:
                        st.write("População Final")
                        try:
                            pop_final_df = pd.read_excel(pop_final_xlsx_file)
                            st.dataframe(pop_final_df)
                        except Exception as e:
                            st.error(f"Erro ao carregar a população final: {e}")
                            st.write("População final não disponível.")
                            
                            
        
    # Mostra toda a tabela de execuções primeiro
    #st.subheader("Tabela de Horários de Agendamento")
    #st.dataframe(execution_df)

    # Cria abas para cada execução disponível em execution_df
    abas = st.tabs([f"Execução {row['execution']}" for _, row in execution_df.iterrows()])
    for i, aba in enumerate(abas):
        with aba:
            exec_data = execution_df.iloc[i]
            st.write(exec_data)
            time_line_from_solution_variables(agendamento_df, contingencia_df, exec_data)