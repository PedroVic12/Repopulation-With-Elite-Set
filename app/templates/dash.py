import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from RedeEletrica import RedeEletricaPandaPower  # Certifique-se de que este caminho de importação esteja correto

# Configurações de layout
st.set_page_config(page_title="Automação de Rede Elétrica", layout="wide")

# Função para exibir o modal de entrada de dados
def show_data_entry_modal():
    with st.form("data_entry_form", clear_on_submit=True):
        st.write("### Dados de Agendamento")
        num_ramos = st.number_input("Número de Ramos", min_value=1, value=1, step=1)
        agendamento_data = []
        
        for i in range(num_ramos):
            ramo = st.text_input(f"Ramo {i+1} (ex: '1,4')", value="1,4")
            inicio = st.text_input(f"Início {i+1} (ex: '14:00')", value="14:00")
            duracao = st.number_input(f"Duração {i+1} (em horas)", min_value=1, value=6, step=1)
            prioridade = st.number_input(f"Prioridade {i+1}", min_value=1, value=1, step=1)
            agendamento_data.append({"ramo": [int(x) for x in ramo.split(',')], "inicio": inicio, "duracao": duracao, "prioridade": prioridade})
        
        st.write("### Dados de Contingência")
        num_contingencias = st.number_input("Número de Contingências", min_value=1, value=1, step=1)
        contingencia_data = []
        
        for i in range(num_contingencias):
            contingencia = st.number_input(f"Contingência {i+1}", min_value=1, value=1, step=1)
            from_bus = st.number_input(f"From {i+1}", min_value=1, value=1, step=1)
            to_bus = st.number_input(f"To {i+1}", min_value=1, value=1, step=1)
            contingencia_data.append({"contingencia": contingencia, "from": from_bus, "to": to_bus})
        
        submitted = st.form_submit_button("Submeter")
        if submitted:
            return pd.DataFrame(agendamento_data), pd.DataFrame(contingencia_data)
    return None, None

# Função para processar os dados e executar a automação
def process_data(agendamento_df, contingencia_df):
    rede = RedeEletricaPandaPower("14", debug=True)
    rede.pesos["tensao"] = {"min": 100, "max": 100}
    rede.pesos["loading_linhas"] = 100
    rede.pesos["loading_trafos"] = 100

    agendamento_df['inicio'] = agendamento_df['inicio'].apply(lambda x: int(x.split(':')[0]))
    agendamento_df['final'] = agendamento_df.apply(lambda row: (row['inicio'] + row['duracao']) % 24, axis=1)

    rede.validar_dados(agendamento_df, contingencia_df)

    matriz_cenarios = rede.avalia_cenarios(
            horas=32,
            hora_inicio=agendamento_df['inicio'],
            duracao=agendamento_df['duracao'],
            ls=0, le=8,
            ms=8, me=18,
            hs=18, he=24
        )

    violacoes_total = []
    violacoes_hash_table = {}
    num_carregamentos = 3
    num_contingencias = len(contingencia_df)
    num_desligamentos = len(agendamento_df)

    bd_aptidao_cenario = [-1.0] * (num_contingencias * num_carregamentos * (2**num_desligamentos))

    for cenario in matriz_cenarios:
        perfil = cenario[0]
        estado_ramos = cenario[1:]

        for contingencia_atual in range(num_contingencias):
            contingencia_atual += 1
            rede.religar_todos_os_ramos_agendamento()
            rede.desligar_elementos_agendamento(estado_ramos)

            ramo_contingencia = list(contingencia_df.loc[contingencia_df['contingencia'] == contingencia_atual, ['from', 'to']].values[0])
            rede.desligar_contingencia(ramo_contingencia)

            if rede.executar_fluxo_de_carga():
                fitness, violacoes_df = rede.calcular_violacoes_fitness()
                violacoes_total.append(fitness)
            else:
                fitness = rede.pesos["demanda"]

            hash_key = rede.hashtableindex(perfil, num_carregamentos, contingencia_atual, num_contingencias, estado_ramos)
            violacoes_hash_table[hash_key] = fitness
            bd_aptidao_cenario[hash_key] = fitness

    hash_df = pd.DataFrame(bd_aptidao_cenario, columns=['Fitness'])
    filtered_hash_table = hash_df.loc[hash_df['Fitness'] > 0]
    
    fitness_final = sum(violacoes_total)
    results = rede.imprimir_resultados()

    return fitness_final, hash_df, results

# Função para exibir os resultados
def display_results(fitness_final, hash_df):
    st.write("### Resultados do Fitness")
    st.write(f"Fitness Final: {fitness_final:.2f}")

    st.write("### Hash Table")
    st.dataframe(hash_df)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        hash_df.to_excel(writer, sheet_name='Hash Table')
    st.download_button(
        label="Baixar Hash Table",
        data=buffer,
        file_name="hash_table.xlsx",
        mime="application/vnd.ms-excel"
    )

# Interface do Streamlit
st.title("Automação de Rede Elétrica")

if st.button("Inserir Dados de Entrada"):
    st.session_state.agendamento_df, st.session_state.contingencia_df = show_data_entry_modal()

if "agendamento_df" in st.session_state and "contingencia_df" in st.session_state:
    if st.session_state.agendamento_df is not None and st.session_state.contingencia_df is not None:
        st.write("### Dados de Agendamento")
        st.dataframe(st.session_state.agendamento_df)
        st.write("### Dados de Contingência")
        st.dataframe(st.session_state.contingencia_df)

        if st.button("Executar Automação"):
            fitness_final, hash_df, _ = process_data(st.session_state.agendamento_df, st.session_state.contingencia_df)
            display_results(fitness_final, hash_df)