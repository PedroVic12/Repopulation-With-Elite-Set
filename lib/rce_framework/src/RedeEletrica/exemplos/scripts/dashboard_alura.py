# dashboard.py
import streamlit as st
import plotly.express as px


# repository.py
import pandas as pd

class DataRepository:
    def __init__(self, path: str, file_type: str = "excel"):
        self.path = path
        self.file_type = file_type

    def load_data(self) -> pd.DataFrame:
        if self.file_type == "excel":
            return pd.read_excel(self.path)
        elif self.file_type == "json":
            return pd.read_json(self.path)
        else:
            raise ValueError("Formato não suportado: use 'excel' ou 'json'")


# --- Estado (useState do React) ---
if "year_filter" not in st.session_state:
    st.session_state.year_filter = []
if "level_filter" not in st.session_state:
    st.session_state.level_filter = []
if "contract_filter" not in st.session_state:
    st.session_state.contract_filter = []

# --- Carregar dados ---
repo = DataRepository("salarios.xlsx", file_type="excel")
df = repo.load_data()

st.title("📊 Dashboard de Análise de Salários na Área de Dados")

# --- Filtros ---
years = st.multiselect("Ano", df["ano"].unique(), default=st.session_state.year_filter)
levels = st.multiselect("Senioridade", df["senioridade"].unique(), default=st.session_state.level_filter)
contracts = st.multiselect("Contrato", df["contrato"].unique(), default=st.session_state.contract_filter)

# Aplicar filtros
filtered_df = df.copy()
if years:
    filtered_df = filtered_df[filtered_df["ano"].isin(years)]
if levels:
    filtered_df = filtered_df[filtered_df["senioridade"].isin(levels)]
if contracts:
    filtered_df = filtered_df[filtered_df["contrato"].isin(contracts)]

# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Salário médio", f"${filtered_df['salario'].mean():,.0f}")
col2.metric("Salário mínimo", f"${filtered_df['salario'].min():,.0f}")
col3.metric("Total registros", f"{len(filtered_df):,}")
col4.metric("Cargo mais comum", filtered_df['cargo'].mode()[0] if not filtered_df.empty else "N/A")

# --- Gráficos ---
st.subheader("Top 10 cargos por salário médio")
top_cargos = filtered_df.groupby("cargo")["salario"].mean().nlargest(10).reset_index()
st.plotly_chart(px.bar(top_cargos, x="salario", y="cargo", orientation="h"))

st.subheader("Distribuição dos salários anuais")
st.plotly_chart(px.histogram(filtered_df, x="salario", nbins=30))

st.subheader("Proporção dos tipos de trabalho")
st.plotly_chart(px.pie(filtered_df, names="tipo_trabalho"))

st.subheader("Salário médio de Cientistas de Dados por país")
mapa = filtered_df.groupby("residencia")["salario"].mean().reset_index()
st.plotly_chart(px.choropleth(mapa, locations="residencia", locationmode="country names", color="salario"))
