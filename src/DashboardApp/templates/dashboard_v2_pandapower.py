import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from PIL.ImageOps import _border


class DashboardApp:
    """Classe para criar o dashboard interativo com Streamlit."""

    def __init__(self):
        self.df = None

    def load_data(self):
        """Carrega os dados de entrada a partir de um arquivo Excel."""
        st.sidebar.title("Carregar Dados")
        uploaded_file = st.sidebar.file_uploader("Envie um arquivo Excel", type=["xlsx", "xls"])
        if uploaded_file:
            try:
                self.df = pd.read_excel(uploaded_file, sheet_name=None)  # Carrega todas as tabelas
                st.sidebar.success("Arquivo carregado com sucesso!")
            except Exception as e:
                st.sidebar.error(f"Erro ao carregar arquivo: {e}")
        else:
            st.sidebar.info("Envie um arquivo Excel para começar.")

    def select_table(self):
        """Seleciona uma tabela do arquivo Excel carregado."""
        if self.df:
            table_name = st.sidebar.selectbox("Selecione a tabela", list(self.df.keys()))
            return self.df[table_name]
        else:
            st.warning("Nenhuma tabela disponível. Carregue um arquivo Excel.")
            return None

    def select_axes(self, df):
        """Seleciona as colunas para os eixos X e Y."""
        x_col = st.sidebar.selectbox("Selecione a coluna para o eixo X", df.columns)
        y_col = st.sidebar.selectbox("Selecione a coluna para o eixo Y", df.columns)
        return x_col, y_col

    def create_scatter_plot(self, df, x_col, y_col):
        """Cria um gráfico de dispersão."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df[x_col], y=df[y_col],
            mode='lines+markers', name=f'{y_col} vs {x_col}'
        ))
        fig.update_layout(
            title=f'Gráfico de {y_col} vs {x_col}',
            xaxis_title=x_col,
            yaxis_title=y_col,
            template='plotly_white'
        )
        st.plotly_chart(fig, use_container_width=True)

    def create_bar_plot(self, df, x_col, y_col):
        """Cria um gráfico de barras."""
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df[x_col], y=df[y_col], name=f'{y_col} vs {x_col}'
        ))
        fig.update_layout(
            title=f'Gráfico de Barras: {y_col} vs {x_col}',
            xaxis_title=x_col,
            yaxis_title=y_col,
            template='plotly_white'
        )
        st.plotly_chart(fig, use_container_width=True)

    def create_pie_chart(self, df, x_col, y_col):
        """Cria um gráfico de pizza."""
        fig = go.Figure(data=[go.Pie(
            labels=df[x_col], values=df[y_col]
        )])
        fig.update_layout(
            title=f'Gráfico de Pizza: {y_col} por {x_col}',
            template='plotly_white'
        )
        st.plotly_chart(fig, use_container_width=True)

    def display_dashboard(self):
        """Exibe o dashboard com os gráficos."""
        st.title("Dashboard Interativo com Controle de Eixos")
        self.load_data()

        if self.df:
            selected_table = self.select_table()
            if selected_table is not None:
                # Seção de Estatísticas
                st.sidebar.subheader("Análise Estatística")
                stat_col = st.sidebar.selectbox("Selecione uma coluna para análise estatística", selected_table.columns)

                if stat_col:
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Mínimo", f"{selected_table[stat_col].min():.2f}", delta_color="inverse", border = True , delta=-0.5)
                    col2.metric("Máximo", f"{selected_table[stat_col].max():.2f}",  delta_color="inverse", border = True, delta=-0.5)
                    col3.metric("Média", f"{selected_table[stat_col].mean():.2f}", delta_color="inverse", border = True, delta=-0.5)
                    col4.metric("Desvio Padrão", f"{selected_table[stat_col].std():.2f}",  delta_color="inverse", border = True, delta=-0.5)

                # Configuração de Eixos para os Gráficos
                x_col, y_col = self.select_axes(selected_table)

                # Organização da Tabela e Gráficos Lado a Lado
                st.subheader("Tabela e Gráficos")

                table_col, graph_col = st.columns([3, 3])


                st.subheader("Tabela Selecionada")
                st.dataframe(selected_table, use_container_width=False)


                st.subheader("Gráficos")
                st.write("Escolha o tipo de gráfico que deseja exibir:")

                graph_type = st.radio(
                        "Tipo de Gráfico",
                        ('Dispersão', 'Barras', 'Pizza'),
                        horizontal=True
                    )

                if graph_type == 'Dispersão':
                        self.create_scatter_plot(selected_table, x_col, y_col)
                elif graph_type == 'Barras':
                        self.create_bar_plot(selected_table, x_col, y_col)
                elif graph_type == 'Pizza':
                        self.create_pie_chart(selected_table, x_col, y_col)


if __name__ == "__main__":
    app = DashboardApp()
    app.display_dashboard()
