# -*- coding: utf-8 -*-
"""
DatabaseController - Versão Revisada com Observer Pattern
---------------------------------------------------------

Esta é uma versão melhorada do DatabaseController.

Melhorias:
- Herda de `EventPublisher` para implementar o padrão Observer.
- Notifica os observadores inscritos sempre que dados importantes são salvos,
  permitindo que outras partes do sistema (como a UI) reajam a essas mudanças.
"""

import json
import pandas as pd
from pathlib import Path
import glob

# Importa o sistema de eventos
from event_system import EventPublisher

class DatabaseController(EventPublisher):
    """
    Controlador para gerenciar o acesso aos dados (configurações e resultados).
    Atua como um Publisher, notificando sobre mudanças nos dados.
    """
    def __init__(self, base_dir: Path = None):
        """
        Inicializa o controlador e o sistema de eventos.
        """
        # Inicializa a capacidade de publicar eventos
        super().__init__()

        if base_dir is None:
            self.base_dir = Path(__file__).resolve().parent.parent
        else:
            self.base_dir = base_dir
            
        self.src_dir = self.base_dir / "src"
        self.output_dir = self.src_dir / "output"
        self.params_file = self.src_dir / "params.json"
        self.options_file = self.src_dir / "options.json"
        self.consolidated_results_file = self.output_dir / "resultados_consolidados.xlsx"
        
        self.output_dir.mkdir(exist_ok=True)

    def get_params(self) -> dict:
        """Carrega os parâmetros base de params.json."""
        try:
            with open(self.params_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Aviso ao ler {self.params_file}: {e}. Retornando dicionário vazio.")
            return {}

    def save_params(self, data: dict) -> bool:
        """Salva os parâmetros e notifica os observadores."""
        try:
            with open(self.params_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            # Notifica que os parâmetros foram alterados
            self.notify("params_changed", data)
            print(f"Parâmetros salvos e notificação enviada.")
            return True
        except Exception as e:
            print(f"Erro ao salvar {self.params_file}: {e}")
            return False

    def get_options(self) -> dict:
        """Carrega as opções de variação de options.json."""
        try:
            with open(self.options_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Aviso ao ler {self.options_file}: {e}. Retornando dicionário vazio.")
            return {}

    def save_options(self, data: dict) -> bool:
        """Salva as opções de variação e notifica os observadores."""
        try:
            with open(self.options_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            # Notifica que as opções foram alteradas
            self.notify("options_changed", data)
            print(f"Opções salvas e notificação enviada.")
            return True
        except Exception as e:
            print(f"Erro ao salvar {self.options_file}: {e}")
            return False

    def save_individual_result(self, result_data: dict):
        """Salva o resultado de uma única execução."""
        config_num = result_data.get("config_num", 0)
        exec_num = result_data.get("exec_num", 0)
        filename = f"config_{config_num}_exec_{exec_num}_results.json"
        filepath = self.output_dir / filename
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar resultado individual em {filepath}: {e}")

    def consolidate_results(self):
        """
        Lê todos os JSONs de resultado individuais, cria o arquivo Excel 
        e notifica os observadores.
        """
        print("Iniciando consolidação de resultados...")
        json_files = glob.glob(str(self.output_dir / "config_*_exec_*_results.json"))
        
        if not json_files:
            print("Nenhum arquivo de resultado individual encontrado para consolidar.")
            return

        all_results = []
        for f_path in json_files:
            try:
                with open(f_path, 'r', encoding='utf-8') as f:
                    all_results.append(json.load(f))
            except Exception as e:
                print(f"Erro ao processar o arquivo {f_path}: {e}")

        if not all_results:
            print("Nenhum dado de resultado pôde ser processado.")
            return
            
        df = pd.json_normalize(all_results, sep='_')
        
        try:
            with pd.ExcelWriter(self.consolidated_results_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Resultados_Consolidados', index=False)
            print(f"Resultados consolidados salvos com sucesso em: {self.consolidated_results_file}")
            # Notifica que a consolidação foi concluída, enviando o DataFrame
            self.notify("consolidation_finished", df)
        except Exception as e:
            print(f"Erro ao salvar o arquivo Excel consolidado: {e}")
