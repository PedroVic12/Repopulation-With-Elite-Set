
import streamlit as st
import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def menu_lateral():
    st.sidebar.title("Menu Lateral")
    st.sidebar.write("Selecione uma opção:")

    # ver como funciona para navegar entre paginas aqui e no TABS
    st.sidebar.radio("Opções", ["Opção 1", "Opção 2", "Opção 3"])


    input = st.sidebar.text_input("Digite algo para aparecer na sua tela:")


def TabsLayout():
    tab1, tab2, tab3 = st.tabs(["Tab 1", "Tab 2", "Tab 3"])

    with tab1:
        st.subheader("Tab 1")

    with tab2:
        st.subheader("Tab 2")

    with tab3:
        st.subheader("Tab 3")

def ColumnsLayout(num_cols, components):
    cols = st.columns(num_cols)

    for i, col in enumerate(cols):
        with col:
            components[i]


def Container():
    with st.container(border= True):
        st.write("Este é um container.")
        st.write("Você pode adicionar vários componentes dentro dele.")
        st.button("Botão dentro do container")
        st.write("Mais informações ou componentes podem ser adicionados aqui.")


def Placeholder():
    placeholder = st.empty()
    placeholder.write("Este é um espaço reservado.")

    if st.button("Atualizar placeholder"):
        placeholder.write("O placeholder foi atualizado com novos dados.")
        #placeholder.button("Novo botão no placeholder")

    return placeholder


def Expander():
    expander = st.expander("Clique para expandir")
    with expander:
        st.write("Este é um conteúdo dentro de um expander.")
        st.write("Você pode adicionar texto, gráficos ou qualquer outro componente aqui.")


def Tooltip():
    st.write("Passe o mouse sobre o botão para ver o tooltip.")
    st.button("Botão com Tooltip", help="Este é um tooltip que aparece quando você passa o mouse sobre o botão.")


def Alert():
    st.warning("Este é um alerta de aviso.")
    st.success("Este é um alerta de sucesso.")
    st.error("Este é um alerta de erro.")
    st.info("Este é um alerta informativo.")

    
def ProgressBar():
    progress = st.progress(0)
    for i in range(100):
        progress.progress(i + 1)
        time.sleep(0.1)  # Simula um atraso para mostrar o progresso


def Spinner():
    with st.spinner("Carregando..."):
        time.sleep(1)  # Simula um atraso para mostrar o spinner


def Plot(x,y):


    # Criar o gráfico
    fig, ax = plt.subplots()
    ax.plot(x, y)
    ax.set_title("Gráfico de Exemplo")
    ax.set_xlabel("Eixo X")
    ax.set_ylabel("Eixo Y")

    # Exibir o gráfico no Streamlit
    st.pyplot(fig)


def DataFrame():
    # Criar um DataFrame de exemplo
    data = {'Nome': ['Alice', 'Bob', 'Charlie'],
            'Idade': [25, 30, 35]}
    df = pd.DataFrame(data)

    # Exibir o DataFrame no Streamlit
    st.dataframe(df)


def header():
    st.title("Layout Components Template")
    st.write("Este é um exemplo de layout com componentes Streamlit.")
    st.write("Você pode adicionar texto, tabelas, gráficos e muito mais.")
    st.write("Aqui estão alguns exemplos de componentes:")


def footer():
    st.write("---")
    st.write("Este é o rodapé da página.")
    st.write("Você pode adicionar informações adicionais ou links aqui.")
    st.sidebar.write(f"Você digitou: {input}")









# Gerar dados de exemplo
x = np.linspace(0, 50, 300)
y = np.sin(x)


def LayoutTemplatePage():
    header()

    # Meus componentes
    menu_lateral()
    TabsLayout()
    ColumnsLayout(3, [st.button("Botão 1"), st.button("Botão 2"), st.button("Botão 3")])
    st.write("Texto adicional ou informações podem ser adicionadas aqui.")
    Container()
    
    #Spinner()
    #ProgressBar()
    Expander()

    Plot(x, y)
    DataFrame()

    Placeholder()
    Tooltip()
    Alert()
    



    footer()

LayoutTemplatePage()