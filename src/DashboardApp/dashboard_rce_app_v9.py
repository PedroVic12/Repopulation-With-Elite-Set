
import streamlit as st
from views.pages.themes import Theme

from views.pages.screens import  RCEFrameworkPage, AgendamentosRedesPage, BenchmarkingPage,  TabExamplePage
from views.pages.FramewrokRCEDashboardPage import FrameworkRCEDashboard
from views.pages.c3po_chatbot_page import C3poChatbotPage
from views.pages.StreamlitDashbord import StreamlitDashboard




def DrawerSideBar():
    """Placeholder for a sidebar class to manage navigation and settings."""

    # --- Sidebar Navigation ---
    st.sidebar.title("🧭 Side Bar Navigation")
    st.sidebar.markdown("---") # Separator

    dashboard = FrameworkRCEDashboard()
    template = DashboardAppTemplate()
    home_page = StreamlitDashboard()

    # Combine page options into a dictionary for cleaner mapping
    # Key: Display Name, Value: Function/Method to call
    page_options = {
        "🧩 Core Template": template.run, # Reference the method directly
        "🤖 C3po Chatbot":C3poChatbotPage,
       #" ⚡Framework RCE": dashboard.run(),

       # "📊 Benchmarking Analysis": BenchmarkingPage,
       #⚡ Old Dash": home_page.HomePage()
        "📑 Tab Demonstration": TabExamplePage,
    }

    # Use radio buttons for page selection
    pagina_selecionada_key = st.sidebar.radio(
        "Select Page:",
        options=list(page_options.keys()), # Get the display names for options
        key="main_nav_radio" # Unique key for the widget
    )

    st.sidebar.markdown("---")
    st.sidebar.info("Select a page above to view its content.")

    # --- Page Rendering ---
    # Get the function/method associated with the selected display name
    page_to_render = page_options[pagina_selecionada_key]

    return st.sidebar, page_to_render # Return the function/method to be called


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
            initial_sidebar_state="expanded"
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

    menu_lateral, pagina_selecionada = DrawerSideBar()

    # Render the selected page by calling its function/method
    app.run(pagina_selecionada)