from pathlib import Path
import pathlib
import pandas as pd
from datetime import datetime

from DashboardApp.controllers.Utils import FOLDER_NAME, PARAMETROS_JSON


# Função para obter o caminho da pasta "output" dentro do projeto
def get_folder_path(debug = False):
    BASE_DIR = pathlib.Path(__file__).resolve().parent  

    # Define o caminho relativo para a pasta "output" dentro do projeto
    FOLDER_NAME = BASE_DIR / "output"

    # Cria a pasta "output" se ela não existir
    FOLDER_NAME.mkdir(parents=True, exist_ok=True)

    if debug:
        print("\nFOLDER_NAME =", FOLDER_NAME)
        print("FOLDER RAIZ do projeto =", FOLDER_NAME.parent)
        print("\n")

    return FOLDER_NAME


FOLDER_NAME = get_folder_path() # nome da pasta output resolvendo problemas de caminho



def format_elapsed_time(elapsed_time):
    """Formats the elapsed time into a human-readable string.

    Args:
        elapsed_time: A string representing the elapsed time in HH:MM:SS.ffffff format.

    Returns:
        A formatted string like "X h Y min Z s".
    """
    parts = str(elapsed_time).split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])

    formatted_time = ""
    if hours > 0:
        formatted_time += f"{hours} horas "
    if minutes > 0:
        formatted_time += f"{minutes} minutos "
    # Round seconds to the nearest second
    formatted_time += f"{int(round(seconds))} segundos"

    return formatted_time.strip()
