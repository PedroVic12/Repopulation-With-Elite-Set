import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import random
import time

# Definir configurações da página
st.set_page_config(
    page_title="Dashboard Interativo",
    page_icon="📊",
    layout="wide",
)

# Função para gerar uma resposta aleatória no chat
def response_generator(df, x_col, y_col):
    question = random.choice([
        f"O que você pode me dizer sobre a média de {x_col}?",
        f"Qual é o valor máximo de {y_col}?",
        f"Me diga mais sobre os valores de {x_col}."
    ])

    # Dependendo da pergunta, o chat responde com base nas colunas selecionadas
    if "média" in question:
        answer = f"A média de {x_col} é {df[x_col].mean():.2f}."
    elif "máximo" in question:
        answer = f"O valor máximo de {y_col} é {df[y_col].max():.2f}."
    else:
        answer = f"Os valores de {x_col} são entre {df[x_col].min()} e {df[x_col].max()}."

    return answer


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
            st.sidebar.subheader("Seleciona uma tabela do arquivo Excel carregado.")
            table_name = st.sidebar.selectbox("Selecione a tabela", list(self.df.keys()))
            return self.df[table_name]
        else:
            st.warning("Nenhuma tabela disponível. Carregue um arquivo Excel.")
            return None

    def select_axes(self, df):
        """Seleciona as colunas para os eixos X e Y."""
        st.sidebar.subheader("Selecionar as colunas dos graficos")
        x_col = st.sidebar.selectbox("Coluna para o eixo X", df.columns)
        y_col = st.sidebar.selectbox("Coluna para o eixo Y", df.columns)
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
        """Exibe o dashboard com os gráficos e chat interativo."""
        st.title("Dashboard Interativo Streamlit App")
        self.load_data()

        if self.df:
            selected_table = self.select_table()
            if selected_table is not None:
                # Seção de Estatísticas
                st.sidebar.subheader("Análise Estatística")
                stat_col = st.sidebar.selectbox("Selecione uma coluna para análise estatística", selected_table.columns)

                if stat_col:
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Mínimo", f"{selected_table[stat_col].min():.2f}", delta=-0.5, delta_color="inverse", border=True)
                    col2.metric("Máximo", f"{selected_table[stat_col].max():.2f}", delta=-0.5, delta_color="inverse", border=True)
                    col3.metric("Média", f"{selected_table[stat_col].mean():.2f}", delta=-0.5, delta_color="inverse", border=True)
                    col4.metric("Desvio Padrão", f"{selected_table[stat_col].std():.2f}", delta=-0.5, delta_color="inverse", border=True)

                # Configuração de Eixos para os Gráficos
                x_col, y_col = self.select_axes(selected_table)

                # Organizar a Tabela e Gráficos Lado a Lado
                table_col, graph_col = st.columns([1, 1])

                # Alinhamento de tabela e gráficos
                with table_col:
                    print(selected_table.columns)
                    st.subheader(f"Tabela Selecionada ")
                    # Adicionando um espaçamento entre a tabela e os gráficos
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)

                    st.dataframe(selected_table, use_container_width=True)

                with graph_col:
                    st.subheader("Gráficos")
                    # Criando duas colunas lado a lado para o tipo de gráfico
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        st.write("Escolha o tipo de gráfico que deseja exibir:")

                    with col2:
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

                # Chat Interativo
                st.subheader("Chat Interativo com os Dados")
                if "messages" not in st.session_state:
                    st.session_state.messages = []

                # Exibe o histórico de mensagens
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

                # Aceita a entrada de texto do usuário
                if prompt := st.chat_input("Pergunte sobre os dados..."):
                    # Adiciona a mensagem do usuário
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)

                    # Resposta da "IA" com base nos dados
                    response = response_generator(selected_table, x_col, y_col)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    with st.chat_message("assistant"):
                        st.markdown(response)


if __name__ == "__main__":
    app = DashboardApp()
    app.display_dashboard()
