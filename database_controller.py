import glob
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import traceback

def consolidar_resultados(output_dir: Path):
    """
    Consolida todos os resultados das execuções em um único DataFrame.
    """
    resultados_consolidados = []
    print(f"Pasta de saída definida como: {output_dir.resolve()}")

    pastas_run = glob.glob(str(output_dir / "run_*"))
    print(f"Encontradas {len(pastas_run)} pastas de execução:")

    for pasta_run in pastas_run:
        pasta_run_path = Path(pasta_run)
        nome_run = pasta_run_path.name
        configs = glob.glob(str(pasta_run_path / "config_*"))
        print(f"  {nome_run}: {len(configs)} configurações")

        for config in configs:
            config_path = Path(config)
            nome_config = config_path.name
            resultados = glob.glob(str(config_path / "*_exec_*_results.json"))

            for resultado in resultados:
                try:
                    with open(resultado, 'r', encoding='utf-8') as f:
                        dados = json.load(f)

                    linha_resultado = {
                        'pasta_run': nome_run,
                        'configuracao': nome_config,
                        'execucao': dados.get('exec_num', 'N/A'),
                        'config_num': dados.get('config_num', 'N/A')
                    }

                    params = dados.get('params', {})
                    for param, valor in params.items():
                        if isinstance(valor, list):
                            for i, v in enumerate(valor):
                                linha_resultado[f'{param}_{i+1}'] = v
                        else:
                            linha_resultado[f'param_{param}'] = valor

                    best_vars = dados.get('best_variables', [])
                    for i, var in enumerate(best_vars):
                        linha_resultado[f'best_var_{i+1}'] = var

                    linha_resultado['best_fitness'] = dados.get('best_fitness', 'N/A')
                    linha_resultado['best_gen_idx'] = dados.get('best_gen_idx', 'N/A')
                    resultados_consolidados.append(linha_resultado)
                except Exception as e:
                    print(f"    Erro ao processar {resultado}: {e}")

    return resultados_consolidados

def salvar_excel(resultados: list, output_dir: Path):
    """
    Salva os resultados consolidados em um arquivo Excel.
    """
    if not resultados:
        print("Nenhum resultado encontrado para consolidar!")
        return None

    df = pd.DataFrame(resultados)
    colunas_ordenadas = ['pasta_run', 'configuracao', 'execucao', 'config_num']
    colunas_params = sorted([col for col in df.columns if col.startswith('param_')])
    colunas_best = sorted([col for col in df.columns if col.startswith('best_var_')])
    colunas_fitness = ['best_fitness', 'best_gen_idx']
    
    colunas_ordenadas.extend(colunas_params)
    colunas_ordenadas.extend(colunas_best)
    colunas_ordenadas.extend(colunas_fitness)
    
    df = df[[col for col in colunas_ordenadas if col in df.columns]]

    nome_arquivo = "resultados_consolidados.xlsx"
    caminho_arquivo = output_dir / nome_arquivo

    with pd.ExcelWriter(caminho_arquivo, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Resultados_Consolidados', index=False)
        worksheet = writer.sheets['Resultados_Consolidados']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    print(f"\nArquivo salvo com sucesso: {caminho_arquivo}")
    print(f"Total de resultados consolidados: {len(resultados)}")
    print(f"\nEstatísticas:")
    print(f"  - Pastas de execução: {df['pasta_run'].nunique()}")
    print(f"  - Configurações: {df['configuracao'].nunique()}")
    print(f"  - Execuções: {df['execucao'].nunique()}")

    return caminho_arquivo

class DatabaseController:
    """
    Controlador para gerenciar o acesso aos dados (configurações e resultados).
    """
    def __init__(self, base_dir: Path = None):
        """
        Inicializa o controlador.
        """
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
            print(f"Aviso: Não foi possível ler {self.params_file}: {e}. Retornando dicionário vazio.")
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
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Aviso: Não foi possível ler {self.options_file}: {e}. Retornando dicionário vazio.")
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

    def save_individual_result(self, result_data: dict, run_name: str, config_name: str):
        """Salva o resultado de uma única execução em um JSON individual."""
        run_dir = self.output_dir / run_name
        config_dir = run_dir / config_name
        config_dir.mkdir(parents=True, exist_ok=True)
        
        config_num = result_data.get("config_num", 0)
        exec_num = result_data.get("exec_num", 0)
        filename = f"config_{config_num}_exec_{exec_num}_results.json"
        filepath = config_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=4, ensure_ascii=False)
            print(f"Resultado individual salvo em: {filepath}")
        except Exception as e:
            print(f"Erro ao salvar resultado individual em {filepath}: {e}")

    def get_consolidated_data(self) -> pd.DataFrame | None:
        """Lê o arquivo Excel consolidado e retorna um DataFrame."""
        try:
            df = pd.read_excel(self.consolidated_results_file)
            return df
        except FileNotFoundError:
            print(f"Arquivo consolidado não encontrado em: {self.consolidated_results_file}")
            return None

    def get_visualization_data(self) -> list:
        """Lê todos os arquivos JSON de visualização e retorna uma lista de dados."""
        json_files = glob.glob(str(self.output_dir / "run_*/config_*/visualization.json"))
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
        Chama a lógica de consolidação para gerar o arquivo Excel.
        """
        print("Iniciando consolidação de resultados...")
        try:
            resultados = consolidar_resultados(self.output_dir)
            if resultados:
                salvar_excel(resultados, self.output_dir)
                print(f"Resultados consolidados salvos com sucesso em: {self.consolidated_results_file}")
            else:
                print("Nenhum resultado para consolidar.")
        except Exception as e:
            print(f"Erro ao chamar o processo de consolidação: {e}")


if __name__ == "__main__":
    print("Este arquivo contém a classe DatabaseController e funções de consolidação.")
    print("Para usar, importe a classe DatabaseController em seu script principal.")
    print("Exemplo de uso:")
    print("  from database_controller import DatabaseController")
    print("  db_controller = DatabaseController()")
    print("  db_controller.consolidate_results()")
