import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from io import StringIO, BytesIO
import base64


    

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
def Card(title, content, key=None):
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
def NavigationLateral():

    st.sidebar.title("Barra Navegação Lateral")
    st.sidebar.markdown("---")

    pages = {
        "Home": "home",
        "Page 1": "page-1",
        "Page 2": "page-2",
        "Graph Page": "graph-page"
    }
    
    selected_page = st.sidebar.radio("Paginas", list(pages.keys()))
    
    # Separador
    st.sidebar.markdown("---")
    
    return pages[selected_page]


def DrawerMenuLateral():
    utils = Utils()

    temas = {
        "titulo": "App Streamlit",
        "paleta_dark": ["#1a365d", "#2d547d", "#38bdf8", "#f8fafc"],
        "paleta_light": ["#f8fafc", "#e0e0e0", "#38bdf8", "#1a365d"],
    }
    with st.sidebar:
        # Sidebar content
        st.markdown(f"""
                        <img src = "https://avatars.githubusercontent.com/u/83238564?s=200&v=4" style = "width: 50%; border-radius: 50%;">
                        <h3 style = "color: var(--primary-color);"> {temas["titulo"]} </h3> 
                        <p style = "color: var(--primary-color);">
                        Ola mundo, meu nome é <strong>Pedro Victor</strong> e sou um desenvolvedor de software.
                        </p>
                    """, unsafe_allow_html=True)


        with st.expander("Contato", expanded=True):
            st.markdown("""
                    <hr style = "border: 1px solid var(--primary-color);">
                    <p> <i class="fas fa-user"></i> <strong>Nome:</strong> Pedro Victor </p>
                    <p> <i class="fas fa-phone"></i> <strong>Nome:</strong> Rio de janeiro </p>
                    <p> <i class="fas fa-envelope"></i> <strong>Nome:</strong> 21999289987 </p>
                    <p> <i class="fas fa-map-marker-alt"></i> <strong>Nome:</strong> pedrovictorveras@id.uff.br </p>
                    """, unsafe_allow_html=True)
        
    st.sidebar.markdown("---")

array_labels = ["Cat", "Dog", "Owl"]
def Tabs():
    tab1, tab2, tab3 = st.tabs(array_labels)

    with tab1:
        st.header(array_labels[0])
        st.image("https://static.streamlit.io/examples/cat.jpg", width=200)
    with tab2:
        st.header(array_labels[1])
        st.image("https://static.streamlit.io/examples/dog.jpg", width=200)
    with tab3:
        st.header(array_labels[2])
        st.image("https://static.streamlit.io/examples/owl.jpg", width=200)

def GraficoTabs():
    tab1, tab2 = st.tabs(["📈 Chart", "🗃 Data"])
    data = np.random.randn(10, 1)

    tab1.subheader("A tab with a chart")
    tab1.line_chart(data)

    tab2.subheader("A tab with the data")
    tab2.write(data)


def FormularioComponent():
    def init_values():
        if "form_data" not in st.session_state:
            st.session_state.form_data = {
                "nome": "Pedro Victor",
                "email": "",
                "telefone": "",
                "descricao": "",
                "data": pd.Timestamp.today().date(),
            }

        print("\nDados da Session:", st.session_state.form_data)

    init_values()

    st.title("Formulário de Contato")
    
    nome = st.text_input("Nome", st.session_state.form_data["nome"])
    email = st.text_input("Email", st.session_state.form_data["email"])
    telefone = st.text_input("Telefone", st.session_state.form_data["telefone"])
    descricao = st.text_area("Descrição", st.session_state.form_data["descricao"])
    data = st.date_input("Data", st.session_state.form_data["data"])


    btnSubmit = st.button("Agendar consulta")

    if btnSubmit:
        st.session_state.form_data = {
            "nome": nome,
            "email": email,
            "telefone": telefone,
            "descricao": descricao,
            "data": data,
        }

        st.success("Formulário enviado com sucesso!")
        st.info(f"Nome: {nome}, Email: {email}, Data: {data}")


    st.subheader("Consultas agendadas")
    st.write("Aqui estão as consultas agendadas para os próximos dias:")



class Utils:
    def __init__(self):
        pass

    def Markdown(self, texto: str):
        st.markdown(texto, unsafe_allow_html=True)

    def CardSuspenso(self, titulo: str, conteudo: dict = {}):
        with st.expander(titulo, expanded=True):
            st.markdown("""
                    <hr style = "border: 1px solid var(--primary-color);">
                    <p> <i class="fas fa-user"></i> <strong>Nome:</strong> Pedro Victor </p>
                    <p> <i class="fas fa-phone"></i> <strong>Nome:</strong> Rio de janeiro </p>
                    <p> <i class="fas fa-envelope"></i> <strong>Nome:</strong> 21999289987 </p>
                    <p> <i class="fas fa-map-marker-alt"></i> <strong>Nome:</strong> pedrovictorveras@id.uff.br </p>
                    """, unsafe_allow_html=True)

    def div(self, texto: str):
        st.markdown(f'<div style="text-aling: center; margin: 2rem 0">{texto}</div>', unsafe_allow_html=True)

    def social_links(self):

        info = {
            "link": "https://www.linkedin.com/in/pedro-victor-veras-de-lima-7b5b3b1b3/",
            "social": "linkedin",
        }

        link_html = "".join(
            f"<a href='{info['link']}' target='_blank'><i class='fab fa-{info['social']}' style='font-size: 24px; color: var(--primary-color);'></i></a>"
            f"<i class={info['social']}></i>"

            #for name,info in info.items():
            
        
        )



        self.Markdown(f"""
            <a href="https://www.linkedin.com/in/pedro-victor-veras-de-lima-7b5b3b1b3/" target="_blank">
                      <i class="fab fa-linkedin fa-2x"></i>
            </a>
                
            <div style="text-aling: center; margin: 2rem 0"> {link_html} </div>       

                    """)