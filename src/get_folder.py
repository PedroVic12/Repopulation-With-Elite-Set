import pathlib

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