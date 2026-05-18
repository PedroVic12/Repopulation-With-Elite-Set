import streamlit as st
from components import (
    menu_lateral, select_table, select_axes, select_analysis_column,
    input_img, input_pdf, formulario, header, cards, footer,
    ChatBot, Graficos
)

class DashboardApp:
    """Classe principal para criar o dashboard interativo com Streamlit."""

    def __init__(self):
        st.set_page_config(layout="wide", page_title="Dashboard Interativo")
        self.df = None
        self.chatbot = ChatBot()
        
        # Inicializar estado para o chatbot e menu
        if 'show_chat' not in st.session_state:
            st.session_state.show_chat = False
        if 'show_menu' not in st.session_state:
            st.session_state.show_menu = False
        
        # Configurar tema escuro
        st.markdown("""
            <style>
            .stApp {
                background-color: #1a1a2e;
                color: white;
            }
            </style>
        """, unsafe_allow_html=True)

    def run(self):
        """Executa o dashboard."""
        # Configurar header
        show_menu, show_chat = header()
        
        # Carregar dados
        self.df = menu_lateral()

        # Processar dados carregados
        if self.df:
            selected_table = select_table(self.df)
            
            if selected_table is not None:
                # Selecionar coluna para análise estatística
                stat_col = select_analysis_column(selected_table)
                
                if stat_col:
                    # Mostrar cards com estatísticas
                    st.markdown("## Estatísticas")
                    cards(selected_table, stat_col)
                
                # Configuração de Eixos para os Gráficos
                x_col, y_col = select_axes(selected_table)
                
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
                
                graficos = Graficos()
                
                if graph_type == 'Dispersão':
                    fig = graficos.scatter_plot(selected_table, x_col, y_col)
                    st.plotly_chart(fig, use_container_width=True)
                elif graph_type == 'Barras':
                    fig = graficos.bar_plot(selected_table, x_col, y_col)
                    st.plotly_chart(fig, use_container_width=True)
                elif graph_type == 'Pizza':
                    fig = graficos.pie_chart(selected_table, x_col, y_col)
                    st.plotly_chart(fig, use_container_width=True)
                
        # Opcionalmente mostrar outros componentes de entrada
        if show_menu:
            img_file = input_img()
            pdf_file = input_pdf()
            form_data = formulario()
            
            if form_data:
                st.sidebar.write("Dados enviados:", form_data)
                
        # Menu direito do chatbot
        if show_chat:
            with st.sidebar:
                st.markdown("---")  # Separador
                self.chatbot.display_chat()
                st.markdown("---")  # Separador
        
        # Rodapé
        footer()


if __name__ == "__main__":
    app = DashboardApp()
    app.run()