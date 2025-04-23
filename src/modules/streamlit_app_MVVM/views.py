import streamlit as st
import pandas as pd
import numpy as np
from components import (
    GraficoComponent,
    Card,
    create_rce_grafico,
    botao_flutuante,
    NavigationLateral,
    Utils,
    FormularioComponent,
)

from controllers import  file_upload_component, data_table_component

# Example page functions
def home_page():
    st.title("Home Page")
    st.write("Welcome to the Home Page!")

def about_page():
    st.title("About Page")
    st.write("This is the About Page.")

    
def render_page_1():
        st.title("Página 1")
        
        st.subheader("Conteúdo da Página 1")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Este é um exemplo de conteúdo da Página 1.")
            st.write("Você pode adicionar qualquer conteúdo aqui.")
        
        with col2:
            st.info("Esta é uma caixa de informações.")
            st.warning("Este é um aviso.")
            st.error("Este é um erro.")
            st.success("Esta é uma mensagem de sucesso.")
            
        # Exemplo de uma métrica
        st.metric("Temperatura", "32 °C", delta="1.2 °C", delta_color="inverse")
    
def render_page_2():
        st.title("Página 2 - Tabelas")
        
        # Simulação de tabelas do código original
        st.write("Como não temos acesso aos arquivos originais, vamos criar alguns dados fictícios.")
        
        # Criar alguns DataFrames de exemplo
        df_resumo = pd.DataFrame({
            'Métrica': ['Precisão', 'Recall', 'F1-Score', 'Acurácia'],
            'Valor': [0.92, 0.85, 0.88, 0.90]
        })
        
        df_evolutivos = pd.DataFrame({
            'Geração': range(1, 11),
            'Fitness Mínimo': np.random.rand(10) * 0.1,
            'Fitness Médio': np.random.rand(10) * 0.5,
            'Fitness Máximo': np.random.rand(10) * 0.9 + 0.1
        })
        
        # Exibir tabelas
        st.subheader("Tabela Parâmetros Evolutivos")
        st.dataframe(df_evolutivos, use_container_width=True)
        
        st.subheader("Tabela Resumo")
        st.dataframe(df_resumo, use_container_width=True)
    
def RCEFrameworkPage():
        st.title("Página de Gráficos")

        # Cards na primeira linha
        col1, col2, col3 = st.columns(3)
        
        with col1:
            Card("Best Solution Gen", "145")
        
        with col2:
            Card("Solution Fitness", "0.0024449194511966255")
            
        with col3:
            Card("Best Variables", "[-0.003, 0.001, -1.768, 1.185, -1.900, 0.227, 4.695, -2.824, -1.265, -7.298]")
        
        
        # Como não temos acesso ao arquivo original, vamos criar dados fictícios para o gráfico RCE
        st.write("Como não temos acesso ao arquivo RCE original, vamos criar um gráfico com dados simulados.")
        
        # Criar dados fictícios para o gráfico
        gen = np.arange(1, 101)
        min_fitness = 0.5 * np.exp(-0.02 * gen) + 0.01 * np.random.rand(100)
        avg_fitness = 0.7 * np.exp(-0.015 * gen) + 0.02 * np.random.rand(100)
        max_fitness = 0.9 * np.exp(-0.01 * gen) + 0.03 * np.random.rand(100)
        
        # Criar figura Plotly diretamente
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        fig.add_trace(
            go.Scatter(
                x=gen,
                y=min_fitness,
                mode="lines+markers",
                name="Minimum Fitness",
                marker=dict(symbol="star", color="blue"),
                line=dict(color="blue"),
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=gen,
                y=avg_fitness,
                mode="lines+markers",
                name="Average Fitness",
                marker=dict(symbol="cross", color="red"),
                line=dict(color="red"),
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=gen,
                y=max_fitness,
                mode="lines+markers",
                name="Maximum Fitness",
                marker=dict(symbol="circle", color="green"),
                line=dict(color="green"),
            )
        )
        
        fig.update_layout(
            title="Simulação do Gráfico RCE",
            xaxis_title="Geração",
            yaxis_title="Fitness",
            legend_title="Legenda",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Adicionar algumas métricas
        col1, col2, col3 = st.columns(3)
        col1.metric("Melhor Fitness", f"{min_fitness[-1]:.6f}", delta=f"{min_fitness[0] - min_fitness[-1]:.6f}")
        col2.metric("Gerações Executadas", f"{len(gen)}", delta=None)
        col3.metric("Tempo de Execução", "2m 34s", delta=None)


        render_page_2()
    


def FormularioPage(df = None):

    #! Minuto 26 -> https://www.youtube.com/watch?v=BNc9yUTPzRQ
    st.title("Página de Formulários")

    FormularioComponent()


    Utils().Markdown(
        f""" 
            ## Exemplo de Markdown

            Este é um exemplo de texto em Markdown. Você pode adicionar **negrito**, _itálico_, [links](https://www.streamlit.io/),
            listas:
            - Item 1
            - Item 2
            - Item 3

            E até mesmo imagens:
            ![Streamlit](https://streamlit.io/images/brand/streamlit-mark-color.png)

            E muito mais!

        """)
    

    