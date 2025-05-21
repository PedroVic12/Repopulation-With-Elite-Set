
import streamlit as st
from views.pages.themes import Theme

from views.pages.screens import  RCEFrameworkPage, AgendamentosRedesPage, BenchmarkingPage,  TabExamplePage
from views.pages.FramewrokRCEDashboardPage import FrameworkRCEDashboard
from views.pages.c3po_chatbot_page import C3poChatbotPage
from views.pages.StreamlitDashbord import StreamlitDashboard
from views.pages.code_editor_page import CodeEditorPage


import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))


options_main_file = st.session_state.get("current_options", {
    "name": "default python script",
    "key": True,
    "value": 3,
    "parametros_opcionais": [
        {"MUTACAO": [90,80,70, 60]},
        {"CROSSOVER": [5,10, 15, 20]},
        {"NUM_GENERATIONS": [100, 200, 300, 400]}
    ]
})


#from ..config import  options_main_file



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
    }

    # Navegação com rádio buttons
    selected_page = st.sidebar.radio(
        "Select a page:",
        options=list(page_options.keys()),
        key="main_nav_radio"
    )

    st.sidebar.markdown("---")
    st.sidebar.info("Select a page above to view its content.")

    # Retorna a função da página selecionada
    return page_options[selected_page]




# --- Main Application Class ---
class App:
    def __init__(self):
        st.set_page_config(
            page_title="UFF RCE Web App 2025",
            page_icon="📊",
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

    app = App() # Initialize app config and styling

    pagina_selecionada = DrawerSideBar()

    # Render the selected page by calling its function/method
    app.run(pagina_selecionada)