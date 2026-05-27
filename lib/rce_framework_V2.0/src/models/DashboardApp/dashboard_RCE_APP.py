
import sys
import os
from pathlib import Path

# Adiciona o diretório 'src' ao sys.path para encontrar 'tools' e 'views' (do projeto)
# src/models/DashboardApp/dashboard_RCE_APP.py -> src/
SRC_DIR = Path(__file__).resolve().parent.parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

import streamlit as st
from views.pages.themes import Theme
from views.Screens.RCE_Framework_Page import FrameworkRCEDashboard
from config import options_main_file


def DrawerSideBar():

    # Opções de páginas 
    page_options = {
        "⚡ Framework RCE ": FrameworkRCEDashboard(options_main_file).run,

        #"Dashboard Simulação de Contigencias": SimulacaoAnaliseContigenciasPage,
        #"Gerador de PDF": EasyPDF,
        #"Tela de Agendamentos de Redes": AgendamentoRedePage,
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
            page_title="UFF RCE WebAPP",
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
        # Passando a pagina que desejo exibir
        #pagina_selecionada = FrameworkRCEDashboard().run()
        #app.run(pagina_selecionada) 
        page = FrameworkRCEDashboard()
        page.run()

    except Exception as e:
        st.exception(e)
