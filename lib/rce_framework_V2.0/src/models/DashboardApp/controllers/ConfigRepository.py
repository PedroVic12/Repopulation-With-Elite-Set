import json
from pathlib import Path
import re

class ConfigRepository:
    """
    Responsável por acessar e ler os dados de configuração do sistema de arquivos.
    """
    def __init__(self, output_path: Path):
        if not output_path.is_dir():
            raise FileNotFoundError(f"O diretório de output especificado não existe: {output_path}")
        self.output_path = output_path

    def get_all_configs(self) -> dict[int, dict]:
        """
        Lê todos os arquivos de parâmetros (params_config*.json) do diretório de output.

        Returns:
            dict: Um dicionário onde a chave é o número da configuração e o valor
                  é um dicionário com os parâmetros daquela configuração.
        """
        configs = {}
        config_files = sorted(self.output_path.glob("params_config*.json"))

        for config_file in config_files:
            match = re.search(r"config(\d+)", config_file.stem)
            if match:
                config_num = int(match.group(1))
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        configs[config_num] = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Alerta: Não foi possível ler ou decodificar o arquivo {config_file.name}: {e}")
        
        return configs
