import json
from pathlib import Path
import pathlib
import streamlit as st


options_main_file = st.session_state.get("current_options", {
    "name": "default python script",
    "key": True,
    "value": 3,
    "parametros_opcionais": [
        {"MUTACAO": [90,80,70, 60]},
        {"CROSSOVER": [5,10, 15, 20]},
        {"NUM_GENERATIONS": [100, 200, 300, 400]}
    ]
})






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



