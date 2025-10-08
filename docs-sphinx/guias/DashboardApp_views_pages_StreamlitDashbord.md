# StreamlitDashbord.py

```python
import streamlit as st
import pandas as pd
import plotly.graph_objects as go


class StreamlitDashboard:
    def __init__(self):
        """Inicializa o dashboard."""
        self.df = None
        

        #self.HomePage()


# componentes
    def setup_header(self):
        """Configura o cabeçalho do dashboard."""
        col1, col2, col3 = st.columns([1, 8, 1])

        with col1:
            st.button("≡")

        with col2:
            st.title("Dashboard Interativo")

        with col3:
            if st.button("🔔"):
                
                    st.success("Chatbot ativado!")
            else:
                    st.warning("Chatbot desativado!")

    def load_data(self):
        """Carrega os dados de entrada a partir de um arquivo Excel."""
        with st.sidebar:

            st.title("Dashboard de Análise de Dados")
            st.markdown("---")  # Separa

            uploaded_file = st.file_uploader("Envie um arquivo Excel", type=["xlsx", "xls"])
            if uploaded_file:
                try:
                    self.df = pd.read_excel(uploaded_file, sheet_name=None)  # Carrega todas as tabelas
                    st.success("Arquivo carregado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao carregar arquivo: {e}")
            else:
                st.info("Envie um arquivo Excel para começar.")

    def select_table(self):
        """Seleciona uma tabela do arquivo Excel carregado."""
        if self.df:
            table_name = st.sidebar.selectbox("Selecione a tabela", list(self.df.keys()))
            return self.df[table_name]
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
            template='plotly_dark',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
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
            template='plotly_dark',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)

    def create_pie_chart(self, df, x_col, y_col):
        """Cria um gráfico de pizza."""
        fig = go.Figure(data=[go.Pie(
            labels=df[x_col], values=df[y_col]
        )])
        fig.update_layout(
            title=f'Gráfico de Pizza: {y_col} por {x_col}',
            template='plotly_dark',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)

    def display_statistics(self, df, stat_col):
        """Exibe estatísticas da coluna selecionada."""
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Mínimo", f"{df[stat_col].min():.2f}", delta=-0.5, delta_color="inverse")
        col2.metric("Máximo", f"{df[stat_col].max():.2f}", delta=-0.5, delta_color="inverse")
        col3.metric("Média", f"{df[stat_col].mean():.2f}", delta=-0.5, delta_color="inverse")
        col4.metric("Desvio Padrão", f"{df[stat_col].std():.2f}", delta=-0.5, delta_color="inverse")

    def footer(self):
        """Exibe o rodapé do dashboard."""
        st.markdown("""
            <footer>
            <p>Powered by <a href="https://streamlit.io/">Streamlit</a> and <a href="https://plotly.com/python/">Plotly</a></p>
            </footer>
        """, unsafe_allow_html=True)


    def HomePage(self):
        """Executa o dashboard."""
        self.setup_header()
        self.load_data()


        if self.df:
            selected_table = self.select_table()
            if selected_table is not None:
                # Seção de Estatísticas
                st.markdown("---")  # Separa
                st.sidebar.title("Análise do arquivo Excel")
                st.markdown("---")  # Separa

                stat_col = st.sidebar.selectbox("Selecione uma coluna para análise estatística", selected_table.columns)

                if stat_col:
                    self.display_statistics(selected_table, stat_col)

                # Configuração de Eixos para os Gráficos
                x_col, y_col = self.select_axes(selected_table)

                # Exibir tabela
                st.subheader("Tabela Selecionada")
                st.dataframe(selected_table, use_container_width=True)

                # Exibir gráficos
                st.subheader("Gráficos")
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


        self.footer()


```