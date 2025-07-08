import streamlit as st
import pandas as pd
import pandapower as pp
import pandapower.networks as pn
import pandapower.plotting as plot
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard de Análise de Redes Elétricas",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Classe de Lógica da Rede ---
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
            return pp.create_empty_network()

    def resetar_rede(self):
        """Restaura a rede para o estado operacional religando todos os elementos."""
        self.net.line['in_service'] = True
        if not self.net.trafo.empty:
            self.net.trafo['in_service'] = True

    def executar_fluxo_de_carga(self):
        """Executa o fluxo de carga e retorna o status de convergência."""
        try:
            pp.runpp(self.net, algorithm="nr", numba=True)
            return True, None
        except pp.LoadflowNotConverged:
            return False, "Fluxo de Potência não convergiu."
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
    Classe para buscar e formatar os dados de resultados da rede para os gráficos e KPIs.
    """
    def __init__(self, net):
        if net is None or not hasattr(net, 'res_bus') or net.res_bus.empty:
            raise ValueError("A rede pandapower não foi simulada ou não contém resultados.")
        self.net = net

    def get_kpis(self):
        """Calcula e retorna os principais indicadores (KPIs) da rede."""
        kpis = {
            "total_load_mw": self.net.res_load.p_mw.sum(),
            "total_gen_mw": self.net.res_gen.p_mw.sum(),
            "voltage_violations": len(self.net.res_bus[self.net.res_bus.vm_pu > self.net.bus.max_vm_pu]) + \
                                  len(self.net.res_bus[self.net.res_bus.vm_pu < self.net.bus.min_vm_pu]),
            "overloads": len(self.net.res_line[self.net.res_line.loading_percent > 100]) + \
                         len(self.net.res_trafo[self.net.res_trafo.loading_percent > 100] if hasattr(self.net, 'res_trafo') else [])
        }
        return kpis

    def get_centralized_generation_data(self):
        """Retorna um DataFrame com os dados de Geração Centralizada (baseado na imagem ONS)."""
        data = {
            'Fonte': ['Hidráulica', 'Eólica', 'Fotovoltaica', 'Térmica', 'Nuclear'],
            'Geração (MW)': [31675, 16416, 6719, 7531, 1365]
        }
        return pd.DataFrame(data)

    def get_distributed_generation_data(self):
        """Retorna um DataFrame com os dados de Geração Distribuída (baseado na imagem ONS)."""
        data = {
            'Fonte': ['MMGD', 'PCH', 'PCT'],
            'Geração (MW)': [10316, 2816, 2054]
        }
        return pd.DataFrame(data)

    def get_bus_voltage_data(self):
        df = self.net.res_bus[['vm_pu']].copy()
        df = df.reset_index().rename(columns={'index': 'Barra', 'vm_pu': 'Tensão (p.u.)'})
        return df

    def get_line_loading_data(self):
        df = self.net.res_line[['loading_percent']].copy()
        df = df.reset_index().rename(columns={'index': 'Linha', 'loading_percent': 'Carregamento (%)'})
        return df

    def get_trafo_loading_data(self):
        if not hasattr(self.net, 'res_trafo') or self.net.res_trafo.empty:
            return pd.DataFrame(columns=['Transformador', 'Carregamento (%)'])
        df = self.net.res_trafo[['loading_percent']].copy()
        df = df.reset_index().rename(columns={'index': 'Transformador', 'loading_percent': 'Carregamento (%)'})
        return df

# --- Funções de Plotagem ---
def plotar_rede(net):
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_facecolor("#f0f2f6")
    fig.patch.set_facecolor("#f0f2f6")
    try:
        titulo = f"Diagrama da Rede: {net.name.upper() if hasattr(net, 'name') and net.name else 'Desconhecida'}"
        plot.simple_plot(net, ax=ax, bus_size=0.6, line_width=2.0)
        ax.set_title(titulo, fontsize=16)
    except Exception as e:
        ax.text(0.5, 0.5, f"Erro ao plotar a rede:\n{e}", ha='center', va='center')
    return fig

def plotar_grafico_barra_plotly(df, x, y, titulo):
    fig = px.bar(df, x=x, y=y, title=titulo, text_auto='.2f')
    fig.update_traces(textposition='outside')
    fig.update_layout(title_x=0.5, xaxis_title=None, yaxis_title=y, height=350, xaxis={'type': 'category'})
    return fig

def plotar_grafico_donut_plotly(df, values, names, titulo):
    fig = go.Figure(data=[go.Pie(labels=df[names], values=df[values], hole=.4, textinfo='percent+label')])
    fig.update_layout(title_text=titulo, title_x=0.5, height=350, showlegend=False)
    return fig

# --- Interface Principal do Streamlit ---
st.title("⚡ Dashboard de Análise de Contingências Elétricas")

# --- Barra Lateral de Controles ---
with st.sidebar:
    st.header("Parâmetros da Simulação")
    nome_rede = st.selectbox("Selecione a Rede Elétrica:", ("case14", "case30", "case57", "case118"), key="rede_selecionada")

    if 'rede_eletrica' not in st.session_state or st.session_state.rede_eletrica.network_name != nome_rede:
        with st.spinner(f"Carregando a rede {nome_rede}..."):
            st.session_state.rede_eletrica = RedeEletricaPandaPower(nome_rede)

    rede = st.session_state.rede_eletrica
    rede.resetar_rede()

    st.subheader("Análise de Contingência (N-1)")
    tipo_elemento = st.radio("Tipo de Elemento para Desligar:", ('Nenhum', 'Linha', 'Transformador'), key="tipo_contingencia", horizontal=True)

    if tipo_elemento == 'Linha':
        elemento_id = st.selectbox("Selecione a Linha:", rede.net.line.index, format_func=lambda x: f"Linha {x} ({rede.net.line.at[x, 'from_bus']}↔{rede.net.line.at[x, 'to_bus']})")
        rede.aplicar_contingencia('Linha', elemento_id)
    elif tipo_elemento == 'Transformador':
        if not rede.net.trafo.empty:
            elemento_id = st.selectbox("Selecione o Transformador:", rede.net.trafo.index, format_func=lambda x: f"Trafo {x} ({rede.net.trafo.at[x, 'hv_bus']}↔{rede.net.trafo.at[x, 'lv_bus']})")
            rede.aplicar_contingencia('Transformador', elemento_id)
        else:
            st.warning("Esta rede não possui transformadores.")

# --- Execução da Análise ---
with st.spinner("Executando fluxo de potência..."):
    convergiu, mensagem_erro = rede.executar_fluxo_de_carga()

if not convergiu:
    st.error(f"**Falha na Simulação:** {mensagem_erro}")
else:
    st.success("**Simulação concluída com sucesso!**")
    
    try:
        repo = ResultsRepository(rede.net)
        kpis = repo.get_kpis()

        # --- Painel de Métricas (KPIs) ---
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Carga Total (MW)", f"{kpis['total_load_mw']:.2f}")
        col2.metric("Geração Total (MW)", f"{kpis['total_gen_mw']:.2f}")
        col3.metric("Violações de Tensão", f"{kpis['voltage_violations']}", delta=kpis['voltage_violations'], delta_color="inverse")
        col4.metric("Sobrecargas (Linha/Trafo)", f"{kpis['overloads']}", delta=kpis['overloads'], delta_color="inverse")
        st.divider()

        # --- Layout Principal ---
        col_esq, col_dir = st.columns([0.8, 1.2], gap="large")

        with col_esq:

            st.subheader("Simulação da Rede")
            fig_rede = plotar_rede(rede.net)
            st.pyplot(fig_rede)



        with col_dir:

                        # --- Abas com Análises Detalhadas ---
            st.subheader("Resultados Detalhados da Simulação")
            tab1, tab2, tab3 = st.tabs(["📊 Tensões nas Barras", "📈 Carregamento das Linhas", "📈 Carregamento dos Transformadores"])

            with tab1:
                df_tensao = repo.get_bus_voltage_data()
                fig_tensao = plotar_grafico_barra_plotly(df_tensao, 'Barra', 'Tensão (p.u.)', 'Tensão por Barra (p.u.)')
                st.plotly_chart(fig_tensao, use_container_width=True)
                with st.expander("Ver dados de tensão"):
                    st.dataframe(df_tensao, use_container_width=True)

            with tab2:
                df_linhas = repo.get_line_loading_data()
                fig_linhas = plotar_grafico_barra_plotly(df_linhas, 'Linha', 'Carregamento (%)', 'Carregamento das Linhas (%)')
                st.plotly_chart(fig_linhas, use_container_width=True)
                with st.expander("Ver dados de carregamento de linhas"):
                    st.dataframe(df_linhas, use_container_width=True)

            with tab3:
                df_trafos = repo.get_trafo_loading_data()
                if df_trafos.empty:
                    st.info("Não há transformadores nesta rede para exibir resultados.")
                else:
                    fig_trafos = plotar_grafico_barra_plotly(df_trafos, 'Transformador', 'Carregamento (%)', 'Carregamento dos Transformadores (%)')
                    st.plotly_chart(fig_trafos, use_container_width=True)
                    with st.expander("Ver dados de carregamento de transformadores"):
                        st.dataframe(df_trafos, use_container_width=True)
                        
            st.subheader("Visualização do Sistema")
            
            # --- Diagrama e Gráficos de Geração ---
            c1, c2 = st.columns(2)
            with c1:
                df_centralizada = repo.get_centralized_generation_data()
                fig_centralizada = plotar_grafico_donut_plotly(df_centralizada, "Geração (MW)", "Fonte", "Geração Centralizada (81%)")
                st.plotly_chart(fig_centralizada, use_container_width=True)
            
            with c2:
                df_distribuida = repo.get_distributed_generation_data()
                fig_distribuida = plotar_grafico_donut_plotly(df_distribuida, "Geração (MW)", "Fonte", "Geração Distribuída (19%)")
                st.plotly_chart(fig_distribuida, use_container_width=True)

            st.subheader("Resumo de Análise do Cenário da Rede")
            st.markdown("""
            Este painel oferece uma visão interativa do estado do sistema elétrico. Use os controles na barra lateral para simular cenários e avaliar a segurança da rede.

            **Componentes do Dashboard:**
            - **Indicadores (KPIs):** Resumo da situação atual, incluindo carga, geração e alertas de violações.
            - **Diagrama da Rede:** Topologia do sistema elétrico selecionado.
            - **Mix de Geração:** Detalha a matriz energética do cenário base, inspirado no painel do ONS.
            - **Resultados da Análise (Abas):** Monitoramento de tensões e carregamento de equipamentos.

            Use a simulação de contingência (N-1) para desligar um elemento e observar como o sistema reage à falha.
            """)


            
            

    
    except ValueError as e:
        st.error(f"Erro ao processar os resultados: {e}")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao exibir os resultados: {e}")
        st.exception(e)

