import streamlit as st
import pandas as pd
import io  # Para manipulação de bytes em memória

# --- Funções Auxiliares ---
# Função para converter DataFrame para Excel em bytes (necessário para download)
def dataframe_to_excel_bytes(df):
    output = io.BytesIO()
    # Usar 'with' garante que o writer será fechado corretamente
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Produtos')
        # Não precisa chamar writer.save() ou writer.close() explicitamente com 'with'
    processed_data = output.getvalue()
    return processed_data

# --- Inicialização do Estado da Sessão ---
# Usamos o session_state para guardar os valores dos campos e
# permitir que o botão "Limpar" funcione corretamente.
default_values = {
    'codigo_produto': '',
    'marca_produto': '',
    'tipo_produto': '',
    'categoria_produto': '',
    'preco_unitario': 0.0,
    'custo_produto': 0.0,
    'observacao': '' # Adicionando um campo de observação como exemplo
}

for key, value in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Layout da Aplicação Streamlit ---
st.set_page_config(layout="wide") # Opcional: usa layout mais largo
st.title("📝 Formulário de Cadastro de Produtos (Streamlit)")
st.markdown("---")

# --- Formulário ---
# Usar colunas pode ajudar na organização, mas vamos fazer simples por enquanto
codigo = st.text_input("Código do Produto", key='codigo_produto')
marca = st.text_input("Marca do Produto", key='marca_produto')
tipo = st.text_input("Tipo do Produto", key='tipo_produto')
categoria = st.text_input("Categoria do Produto", key='categoria_produto')
preco = st.number_input("Preço Unitário do Produto", min_value=0.0, format="%.2f", key='preco_unitario', step=0.50)
custo = st.number_input("Custo do Produto", min_value=0.0, format="%.2f", key='custo_produto', step=0.50)
obs = st.text_area("Observação", key='observacao')

st.markdown("---")

# --- Botões de Ação ---
col1, col2, col_spacer = st.columns([2, 2, 5]) # Cria 3 colunas para os botões

with col1:
    # Botão para preparar os dados para Excel
    if st.button("💾 Preparar para Salvar em Excel", type="primary"):
        # Verifica se campos essenciais foram preenchidos (exemplo)
        if not st.session_state.codigo_produto or not st.session_state.marca_produto:
            st.warning("⚠️ Por favor, preencha pelo menos o Código e a Marca do Produto.")
        else:
            # Cria um dicionário com os dados do formulário (usando session_state)
            data = {
                'Código do Produto': [st.session_state.codigo_produto],
                'Marca do Produto': [st.session_state.marca_produto],
                'Tipo do Produto': [st.session_state.tipo_produto],
                'Categoria do Produto': [st.session_state.categoria_produto],
                'Preço Unitário': [st.session_state.preco_unitario],
                'Custo do Produto': [st.session_state.custo_produto],
                'Observação': [st.session_state.observacao]
            }
            # Converte o dicionário em DataFrame
            df = pd.DataFrame(data)

            # Armazena o DataFrame no estado da sessão para o botão de download usar
            st.session_state.df_pronto_para_download = df
            st.success("✅ Dados prontos! Clique em 'Baixar Excel' abaixo.")

with col2:
    # Botão para limpar os campos
    if st.button("🧹 Limpar Campos"):
        # Reseta os valores no session_state para os padrões
        for key in default_values.keys():
            st.session_state[key] = default_values[key]
        # Remove o dataframe pronto para download, se existir
        if 'df_pronto_para_download' in st.session_state:
            del st.session_state.df_pronto_para_download
        # Força o re-run do script para atualizar a interface
        st.rerun()

# --- Botão de Download (Aparece após clicar em "Preparar para Salvar") ---
if 'df_pronto_para_download' in st.session_state:
    st.markdown("---")
    df_para_baixar = st.session_state.df_pronto_para_download
    excel_bytes = dataframe_to_excel_bytes(df_para_baixar)

    st.download_button(
        label="⬇️ Baixar Arquivo Excel",
        data=excel_bytes,
        file_name='cadastro_produtos.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        # Ao clicar, podemos remover o estado para o botão sumir (opcional)
        on_click=lambda: st.session_state.pop('df_pronto_para_download', None)
    )

st.markdown("---")
# --- Explicação sobre PyAutoGUI ---
st.subheader("📌 Nota sobre o Script PyAutoGUI")
st.info(
    """
    O script Python com `pyautogui` que você compartilhou é para **automação de desktop**.
    Ele controla o mouse e teclado do seu computador para interagir com aplicativos, como o navegador.

    Esta aplicação Streamlit cria uma **interface web** e **não executa** o script `pyautogui`.
    Os dados inseridos aqui podem ser salvos em Excel, mas a automação do preenchimento no site original precisaria rodar o script `pyautogui` separadamente no seu PC.
    """
)