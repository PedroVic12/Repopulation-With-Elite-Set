import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import plotly.io as pio
import json
import plotly
from IPython import display


class dashPY:
    def __init__(self, arquivo_excel):
        self.df = pd.read_excel(arquivo_excel)

    def gerar_graficos_interativos(self, numero_colunas, nome_coluna):
        """
        Gera histogramas interativos para colunas selecionadas do DataFrame.

        Args:
            numero_colunas: Número de colunas para gerar gráficos.
            nome_coluna: Nome da coluna a ser usada para o eixo X dos histogramas.
        """
        for i in range(numero_colunas):
            tabela = self.df.iloc[:, i]
            fig = px.histogram(tabela, x=nome_coluna)
            fig.show()
            print(tabela)

    def exibir_dataset(self, arquivo_excel):

        arquivo_excel = st.text_input("Insira o caminho do arquivo Excel:")
        dash = dashPY(arquivo_excel)

        if arquivo_excel:

            # Mostra as colunas do DataFrame
            colunas = dash.df.columns
            st.write("Colunas do DataFrame:", colunas)

            # Limpa dados NaN
            dash.df.dropna(inplace=True)
            st.dataframe(dash.df)

            # Gera gráficos interativos (opcional)
            numero_colunas = st.number_input(
                "Número de colunas para gráficos interativos:",
                min_value=1,
                max_value=len(colunas),
            )
            nome_coluna = st.text_input("Nome da coluna para o eixo X dos histogramas:")
            if st.button("Gerar Gráficos Interativos"):
                dash.gerar_graficos_interativos(numero_colunas, nome_coluna)

            # Gera gráfico animado
            consumo = dash.df["consumo"]
            dias = dash.df["dias"]
            estacao = dash.df["estacao do ano"]

            # Formata a coluna de datas
            y = dias.dt.strftime("%d-%m-%y")

            if st.button("Gerar Gráfico Animado"):
                dash.desenhar_grafico_animado(consumo, estacao, y)
        else:
            st.write("Por favor,  insira o caminho do arquivo Excel.")

    def desenhar_grafico_animado(self, x, y, tempo):
        """
        Cria um gráfico de barras animado com base nas colunas do DataFrame.

        Args:
            x: Nome da coluna para o eixo X.
            y: Nome da coluna para o eixo Y.
            tempo: Nome da coluna com valores temporais para a animação.
        """
        fig = px.bar(
            self.df,
            x=x,
            y=y,
            color=x,
            animation_frame=tempo,
            animation_group=x,
            range_y=[0, 1200],
        )

        # Salva o gráfico como HTML
        plotly.offline.plot(fig, filename="./grafico.html")
        pio.write_html(fig, file="./index.html", auto_open=True)

    def grafico_interativo(self, df):
        st.title("Visualização de dados Alg Evolutivo")

        mes_selecionado = st.sidebar.multiselect(
            "Escolha a coluna", df.columns, placeholder="Selecione"
        )

        if mes_selecionado:
            fig = px.line(df, x="dias", y=mes_selecionado)
            st.plotly_chart(fig)

            st.write(df[mes_selecionado])

            col1, col2, col3 = st.columns(3)

            col1.bar_chart(df[mes_selecionado])
            col2.line_chart(df[mes_selecionado])
            col2.area_chart(df[mes_selecionado])

            col3.line_chart(df[mes_selecionado])


def load_params(file_path):
    with open(file_path, "r") as file:
        params = json.load(file)
    return params


def main():
    # CONFIGURAÇÃO DO STREAMLIT

    excel = "/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/evolution_rce_master/src/db/consumo_eletrico_agua.xlsx"
    dash = dashPY(excel)
    params = load_params(
        r"/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/evolution_rce_master/src/db/parameters.json"
    )
    print(params)
    st.title("Visualização de Dados Interativos")
    df = pd.read_excel(
        "/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/evolution_rce_master/src/db/consumo_eletrico_agua.xlsx",
    )
    colunas = df.columns
    print(colunas)

    df.dropna()
    print(df)

    consumo = df["consumo"]
    dias = df["dias"]
    estacao = df["estacao do ano"]

    # checa coluna temporal
    y = dias.dt.strftime("%d-%m-%y")
    dash.desenhar_grafico_animado(consumo, estacao, y)

    # Mostra as colunas do DataFrame
    colunas = dash.df.columns
    st.write("Colunas do DataFrame:", colunas)
    dash.grafico_interativo(df)

    if st.button("Gerar Gráfico Animado"):
        dash.desenhar_grafico_animado(consumo, estacao, y)


if __name__ == "__main__":
    main()
