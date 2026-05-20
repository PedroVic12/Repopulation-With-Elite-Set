import streamlit as st
import pandas as pd
import datetime
from streamlit_timeline import st_timeline

# ==============================================================================
# 1. SIMULAÇÃO DE DADOS
# Em uma aplicação real, estes dados viriam de um banco de dados, API ou arquivo.
# ==============================================================================

def get_scheduling_data():
    """
    Fornece um DataFrame de exemplo com intervenções de agendamento.
    'ramo' = ramo, 'inicio' = hora de início, 'duracao' = duração, 'prioridade' = prioridade.
    """
    return pd.DataFrame([
        {"ramo": "[1, 4]", "inicio": "14:00", "duracao": 6, "prioridade": 4},
        {"ramo": "[1, 3]", "inicio": "15:00", "duracao": 5, "prioridade": 1},
        {"ramo": "[3, 6]", "inicio": "14:00", "duracao": 6, "prioridade": 1},
        {"ramo": "[11, 12]", "inicio": "18:00", "duracao": 6, "prioridade": 1},
        {"ramo": "[9, 10]", "inicio": "15:00", "duracao": 4, "prioridade": 1}
    ])

def get_contingency_data():
    """
    Fornece um DataFrame de exemplo com contingências.
    'from' e 'to' representam nós da rede.
    """
    return pd.DataFrame([
        {"contingencia": 1, "from": 2, "to": 3},
        {"contingencia": 2, "from": 5, "to": 12},
        {"contingencia": 3, "from": 12, "to": 13},
    ])

def get_execution_results():
    """
    Fornece resultados de exemplo de diferentes execuções do algoritmo.
    'solution_variables' são os horários de início ótimos (em horas a partir de um ponto de referência)
    para as intervenções.
    """
    return pd.DataFrame([
        {"execution": 1, "solution_variables": [3, 11, 1, 18, 31], "best_fitness": 931.71, "best_generations": 1, "execution_time": "15.06s"},
        {"execution": 2, "solution_variables": [30, 1, 14, 30, 9], "best_fitness": 649.91, "best_generations": 6, "execution_time": "6.46s"},
        {"execution": 3, "solution_variables": [30, 17, 30, 30, 9], "best_fitness": 570.33, "best_generations": 11, "execution_time": "5.64s"},
        {"execution": 4, "solution_variables": [30, 25, 30, 30, 9], "best_fitness": 479.35, "best_generations": 15, "execution_time": "6.23s"},
        {"execution": 5, "solution_variables": [30, 25, 30, 30, 9], "best_fitness": 479.35, "best_generations": 15, "execution_time": "5.60s"},
    ])

# ==============================================================================
# 2. LÓGICA PRINCIPAL DA APLICAÇÃO
# Esta seção contém a função principal para criar a visualização interativa.
# ==============================================================================

def create_interactive_timeline(agendamento_df, contingencia_df, exec_data):
    """
    Gera e exibe uma linha do tempo interativa para os resultados de uma determinada execução.
    Quando um intervalo é selecionado na linha do tempo, exibe dados relacionados.

    Args:
        agendamento_df (pd.DataFrame): DataFrame com dados de agendamento.
        contingencia_df (pd.DataFrame): DataFrame com dados de contingência.
        exec_data (pd.Series): Uma linha do DataFrame de resultados da execução.
    """
    st.subheader(f"📊 Linha do Tempo para a Execução {exec_data['execution']}")
    st.write(f"Melhor Fitness: **{exec_data['best_fitness']:.2f}** | Gerações: **{exec_data['best_generations']}** | Tempo: **{exec_data['execution_time']}**")

    # Ordena as variáveis de solução para criar intervalos cronológicos
    solution_variables = sorted(exec_data["solution_variables"])
    items = []
    
    # Uma data base para fins de visualização
    base_date = datetime.datetime(2025, 6, 18)

    # Cria itens da linha do tempo a partir dos intervalos entre as variáveis de solução
    for j in range(len(solution_variables) - 1):
        start_hour_total = solution_variables[j]
        end_hour_total = solution_variables[j + 1]
        duration = end_hour_total - start_hour_total

        # Calcula os objetos datetime de início e fim
        start_datetime = base_date + datetime.timedelta(hours=start_hour_total)
        end_datetime = base_date + datetime.timedelta(hours=end_hour_total)

        # Apenas para fins de exibição no "content"
        start_hour_of_day = start_hour_total % 24
        end_hour_of_day = end_hour_total % 24

        items.append({
            "id": f"{exec_data['execution']}-{j}",
            "content": f"{start_hour_of_day:02d}h - {end_hour_of_day:02d}h ({duration}h)",
            "start": start_datetime.isoformat(),
            "end": end_datetime.isoformat(),
            "title": f"Intervalo: {start_hour_of_day:02d}h - {end_hour_of_day:02d}h"
        })

    # Exibe o componente da linha do tempo
    timeline = st_timeline(items, groups=[], options={"height": 250})

    # --- Exibe detalhes quando um item é selecionado ---
    if timeline and "id" in timeline:
        try:
            # Extrai o índice do intervalo selecionado a partir do seu ID
            selected_index = int(timeline["id"].split("-")[1])
            
            # Obtém as horas de início e fim para o intervalo selecionado
            start_hour_total = solution_variables[selected_index]
            end_hour_total = solution_variables[selected_index + 1]
            duration = end_hour_total - start_hour_total
            
            # Precisamos apenas da hora do dia para a filtragem
            start_hour_of_day = start_hour_total % 24
            end_hour_of_day = end_hour_total % 24

            # --- Filtra dados relacionados com base no intervalo selecionado ---
            # Esta lógica encontra agendamentos que estão ativos durante a janela de tempo selecionada.
            agendamentos_relacionados = agendamento_df[
                (agendamento_df["inicio"].apply(lambda x: int(x.split(":")[0])) <= start_hour_of_day) &
                ((agendamento_df["inicio"].apply(lambda x: int(x.split(":")[0])) + agendamento_df["duracao"]) >= end_hour_of_day)
            ]

            # --- Exibe as informações dinâmicas em tabelas editáveis ---
            st.markdown("---")
            st.subheader("🕒 Detalhes do Intervalo Selecionado")
            st.markdown(f"**Intervalo:** `{start_hour_of_day:02d}h - {end_hour_of_day:02d}h` (Duração: {duration}h)")

            st.subheader("📌 Agendamentos Relacionados")
            st.info("Você pode editar os dados diretamente na tabela abaixo.")
            st.data_editor(
                agendamentos_relacionados, 
                use_container_width=True, 
                key=f"edit_agendamentos_{exec_data['execution']}"
            )

            st.subheader("⚠️ Contingências Relacionadas")
            st.info("Os dados de contingência são mostrados para contexto.")
            st.data_editor(
                contingencia_df, 
                use_container_width=True, 
                key=f"edit_contingencias_{exec_data['execution']}"
            )

        except (ValueError, IndexError) as e:
            st.error(f"Não foi possível processar a seleção. Tente novamente. Erro: {e}")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")

# ==============================================================================
# 3. LAYOUT PRINCIPAL DA APLICAÇÃO
# Este é o ponto de entrada que configura a página do Streamlit.
# ==============================================================================

def main():
    """
    Configura o layout da página principal e orquestra o fluxo da aplicação.
    """
    st.set_page_config("Agendador Interativo", layout="wide", initial_sidebar_state="collapsed")
    
    st.title("🧠 Visualização Interativa dos Resultados da Execução")
    st.markdown("""
        Esta aplicação exibe os resultados de diferentes execuções de otimização. 
        Selecione uma execução na lista para ver o cronograma proposto na linha do tempo. 
        Clique em qualquer intervalo na linha do tempo para ver e editar os dados associados.
    """)
    st.markdown("---")

    # Carrega todos os dados necessários
    agendamento_df = get_scheduling_data()
    contingencia_df = get_contingency_data()
    execucoes_df = get_execution_results()

    # Cria uma lista suspensa para selecionar qual execução visualizar
    execucoes_opcoes = execucoes_df["execution"].tolist()
    execucao_selecionada = st.selectbox(
        "Selecione uma execução para analisar:", 
        execucoes_opcoes,
        help="Cada execução representa uma rodada diferente do algoritmo de otimização."
    )

    if execucao_selecionada:
        # Obtém os dados para a execução escolhida
        dados_execucao = execucoes_df[execucoes_df["execution"] == execucao_selecionada].iloc[0]
        
        # Exibe a linha do tempo e os componentes interativos
        create_interactive_timeline(agendamento_df, contingencia_df, dados_execucao)
    else:
        st.warning("Por favor, selecione uma execução para continuar.")

if __name__ == "__main__":
    main()
