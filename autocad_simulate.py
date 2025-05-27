import pandas as pd
from pyautocad import Autocad, APoint

# 1. Carregar dados da planilha
df = pd.read_excel("painel_eletrico.xlsx")

# 2. Conectar ao AutoCAD
acad = Autocad(create_if_not_exists=True)

# 3. Iterar pelos circuitos e inserir blocos e textos
for i, row in df.iterrows():
    pos = APoint(row['X'], row['Y'])

    # Inserir bloco do disjuntor
    acad.model.InsertBlock(pos, "disjuntor_bloc", 1, 1, 1, 0)

    # Inserir etiqueta do circuito
    acad.model.AddText(f"{row['Etiqueta']}", pos + APoint(10, 0), 2.5)
