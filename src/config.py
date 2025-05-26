import json
from pathlib import Path
import pathlib
import streamlit as st

# 4 parametros variando [Mutação, Crossover, Var DIFF, DELTA e restante fixo 
options_main_file = st.session_state.get("current_options", {
    
    "name": "default python script",
    "key": True,
    "value": 15,
    "parametros_opcionais": [
        {"MUTACAO": [90,80,70, 60] },
        {"CROSSOVER": [5,10, 15, 70]},
        {"NUM_GENERATIONS": [100, 200, 300, 400]}
    ]
})

"""

1 - 256 conjuntos de parametros (4⁴) 
2 - 10 ou 20 numero de execucoes
3 - 4 parametros variando [Mutação, Crossover, Var DIFF, DELTA e restante fixo 
4 - 4 Caixas de texto fixas para esses parametros variando
5 - Criar checkbox para o usuario desabilitar as demais caixas de texto, deixando um valor possivel para aquele parametro 
6 - butao Radio para selecionar a tabela a configuração das 256 conjuntos
7 - Progress bar para cada geração em tempo de execução 

"""




def get_folder_path():
    BASE_DIR = pathlib.Path(__file__).resolve().parent  

    # Define o caminho relativo para a pasta "output" dentro do projeto
    FOLDER_NAME = BASE_DIR / "output"

    # Cria a pasta "output" se ela não existir
    FOLDER_NAME.mkdir(parents=True, exist_ok=True)
    print("\nFOLDER_NAME =", FOLDER_NAME)
    print("FOLDER RAIZ do projeto =", FOLDER_NAME.parent)
    print("\n")

    return FOLDER_NAME

FOLDER_NAME = get_folder_path()



