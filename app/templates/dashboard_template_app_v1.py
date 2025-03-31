import streamlit as st
from PIL import Image
import pandas as pd
import webbrowser

# Set page configuration as the first Streamlit command
st.set_page_config(
    page_title="App Streamlit",
    page_icon=":shark:",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://www.google.com",
        "Report a bug": "https://www.google.com",
        "About": "https://www.google.com",
    }
)

temas = {
    "titulo": "App Streamlit",
    "paleta_dark": ["#1a365d", "#2d547d", "#38bdf8", "#f8fafc"],
    "paleta_light": ["#f8fafc", "#e0e0e0", "#38bdf8", "#1a365d"],
}

class Utils:
    def __init__(self):
        pass

    def Markdown(self, texto: str):
        st.markdown(texto, unsafe_allow_html=True)

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

def DrawerMenuLateral():
    utils = Utils()
    with st.sidebar:
        # Sidebar content
        st.markdown(f"""
                        <img src = "https://avatars.githubusercontent.com/u/83238564?s=200&v=4" style = "width: 50%; border-radius: 50%;">
                        <h3 style = "color: var(--primary-color);"> {temas["titulo"]} </h3> 

                        <hr style = "border: 1px solid var(--primary-color);">

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

        

def load_css(file_name: str):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def init_css():
    st.markdown("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            :root {
                --primary-color: #1a365d;
                --secondary-color: #2d547d;
                --accent-color: #38bdf8;
                --text-light: #f8fafc;
                --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }

            .project-card {
                background: white;
                border-radius: 10px;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                box-shadow: var(--shadow);
                transition: all 0.3s ease;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }

            .project-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            }

            .experience-item {
                padding: 1.5rem;
                background: white;
                border-radius: 10px;
                box-shadow: var(--shadow);
                margin-bottom: 1.5rem;
                transition: all 0.3s ease;
            }

            .experience-item:hover {
                transform: translateY(-3px);
            }
        </style>
    """, unsafe_allow_html=True)

class App:
    def __init__(self, tema = None):
        self.tema = tema
        init_css()
        DrawerMenuLateral()

    def render_page(self, page_function):
        page_function()



# Example page functions
def home_page():
    st.title("Home Page")
    st.write("Welcome to the Home Page!")

def about_page():
    st.title("About Page")
    st.write("This is the About Page.")


if __name__ == "__main__":
    app = App()
    selected_page = st.sidebar.selectbox("Select Page", ["Home", "About"])
    pagina_selecionada = st.sidebar.radio(
            "Menu de Navegação",
            [
                "Framework RCE",
                "Agendamentos de Redes Eletricas",
                "Analise de dados para testes benchmarking",
                "Pagina de formularios"

            ],
            format_func=lambda x: f'<span style="color: blue; font-size: 20px;">{x}</span>'
        )
    
    print("pagina_selecionada", pagina_selecionada)

    if pagina_selecionada == "Framework RCE":
        app.render_page(home_page)
    elif pagina_selecionada == "Agendamentos de Redes Eletricas":
        app.render_page(about_page)