# app_rce.py
import streamlit as st
import subprocess
import pandas as pd
import os

st.set_page_config(layout="wide", page_title="Dashboard RCE Framework")

st.title("🚀 Dashboard de Execução do Framework RCE com Prefect")
st.markdown("Use esta interface para disparar e monitorar as execuções do seu algoritmo evolutivo.")

# --- PAINEL DE CONTROLE ---
st.sidebar.header("Painel de Controle")
tipo_execucao = st.sidebar.radio(
    "Selecione o tipo de execução:",
    ("Execução Única", "Múltiplas Execuções")
)

num_execucoes = 1
if tipo_execucao == "Múltiplas Execuções":
    num_execucoes = st.sidebar.number_input(
        "Número de execuções:", min_value=2, max_value=50, value=3, step=1
    )

if st.sidebar.button("▶️ EXECUTAR OTIMIZAÇÃO", use_container_width=True):
    
    st.info(f"Disparando {tipo_execucao}...")
    
    # Constrói o comando para chamar o script Prefect
    comando = ["python", "run_rce_prefect.py"]
    if tipo_execucao == "Múltiplas Execuções":
        comando.extend(["multipla", str(num_execucoes)])
    else:
        comando.append("unica")

    log_placeholder = st.empty()
    log_placeholder.code("Iniciando processo...\nComando: " + " ".join(comando))
    
    # Usando subprocess para executar o script e capturar o output em tempo real
    try:
        processo = subprocess.Popen(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        log_output = ""
        with log_placeholder.container():
            log_box = st.code(log_output, language='bash')
            for linha in iter(processo.stdout.readline, ''):
                log_output += linha
                log_box.text(log_output)
        
        processo.wait() # Espera o processo terminar
        
        if processo.returncode == 0:
            st.success("Execução do Prefect concluída com sucesso!")
        else:
            st.error(f"Ocorreu um erro durante a execução. Código de saída: {processo.returncode}")

    except FileNotFoundError:
        st.error("Erro: O script 'run_rce_prefect.py' não foi encontrado. Certifique-se de que ele está no mesmo diretório.")
    except Exception as e:
        st.error(f"Um erro inesperado ocorreu: {e}")


# --- PAINEL DE RESULTADOS ---
st.header("Resultados da Última Execução")

# Verifica se o arquivo de hash existe e o exibe
hash_file = "hash_table.xlsx"
if os.path.exists(hash_file):
    st.subheader("Tabela Hash de Resultados (Cache)")
    try:
        df_hash = pd.read_excel(hash_file)
        st.dataframe(df_hash.head(20)) # Mostra as 20 melhores soluções
        
        st.download_button(
            label="📥 Baixar Tabela Hash Completa (.xlsx)",
            data=open(hash_file, "rb").read(),
            file_name="hash_table_resultado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"Não foi possível ler o arquivo de resultados: {e}")
else:
    st.info("Nenhum resultado encontrado. Execute uma otimização para gerar a tabela hash.")