
import streamlit as st


# Componentes de Upload
def file_upload_component(key="upload-data"):
    st.subheader("Carregar Dados")
    uploaded_file = st.file_uploader(
        "Arraste e solte ou selecione os arquivos", 
        type=["csv", "xlsx", "xls"], 
        key=key
    )
    return uploaded_file

# Componente de Tabela
def data_table_component(df=None, key="data-table"):
    if df is None or df.empty:
        st.info("Nenhum dado disponível. Por favor, carregue um arquivo.")
        return
    
    st.dataframe(df, use_container_width=True, height=600)


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
