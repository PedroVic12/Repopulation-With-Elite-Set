import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import numpy as np
import datetime
from streamlit_timeline import st_timeline
import ast

from .components.dashboard_config import get_config


#! Refatorar os novos componentes
# from .components.dash_rce_components import  StatisticsTableComponent


class StatisticsTableComponent:
    """Componente para exibir a tabela de estatísticas por geração."""

    @staticmethod
    def render(data):
        if data.empty:
            st.info("Não há dados de estatísticas por geração para exibir.")
            return
        try:
            if isinstance(data, pd.DataFrame):
                df = data
            else:
                df = pd.DataFrame(data)
            st.dataframe(df)
        except Exception as e:
            st.error(f"Não foi possível exibir tabela de estatísticas: {e}")


# --- Adiciona o diretório raiz ao path para encontrar os módulos ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from tools.database_controller import DatabaseController, ConsolidationManager

# print(f"Dashboard importing database_controller from: {DatabaseController.__module__}")
# print(BASE_DIR)

import streamlit.components.v1 as components
import os


def card_metric(label, value, bg_color, icon="fas fa-asterisk"):

    # referencia
    # https://py.cafe/maartenbreddels/streamlit-custom-metrics

    fontsize = 18
    valign = "left"
    lnk = '<link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.12.1/css/all.css" crossorigin="anonymous">'

    bg_color_css = f"rgb({bg_color[0]}, {bg_color[1]}, {bg_color[2]}, 0.75)"

    htmlstr = f"""<p style='background-color: {bg_color_css}; 
                            font-size: {fontsize}px; 
                            border-radius: 7px; 
                            padding-left: 12px; 
                            padding-top: 18px; 
                            padding-bottom: 18px; 
                            line-height:25px;'>
                            <i class='{icon} fa-xs'></i> {value}
                            </style><BR><span style='font-size: 14px; 
                            margin-top: 0;'>{label}</style></span></p>"""

    st.markdown(lnk + htmlstr, unsafe_allow_html=True)


def render_metrics():
    green = (0, 204, 102)
    red = (204, 0, 102)
    icon_error = "fas fa-bug"
    icon_observation = "fas fa-asterisk"

    card_metric("Observations", 123, green)
    card_metric("Errors", 13, red, icon_error)

    st.markdown("# Render my card metrics components in columns")

    col1, col2 = st.columns(2)
    with col1:
        card_metric("Observations", 123, green, icon_observation)
    with col2:
        card_metric("Errors", 13, red, icon_error)


def CardsSolutions(results_data: dict):
    """
    Renderiza os cartões com os principais resultados da solução e as
    variáveis de decisão, incluindo um tooltip para horários > 24h.
    """
    st.subheader("Solução de melhores horários de agendamento para o SEP")

    # CSS do st.metric
    st.markdown(
        """
    <style>
    div[data-testid="stMetricValue"] > div {
        font-size: 10; 
    }
    div[data-testid="stMetricLabel"] > div{
        font-size: 40;
                
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # render_metrics()

    # Cria duas colunas principais para o layout
    left_col, right_col = st.columns([1, 1])  # A coluna da direita é mais larga

    # Coluna da esquerda para as métricas principais
    with left_col:
        with st.container(border=False):
            st.metric(
                "🏆 Melhor Fitness",
                f"{results_data.get('best_fitness', 0):.2f}",
                border=True,
            )
            st.metric(
                "Função aptidão usada",
                f"{results_data.get('Funcao_objetivo', 'N/A').upper()}",
                border=True,
            )

    # Coluna da direita para as variáveis de decisão
    with right_col:
        with st.container(border=False):
            st.metric(
                "⏳ Melhor Geração",
                f"{results_data.get('best_gen_idx', 'N/A')}",
                border=True,
            )
            st.metric(
                "⏱️ Tempo de Execução",
                f"{results_data.get('Tempo_total_execucao', 'N/A')}",
                border=True,
            )

    st.subheader("**Melhores Variáveis de Decisão (Horários)**")
    solution_variables = results_data.get("best_variables", [])
    if not solution_variables:
        st.info("Nenhuma variável de decisão encontrada.")
        return

    # Cria uma linha de colunas dentro da coluna da direita para as variáveis
    var_cols = st.columns(len(solution_variables))
    for i, (col, var) in enumerate(zip(var_cols, solution_variables)):
        with col:
            with st.container(border=True):
                tooltip_text = None
                # Certifica que a variável é tratada como float
                try:
                    var_value = float(var)
                except (ValueError, TypeError):
                    var_value = 0.0  # Valor padrão em caso de erro

                # Adiciona o tooltip se o valor for maior que 24
                if var_value > 24:
                    dias = int(var_value // 24)
                    horas = var_value % 24
                    dia_str = "dia seguinte" if dias == 1 else f"{dias} dias depois"
                    tooltip_text = f"Equivale a: {dias*24}h + {horas:.2f}h ({dia_str})"

                st.metric(
                    label=f"Var {i+1}",
                    value=f"{var_value:.2f}",
                    help=tooltip_text,  # O parâmetro 'help' cria o tooltip
                    delta_color="inverse",
                )


def AgendamentoRedePage(results_data: dict, run_config_key: str, exec_num: int):
    """
    Renderiza o componente da linha do tempo interativa e seus detalhes.
    """
    st.subheader("🗓️ Linha do Tempo Interativa do Agendamento")

    # 1. Tenta carregar pelo nome de arquivo específico salvo no JSON de resultados
    excel_name = results_data.get("agendamento_excel_file")
    base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
    
    agendamento_info = []
    
    if excel_name:
        excel_path = base_dir / "output" / excel_name
        if excel_path.exists():
            try:
                df_ag = pd.read_excel(excel_path)
                agendamento_info = df_ag.to_dict(orient="records")
                st.info(f"✅ Dados carregados da execução específica: `{excel_name}`")
            except Exception as e:
                st.error(f"Erro ao ler Excel da execução: {e}")

    # 2. Se não encontrou o específico, tenta o padrão (fallback)
    if not agendamento_info:
        func_name = results_data.get("fitness_function", "funcao_objetivo_IEEE30")
        fallback_path = base_dir / "output" / f"resultados_agendamento_{func_name}.xlsx"
        if fallback_path.exists():
            try:
                df_ag = pd.read_excel(fallback_path)
                agendamento_info = df_ag.to_dict(orient="records")
                st.warning(f"⚠️ Usando arquivo de fallback (pode estar desatualizado): `{fallback_path.name}`")
            except Exception as e:
                st.error(f"Erro ao ler Excel de fallback: {e}")
    
    # 3. Fallback final para o agendamento_info do JSON
    if not agendamento_info:
        agendamento_info = results_data.get("agendamento_info", [])

    items = []
    base_date = datetime.datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    if agendamento_info:
        for i, entry in enumerate(agendamento_info):
            ramo = entry.get("ramo")
            if not ramo:
                ramo_from = entry.get("ramo_desligado_from")
                ramo_to = entry.get("ramo_desligado_to")
                ramo = f"[{ramo_from}, {ramo_to}]" if ramo_from and ramo_to else f"ID {i}"

            inicio = entry.get("inicio")
            duracao = entry.get("duracao")
            perfil = entry.get("perfil") # 0: Leve, 1: Média, 2: Pesada

            if inicio is None or duracao is None:
                continue

            if isinstance(inicio, str) and ":" in inicio:
                inicio = int(inicio.split(":")[0])
            
            # Lógica de Cores por Patamar de Carga
            # 🟢 Leve (0-8h), 🟡 Média (8-18h), 🔴 Pesada (18-24h)
            # Se vier do cenario, usamos o perfil. Se não, baseamos no horário.
            if perfil == 0 or (perfil is None and float(inicio) < 8):
                emoji = "🟢"
                label_perfil = "Leve"
            elif perfil == 1 or (perfil is None and float(inicio) < 18):
                emoji = "🟡"
                label_perfil = "Média"
            else:
                emoji = "🔴"
                label_perfil = "Pesada"

            items.append(
                {
                    "id": i,
                    "content": f"{emoji} Ramo {ramo}",
                    "start": (base_date + datetime.timedelta(hours=float(inicio))).isoformat(),
                    "end": (base_date + datetime.timedelta(hours=float(inicio) + float(duracao))).isoformat(),
                    "title": f"Perfil: {label_perfil} | Início: {inicio}h | Duração: {duracao}h",
                    "group": i % 3 # Opcional: agrupar visualmente se quiser
                }
            )
    
    if not items:
        st.info("Nenhum item para exibir na linha do tempo.")
        return

    selected_item = st_timeline(
        items,
        groups=[],
        options={"height": 350, "showCurrentTime": False},
        key=f"timeline_{run_config_key}_{exec_num}",
    )

    if selected_item:
        st.markdown("---")
        idx = selected_item['id']
        # Proteção contra erro de índice caso a lista mude
        data_item = agendamento_info[idx] if idx < len(agendamento_info) else {}
        
        st.subheader(f"🔍 Detalhes da Intervenção selecionada")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("🏆 Fitness Local", f"{data_item.get('fitness', 0):.4f}")
        with c2:
            st.metric("🕒 Horário Início", f"{data_item.get('inicio')}h")
        with c3:
            st.metric("⏳ Duração", f"{data_item.get('duracao')}h")

        # Mostra detalhes de contingências se disponíveis
        st.markdown("#### ⚠️ Contingências e Ramos")
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.write("**Dados da Simulação:**")
            st.json({
                "Cenário": data_item.get("cenario", "N/A"),
                "Perfil Carga": data_item.get("perfil", "N/A"),
                "Contingência ID": data_item.get("contingencia", "N/A"),
            })
            
        with col_right:
            st.write("**Ramos Envolvidos:**")
            r_cont_from = data_item.get('ramo_cont_from', 'N/A')
            r_cont_to = data_item.get('ramo_cont_to', 'N/A')
            r_desl_from = data_item.get('ramo_desligado_from', 'N/A')
            r_desl_to = data_item.get('ramo_desligado_to', 'N/A')
            
            st.write(f"- Contingência no Ramo: `[{r_cont_from}, {r_cont_to}]`")
            st.write(f"- Ramo em Manutenção: `[{r_desl_from}, {r_desl_to}]`")
            
        # Adiciona Best Variables daquela execução específica para contexto
        if "best_variables" in results_data:
            st.markdown("---")
            st.write("**🎯 Horários Ótimos do Agendamento (Varaíveis de Decisão):**")
            st.write(results_data["best_variables"])


class TabPinningController:
    def __init__(self):
        pass

    def render_toggle(self, config_num: str):
        """Renderiza o toggle e gerencia o estado de fixação de forma centralizada."""
        toggle_key = f"pin_toggle_{config_num}"

        def pin_tab_callback():
            # Se o toggle foi LIGADO
            if st.session_state[toggle_key]:
                st.session_state.locked_config = config_num
            # Se o toggle foi DESLIGADO
            else:
                # Limpa o lock apenas se este era o config que estava fixado
                if st.session_state.locked_config == config_num:
                    st.session_state.locked_config = None

        # O valor do toggle é definido pelo estado central
        is_this_tab_pinned = st.session_state.locked_config == config_num

        st.toggle(
            "📌 Fixar Aba",
            value=is_this_tab_pinned,
            key=toggle_key,
            on_change=pin_tab_callback,
            help="Ative para selecionar e fixar a visualização de uma única aba.",
        )

        # Retorna o estado definitivo após a renderização do widget
        return st.session_state.locked_config == config_num

    def render_selection_box(self, tab_options, key):
        return st.selectbox("Selecione a aba para fixar:", options=tab_options, key=key)


# Renderizar tempalte em HTML
def rede_template_view(html_path: str | None = None, height: int = 1200):
    """Renderiza o template HTML da rede IEEE dentro do Streamlit."""
    if html_path is None:
        html_path = (
            BASE_DIR
            / "resultados - Artigo PIBIC"
            / "plot_rede_IEEE_template_dashboard.html"
        )
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    except FileNotFoundError:
        st.error(f"Arquivo HTML não encontrado: {os.path.abspath(html_path)}")
        st.info(
            "Crie o arquivo ou informe um caminho válido em rede_template_view(html_path=...)"
        )
        return
    components.html(html_content, height=height, scrolling=True)


#! Pagina Dashboard
class FrameworkRCEDashboard:
    """Dashboard principal, com a timeline integrada na aba Solução."""

    def __init__(self):
        self.db_controller = DatabaseController(base_dir=BASE_DIR)
        self.consolidation_manager = ConsolidationManager(base_dir=BASE_DIR)
        self.config = get_config()
        self.tab_pinning_controller = TabPinningController()
        self._init_state()
        # A chamada do MenuLateral foi movida para o método run()

    def MenuLateral(self, df: pd.DataFrame) -> pd.DataFrame:
        """Renderiza o menu lateral com os filtros e retorna o DataFrame filtrado."""
        st.sidebar.title("🧭 Menu Dashboard")
        st.sidebar.image(
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRHVsZ1z9B-HIP8Ddsks0mP3aETeG1CkYixtA&s",
            use_container_width=True,
        )
        st.sidebar.markdown("---")

        if df is None or df.empty:
            st.sidebar.warning("Não há dados consolidados para filtrar.")
            return pd.DataFrame()

        st.sidebar.header("🔎 Filtros para Resultados Consolidados")

        filtered_df = df.copy()

        # Filtro por Configuração
        config_col, _ = self._validate_required_columns(df)
        if config_col and not df[config_col].empty:
            unique_configs = sorted(df[config_col].astype(str).unique())
            selected_configs = st.sidebar.multiselect(
                "Configuração",
                options=unique_configs,
                default=unique_configs,
                key="filter_config",
            )
            if selected_configs:
                filtered_df = filtered_df[
                    filtered_df[config_col].astype(str).isin(selected_configs)
                ]

        return filtered_df

    def _init_state(self):
        if "df_consolidado" not in st.session_state:
            st.session_state.df_consolidado = self.db_controller.get_consolidated_data()
        if "executions_map" not in st.session_state:
            st.session_state.executions_map = self._get_executions_map()
        if "locked_config" not in st.session_state:
            st.session_state.locked_config = None

    def _get_column_name_insensitive(self, df, possible_names):
        df_columns = [str(col).lower().strip() for col in df.columns]
        for name in possible_names:
            if name.lower() in df_columns:
                return df.columns[df_columns.index(name.lower())]
        return None

    def _validate_required_columns(self, df):
        config_col_names = [
            "config_num",
            "config",
            "configuration",
            "configuracao",
            "configuração",
        ]
        exec_col_names = [
            "exec_num",
            "exec",
            "execution",
            "run",
            "execucao",
            "execução",
        ]
        config_col = self._get_column_name_insensitive(df, config_col_names)
        exec_col = self._get_column_name_insensitive(df, exec_col_names)
        return config_col, exec_col

    def _get_executions_map(self) -> dict:
        df = st.session_state.df_consolidado
        if df is None or df.empty:
            return {}
        
        # Colunas necessárias
        run_col = self._get_column_name_insensitive(df, ["pasta_run", "run", "pasta"])
        config_col, exec_col = self._validate_required_columns(df)
        func_col = self._get_column_name_insensitive(df, ["Funcao_objetivo", "fitness_function", "funcao"])
        
        if not run_col or not config_col or not exec_col:
            st.error("O arquivo consolidado não contém colunas suficientes (Run, Config, Exec).")
            return {}

        df[run_col] = df[run_col].astype(str)
        df[config_col] = df[config_col].astype(str)
        df[exec_col] = df[exec_col].astype(str)
        
        # Cria label amigável: [Função] Data/Hora | Config X
        if func_col:
            df["func_clean"] = df[func_col].str.replace("funcao_objetivo_", "").str.replace("_otimizacao", "")
            df["run_config_key"] = "🧪 " + df["func_clean"] + " (" + df[run_col].str.replace("run_", "") + ") | Config " + df[config_col]
        else:
            df["run_config_key"] = df[run_col] + " | Config " + df[config_col]
        
        return (
            df.groupby("run_config_key")[exec_col]
            .apply(lambda x: sorted(x.unique()))
            .to_dict()
        )

    def renderHeader(self):
        st.title(f"{self.config.PAGE_TITLE} (Versão Estável)")
        st.markdown(
            "Análise de resultados de otimização AG com Repopulation-With-Elite-Set usando DEAP + PandaPower em Python."
        )
        st.markdown("---")

        if st.session_state.df_consolidado is not None:
            df = st.session_state.df_consolidado
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📁 Total de Execuções", len(df))
            with col2:
                # Conta pares únicos de Run e Config
                run_col = self._get_column_name_insensitive(df, ["pasta_run", "run", "pasta"])
                config_col, _ = self._validate_required_columns(df)
                if run_col and config_col:
                    unique_pairs = df.drop_duplicates(subset=[run_col, config_col])
                    st.metric("⚙️ Configurações (Total)", len(unique_pairs))
                else:
                    st.metric("⚙️ Configurações", df[config_col].nunique() if config_col else "N/A")
            with col3:
                st.metric("📊 Conjuntos Detectados", len(st.session_state.executions_map))
            with col4:
                st.metric(
                    "📌 Config Fixada", st.session_state.locked_config or "Nenhuma"
                )

        st.markdown("---")

    def renderFooter(self):
        st.markdown("---")

        with st.expander("📞 Contato e Suporte", expanded=True):
            st.write(f"**Versão:** {self.config.PAGE_TITLE} v17.0")
            st.write("**Desenvolvedores:** Pedro Victor Veras e Rainer Zanghi")
        if st.button("🧹 Limpar Cache", key="clear_cache_btn"):
            self.clearCache()
        self.showSystemInfo()

    def clearCache(self):
        try:
            for key in ["df_consolidado", "executions_map"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.success(self.config.get_message("success", "cache_cleared"))
            st.rerun()
        except Exception as e:
            st.error(f"{self.config.get_message('error', 'cache_error')}: {e}")

    def renderExecutionDetails(self, run_config_key, exec_num, pinned_tab_name=None):
        import re
        try:
            run_name, config_part = run_config_key.split(" | ")
            config_num = re.search(r"Config (\d+)", config_part).group(1)
        except:
            st.error(f"Erro ao parsear chave: {run_config_key}")
            return

        results_data = self.db_controller.get_run_data(int(config_num), int(exec_num), run_name=run_name) or {}
        df_consolidado = st.session_state.df_consolidado

        if df_consolidado is not None:
            run_col = self._get_column_name_insensitive(df_consolidado, ["pasta_run", "run", "pasta"])
            config_col, exec_col = self._validate_required_columns(df_consolidado)
            if run_col and config_col and exec_col:
                row = df_consolidado[
                    (df_consolidado[run_col].astype(str) == str(run_name)) &
                    (df_consolidado[config_col].astype(str) == str(config_num)) &
                    (df_consolidado[exec_col].astype(str) == str(exec_num))
                ]
                if not row.empty:
                    results_data.update(row.iloc[0].to_dict())

        if not results_data.get("best_variables") and results_data:
            var_keys = sorted(
                [k for k in results_data if str(k).startswith("best_var_")],
                key=lambda x: int(str(x).split("_")[-1]),
            )
            if var_keys:
                results_data["best_variables"] = [results_data[k] for k in var_keys]

        viz_data_list = self.db_controller.get_visualization_data_for_run(
            int(config_num), int(exec_num), run_name=run_name
        )
        df_viz = pd.DataFrame(viz_data_list) if viz_data_list else pd.DataFrame()

        def render_solucao_tab():
            try:
                # Chama a nova função que renderiza os cards com tooltip
                CardsSolutions(results_data)

                st.markdown("---")

                # Chama a função refatorada para a timeline
                AgendamentoRedePage(results_data, run_config_key, exec_num)
            except Exception as e:
                st.error(f"Erro ao renderizar a aba de Solução: {e}")

        def render_graficos_tab():
            st.subheader("Gráfico de Fitness x Generations com RCE")
            if not df_viz.empty:
                try:
                    if "gen" in df_viz.columns:
                        stats_df = df_viz.rename(
                            columns={
                                "gen": "Generation",
                                "avg": "Média",
                                "min": "Mínimo",
                                "max": "Máximo",
                            }
                        )
                        st.line_chart(
                            stats_df,
                            x="Generation",
                            y=["Média", "Mínimo", "Máximo"],
                            height=self.config.CHART_HEIGHT,
                        )

                    elif "Generations" in df_viz.columns:
                        stats_df = (
                            df_viz.groupby("Generations")["Fitness"]
                            .agg(["mean", "min", "max"])
                            .reset_index()
                        )
                        stats_df = stats_df.rename(
                            columns={
                                "Generations": "Generation",
                                "mean": "Média",
                                "min": "Mínimo",
                                "max": "Máximo",
                            }
                        )
                        st.line_chart(
                            stats_df,
                            x="Generation",
                            y=["Média", "Mínimo", "Máximo"],
                            height=self.config.CHART_HEIGHT,
                        )
                    else:
                        st.warning(
                            "Colunas 'gen' ou 'Generations' não encontradas para o gráfico de convergência."
                        )
                except Exception as e:
                    st.error(f"Erro ao renderizar gráfico: {e}")
            else:
                st.warning(
                    "Dados de visualização não disponíveis para o gráfico de estatísticas."
                )

        def render_pop_final_tab():
            st.subheader("Análise da População Final")
            pop_final_path = self.config.POP_FINAL_FILE
            st.write(pop_final_path)
            if pop_final_path.exists():
                try:
                    pop_df = pd.read_excel(pop_final_path)
                    # st.dataframe(pop_df.head(self.config.MAX_ROWS_IN_TABLE))
                    st.dataframe(pop_df)
                except Exception as e:
                    st.error(f"Erro ao ler população final: {e}")
            else:
                st.info("Arquivo de população final não encontrado ma pasta output")

        tab_definitions = {
            "Solução": render_solucao_tab,
            "Gráficos": render_graficos_tab,
            "População Final": render_pop_final_tab,
            # "Dashboard Sistema Elétrico":rede_template_view
        }

        if pinned_tab_name:
            if render_function := tab_definitions.get(pinned_tab_name):
                render_function()
        else:
            tabs = st.tabs(list(tab_definitions.keys()))
            for tab, render_func in zip(tabs, tab_definitions.values()):
                with tab:
                    render_func()

    def showSystemInfo(self):
        with st.expander("ℹ️ Informações do Sistema", expanded=False):
            st.write(f"**Debug Mode:** {self.config.DEBUG_MODE}")
            if st.session_state.df_consolidado is not None:
                st.write(
                    f"**Total de Execuções:** {len(st.session_state.df_consolidado)}"
                )

            summary = self.db_controller.get_execution_summary()
            st.write(f"**Execuções Detectadas:** {summary.get('total_runs')}")

            status = self.consolidation_manager.get_consolidation_status()
            st.write(
                f"**Arquivo Consolidado:** {'✅ Encontrado' if status.get('consolidated_file_exists') else '❌ Não Encontrado'}"
            )

    def calcula_tempo_medio_execucao(self, filtered_df):

        try:
            # converte para segundos
            filtered_df["Tempo_total_execucao_seg"] = filtered_df[
                "Tempo_total_execucao"
            ].apply(
                lambda x: (
                    int(x.split()[0]) * 60 + int(x.split()[2])
                    if isinstance(x, str)
                    else None
                )
            )

            # tempo médio
            tempo_medio = filtered_df["Tempo_total_execucao_seg"].mean()

            # soma acumulada
            filtered_df["Soma_acumulada"] = filtered_df[
                "Tempo_total_execucao_seg"
            ].cumsum()

            # média em minutos
            minutos_medio, segundos_medio = divmod(int(tempo_medio), 60)
            st.write(f"Tempo médio: {minutos_medio} minutos {segundos_medio} segundos")

            # tempo total acumulado em minutos
            total_segundos = filtered_df["Soma_acumulada"].iloc[-1]
            minutos_totais, segundos_totais = divmod(int(total_segundos), 60)
            st.write(
                f"Tempo total da simulação: {minutos_totais} minutos {segundos_totais} segundos"
            )
        except:
            st.warning("Erro ao calcular tempo médio e tempo total acumulado.")

    def run(self):
        df_consolidado = st.session_state.df_consolidado

        # O menu lateral agora é chamado aqui e retorna o dataframe filtrado
        filtered_df = self.MenuLateral(df_consolidado)

        # Header
        self.renderHeader()
        executions_map = st.session_state.executions_map

        if not executions_map:
            st.warning(
                "Nenhum resultado consolidado encontrado. Execute a consolidação através do Launcher."
            )
            st.stop()

        st.subheader("📈 Resultados Consolidados de Todas as Configurações e Execuções")
        if filtered_df is not None and not filtered_df.empty:
            st.dataframe(filtered_df, use_container_width=True)

            self.calcula_tempo_medio_execucao(filtered_df)

        else:
            st.warning("Nenhum resultado encontrado para os filtros aplicados.")

        # Configuração dos TABS
        run_config_keys = sorted(executions_map.keys())
        # Labels mais limpas para as abas
        tab_labels = [key.replace("run_", "") for key in run_config_keys]
        config_tabs = st.tabs(tab_labels)

        # Run|Config -> Executions -> Components (com uso de fixar aba)
        for i, config_tab_ui in enumerate(config_tabs):
            with config_tab_ui:
                run_config_key = run_config_keys[i]
                tab_names = [
                    "Solução",
                    "Gráficos",
                    "População Final",
                    "Dashboard Sistema Elétrico",
                ]

                is_pinned = self.tab_pinning_controller.render_toggle(
                    config_num=run_config_key
                )

                select_key = f"pin_select_{run_config_key}"

                if is_pinned:
                    selected_tab_name = (
                        self.tab_pinning_controller.render_selection_box(
                            tab_names, key=select_key
                        )
                    )
                    exec_numbers = executions_map.get(run_config_key, [])

                    if not exec_numbers:
                        st.warning(
                            "Nenhuma execução encontrada para esta configuração."
                        )
                        continue

                    # Quando uma aba está fixada, mostramos abas para cada execução
                    exec_tabs = st.tabs([f"Execução {en}" for en in exec_numbers])
                    for j, exec_tab_ui in enumerate(exec_tabs):
                        with exec_tab_ui:
                            exec_num = exec_numbers[j]
                            self.renderExecutionDetails(
                                run_config_key, exec_num, pinned_tab_name=selected_tab_name
                            )

                else:
                    # Se não está fixado, continua com a lógica de abas para cada execução
                    exec_numbers = executions_map.get(run_config_key, [])
                    if not exec_numbers:
                        st.warning(
                            "Nenhuma execução encontrada para esta configuração."
                        )
                        continue

                    exec_tabs = st.tabs([f"Execução {en}" for en in exec_numbers])
                    for j, exec_tab_ui in enumerate(exec_tabs):
                        with exec_tab_ui:
                            self.renderExecutionDetails(run_config_key, exec_numbers[j])

                    st.markdown("---")

        # footer
        self.renderFooter()
