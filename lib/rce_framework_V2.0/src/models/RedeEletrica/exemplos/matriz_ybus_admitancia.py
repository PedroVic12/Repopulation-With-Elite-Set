import numpy as np
import pandas as pd

def gerar_ybus(linhas_df, num_barras):
    # Inicializa matriz complexa com zeros
    Ybus = np.zeros((num_barras, num_barras), dtype=complex)
    
    for idx, row in linhas_df.iterrows():
        # Ajuste de índice (Python começa em 0, Barras em 1)
        k = int(row['from_bus']) - 1
        m = int(row['to_bus']) - 1
        
        # Impedância e Admitância Série
        r = row['r_pu']
        x = row['x_pu']
        z = complex(r, x)
        y_serie = 1 / z
        
        # Susceptância Shunt (B_sh) se houver (metade para cada lado no modelo Pi)
        b_sh = complex(0, row['b_pu'] / 2)
        
        # Elementos fora da diagonal (Ykm = -y_serie)
        Ybus[k, m] -= y_serie
        Ybus[m, k] -= y_serie
        
        # Elementos da diagonal (Ykk = soma das admitâncias conectadas + shunt)
        Ybus[k, k] += y_serie + b_sh
        Ybus[m, m] += y_serie + b_sh
        
    return Ybus

# Exemplo de uso (simulando dados de entrada)
dados_linhas = pd.DataFrame({
    'from_bus': [1, 1, 2],
    'to_bus':   [2, 3, 3],
    'r_pu':     [0.02, 0.01, 0.03],
    'x_pu':     [0.06, 0.04, 0.08],
    'b_pu':     [0.0, 0.0, 0.0] # Susceptância total da linha
})

# Matriz 3x3
Y = gerar_ybus(dados_linhas, 3)
print("Matriz de Admitância Nodal (Y-Bus):")
print(np.round(Y, 2))