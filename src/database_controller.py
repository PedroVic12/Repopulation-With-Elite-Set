# -*- coding: utf-8 -*-
"""
DatabaseController
------------------
Classe central para gerenciar toda a leitura e escrita de dados do framework,
como arquivos de configuração (params, options) e resultados de execuções.

Isso abstrai a lógica de I/O de arquivos do resto da aplicação,
tornando o código mais limpo, robusto e fácil de manter.
"""

import json
import pandas as pd
from pathlib import Path
import glob
from datetime import datetime

class DatabaseController:
    """
    Controlador para gerenciar o acesso aos dados (configurações e resultados).
    """
    def __init__(self, base_dir: Path = None):
        """
        Inicializa o controlador.
        
        Args:
            base_dir (Path, optional): O diretório raiz do projeto. 
                                       Se não for fornecido, será o pai do diretório do script.
        """
        if base_dir is None:
            # Assume que este arquivo está em 'src', então o pai é a raiz do projeto.
            self.base_dir = Path(__file__).resolve().parent.parent
        else:
            self.base_dir = base_dir
            
        self.src_dir = self.base_dir / "src"
        self.output_dir = self.src_dir / "output"
        self.params_file = self.src_dir / "params.json"
        self.options_file = self.src_dir / "options.json"
        self.consolidated_results_file = self.output_dir / "resultados_consolidados.xlsx"
        
        # Garante que o diretório de saída exista
        self.output_dir.mkdir(exist_ok=True)

    def get_params(self) -> dict:
        """Carrega os parâmetros base de params.json."""
        try:
            with open(self.params_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Aviso: Arquivo não encontrado: {self.params_file}. Retornando dicionário vazio.")
            return {}
        except json.JSONDecodeError:
            print(f"Aviso: Erro ao decodificar JSON de {self.params_file}. Retornando dicionário vazio.")
            return {}

    def save_params(self, data: dict) -> bool:
        """Salva os parâmetros em params.json."""
        try:
            with open(self.params_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar {self.params_file}: {e}")
            return False

    def get_options(self) -> dict:
        """Carrega as opções de variação de options.json."""
        try:
            with open(self.options_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Aviso: Arquivo não encontrado: {self.options_file}. Retornando dicionário vazio.")
            return {}
        except json.JSONDecodeError:
            print(f"Aviso: Erro ao decodificar JSON de {self.options_file}. Retornando dicionário vazio.")
            return {}

    def save_options(self, data: dict) -> bool:
        """Salva as opções de variação em options.json."""
        try:
            with open(self.options_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar {self.options_file}: {e}")
            return False

    def save_individual_result(self, result_data: dict):
        """Salva o resultado de uma única execução em um JSON individual."""
        config_num = result_data.get("config_num", 0)
        exec_num = result_data.get("exec_num", 0)
        filename = f"config_{config_num}_exec_{exec_num}_results.json"
        filepath = self.output_dir / filename
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=4, ensure_ascii=False)
            print(f"Resultado individual salvo em: {filepath}")
        except Exception as e:
            print(f"Erro ao salvar resultado individual em {filepath}: {e}")

    def get_consolidated_data(self):
        df = pd.read_excel("/home/pedrov12/Documentos/GitHub/Repopulation-With-Elite-Set/src/output/resultados_consolidados.xlsx")
        return df
    
    def get_visualization_data(self):
        #ler arquivo json das pastas output
        json_files = glob.glob(str(self.output_dir / "config_*_exec_*_visualization.json"))
        all_viz_data = []
        for f_path in json_files:
            try:
                with open(f_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                viz_data = data.get('viz_data', [])
                all_viz_data.extend(viz_data)
            except Exception as e:
                print(f"Erro ao ler arquivo {f_path} para visualização: {e}")
        return all_viz_data

    def consolidate_results(self):
        """
        Lê todos os JSONs de resultado individuais da pasta de saída,
        e cria (ou sobrescreve) o arquivo Excel consolidado.
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
                    data = json.load(f)
                
                flat_data = {}
                flat_data['config_num'] = data.get('config_num')
                flat_data['exec_num'] = data.get('exec_num')
                
                params = data.get('params', {})
                for p_key, p_val in params.items():
                    flat_data[f'param_{p_key}'] = str(p_val) if isinstance(p_val, list) else p_val
                
                flat_data['best_variables'] = str(data.get('best_variables'))
                flat_data['best_fitness'] = data.get('best_fitness')
                flat_data['best_gen_idx'] = data.get('best_gen_idx')
                
                all_results.append(flat_data)
            except Exception as e:
                print(f"Erro ao processar o arquivo {f_path}: {e}")

        if not all_results:
            print("Nenhum dado de resultado pôde ser processado.")
            return
            
        df = pd.DataFrame(all_results)
        
        try:
            with pd.ExcelWriter(self.consolidated_results_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Resultados_Consolidados', index=False)
            print(f"Resultados consolidados salvos com sucesso em: {self.consolidated_results_file}")
        except Exception as e:
            print(f"Erro ao salvar o arquivo Excel consolidado: {e}")
