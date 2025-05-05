# main_app_functional.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_ace import st_ace # Editor de código
import io                     # Para capturar output de texto
import contextlib           # Para redirecionar stdout/stderr
import traceback            # Para formatar exceções

# --- Constantes ---
DEFAULT_PLOT_CODE = """
# O DataFrame carregado está na variável 'df'
# Use plt (matplotlib.pyplot) ou importe plotly.express as px

st.subheader("Visão Geral dos Dados")
st.write("Primeiras 5 linhas do DataFrame:", df.head())

# Tenta exibir informações do DataFrame (pode falhar se df for None inicialmente)
try:
    buffer = io.StringIO()
    df.info(buf=buffer)
    s = buffer.getvalue()
    st.text_area("Informações do DataFrame:", s, height=150)
except AttributeError:
    st.warning("Carregue dados para ver as informações do DataFrame.")


# Exemplo de Gráfico Matplotlib: Histograma da primeira coluna numérica
numeric_cols = df.select_dtypes(include='number').columns if df is not None else []
if len(numeric_cols) > 0:
    col_to_plot = numeric_cols[0]
    st.subheader(f"Histograma de '{col_to_plot}' (Matplotlib)")
    fig, ax = plt.subplots()
    # Garante que só plota se df não for None
    if df is not None and col_to_plot in df:
         ax.hist(df[col_to_plot].dropna(), bins=15) # dropna() para evitar erros com nulos
         ax.set_title(f'Histograma de {col_to_plot}')
         ax.set_xlabel(col_to_plot)
         ax.set_ylabel('Frequência')
         # A linha crucial para exibir o gráfico Matplotlib no Streamlit:
         st.pyplot(fig)
    else:
         st.warning(f"Coluna '{col_to_plot}' não encontrada ou dados não carregados.")

else:
    st.warning("Não foram encontradas colunas numéricas para plotar o histograma (ou dados não carregados).")

# Exemplo de Print
print("Exemplo de saída de texto: Análise concluída.")

# Você pode adicionar código Plotly aqui também:
# import plotly.express as px
# if len(numeric_cols) > 0:
#    st.subheader(f"Gráfico de Dispersão (Plotly)")
#    if len(numeric_cols) >= 2:
#       fig_plotly = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], title="Plotly Scatter Plot")
#       # A linha crucial para exibir o gráfico Plotly:
#       st.plotly_chart(fig_plotly)
#    else:
#       st.warning("São necessárias pelo menos 2 colunas numéricas para o gráfico de dispersão Plotly.")
"""

# --- Model Functions ---

def load_data(uploaded_file):
    """
    Carrega dados de um arquivo Excel ou CSV.
    Retorna uma tupla: (DataFrame, error_message).
    DataFrame é None se houver erro, error_message contém a descrição do erro.
    Minimiza side-effects diretos (st.warning/error).
    """
    if uploaded_file is None:
        return None, "Nenhum arquivo carregado."
    try:
        df = pd.read_excel(uploaded_file)
        return df, None
    except Exception as e_excel:
        error_msg_excel = f"Falha ao ler como Excel: {e_excel}."
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file)
            return df, f"{error_msg_excel} Carregado como CSV." # Retorna aviso como parte da mensagem
        except Exception as e_csv:
            return None, f"{error_msg_excel} Falha ao ler como CSV: {e_csv}. Verifique o formato."

def execute_user_code(code_string, df):
    """
    Executa o código Python do usuário e captura saídas e erros.
    Retorna um dicionário com 'stdout', 'stderr', 'error' (exceção), 'traceback'.
    Ainda impuro devido ao exec() e ao plot interno (st.pyplot/st.plotly_chart).
    """
    output_capture = io.StringIO()
    error_capture = io.StringIO()
    exec_error = None
    exec_traceback = None

    # --- CORREÇÃO AQUI ---
    # Adiciona o módulo 'io' ao escopo disponível para o código executado
    available_scope = {
        'st': st,
        'pd': pd,
        'plt': plt,
        'df': df,
        'io': io,  # Adiciona o módulo io ao escopo
        '__builtins__': __builtins__
    }
    # ---------------------

    # Importar plotly se necessário (opcional)
    # try:
    #     import plotly.express as px
    #     available_scope['px'] = px
    # except ImportError:
    #     pass # Plotly não está disponível

    try:
        with contextlib.redirect_stdout(output_capture):
            with contextlib.redirect_stderr(error_capture):
                # A plotagem (st.pyplot/st.plotly_chart) deve ocorrer aqui dentro
                exec(code_string, available_scope)
    except Exception as e:
        exec_error = e
        exec_traceback = traceback.format_exc()
    finally:
        stdout_output = output_capture.getvalue()
        stderr_output = error_capture.getvalue()
        output_capture.close()
        error_capture.close()
        plt.close('all') # Limpa figuras matplotlib

    return {
        'stdout': stdout_output,
        'stderr': stderr_output,
        'error': exec_error,
        'traceback': exec_traceback
    }

# --- View Functions ---

def setup_page():
    """Configura o título e layout da página e exibe o aviso de segurança."""
    #st.set_page_config(page_title='Editor Python Funcional', layout='wide')
    st.title('📊 Editor Python Interativo (Estilo Funcional)')
    st.warning("""
        ⚠️ **Aviso de Segurança:** Este aplicativo executa código Python inserido pelo usuário
        usando a função `exec()`. Isso é **inseguro** em ambientes não controlados.
        Use apenas para fins educacionais e com código de fontes confiáveis.
        """)

def render_sidebar():
    """Renderiza o conteúdo da barra lateral."""
    st.sidebar.header("Sobre")
    st.sidebar.info(
        "Aplicativo Streamlit refatorado para um estilo mais funcional, "
        "permitindo carregar dados, editar e executar código Python para gerar visualizações."
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Estrutura Funcional:**")
    st.sidebar.markdown("- **Model:** `load_data`, `execute_user_code`.")
    st.sidebar.markdown("- **View:** `setup_page`, `render_sidebar`, `render_editor_panel`, `render_results_panel`, `display_execution_results`.")
    st.sidebar.markdown("- **Controller:** Função `run_app` orquestrando as chamadas.")
    st.sidebar.markdown("---")
    st.sidebar.warning("**Lembrete de Segurança:** A execução de código via `exec()` é arriscada.")

def render_editor_panel(initial_code):
    """Renderiza o painel de upload e o editor de código. Retorna (uploaded_file, current_code)."""
    st.header("1. Carregar Dados")
    uploaded_file = st.file_uploader("Selecione um arquivo Excel (.xlsx) ou CSV (.csv)", type=['xlsx', 'csv'])

    st.header("2. Escrever Código Python")
    st.markdown("""
        Use `df` para o DataFrame, `plt` para Matplotlib, `st` para Streamlit.
        Chame `st.pyplot(fig)` ou `st.plotly_chart(fig)` para exibir gráficos.
        Use `print()` para saída de texto.
    """)

    current_code = st_ace(
        value=initial_code,
        language='python', theme='tomorrow_night', keybinding='vscode',
        min_lines=15, max_lines=35, font_size=14, tab_size=4,
        wrap=True, auto_update=False, key="code_editor"
    )
    return uploaded_file, current_code

def render_results_panel():
    """Renderiza a área de resultados e retorna os placeholders."""
    st.header("3. Resultados")
    # Usar colunas dentro da coluna direita pode ajudar a organizar plots e texto
    plot_col, text_col = st.columns(2)
    with plot_col:
        plot_placeholder = st.container()
        plot_placeholder.caption("Gráficos aparecerão aqui.") # Placeholder inicial
    with text_col:
        output_placeholder = st.container()
        output_placeholder.caption("Saída de texto e erros aparecerão aqui.") # Placeholder inicial

    # É importante notar que st.pyplot/st.plotly_chart chamados dentro do exec
    # vão renderizar onde o Streamlit decidir (geralmente no fluxo principal).
    # Se quisermos controle fino, teríamos que retornar a figura e plotar aqui.
    # Mantendo a simplicidade por enquanto.
    return plot_placeholder, output_placeholder # Retornar se precisarmos deles fora

def display_execution_results(results, output_container):
    """Exibe os resultados (stdout, stderr, errors) no container fornecido."""
    with output_container:
        # Limpa container anterior
        output_container.empty()
        st.subheader("Saídas da Execução")

        if results['stdout']:
            st.text_area("Saída Padrão (stdout):", value=results['stdout'], height=100, key="stdout_area")
        if results['stderr']:
            st.warning("Saída de Erro Padrão (stderr):")
            st.text_area("", value=results['stderr'], height=100, key="stderr_area")
        if results['error']:
            st.error(f"Erro de Execução: {type(results['error']).__name__}")
            st.exception(results['error']) # Mostra o traceback formatado do Streamlit
            # st.text_area("Traceback:", value=results['traceback'], height=200, key="traceback_area") # Alternativa
        if not results['stdout'] and not results['stderr'] and not results['error']:
            st.success("Código executado com sucesso, sem saídas de texto ou erros.")


# --- Controller / Main Application Function ---

def CodeEditorPage():
    """Função principal que orquestra a aplicação Streamlit."""

    setup_page()
    render_sidebar()

    # Inicializa o código no estado da sessão
    if 'user_code' not in st.session_state:
        st.session_state.user_code = DEFAULT_PLOT_CODE

    # Layout principal
    left_column, right_column = st.columns(2)

    with left_column:
        uploaded_file, current_editor_code = render_editor_panel(st.session_state.user_code)
        run_button = st.button("Executar Código", type="primary")

    with right_column:
         # Mesmo que a plotagem ocorra "globalmente", preparamos a área de texto
        _, output_placeholder = render_results_panel()

    # Lógica de execução (Controlador)
    if run_button:
        # 1. Atualizar o estado com o código do editor
        st.session_state.user_code = current_editor_code

        # 2. Validar Input
        if uploaded_file is None:
            st.warning("Por favor, carregue um arquivo Excel ou CSV primeiro.")
            st.stop() # Impede a execução do resto

        # 3. Carregar Dados (Model)
        df, error_msg = load_data(uploaded_file)

        # 4. Tratar Erro de Carregamento
        if error_msg and df is None: # Se houve erro fatal
             st.error(f"Erro ao carregar dados: {error_msg}")
             st.stop()
        elif error_msg and df is not None: # Se houve aviso (ex: carregou como CSV)
             st.info(f"Aviso no carregamento: {error_msg}")
             # Continua a execução

        # 5. Executar Código do Usuário (Model)
        if df is not None:
             # Limpar saídas de texto anteriores ANTES da execução
             # (a plotagem dentro do exec pode acontecer antes de chegarmos a display_results)
             output_placeholder.empty()
             output_placeholder.caption("Executando...") # Feedback

             with st.spinner("Executando código..."):
                 execution_results = execute_user_code(st.session_state.user_code, df)

             # 6. Exibir Resultados (View)
             # A plotagem já deve ter ocorrido via st.pyplot/st.plotly_chart dentro do exec
             # Agora exibimos stdout/stderr/errors
             display_execution_results(execution_results, output_placeholder)
        else:
             # Caso extremo onde df se tornou None após aviso (não deveria acontecer com a lógica atual)
             st.error("Não foi possível obter um DataFrame válido para executar o código.")


# --- Entry Point ---
if __name__ == "__main__":
    CodeEditorPage()