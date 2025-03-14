import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from io import StringIO, BytesIO
import base64

# Modelo de dados
class DataModel:
    def __init__(self):
        self.df = pd.DataFrame()

    def load_data(self, file):
        try:
            if file is not None:
                if file.name.endswith('.csv'):
                    self.df = pd.read_csv(file)
                elif file.name.endswith(('.xls', '.xlsx')):
                    self.df = pd.read_excel(file)
                else:
                    st.error("Formato de arquivo não suportado. Por favor, envie um arquivo CSV ou Excel.")
                    return False
                return True
            return False
        except Exception as e:
            st.error(f"Erro ao carregar arquivo: {e}")
            return False

# Componentes de Upload
def file_upload_component(key="upload-data"):
    st.subheader("Carregar Dados")
    uploaded_file = st.file_uploader(
        "Arraste e solte ou selecione os arquivos", 
        type=["csv", "xlsx", "xls"], 
        key=key
    )
    return uploaded_file

# Componente de Tabela
def data_table_component(df=None, key="data-table"):
    if df is None or df.empty:
        st.info("Nenhum dado disponível. Por favor, carregue um arquivo.")
        return
    
    st.dataframe(df, use_container_width=True, height=600)

# Componente de Gráficos
class GraficoComponent:
    def __init__(self):
        self.chart_types = ["Bar Chart", "Line Chart", "Scatter Chart"]
    
    def render_chart_selector(self, key="chart-selector"):
        selected_chart = st.selectbox(
            "Selecione o tipo de gráfico:",
            options=self.chart_types,
            key=key
        )
        return selected_chart
    
    def create_chart(self, df, selected_chart):
        if df.empty or len(df.columns) < 3:
            st.warning("Dados insuficientes para criar o gráfico. Carregue um arquivo com pelo menos 3 colunas.")
            return None
        
        fig = None
        
        try:
            if selected_chart == "Bar Chart":
                fig = px.bar(
                    df,
                    x=df.columns[0],
                    y=df.columns[1],
                    color=df.columns[2] if len(df.columns) > 2 else None,
                )
            elif selected_chart == "Line Chart":
                fig = px.line(
                    df,
                    x=df.columns[0],
                    y=df.columns[1],
                    color=df.columns[2] if len(df.columns) > 2 else None,
                )
            elif selected_chart == "Scatter Chart":
                fig = px.scatter(
                    df,
                    x=df.columns[0],
                    y=df.columns[1],
                    color=df.columns[2] if len(df.columns) > 2 else None,
                )
            
            if fig:
                fig.update_layout(
                    title=f"{selected_chart}",
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)"
                )
                
            return fig
            
        except Exception as e:
            st.error(f"Erro ao criar gráfico: {e}")
            return None
    
    def generate_insights(self, selected_chart):
        return f"Este {selected_chart} mostra as tendências no número de sistemas de IA em diferentes domínios ao longo do tempo. Você pode ver que..."

# Componente de Cartão
def create_card(title, content, key=None):
    with st.container():
        st.markdown(f"""
        <div style="padding: 1.5rem; border-radius: 0.5rem; background-color: #2c3e50; margin-bottom: 1rem;">
            <h4 style="margin-top: 0;">{title}</h4>
            <p>{content}</p>
        </div>
        """, unsafe_allow_html=True)

# Componente para RCE Gráfico
def create_rce_grafico(filepath):
    try:
        df = pd.read_excel(filepath)
        
        # Verificar se as colunas necessárias existem
        if "Generations" not in df.columns or "min_fitness" not in df.columns or "max_fitness" not in df.columns or "avg_fitness" not in df.columns:
            st.error("O arquivo não contém as colunas necessárias")
            return None
        
        gen = np.array(df["Generations"].dropna().values[0])
        min_fitness = np.array(df["min_fitness"].dropna().values[0])
        avg_fitness = np.array(df["avg_fitness"].dropna().values[0])
        max_fitness = np.array(df["max_fitness"].dropna().values[0])
        
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
            title="RCE Graph",
            xaxis_title="Generation",
            yaxis_title="Fitness",
            legend_title="Legend",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        
        return fig
    except Exception as e:
        st.error(f"Erro ao criar gráfico RCE: {e}")
        return None

# Componente de Botão Flutuante
def botao_flutuante():
    # CSS para o botão flutuante
    st.markdown("""
    <style>
    .botao-flutuante {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        text-align: center;
        font-size: 24px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        cursor: pointer;
        z-index: 1000;
    }
    .botao-flutuante:hover {
        background-color: #45a049;
    }
    
    /* Estilo para o modal */
    .modal {
        display: none;
        position: fixed;
        z-index: 1001;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0,0,0,0.5);
    }
    .modal-content {
        background-color: #2c3e50;
        margin: 15% auto;
        padding: 20px;
        border-radius: 10px;
        width: 70%;
        color: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    .close {
        color: white;
        float: right;
        font-size: 28px;
        font-weight: bold;
        cursor: pointer;
    }
    .close:hover {
        color: #cccccc;
    }
    
    /* Classe para quando o modal está visível */
    .modal.show {
        display: block;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # JavaScript para controlar a exibição do modal
    js_code = """
    <script>
    function showModal() {
        document.getElementById("myModal").classList.add("show");
    }
    
    function closeModal() {
        document.getElementById("myModal").classList.remove("show");
    }
    
    // Fechar o modal se o usuário clicar fora dele
    window.onclick = function(event) {
        var modal = document.getElementById("myModal");
        if (event.target == modal) {
            closeModal();
        }
    }
    </script>
    """
    
    # Botão flutuante e modal
    html_code = f"""
    {js_code}
    <button class="botao-flutuante" onclick="showModal()">+</button>
    
    <div id="myModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <h2>Olá Mundo!</h2>
            <p>Este é um modal criado com HTML/CSS/JavaScript no Streamlit!</p>
        </div>
    </div>
    """
    
    st.components.v1.html(html_code, height=0)

# Componente de Navegação
def render_navbar():
    st.sidebar.title("Navigation")
    
    pages = {
        "Home": "home",
        "Page 1": "page-1",
        "Page 2": "page-2",
        "Graph Page": "graph-page"
    }
    
    selected_page = st.sidebar.radio("Go to", list(pages.keys()))
    
    # Separador
    st.sidebar.markdown("---")
    
    return pages[selected_page]