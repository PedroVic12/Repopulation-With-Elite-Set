import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from abc import ABC, abstractmethod

# -------------------- Model (Camada de Dados) --------------------
class DataModel:
    def __init__(self):
        self._data = None
    
    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, value):
        self._data = value

    def load_excel(self, uploaded_file):
        try:
            self._data = pd.read_excel(uploaded_file, sheet_name=None)
            return True, "Arquivo carregado com sucesso!"
        except Exception as e:
            return False, f"Erro ao carregar arquivo: {e}"

# -------------------- ViewModel (Lógica de Apresentação) --------------------
class DashboardViewModel:
    def __init__(self, model):
        self.model = model
        self._initialize_session_state()
        
    def _initialize_session_state(self):
        if 'show_chat' not in st.session_state:
            st.session_state.show_chat = False
        if 'messages' not in st.session_state:
            st.session_state.messages = []
    
    def get_available_tables(self):
        return list(self.model.data.keys()) if self.model.data else []
    
    def get_table_data(self, table_name):
        return self.model.data[table_name] if self.model.data else None
    
    def calculate_statistics(self, df, column):
        return {
            'min': df[column].min(),
            'max': df[column].max(),
            'mean': df[column].mean(),
            'std': df[column].std()
        }

# -------------------- View Components (Componentes de UI) --------------------
class ChatBot:
    def display(self):
        with st.sidebar:
            st.title("Chatbot")
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])

            if prompt := st.chat_input("Digite sua mensagem..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                response = self._generate_response(prompt)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
    
    def _generate_response(self, prompt):
        return "pong" if prompt.lower() == "ping" else "Como posso ajudar?"

class Header:
    def display(self):
        col1, col2, col3 = st.columns([1, 8, 1])
        with col1:
            st.button("≡", key='menu_button')
        with col2:
            st.title("Dashboard Interativo")
        with col3:
            if st.button("🔔", key='notification_button'):
                st.session_state.show_chat = not st.session_state.show_chat

class Sidebar:
    def __init__(self, view_model):
        self.view_model = view_model
    
    def display(self):
        with st.sidebar:
            self._display_file_uploader()
            if self.view_model.model.data:
                self._display_table_selector()
    
    def _display_file_uploader(self):
        st.markdown("---")
        st.title("Carregar Dados")
        uploaded_file = st.file_uploader("Envie um arquivo Excel", type=["xlsx", "xls"])
        if uploaded_file:
            success, message = self.view_model.model.load_excel(uploaded_file)
            if success:
                st.success(message)
            else:
                st.error(message)
    
    def _display_table_selector(self):
        st.markdown("---")
        st.title("Análise")
        selected_table = st.selectbox("Selecione a tabela", self.view_model.get_available_tables())
        st.session_state.selected_table = selected_table

class Body:
    def __init__(self, view_model):
        self.view_model = view_model
    
    def display(self):
        if self.view_model.model.data:
            self._display_main_content()
    
    def _display_main_content(self):
        df = self.view_model.get_table_data(st.session_state.selected_table)
        
        # Seção de Estatísticas
        self._display_statistics(df)
        
        # Seção de Gráficos
        self._display_charts(df)
        
        # Tabela de Dados
        st.subheader("Tabela Selecionada")
        st.dataframe(df, use_container_width=True)
    
    def _display_statistics(self, df):
        st.markdown("---")
        stat_col = st.selectbox("Selecione para análise estatística", df.columns)
        stats = self.view_model.calculate_statistics(df, stat_col)
        
        cols = st.columns(4)
        metrics = [
            ("Mínimo", stats['min']),
            ("Máximo", stats['max']),
            ("Média", stats['mean']),
            ("Desvio Padrão", stats['std'])
        ]
        
        for col, (label, value) in zip(cols, metrics):
            col.metric(label, f"{value:.2f}")
    
    def _display_charts(self, df):
        st.markdown("---")
        st.subheader("Gráficos")
        
        col1, col2 = st.columns(2)
        with col1:
            x_col = st.selectbox("Eixo X", df.columns)
        with col2:
            y_col = st.selectbox("Eixo Y", df.columns)
        
        graph_type = st.radio("Tipo de Gráfico", ('Dispersão', 'Barras', 'Pizza'), horizontal=True)
        
        if graph_type == 'Dispersão':
            self._create_scatter_plot(df, x_col, y_col)
        elif graph_type == 'Barras':
            self._create_bar_plot(df, x_col, y_col)
        elif graph_type == 'Pizza':
            self._create_pie_chart(df, x_col, y_col)
    
    def _create_scatter_plot(self, df, x_col, y_col):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df[x_col], y=df[y_col], mode='lines+markers'))
        fig.update_layout(template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)
    
    def _create_bar_plot(self, df, x_col, y_col):
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df[x_col], y=df[y_col]))
        fig.update_layout(template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)
    
    def _create_pie_chart(self, df, x_col, y_col):
        fig = go.Figure(data=[go.Pie(labels=df[x_col], values=df[y_col])])
        fig.update_layout(template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)

class Footer:
    def display(self):
        st.markdown("---")
        st.markdown("""
            <footer style='text-align: center'>
                <p>Powered by Streamlit e Plotly</p>
            </footer>
        """, unsafe_allow_html=True)

# -------------------- Main App --------------------
class DashboardApp:
    def __init__(self):
        self._configure_page()
        self.model = DataModel()
        self.view_model = DashboardViewModel(self.model)
        self.chatbot = ChatBot()
    
    def _configure_page(self):
        st.set_page_config(layout="wide", page_title="Dashboard Interativo")
        st.markdown("""
            <style>
            .stApp {
                background-color: #1a1a2e;
                color: white;
            }
            </style>
        """, unsafe_allow_html=True)
    
    def run(self):
        Header().display()
        
        # Layout Principal
        sidebar = Sidebar(self.view_model)
        sidebar.display()
        
        Body(self.view_model).display()
        Footer().display()
        
        # Chatbot
        if st.session_state.show_chat:
            self.chatbot.display()

if __name__ == "__main__":
    app = DashboardApp()
    app.run()