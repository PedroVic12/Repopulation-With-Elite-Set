import streamlit as st
import pandas as pd
import streamlit as st
from DashboardApp.views.pages.themes import Theme

from DashboardApp.views.pages.AgendamentoRedePage import AgendamentoRedePage
from DashboardApp.views.pages.EasyPDF_page import EasyPDF
from DashboardApp.views.Screens.simulacao_redes_IEEE_page import SimulacaoAnaliseContigenciasPage

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import options_main_file




def DrawerSideBar():
    """Menu lateral único para navegação."""
    st.sidebar.title("🧭 Menu Dashboard")
    
    # logo da UFF
    st.sidebar.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRHVsZ1z9B-HIP8Ddsks0mP3aETeG1CkYixtA&s", width=800)
    st.sidebar.markdown("---")  # Separador visual

    # Opções de páginas 
    page_options = {
        #"⚡ Framework RCE ": FrameworkRCEDashboard(options_main_file).run,

        "Dashboard Simulação de Contigencias": SimulacaoAnaliseContigenciasPage,
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




def run( page_function):
        """Calls the function responsible for rendering the selected page."""
        # page_function might be a function or a method like template.run
        if callable(page_function):
            page_function()
        else:
            st.error("Invalid page function provided.")


if __name__ == "__main__":
    st.set_page_config(page_title="Simulador de Redes Elétricas", page_icon=":zap:", layout="wide")

    st.title("Simulador de Redes Elétricas")
    st.write("Este é um simulador para análise de redes elétricas.")

    # Exemplo de uso de DataFrame
    data = {
        "Elemento": ["Transformador", "Linha de Transmissão", "Subestação"],
        "Capacidade (MVA)": [100, 200, 150],
        "Status": ["Ativo", "Ativo", "Inativo"]
    }
    df = pd.DataFrame(data) 
    st.subheader("Dados da Rede Elétrica")
    st.dataframe(df)    

    pagina_selecionada = DrawerSideBar()
    #pagina_selecionada = AgendamentoRedePage()
    run(pagina_selecionada)
    
