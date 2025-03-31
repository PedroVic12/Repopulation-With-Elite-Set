from views import   home_page, about_page, RCEFrameworkPage, render_page_2
import streamlit as st
import pandas as pd
from PIL import Image
from controllers import  init_css
from components import DrawerMenuLateral
from core import DashboardAppTemplate

def load_css(file_name: str):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

class App:
    def __init__(self):
        st.set_page_config(
            page_title="Dashboard Interativo 2025 - RCE",
            page_icon="📊",
            layout="wide", 
            initial_sidebar_state="expanded"
        )
        
        # Configurar tema escuro
        st.markdown("""
            <style>
            .stApp {
                background-color: #1a1a2e;
                color: white;
            }
            .stSidebar {
                background-color: #0f0f23;
            }
            </style>
        """, unsafe_allow_html=True)
        

    def render_page(self, page_function):
        page_function()



    #! Boa pratica ao usar estrutura HTML e esta tudo no arquivo core.py
    # def run(self):
    #     Header().display()
        
    #     # Layout Principal
    #     sidebar = Sidebar(self.view_model)
    #     sidebar.display()
        
    #     Body(self.view_model).display()
    #     Footer().display()
        
    #     # Chatbot
    #     if st.session_state.show_chat:
    #         self.chatbot.display()


if __name__ == "__main__":

    


    app = App()
    template = DashboardAppTemplate()


    #! Sidebar
    DrawerMenuLateral()


    #! Carrega estilos
    #init_css()
    #load_css("style.css")


    #! Controle de navefação
    selected_page = st.sidebar.selectbox("Select Page",       
            [
                "Framework RCE",
                "Agendamentos de Redes Eletricas",
                "Analise de dados para testes benchmarking",
                "Pagina de formularios"

            ])
    pagina_selecionada = st.sidebar.radio(
            "Menu Navegação",
            [
                "Framework RCE",
                "Agendamentos de Redes Eletricas",
                "Analise de dados para testes benchmarking",
                "Pagina de formularios",
                "Template Dashboard"

            ]
        )
    
    print("pagina_selecionada", pagina_selecionada)


    if pagina_selecionada == "Framework RCE":
        app.render_page(RCEFrameworkPage)
    elif pagina_selecionada == "Agendamentos de Redes Eletricas":
        app.render_page(render_page_2)
    elif pagina_selecionada == "Analise de dados para testes benchmarking":
        app.render_page(home_page)
    elif pagina_selecionada == "Pagina de formularios":
        app.render_page(about_page)
    elif pagina_selecionada == "Template Dashboard":
        app.render_page(template.run())
    else:
        app.render_page(home_page)
    
    
