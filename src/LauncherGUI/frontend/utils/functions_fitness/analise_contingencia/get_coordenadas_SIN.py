import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

# Carregar o DataFrame de barras
df_bus = pd.read_excel("/home/pedrov12/Documentos/GitHub/Repopulation-With-Elite-Set/src/utils/functions_fitness/SIN_45_barras_dataset.xlsx", sheet_name="bus")

# Inicializar o geocodificador com um timeout maior
geolocator = Nominatim(user_agent="geoapi_for_pandapower_sin", timeout=5) # Aumentado o timeout para 5 segundos
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=2) # Mantido o delay para 2 segundos

# Adicionar colunas para latitude e longitude
df_bus["latitude"] = None
df_bus["longitude"] = None

# Iterar sobre as barras e buscar as coordenadas
for index, row in df_bus.iterrows():
    bus_name = row["Nome"]
    try:
        location = geocode(bus_name + ", Brasil")
        if location:
            df_bus.loc[index, "latitude"] = location.latitude
            df_bus.loc[index, "longitude"] = location.longitude
            print(f"Coordenadas para {bus_name}: {location.latitude}, {location.longitude}")
        else:
            print(f"Não foi possível encontrar coordenadas para {bus_name}")
    except Exception as e:
        print(f"Erro ao buscar coordenadas para {bus_name}: {e}")
    time.sleep(1) # Adicionar um pequeno delay extra para evitar bloqueios

# Salvar o DataFrame atualizado em um novo arquivo Excel
df_bus.to_excel("./SIN_45_barras_com_coordenadas.xlsx", index=False)
print("Coordenadas salvas em SIN_45_barras_com_coordenadas.xlsx")
