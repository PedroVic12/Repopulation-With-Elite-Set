import io
import streamlit as st
import pandas as pd
import numpy as np
import math
from typing import List, Optional, Tuple, Any

# =============================================================================
# CONFIGURAÇÃO INICIAL
# =============================================================================
st.set_page_config(
    page_title='GDP Dashboard',
    page_icon=':earth_americas:',
)

# --- Carregamento de Dados em Cache ---
# A função de cache funciona melhor de forma independente
@st.cache_data
def load_and_transform_data(data_path='data/gdp_data.csv'):
    """Carrega e transforma os dados do PIB de um arquivo CSV."""
    try:
        raw_df = pd.read_csv(data_path)
        gdp_df = raw_df.melt(
            ['Country Code'],
            [str(x) for x in range(1960, 2022 + 1)],
            'Year',
            'GDP',
        )
        gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])
        return gdp_df
    except FileNotFoundError:
        st.error(f"Arquivo de dados não encontrado em '{data_path}'. Certifique-se de que o arquivo 'gdp_data.csv' está dentro de uma pasta 'data'.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar ou transformar os dados: {e}")
        return None

# =============================================================================
# GERENCIAMENTO DE ESTADO
# =============================================================================
class UseState:
    """Classe para gerenciar o estado da aplicação usando st.session_state."""
    
    @staticmethod
    def initialize(key: str, default_value: Any):
        """Inicializa uma chave no session_state se ela não existir."""
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    @staticmethod
    def get(key: str) -> Any:
        """Obtém o valor de uma chave do session_state."""
        return st.session_state.get(key)
    
    @staticmethod
    def set(key: str, value: Any):
        """Define o valor de uma chave no session_state."""
        st.session_state[key] = value

# =============================================================================
# CAMADA DE MODELO
# =============================================================================
class GDPDataModel:
    """Classe do modelo responsável pela lógica de negócio e processamento de dados."""
    
    def get_gdp_data(self) -> Optional[pd.DataFrame]:
        """Invoca a função de carregamento de dados em cache."""
        return load_and_transform_data()

    def filter_data(self, df: pd.DataFrame, selected_countries: List[str], 
                   from_year: int, to_year: int) -> pd.DataFrame:
        """Filtra os dados do PIB com base nos critérios selecionados."""
        if df is None or df.empty:
            return pd.DataFrame()
        return df[
            (df['Country Code'].isin(selected_countries))
            & (df['Year'] >= from_year)
            & (df['Year'] <= to_year)
        ]
    
    def calculate_growth_metrics(self, df: pd.DataFrame, country: str, 
                               from_year: int, to_year: int) -> Tuple[float, str, str]:
        """Calcula as métricas de crescimento para um país entre dois anos."""
        if df is None or df.empty:
            return 0.0, 'n/a', 'off'
        try:
            first_gdp_series = df[(df['Country Code'] == country) & (df['Year'] == from_year)]['GDP']
            last_gdp_series = df[(df['Country Code'] == country) & (df['Year'] == to_year)]['GDP']
            
            if first_gdp_series.empty or last_gdp_series.empty or pd.isna(first_gdp_series.iloc[0]) or pd.isna(last_gdp_series.iloc[0]):
                last_gdp_val = 0.0 if last_gdp_series.empty or pd.isna(last_gdp_series.iloc[0]) else last_gdp_series.iat[0]
                return last_gdp_val / 1e9, 'n/a', 'off'

            first_gdp = first_gdp_series.iat[0]
            last_gdp = last_gdp_series.iat[0]

            if first_gdp == 0:
                return last_gdp / 1e9, 'n/a', 'off'
            
            growth = f'{(last_gdp / first_gdp):.2f}x'
            return last_gdp / 1e9, growth, 'normal'
        except (IndexError, KeyError):
            return 0.0, 'n/a', 'off'

# =============================================================================
# CAMADA DE VISÃO
# =============================================================================
class DashboardView:
    """Classe que agrupa todos os componentes de renderização da UI."""

    def render_header(self):
        st.markdown(
            """
            # :earth_americas: Dashboard de PIB
            Navegue pelos dados do PIB do site [World Bank Open Data](https://data.worldbank.org/).
            """
        )
        st.markdown("---")

    def render_filters(self, gdp_df: pd.DataFrame) -> Tuple[int, int, List[str]]:
        if gdp_df is None or gdp_df.empty:
            st.warning("Não há dados disponíveis para filtragem.")
            return 1960, 2022, []
        
        min_year, max_year = int(gdp_df['Year'].min()), int(gdp_df['Year'].max())
        
        from_year, to_year = st.slider(
            'Selecione o período de anos:',
            min_value=min_year, max_value=max_year, value=[1990, max_year]
        )
        
        countries = sorted(gdp_df['Country Code'].unique())
        default_countries = ['DEU', 'FRA', 'GBR', 'BRA', 'MEX', 'JPN', 'USA', 'CHN', 'IND']
        
        selected_countries = st.multiselect(
            'Selecione os países:',
            countries,
            default=[c for c in default_countries if c in countries]
        )
        
        st.markdown("---")
        return from_year, to_year, selected_countries

    def render_metrics(self, model: GDPDataModel, gdp_df: pd.DataFrame, 
                       selected_countries: List[str], from_year: int, to_year: int):
        st.header(f'PIB em {to_year}', divider='gray')
        cols = st.columns(4)
        for i, country in enumerate(selected_countries):
            last_gdp_b, growth, delta_color = model.calculate_growth_metrics(
                gdp_df, country, from_year, to_year
            )
            cols[i % 4].metric(
                label=f'PIB de {country}',
                value=f'{last_gdp_b:,.0f}B' if last_gdp_b else 'N/A',
                delta=f'{growth} desde {from_year}',
                delta_color=delta_color
            )

    def render_line_chart(self, filtered_gdp_df: pd.DataFrame):
        st.header('PIB ao longo do tempo', divider='gray')
        if filtered_gdp_df.empty:
            st.warning("Não há dados para os filtros selecionados.")
            return
        st.line_chart(filtered_gdp_df, x='Year', y='GDP', color='Country Code')

    def render_download_buttons(self, filtered_gdp_df: pd.DataFrame):
        if filtered_gdp_df.empty:
            return
        st.header('Download dos Dados', divider='gray')
        csv = filtered_gdp_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar CSV", data=csv,
            file_name="gdp_data_filtrado.csv", mime="text/csv"
        )

# =============================================================================
# CAMADA DE CONTROLE
# =============================================================================
class GDPDashboardController:
    """Controlador principal que orquestra a aplicação."""
    
    def __init__(self):
        self.model = GDPDataModel()
        self.view = DashboardView()
        self._initialize_state()
    
    def _initialize_state(self):
        """Inicializa o estado da sessão."""
        UseState.initialize("gdp_data", None)
    
    def run(self):
        """Executa o fluxo principal da aplicação."""
        self.view.render_header()

        # Carrega os dados e armazena no estado da sessão
        if UseState.get("gdp_data") is None:
            with st.spinner("Carregando dados do PIB..."):
                gdp_data = self.model.get_gdp_data()
                UseState.set("gdp_data", gdp_data)
        
        gdp_df = UseState.get("gdp_data")

        if gdp_df is None:
            st.error("Falha ao carregar os dados. A aplicação não pode continuar.")
            st.stop()
        
        # Renderiza filtros e obtém a entrada do usuário
        from_year, to_year, selected_countries = self.view.render_filters(gdp_df)

        if not selected_countries:
            st.warning("Por favor, selecione pelo menos um país para exibir o dashboard.")
            st.stop()

        # Filtra os dados com base na entrada
        filtered_gdp_df = self.model.filter_data(gdp_df, selected_countries, from_year, to_year)

        # Renderiza os resultados
        self.view.render_metrics(self.model, gdp_df, selected_countries, from_year, to_year)
        self.view.render_line_chart(filtered_gdp_df)
        self.view.render_download_buttons(filtered_gdp_df)

# =============================================================================
# PONTO DE ENTRADA
# =============================================================================
def main():
    """Função principal para executar a aplicação."""
    controller = GDPDashboardController()
    controller.run()

if __name__ == "__main__":
    main()
