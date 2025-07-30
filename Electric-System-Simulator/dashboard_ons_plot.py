import streamlit as st
import pandas as pd
import pandapower as pp
import pandapower.networks as pn
import pandapower.plotting as plot
import matplotlib.pyplot as plt
import plotly.express as px

# --- Configuração da Página ---
st.set_page_config(
    page_title="Análise Interativa de Redes Elétricas",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Classe de Lógica da Rede (Corrigida) ---
class RedeEletricaPandaPower:
    """
    Encapsula a lógica de análise de redes elétricas com Pandapower.
    """
    def __init__(self, network_name="case14"):
        self.network_name = network_name
        self.net = self.carregar_rede(network_name)

    def carregar_rede(self, network_name):
        """Carrega uma rede de teste do pandapower."""
        try:
            if network_name == "case14":
                return pn.case14()
            elif network_name == "case30":
                return pn.case_ieee30()
            elif network_name == "case57":
                return pn.case57()
            elif network_name == "case118":
                return pn.case118()
            else:
                st.error(f"Rede '{network_name}' não reconhecida. Usando 'case14'.")
                return pn.case14()
        except Exception as e:
            st.error(f"Falha ao carregar a rede: {e}")
            # Retorna uma rede vazia em caso de falha para evitar mais erros
            return pp.create_empty_network()


    def executar_fluxo_de_carga(self):
        """Executa o fluxo de carga e retorna o status de convergência."""
        try:
            pp.runpp(self.net, algorithm="nr", numba=True)
            return True, None
        except pp.LoadflowNotConverged:
            return False, "Fluxo de Potência não convergiu. O sistema pode estar instável ou sobrecarregado."
        except Exception as e:
            return False, f"Ocorreu um erro inesperado: {e}"

    def aplicar_contingencia(self, tipo_elemento, elemento_id):
        """Aplica uma contingência desligando um elemento da rede."""
        if tipo_elemento == 'Linha' and elemento_id in self.net.line.index:
            self.net.line.loc[elemento_id, 'in_service'] = False
        elif tipo_elemento == 'Transformador' and elemento_id in self.net.trafo.index:
            self.net.trafo.loc[elemento_id, 'in_service'] = False

# --- Classe Repositório de Dados ---
class ResultsRepository:
    """
    Classe para buscar e formatar os dados de resultados da rede para os gráficos.
    """
    def __init__(self, net):
        if net is None or not hasattr(net, 'res_bus') or net.res_bus.empty:
            raise ValueError("A rede pandapower não foi simulada ou não contém resultados.")
        self.net = net

    def get_bus_voltage_data(self):
        """Retorna um DataFrame com os dados de tensão das barras."""
        df = self.net.res_bus[['vm_pu']].copy()
        df = df.reset_index().rename(columns={'index': 'Barra', 'vm_pu': 'Tensão (p.u.)'})
        return df

    def get_line_loading_data(self):
        """Retorna um DataFrame com os dados de carregamento das linhas."""
        df = self.net.res_line[['loading_percent']].copy()
        df = df.reset_index().rename(columns={'index': 'Linha', 'loading_percent': 'Carregamento (%)'})
        return df

    def get_trafo_loading_data(self):
        """Retorna um DataFrame com os dados de carregamento dos transformadores."""
        if not hasattr(self.net, 'res_trafo') or self.net.res_trafo.empty:
            return pd.DataFrame(columns=['Transformador', 'Carregamento (%)'])
        df = self.net.res_trafo[['loading_percent']].copy()
        df = df.reset_index().rename(columns={'index': 'Transformador', 'loading_percent': 'Carregamento (%)'})
        return df

# --- Funções de Plotagem ---
def plotar_rede(net):
    """Cria e retorna uma figura Matplotlib do diagrama da rede."""
    fig, ax = plt.subplots(figsize=(10, 8))
    try:
        # Usar o nome da rede que está guardado no objeto
        titulo = f"Diagrama da Rede: {net.name.upper() if hasattr(net, 'name') and net.name else 'Desconhecida'}"
        plot.simple_plot(net, ax=ax, bus_size=0.6, line_width=2.0)
        ax.set_title(titulo, fontsize=16)
    except Exception as e:
        ax.text(0.5, 0.5, f"Erro ao plotar a rede:\n{e}", ha='center', va='center')
    return fig


def plotar_grafico_barra_plotly(df, x, y, titulo):
    """Cria um gráfico de barras interativo com Plotly."""
    fig = px.bar(df, x=x, y=y, title=titulo, text_auto='.2f')
    fig.update_traces(textposition='outside')
    fig.update_layout(
        title_x=0.5,
        xaxis_title=x,
        yaxis_title=y,
        height=400,
        xaxis={'type': 'category'} # Garante que o eixo X é tratado como categórico
    )
    return fig

# --- Interface Principal do Streamlit ---
st.title("⚡ Dashboard Interativo para Análise de Contingências")
st.markdown("Use os controles na barra lateral para simular falhas e analisar o impacto no sistema elétrico.")

# --- Barra Lateral de Controles ---
with st.sidebar:
    st.header("Parâmetros da Simulação")

    nome_rede = st.selectbox(
        "Selecione a Rede Elétrica:",
        ("case14", "case30", "case57", "case118"),
        key="rede_selecionada"
    )

    if 'rede_eletrica' not in st.session_state or st.session_state.rede_eletrica.network_name != nome_rede:
        with st.spinner(f"Carregando a rede {nome_rede}..."):
            st.session_state.rede_eletrica = RedeEletricaPandaPower(nome_rede)

    rede = st.session_state.rede_eletrica

    st.subheader("Análise de Contingência (N-1)")

    tipo_elemento = st.radio(
        "Tipo de Elemento para Desligar:",
        ('Nenhum', 'Linha', 'Transformador'),
        key="tipo_contingencia",
        horizontal=True
    )

    elemento_id = None
    if tipo_elemento == 'Linha':
        linhas_disponiveis = rede.net.line.index
        elemento_id = st.selectbox(
            "Selecione a Linha:",
            linhas_disponiveis,
            format_func=lambda x: f"Linha {x} (Barra {rede.net.line.at[x, 'from_bus']} ↔ Barra {rede.net.line.at[x, 'to_bus']})"
        )
        rede.aplicar_contingencia('Linha', elemento_id)

    elif tipo_elemento == 'Transformador':
        trafos_disponiveis = rede.net.trafo.index
        if not trafos_disponiveis.empty:
            elemento_id = st.selectbox(
                "Selecione o Transformador:",
                trafos_disponiveis,
                format_func=lambda x: f"Trafo {x} (Barra {rede.net.trafo.at[x, 'hv_bus']} ↔ Barra {rede.net.trafo.at[x, 'lv_bus']})"
            )
            rede.aplicar_contingencia('Transformador', elemento_id)
        else:
            st.warning("Esta rede não possui transformadores para análise.")

# --- Execução da Análise e Exibição dos Resultados ---
with st.spinner("Executando fluxo de potência..."):
    convergiu, mensagem_erro = rede.executar_fluxo_de_carga()

if not convergiu:
    st.error(f"**Falha na Simulação:** {mensagem_erro}")
else:
    st.success("**Simulação concluída com sucesso!**")
    
    try:
        repo = ResultsRepository(rede.net)
        col_plot, col_analise = st.columns([1, 1.2])

        with col_plot:
            st.subheader("Diagrama da Rede Elétrica")
            fig_rede = plotar_rede(rede.net)
            st.pyplot(fig_rede)

        with col_analise:
            st.subheader("Resultados da Análise")
            
            tab1, tab2, tab3 = st.tabs([
                "📊 Tensões nas Barras", 
                "📈 Carregamento das Linhas", 
                "📈 Carregamento dos Transformadores"
            ])

            with tab1:
                st.markdown("##### Análise de Tensão (p.u.)")
                df_tensao = repo.get_bus_voltage_data()
                
                fig_tensao_plotly = plotar_grafico_barra_plotly(df_tensao, 'Barra', 'Tensão (p.u.)', 'Tensão por Barra (p.u.)')
                st.plotly_chart(fig_tensao_plotly, use_container_width=True)
                st.dataframe(df_tensao, use_container_width=True)

            with tab2:
                st.markdown("##### Análise de Carregamento de Linhas (%)")
                df_linhas = repo.get_line_loading_data()


                fig_linhas_plotly = plotar_grafico_barra_plotly(df_linhas, 'Linha', 'Carregamento (%)', 'Carregamento das Linhas (%)')
                st.plotly_chart(fig_linhas_plotly, use_container_width=True)
                st.dataframe(df_linhas, use_container_width=True)

            with tab3:
                st.markdown("##### Análise de Carregamento de Transformadores (%)")
                df_trafos = repo.get_trafo_loading_data()

                if df_trafos.empty:
                    st.info("Não há transformadores nesta rede para exibir resultados.")
                else:
                    fig_trafos_plotly = plotar_grafico_barra_plotly(df_trafos, 'Transformador', 'Carregamento (%)', 'Carregamento dos Transformadores (%)')
                    st.plotly_chart(fig_trafos_plotly, use_container_width=True)
                    st.dataframe(df_trafos, use_container_width=True)
    
    except ValueError as e:
        st.error(f"Erro ao processar os resultados: {e}")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao exibir os resultados: {e}")

