import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List, Any, Union, Tuple

# ====================================
# MODEL LAYER
# ====================================

class DataModel:
    """Model para gerenciamento de dados"""
    
    def __init__(self, data_source: Union[str, pd.DataFrame]):
        self.data_source = data_source
        self.df = None
        self.df_filtered = None
        self.load_data()
    
    def load_data(self) -> pd.DataFrame:
        """Carrega dados de diferentes fontes (.csv, .xlsx) e realiza uma limpeza inicial."""
        try:
            # Caso 1: A fonte de dados é um URL (string)
            if isinstance(self.data_source, str):
                self.df = pd.read_csv(self.data_source)
            # Caso 2: A fonte de dados é um DataFrame já existente
            elif isinstance(self.data_source, pd.DataFrame):
                self.df = self.data_source.copy()
            # Caso 3: A fonte de dados é um ficheiro carregado pelo Streamlit
            elif hasattr(self.data_source, 'name'):
                file_name = self.data_source.name
                if file_name.endswith('.csv'):
                    self.df = pd.read_csv(self.data_source)
                elif file_name.endswith(('.xlsx', '.xls')):
                    # Para ler ficheiros Excel, a biblioteca openpyxl é necessária
                    # O Streamlit Cloud geralmente já a tem. Localmente: pip install openpyxl
                    self.df = pd.read_excel(self.data_source, engine='openpyxl')
                else:
                    raise ValueError("Formato de ficheiro não suportado. Use .csv ou .xlsx.")
            else:
                raise ValueError("Fonte de dados inválida")

            # Limpa colunas de índice sem nome (ex: 'Unnamed: 0')
            self.df = self.df.loc[:, ~self.df.columns.str.contains('^Unnamed')]
            
            self.df.columns = [str(col).strip() for col in self.df.columns]
            self.df_filtered = self.df.copy()
            return self.df
            
        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")
            return pd.DataFrame()
    
    def apply_filters(self, filters: Dict[str, Any]) -> pd.DataFrame:
        """Aplica filtros aos dados"""
        if self.df is None or self.df.empty:
            return pd.DataFrame()
        
        df_temp = self.df.copy()
        
        for column, values in filters.items():
            if values and column in df_temp.columns:
                if isinstance(values, (list, tuple)):
                    # Lógica para filtro numérico (slider)
                    if len(values) == 2 and all(isinstance(v, (int, float)) for v in values):
                        if values[0] <= values[1]:
                           # Condição para manter os valores dentro do intervalo OU se forem NaN
                           condition = (df_temp[column] >= values[0]) & (df_temp[column] <= values[1])
                           df_temp = df_temp[condition | df_temp[column].isna()]
                    # Lógica para filtro categórico (multiselect)
                    else:
                        df_temp = df_temp[df_temp[column].isin(values)]
        
        self.df_filtered = df_temp
        return self.df_filtered
    
    def get_column_info(self) -> Dict[str, List[str]]:
        """Retorna informações sobre tipos de colunas"""
        if self.df is None:
            return {"numeric": [], "categorical": [], "datetime": []}
        
        return {
            "numeric": self.df.select_dtypes(include=np.number).columns.tolist(),
            "categorical": self.df.select_dtypes(include=['object', 'category']).columns.tolist(),
            "datetime": self.df.select_dtypes(include=['datetime64']).columns.tolist()
        }
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calcula métricas gerais e detalhadas dos dados filtrados"""
        if self.df_filtered is None or self.df_filtered.empty:
            return {}
        
        metrics = {
            "total_records": len(self.df_filtered),
            "total_columns": len(self.df_filtered.columns),
            "numeric_details": {}
        }

        column_info = self.get_column_info()
        
        for col in column_info["numeric"]:
            if col in self.df_filtered.columns:
                # Funções do pandas como .mean() já ignoram NaNs por padrão
                metrics["numeric_details"][col] = {
                    "Média": self.df_filtered[col].mean(),
                    "Mediana": self.df_filtered[col].median(),
                    "Máximo": self.df_filtered[col].max(),
                    "Mínimo": self.df_filtered[col].min()
                }
        return metrics

    def calculate_grouped_metrics(self, group_by_col: str, agg_col: str, agg_func: str) -> pd.DataFrame:
        """Calcula métricas agrupadas"""
        if self.df_filtered is None or self.df_filtered.empty:
            return pd.DataFrame()
        
        try:
            grouped_df = self.df_filtered.groupby(group_by_col)[agg_col].agg(agg_func).reset_index()
            return grouped_df.sort_values(by=agg_col, ascending=False)
        except Exception:
            return pd.DataFrame()

# ====================================
# CHART GENERATOR LAYER (using Matplotlib)
# ====================================

class MatplotlibChartGenerator:
    """Gerador de gráficos usando Matplotlib e Seaborn"""
    
    def __init__(self, df: pd.DataFrame, style: str = 'seaborn-v0_8-whitegrid'):
        self.df = df
        plt.style.use(style)
        sns.set_palette("viridis")
    
    def _setup_chart(self, title: str) -> Tuple[plt.Figure, plt.Axes]:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_title(title, fontsize=14, weight='bold')
        return fig, ax

    def create_line_chart(self, x_column: str, y_column: str, color_column: str = None) -> plt.Figure:
        """Cria um gráfico de linhas, com opção de usar o índice e segmentação por cor."""
        x_label = x_column.replace("_", " ").title() if x_column != '[Índice]' else 'Índice'
        title = f'{y_column.replace("_", " ").title()} por {x_label}'
        if color_column:
            title += f' (agrupado por {color_column.title()})'
        
        fig, ax = self._setup_chart(title)
        
        df_plot = self.df.copy()
        if x_column == '[Índice]':
            df_plot['[Índice]'] = df_plot.index
        
        sns.lineplot(data=df_plot, x=x_column, y=y_column, hue=color_column, marker='o', ax=ax)
        
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_column.replace('_', ' ').title())
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        return fig
    
    def create_bar_chart(self, x_column: str, y_column: str = None, color_column: str = None, horizontal: bool = False) -> plt.Figure:
        """Cria um gráfico de barras, podendo ser de contagem ou de média, com segmentação de cor."""
        fig, ax = self._setup_chart("") # Título será definido dentro da lógica

        if y_column:
            title = f'Média de {y_column.title()} por {x_column.title()}'
            if color_column:
                title += f' (agrupado por {color_column.title()})'
            ax.set_title(title, fontsize=14, weight='bold')
            sns.barplot(data=self.df, x=x_column, y=y_column, hue=color_column, ax=ax, orient='v' if not horizontal else 'h')
        else:
            title = f'Contagem de {x_column.title()}'
            if color_column:
                title += f' (agrupado por {color_column.title()})'
            ax.set_title(title, fontsize=14, weight='bold')
            # Para contagem, o ideal é usar countplot
            sns.countplot(data=self.df, x=x_column if not horizontal else None, y=x_column if horizontal else None, hue=color_column, ax=ax)

        if not horizontal:
            plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        return fig

    def create_pie_chart(self, column: str, top_n: int = 7) -> plt.Figure:
        title = f'Distribuição de {column.replace("_", " ").title()}'
        fig, ax = self._setup_chart(title)
        data = self.df[column].value_counts()
        
        if len(data) > top_n:
            top_data = data.head(top_n)
            others = pd.Series([data.iloc[top_n:].sum()], index=['Outros'])
            data_to_plot = pd.concat([top_data, others])
        else:
            data_to_plot = data

        ax.pie(data_to_plot, labels=data_to_plot.index, autopct='%1.1f%%', startangle=90, counterclock=False)
        ax.axis('equal') 
        plt.tight_layout()
        return fig
        
    def create_scatter_plot(self, x_column: str, y_column: str, color_column: str = None) -> plt.Figure:
        title = f'{y_column.title()} vs {x_column.title()}'
        fig, ax = self._setup_chart(title)
        sns.scatterplot(data=self.df, x=x_column, y=y_column, hue=color_column, palette="viridis", ax=ax, alpha=0.8)
        ax.set_xlabel(x_column.title())
        ax.set_ylabel(y_column.title())
        plt.tight_layout()
        return fig

# ====================================
# VIEW LAYER
# ====================================

class DashboardView:
    """View para interface do dashboard"""
    
    def render_header(self, title: str, description: str = None):
        st.title(title)
        if description:
            st.markdown(description)
    
    def render_sidebar_filters(self, df: pd.DataFrame, column_info: Dict[str, List[str]]) -> Dict[str, Any]:
        st.sidebar.header("🔍 Filtros")
        st.sidebar.info(f"**Registos (Total):** {len(df)}\n**Colunas:** {len(df.columns)}")
        filters = {}
        for col in column_info["categorical"]:
            if 1 < df[col].nunique() <= 50:
                # Lógica aprimorada para lidar com valores NaN sem usar dropna()
                unique_vals = df[col].unique()
                
                # Separa NaN dos outros valores para permitir a ordenação
                nan_values = [v for v in unique_vals if pd.isna(v)]
                non_nan_values = sorted([v for v in unique_vals if pd.notna(v)])
                
                # Recombina a lista, colocando NaN no início se existir
                final_options = nan_values + non_nan_values
                
                filters[col] = st.sidebar.multiselect(col.title(), final_options, default=final_options)
        
        for col in column_info["numeric"]:
            # O .dropna() é usado aqui de forma segura apenas para encontrar o min/max para o slider,
            # sem alterar o DataFrame original.
            if not df[col].dropna().empty:
                min_val, max_val = float(df[col].dropna().min()), float(df[col].dropna().max())
                if min_val < max_val:
                    filters[col] = st.sidebar.slider(col.title(), min_val, max_val, (min_val, max_val))
        
        if st.sidebar.button("🔄 Reiniciar Filtros"):
            st.rerun()
        return filters
    
    def render_metrics(self, metrics: Dict[str, Any], column_info: Dict[str, List[str]]):
        st.divider()
        st.subheader("📈 Métricas dos Dados Filtrados")
        
        if not metrics or "total_records" not in metrics:
            st.warning("Nenhuma métrica disponível para a seleção atual.")
            return

        c1, c2 = st.columns(2)
        c1.metric("Total de Registos", f"{metrics.get('total_records', 0):,}")
        c2.metric("Total de Colunas", f"{metrics.get('total_columns', 0):,}")
        
        st.divider()
        st.markdown("##### Análise por Coluna")
        selected_col = st.selectbox("Selecione uma coluna numérica para ver os detalhes:", column_info["numeric"])

        if selected_col and selected_col in metrics.get("numeric_details", {}):
            details = metrics["numeric_details"][selected_col]
            cols = st.columns(4)
            cols[0].metric(f"Média de {selected_col.title()}", f"{details.get('Média', 0):.2f}")
            cols[1].metric(f"Mediana de {selected_col.title()}", f"{details.get('Mediana', 0):.2f}")
            cols[2].metric(f"Mínimo de {selected_col.title()}", f"{details.get('Mínimo', 0):.2f}")
            cols[3].metric(f"Máximo de {selected_col.title()}", f"{details.get('Máximo', 0):.2f}")

    def render_grouped_analysis_controls(self, column_info: Dict[str, List[str]]) -> Dict[str, str]:
        st.subheader("🧩 Análise Agrupada (Group By)")
        if not column_info["categorical"] or not column_info["numeric"]:
            st.warning("A análise agrupada requer pelo menos uma coluna categórica e uma numérica.")
            return {}

        cols = st.columns(3)
        group_by_col = cols[0].selectbox("Agrupar por (coluna categórica):", column_info["categorical"])
        agg_col = cols[1].selectbox("Analisar (coluna numérica):", column_info["numeric"])
        agg_funcs = {"Média": "mean", "Soma": "sum", "Contagem": "count", "Mínimo": "min", "Máximo": "max"}
        selected_func_label = cols[2].selectbox("Cálculo:", list(agg_funcs.keys()))
        
        return {
            "group_by_col": group_by_col,
            "agg_col": agg_col,
            "agg_func": agg_funcs[selected_func_label]
        }

    def render_chart_controls(self, column_info: Dict[str, List[str]]) -> Dict[str, Any]:
        st.subheader("🎨 Visualização dos Dados Filtrados")
        chart_config = {}
        col1, col2, col3, col4 = st.columns(4)
        chart_map = {"Linha": "line", "Barras": "bar", "Pizza": "pie", "Dispersão": "scatter"}
        
        with col1:
            selected_chart = st.selectbox("Tipo de Gráfico", list(chart_map.keys()))
            chart_config["chart_type"] = chart_map[selected_chart]
        with col2:
            if chart_config["chart_type"] in ["line", "bar", "scatter"]:
                options = column_info["numeric"] + column_info["categorical"]
                if chart_config["chart_type"] == 'line':
                    options = ['[Índice]'] + options
                chart_config["x_column"] = st.selectbox("Eixo X", options)
        with col3:
            if chart_config["chart_type"] in ["line", "scatter"]:
                chart_config["y_column"] = st.selectbox("Eixo Y", column_info["numeric"])
            elif chart_config["chart_type"] == "bar":
                chart_config["y_column"] = st.selectbox("Eixo Y (opcional, p/ média)", [None] + column_info["numeric"])
            elif chart_config["chart_type"] == "pie":
                chart_config["pie_column"] = st.selectbox("Coluna", column_info["categorical"])
        with col4:
            if chart_config["chart_type"] in ["line", "bar", "scatter"]:
                 chart_config["color_column"] = st.selectbox("Cor (opcional)", [None] + column_info["categorical"])
            if chart_config["chart_type"] == "bar":
                chart_config["horizontal"] = st.toggle("Gráfico Horizontal")

        return chart_config
    
    def render_chart(self, fig: plt.Figure):
        if fig:
            st.pyplot(fig, use_container_width=True)

    def render_data_table(self, df: pd.DataFrame, title: str):
        st.subheader(title)
        if df.empty:
            st.warning("Nenhum dado para exibir.")
            return

        st.dataframe(df, use_container_width=True)
        st.info(f"Mostrando {len(df)} registos.")

# ====================================
# CONTROLLER LAYER
# ====================================

class DashboardController:
    """Controller principal do dashboard MVC"""
    
    def __init__(self, data_source: Union[str, pd.DataFrame], title: str, description: str = None):
        self.model = DataModel(data_source)
        self.view = DashboardView()
        self.title = title
        self.description = description
    
    def run(self):
        """Executa o fluxo completo do dashboard"""
        if self.model.df is None or self.model.df.empty:
            st.error("Falha ao carregar os dados. Verifique a fonte de dados.")
            return
        
        self.view.render_header(self.title, self.description)
        column_info = self.model.get_column_info()
        
        filters = self.view.render_sidebar_filters(self.model.df, column_info)
        df_filtered = self.model.apply_filters(filters)
        
        metrics = self.model.calculate_metrics()
        self.view.render_metrics(metrics, column_info)
        st.markdown("---")
        
        if df_filtered.empty:
            st.warning("Nenhum dado corresponde aos filtros selecionados.")
            return

        # Análise Agrupada
        grouped_config = self.view.render_grouped_analysis_controls(column_info)
        if all(grouped_config.values()):
            grouped_df = self.model.calculate_grouped_metrics(**grouped_config)
            self.view.render_data_table(grouped_df, f"Tabela Agrupada por {grouped_config['group_by_col'].title()}")
        st.markdown("---")
        
        # Gráficos
        chart_generator = MatplotlibChartGenerator(df_filtered)
        chart_config = self.view.render_chart_controls(column_info)
        self._render_selected_chart(chart_config, chart_generator)
        st.markdown("---")
        
        # Tabela de Dados Detalhados
        self.view.render_data_table(df_filtered, "🗂️ Dados Consolidados")

    def _render_selected_chart(self, config: Dict[str, Any], chart_generator: MatplotlibChartGenerator):
        """Renderiza o gráfico selecionado com base na configuração da view."""
        try:
            chart_type = config.get("chart_type")
            fig = None

            if chart_type == "line" and all(k in config for k in ["x_column", "y_column"]):
                fig = chart_generator.create_line_chart(config["x_column"], config["y_column"], config.get("color_column"))
            elif chart_type == "bar" and "x_column" in config:
                fig = chart_generator.create_bar_chart(config["x_column"], config.get("y_column"), config.get("color_column"), config.get("horizontal", False))
            elif chart_type == "pie" and "pie_column" in config:
                fig = chart_generator.create_pie_chart(config["pie_column"])
            elif chart_type == "scatter" and all(k in config for k in ["x_column", "y_column"]):
                fig = chart_generator.create_scatter_plot(config["x_column"], config["y_column"], config.get("color_column"))
            
            if fig:
                self.view.render_chart(fig)
        except Exception as e:
            st.error(f"Erro ao gerar gráfico: {e}")

# ====================================
# ENTRY POINT
# ====================================

def create_mvc_dashboard(data_source: Union[str, pd.DataFrame], title: str = "Dashboard MVC", description: str = None):
    """Cria e executa um dashboard MVC."""
    controller = DashboardController(data_source, title, description)
    controller.run()

# ====================================
# EXECUTION
# ====================================

if __name__ == "__main__":
    # st.set_page_config() deve ser o primeiro comando Streamlit no script.
    st.set_page_config(page_title="Análise de Resultados", page_icon="📊", layout="wide")

    st.sidebar.title("Fonte de Dados")
    
    # Adiciona a opção de fazer upload ou usar a URL
    data_source_option = st.sidebar.radio(
        "Escolha a fonte dos dados:",
        ("Usar URL de exemplo", "Fazer upload de ficheiro")
    )

    data_source = None
    if data_source_option == "Usar URL de exemplo":
        data_source = "https://raw.githubusercontent.com/PedroVic12/Repopulation-With-Elite-Set/refs/heads/main/resultados%20-%20Artigo%20PIBIC/2025-09-01_resultados.csv"
    else:
        uploaded_file = st.sidebar.file_uploader(
            "Arraste e solte ou clique para fazer upload", 
            type=["csv", "xlsx"]
        )
        if uploaded_file:
            data_source = uploaded_file

    # O dashboard só é renderizado se uma fonte de dados for definida
    if data_source is not None:
        create_mvc_dashboard(
            data_source=data_source,
            title="📊 Análise de Resultados de Otimização",
            description="Dashboard interativo para explorar os resultados do seu algoritmo. Use os filtros e as opções de análise para investigar os dados."
        )
    else:
        st.info("👈 Por favor, selecione uma fonte de dados na barra lateral para começar a análise.")

