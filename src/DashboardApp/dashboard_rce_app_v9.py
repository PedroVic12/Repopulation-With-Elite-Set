
import streamlit as st
from views.pages.themes import Theme

from views.pages.screens import  RCEFrameworkPage, AgendamentosRedesPage, BenchmarkingPage,  TabExamplePage
from views.pages.FramewrokRCEDashboardPage import FrameworkRCEDashboard
from views.pages.c3po_chatbot_page import C3poChatbotPage
from views.pages.StreamlitDashbord import StreamlitDashboard
from views.pages.code_editor_page import CodeEditorPage



def DrawerSideBar():
    """Menu lateral único para navegação."""
    st.sidebar.title("🧭 Side Bar Navigation")
    st.sidebar.markdown("---")  # Separador visual

    # Opções de páginas
    page_options = {
        "⚡ Framework RCE": FrameworkRCEDashboard().run,
        #"🤖 C3po Chatbot": C3poChatbotPage,
        #"📊 Benchmarking Analysis": BenchmarkingPage,
        "📑 Tab Demonstration": TabExamplePage,
        "📊 Python Editor": CodeEditorPage,
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


# ---Core Template ---
class DashboardAppTemplate:
    """Placeholder for a more complex dashboard structure/template."""
    def run(self):
        st.title("🧩 Core Dashboard Template Page")
        st.write("This content comes from the `DashboardAppTemplate.run()` method.")
        st.info("This demonstrates how you might integrate a reusable dashboard class structure.")


# --- Main Application Class ---
class App:
    def __init__(self):
        st.set_page_config(
            page_title="Clean Dashboard App",
            page_icon="📊",
            layout="wide",
            #initial_sidebar_state="expanded"
        )

        # Apply dark theme using Streamlit's base themes and CSS override
        # The below CSS is a simple attempt; for full control, more specific CSS is needed.
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