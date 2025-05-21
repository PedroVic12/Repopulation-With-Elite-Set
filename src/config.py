import json
from pathlib import Path
import pathlib
import streamlit as st


options_main_file = st.session_state.get("current_options", {
    "name": "default python script",
    "key": True,
    "value": 3,
    "parametros_opcionais": [
        {"MUTACAO": 90},
        {"CROSSOVER": 10},
        {"NUM_GENERATIONS": 100}
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



class ConfigManager:
    CONFIG_FILE = Path("configs/options_main_file.json")
    
    @classmethod
    def initialize(cls):
        """Initialize configuration file with default values"""
        default_config = {
            "key": True,
            "value": 5,
            "parametros_opcionais": [
                {"MUTACAO": 90},
                {"CROSSOVER": 90},
                {"NUM_GENERATIONS": 100}
            ]
        }
        
        cls.CONFIG_FILE.parent.mkdir(exist_ok=True)
        if not cls.CONFIG_FILE.exists():
            cls.save_config(default_config)
        return default_config

    @classmethod
    def load_config(cls):
        """Load current configuration"""
        if cls.CONFIG_FILE.exists():
            with open(cls.CONFIG_FILE, 'r') as f:
                return json.load(f)
        return cls.initialize()

    @classmethod
    def save_config(cls, config):
        """Save configuration to file"""
        with open(cls.CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)