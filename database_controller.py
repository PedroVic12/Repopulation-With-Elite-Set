import json
import pandas as pd
from pathlib import Path
import glob
from datetime import datetime
import subprocess
import sys

class DatabaseController:
    """
    Controlador central para gerenciar a leitura, escrita e processamento de dados do framework,
    incluindo configurações, resultados individuais e consolidados.
    """
    def __init__(self, base_dir: Path = None):
        if base_dir is None:
            self.base_dir = Path(__file__).resolve().parent
        else:
            self.base_dir = base_dir
            
        self.src_dir = self.base_dir / "src"
        self.output_dir = self.src_dir / "output"
        self.params_file = self.src_dir / "params.json"
        self.options_file = self.src_dir / "options.json"
        self.consolidated_results_file = self.output_dir / "resultados_consolidados.xlsx"
        
        self.output_dir.mkdir(exist_ok=True)

    # --- Métodos de Configuração (params/options) ---

    def get_params(self) -> dict:
        """Carrega os parâmetros base de params.json."""
        return self._load_json(self.params_file)

    def save_params(self, data: dict) -> bool:
        """Salva os parâmetros em params.json."""
        return self._save_json(self.params_file, data)

    def get_options(self) -> dict:
        """Carrega as opções de variação de options.json."""
        return self._load_json(self.options_file)

    def save_options(self, data: dict) -> bool:
        """Salva as opções de variação em options.json."""
        return self._save_json(self.options_file, data)

    # --- Métodos de Resultados Individuais ---

    def get_run_data(self, config_num: int, exec_num: int) -> dict | None:
        """Carrega os dados de um arquivo de resultado individual (results.json)."""
        filename = f"config_{config_num}_exec_{exec_num}_results.json"
        return self._load_json(self.output_dir / filename)

    def get_visualization_data(self, config_num: int, exec_num: int) -> list | None:
        """Carrega os dados de um arquivo de visualização individual (visualization.json)."""
        filename = f"config_{config_num}_exec_{exec_num}_visualization.json"
        return self._load_json(self.output_dir / filename)

    # --- Métodos de Consolidação ---

    def run_consolidation(self):
        """Executa o processo completo de consolidação e salva em um arquivo Excel."""
        print("=== INICIANDO CONSOLIDAÇÃO DE RESULTADOS ===")
        try:
            results_list = self._gather_all_results()
            if not results_list:
                print("❌ Nenhum resultado encontrado para consolidar!")
                return

            df = self._create_consolidated_dataframe(results_list)
            self._save_dataframe_to_excel(df)
            print("\n✅ Consolidação concluída com sucesso!")

        except Exception as e:
            print(f"❌ Erro durante a consolidação: {e}")
            import traceback
            traceback.print_exc()

    def _gather_all_results(self) -> list:
        """Busca todos os arquivos _results.json e extrai os dados."""
        all_results = []
        search_pattern = str(self.output_dir / "**" / "*_exec_*_results.json")
        result_files = glob.glob(search_pattern, recursive=True)

        print(f"Encontrados {len(result_files)} arquivos de resultado.")

        for filepath in result_files:
            try:
                data = self._load_json(Path(filepath))
                if not data:
                    continue

                flat_data = {
                    'config_num': data.get('config_num'),
                    'exec_num': data.get('exec_num'),
                    'best_fitness': data.get('best_fitness'),
                    'best_gen_idx': data.get('best_gen_idx')
                }

                params = data.get('params', {})
                for p_key, p_val in params.items():
                    flat_data[f'param_{p_key}'] = str(p_val) if isinstance(p_val, list) else p_val

                best_vars = data.get('best_variables', [])
                for i, var in enumerate(best_vars):
                    flat_data[f'best_var_{i+1}'] = var
                
                all_results.append(flat_data)
            except Exception as e:
                print(f"    Erro ao processar {filepath}: {e}")
        return all_results

    def _create_consolidated_dataframe(self, results_list: list) -> pd.DataFrame:
        """Cria e organiza o DataFrame consolidado."""
        df = pd.DataFrame(results_list)
        
        id_cols = ['config_num', 'exec_num']
        param_cols = sorted([col for col in df.columns if col.startswith('param_')])
        var_cols = sorted([col for col in df.columns if col.startswith('best_var_')])
        result_cols = ['best_fitness', 'best_gen_idx']
        
        ordered_cols = id_cols + param_cols + var_cols + result_cols
        # Adiciona colunas que podem não estar presentes em todos os DFs
        final_cols = [col for col in ordered_cols if col in df.columns]
        
        return df[final_cols]

    def _save_dataframe_to_excel(self, df: pd.DataFrame):
        """Salva o DataFrame em um arquivo Excel com formatação."""
        with pd.ExcelWriter(self.consolidated_results_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Resultados_Consolidados', index=False)
            worksheet = writer.sheets['Resultados_Consolidados']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except: pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        print(f"\n📁 Arquivo salvo em: {self.consolidated_results_file}")

    # --- Métodos Auxiliares de I/O ---

    def _load_json(self, file_path: Path) -> dict | list | None:
        """Função auxiliar para carregar um arquivo JSON."""
        if not file_path.exists():
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Aviso: Não foi possível ler o arquivo {file_path}. Erro: {e}")
            return None

    def _save_json(self, file_path: Path, data: dict) -> bool:
        """Função auxiliar para salvar dados em um arquivo JSON."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar {file_path}: {e}")
            return False

# Para permitir a execução direta do script para consolidação
if __name__ == '__main__':
    # O diretório base é o diretório pai do diretório onde o script está
    # Ex: /path/to/project/database_controller.py -> /path/to/project
    base_directory = Path(__file__).resolve().parent
    controller = DatabaseController(base_dir=base_directory)
    controller.run_consolidation()