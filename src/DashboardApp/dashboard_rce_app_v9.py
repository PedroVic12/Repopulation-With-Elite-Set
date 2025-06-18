
import streamlit as st
from views.pages.themes import Theme

from views.pages.screens import  TabExamplePage
from views.pages.AgendamentoRedePage import AgendamentoRedePage
from views.pages.FramewrokRCEDashboardPage import FrameworkRCEDashboard
from views.pages.EasyPDF_page import EasyPDF

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import options_main_file

import sys



def DrawerSideBar():
    """Menu lateral único para navegação."""
    st.sidebar.title("🧭 Menu Dashboard")
    st.sidebar.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRHVsZ1z9B-HIP8Ddsks0mP3aETeG1CkYixtA&s", width=800)
    st.sidebar.markdown("---")  # Separador visual

    # Opções de páginas 
    page_options = {
        "⚡ Framework RCE": FrameworkRCEDashboard(options_main_file).run,
        #"🤖 C3po Chatbot": C3poChatbotPage,
        #"📊 Benchmarking Analysis": BenchmarkingPage,
        "📑 Tab Demonstration": TabExamplePage,
        #"📊 Python Editor": CodeEditorPage,
        "Gerador de PDF": EasyPDF,
        "Tela de Agendamentos de Redes": AgendamentoRedePage,
    }

    # Navegação com rádio buttons
    selected_page = st.sidebar.radio(
        "Select a page:",
        options=list(page_options.keys()),
        format_func=lambda x: x.replace("_", " ").title(),
        horizontal=True,
        key="main_nav_radio"
    )

    #st.experimental_get_query_params(page=selected_page)

    st.sidebar.markdown("---")
    st.sidebar.info("Select a page above to view its content.")

    # Retorna a função da página selecionada
    return page_options[selected_page]




# --- Main Application Class ---
class App:
    def __init__(self):
        st.set_page_config(
            page_title="UFF RCE Web App 2025",
            page_icon="⚡",
            layout="wide",
            initial_sidebar_state="collapsed"
        )

        st.markdown(Theme, unsafe_allow_html=True)

    def run(self, page_function):
        """Calls the function responsible for rendering the selected page."""
        # page_function might be a function or a method like template.run
        if callable(page_function):
            page_function()
        else:
            st.error("Invalid page function provided.")


# --- Main Execution ---
if __name__ == "__main__":
    app = App()  # Initialize app config and styling

    try:
        # Obter parâmetros de URL
        #query_params = st.experimental_get_query_params()
        #selected_page = query_params.get("page", ["framework_rce"])[0]
    
        # Renderizar a página selecionada
        pagina_selecionada = DrawerSideBar()
        app.run(pagina_selecionada)

    except Exception as e:
        print(e)

    finally:

        print("Aplicativo Streamlit carregado!")
