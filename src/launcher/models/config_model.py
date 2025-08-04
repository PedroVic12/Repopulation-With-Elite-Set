# src/launcher/models/config_model.py

import json
from pathlib import Path

class ConfigManager:
    """
    Responsável por toda a interação com os arquivos de configuração (.json).
    Funciona como o "Model" no padrão MVC, gerenciando os dados da aplicação.
    """
    def __init__(self, params_file: Path, options_file: Path):
        """
        Inicializa o gerenciador de configuração.

        Args:
            params_file (Path): O caminho para o arquivo de parâmetros do AG.
            options_file (Path): O caminho para o arquivo de opções de execução.
        """
        self.params_file = params_file
        self.options_file = options_file
        self.params = self._load_json(self.params_file)
        self.options = self._load_json(self.options_file)

    def _load_json(self, file_path: Path) -> dict:
        """Método privado para carregar um arquivo JSON de forma segura."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Erro ao carregar {file_path}: {e}. Retornando dicionário vazio.")
            return {}

    def save_json(self, data: dict, file_path: Path) -> bool:
        """Salva um dicionário de dados em um arquivo JSON."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Erro ao salvar {file_path}: {e}")
            return False

    def get_param(self, key: str, default=None):
        """Busca um valor no dicionário de parâmetros."""
        return self.params.get(key, default)

    def get_option(self, key: str, default=None):
        """Busca um valor no dicionário de opções."""
        return self.options.get(key, default)
