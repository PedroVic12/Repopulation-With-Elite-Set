import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🌎 Visualização Interativa das Maiores Reservas de Petróleo do Mundo")
st.subheader("Com foco em sobreposição com regiões brasileiras (como ONS)")

# -----------------------------------------------------------------------------
# Dados das reservas de petróleo (pontos aproximados com nome e coordenadas)
# -----------------------------------------------------------------------------
petroleo_data = pd.DataFrame({
    'Região': [
        'Zona do Golfo do México', 'Zona do Golfo Pérsico/Mesopotâmia',
        'Zona do Cáspio/Aral', 'Zona da Sibéria Ocidental',
        'Zona Ural/Volga', 'Zona da Pradaria', 'Zona Californiana',
        'Zona do Caribe', 'Zona do Golfo da Guiné', 'Zona Sahariana',
        'Zona Malaio-Indonésia', 'Zona do Mar do Norte', 'Zona Ártica Americana'
    ],
    'Latitude': [25, 30, 43, 60, 55, 50, 35, 15, 5, 25, -5, 57, 70],
    'Longitude': [-90, 45, 55, 75, 50, -105, -120, -75, 5, 10, 120, 3, -100]
})

# -----------------------------------------------------------------------------
# Carrega o shapefile do Brasil ou região da ONS
# -----------------------------------------------------------------------------
@st.cache_data
def carregar_shapefile_brasil():
    try:
        # Você pode baixar um shapefile da ONS ou IBGE e colocar aqui
        brasil = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
        brasil = brasil[brasil['name'] == 'Brazil']
        return brasil
    except:
        st.error("Erro ao carregar shapefile do Brasil.")
        return None

brasil = carregar_shapefile_brasil()

# -----------------------------------------------------------------------------
# Criação do mapa com Plotly
# -----------------------------------------------------------------------------
fig = px.scatter_geo(
    petroleo_data,
    lat='Latitude',
    lon='Longitude',
    text='Região',
    projection="natural earth",
    title="Principais Reservas de Petróleo do Mundo",
)

if brasil is not None:
    fig.add_trace(
        px.choropleth(brasil,
                      geojson=brasil.geometry,
                      locations=brasil.index,
                      color_discrete_sequence=["green"]).data[0]
    )

fig.update_layout(height=600, margin={"r":0,"t":40,"l":0,"b":0})
st.plotly_chart(fig, use_container_width=True)
