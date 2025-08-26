
import streamlit as st
from views.pages.themes import Theme
from views.Screens.RCE_Framework_Page import FrameworkRCEDashboard

import sys

import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config_backup import options_main_file




def DrawerSideBar():
    """Menu lateral único para navegação."""
    st.sidebar.title("🧭 Menu Dashboard")
    
    # logo da UFF
    st.sidebar.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRHVsZ1z9B-HIP8Ddsks0mP3aETeG1CkYixtA&s", width=800)
    st.sidebar.markdown("---")  # Separador visual

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
        pagina_selecionada = FrameworkRCEDashboard().run()
        app.run(pagina_selecionada) 

    except Exception as e:
        st.exception(e)
