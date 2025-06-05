
import streamlit as st
from views.pages.themes import Theme

from views.pages.screens import  RCEFrameworkPage, AgendamentosRedesPage, BenchmarkingPage,  TabExamplePage
from views.pages.FramewrokRCEDashboardPage import FrameworkRCEDashboard
from views.pages.c3po_chatbot_page import C3poChatbotPage
from views.pages.StreamlitDashbord import StreamlitDashboard
from views.pages.code_editor_page import CodeEditorPage
from views.pages.EasyPDF_page import EasyPDF



import sys
from pathlib import Path


#    !TODO GUI para interação com o usuário

#    1 - 256 conjuntos de parametros (4⁴) 
#    2 - 10 ou 20 numero de execucoes
#    3 - 4 parametros variando [Mutação, Crossover, Var DIFF, DELTA e restante fixo 
#    4 - 4 Caixas de texto fixas para esses parametros variando
#    5 - Criar checkbox para o usuario desabilitar as demais caixas de texto, deixando um valor possivel para aquele parametro 
#    6 - butao Radio para selecionar a tabela a configuração das 256 conjuntos
#    7 - Progress bar para cada geração em tempo de execução 




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


#! from ..config import  options_main_file

def OptionsEditor():
    """Interface para editar `options_main_file`."""
    st.subheader("Editar Configurações")
    options = st.session_state["current_options"]

    # Formulário para editar opções
    with st.form("options_editor"):
        options["name"] = st.text_input("Nome do Script", options["name"])
        options["key"] = st.checkbox("MUltiplas execuções Ativada", options["key"])
        
        if options["key"]:

            # Slider para quantidade de execuções
            options["value"] = st.slider("Quantidade de Execuções", 5, 30, options["value"])
        else:
            options["value"] = 1
        # Exibir opções de parâmetros

        # Editar parâmetros opcionais
        st.write("Parâmetros Opcionais:")
        for param in options["parametros_opcionais"]:
            for key, values in param.items():
                param[key] = st.multiselect(f"{key}:", values, default=values)

                text_field = st.text_input(
                    f"Editar {key} (separado por vírgulas):",
                    value=", ".join(map(str, values)),
                    key=f"{key}_input"
                )
                if text_field:
                    param[key] = [int(x) for x in text_field.split(",")]
        # Exibir opções editadas
        st.write("Opções Editadas:")
        st.json(options)
        

        # Botão para salvar alterações
        if st.form_submit_button("Salvar Alterações"):
            st.session_state["current_options"] = options
            st.success("Configurações atualizadas com sucesso!")




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
    app = App()  # Initialize app config and styling

    try:
    
        # Obter parâmetros de URL
        query_params = st.experimental_get_query_params()
        selected_page = query_params.get("page", ["framework_rce"])[0]
    
        # Renderizar a página selecionada
        pagina_selecionada = DrawerSideBar()
        app.run(pagina_selecionada)
    except Exception as e:
        print(e)

    finally:
    
        # Exibir editor de opções na página principal
        #OptionsEditor()
        print("Inicio do app")
