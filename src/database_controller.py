import glob
print(f"Loading database_controller.py from: {__file__}")
import json
import pandas as pd
from pathlib import Path
import glob
from datetime import datetime
import shutil
import os

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

                    # Extrair fitness e geração
                    linha_resultado['best_fitness'] = dados.get('best_fitness', 'N/A')
                    linha_resultado['best_gen_idx'] = dados.get('best_gen_idx', 'N/A')
                    linha_resultado["Funcao_objetivo"] = dados.get("fitness_function", 'N/A')
                    linha_resultado["Tempo_total_execucao"] = dados.get("time", 'N/A')
                    
                    
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
    colunas_fitness = ['best_fitness', 'best_gen_idx', 'Funcao_objetivo', 'Tempo_total_execucao']
    
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
            self.base_dir = Path(__file__).resolve().parent
        else:
            self.base_dir = base_dir
            
        self.src_dir = self.base_dir 
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

    def get_run_data(self, config_num: int, exec_num: int) -> dict | None:
        """Carrega os dados de um arquivo de resultado individual (results.json)."""
        search_pattern = str(self.output_dir / "**" / f"config_{config_num}_exec_{exec_num}_results.json")
        result_files = glob.glob(search_pattern, recursive=True)
        if not result_files:
            return None
        try:
            with open(result_files[0], 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Aviso: Não foi possível ler o arquivo de resultado para config {config_num}, exec {exec_num}. Erro: {e}")
            return None

    def get_visualization_data_for_run(self, config_num: int, exec_num: int) -> list | None:
        """Carrega os dados de um arquivo de visualização individual (visualization.json)."""
        search_pattern = str(self.output_dir / "**" / f"config_{config_num}_exec_{exec_num}_visualization.json")
        viz_files = glob.glob(search_pattern, recursive=True)
        if not viz_files:
            return None
        try:
            with open(viz_files[0], 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return data.get('viz_data', [])
                else:
                    return None
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Aviso: Não foi possível ler o arquivo de visualização para config {config_num}, exec {exec_num}. Erro: {e}")
            return None

    def get_execution_summary(self) -> dict:
        """Retorna um resumo organizado de todas as execuções e arquivos de saída."""
        summary = {
            'total_runs': 0,
            'total_configs': 0,
            'total_files': 0,
            'file_counts': {
                'json': 0,
                'html': 0,
                'pkl': 0,
                'xlsx': 0,
                'other': 0
            }
        }
        
        all_files = glob.glob(str(self.output_dir / "**/*"), recursive=True)
        
        config_exec_pairs = set()
        
        for file_path_str in all_files:
            file_path = Path(file_path_str)
            if file_path.is_file():
                summary['total_files'] += 1
                file_ext = file_path.suffix.lower()
                if file_ext == '.json':
                    summary['file_counts']['json'] += 1
                    # Try to extract config_num and exec_num from results.json
                    if '_results.json' in file_path.name:
                        try:
                            parts = file_path.name.split('_')
                            config_num = int(parts[1])
                            exec_num = int(parts[3])
                            config_exec_pairs.add((config_num, exec_num))
                        except (ValueError, IndexError):
                            pass # Not a standard results file
                elif file_ext == '.html':
                    summary['file_counts']['html'] += 1
                elif file_ext == '.pkl':
                    summary['file_counts']['pkl'] += 1
                elif file_ext == '.xlsx':
                    summary['file_counts']['xlsx'] += 1
                else:
                    summary['file_counts']['other'] += 1
        
        summary['total_runs'] = len(config_exec_pairs)
        # This is a simplification; actual total configs would require parsing all params.json
        # For now, we'll count unique config_nums from results files
        summary['total_configs'] = len(set(pair[0] for pair in config_exec_pairs))
        
        return summary

    def cleanup_empty_folders(self):
        """
        Remove pastas de execução vazias ou pastas de configuração dentro das pastas de execução,
        que podem ser resultado de simulações com falha ou incompletas.
        """
        print("\n🧹 INICIANDO LIMPEZA DE PASTAS VAZIAS...")
        run_folders = glob.glob(str(self.output_dir / "run_*"))
        deleted_folders = []

        for run_folder_path in run_folders:
            # Primeiro, limpa as pastas de configuração vazias dentro
            config_folders = glob.glob(str(Path(run_folder_path) / "config_*"))
            for config_folder_path in config_folders:
                if not os.listdir(config_folder_path):
                    print(f"  - Removendo pasta de configuração vazia: {Path(config_folder_path).name} em {Path(run_folder_path).name}")
                    try:
                        shutil.rmtree(config_folder_path)
                        deleted_folders.append(config_folder_path)
                    except OSError as e:
                        print(f"    Erro ao remover {config_folder_path}: {e}")
            
            # Agora, verifica se a própria pasta de execução está vazia
            if not os.listdir(run_folder_path):
                print(f"  - Removendo pasta de run vazia: {Path(run_folder_path).name}")
                try:
                    shutil.rmtree(run_folder_path)
                    deleted_folders.append(run_folder_path)
                except OSError as e:
                    print(f"    Erro ao remover {run_folder_path}: {e}")

        if deleted_folders:
            print(f"  ✅ Limpeza concluída. {len(deleted_folders)} pastas removidas.")
        else:
            print("  ✅ Nenhuma pasta vazia encontrada para limpar.")
        print("=" * 60)
        return deleted_folders

    def consolidate_results(self):
        """
        Chama a lógica de consolidação para gerar o arquivo Excel.
        """
        try:
            resultados = consolidar_resultados(self.output_dir)
            if resultados:
                salvar_excel(resultados, self.output_dir)
                print(f"Resultados consolidados salvos com sucesso em: {self.consolidated_results_file}")
            else:
                print("Nenhum resultado para consolidar.")
        except Exception as e:
            print(f"Erro ao chamar o processo de consolidação: {e}")

    def run(self, consolidate: bool = True, show_data: bool = True, show_viz_data: bool = True, cleanup: bool = True):
        """
        Executa um fluxo de trabalho completo de gerenciamento de dados.
        Esta é a função "potente" que orquestra várias operações.
        
        Args:
            consolidate (bool): Se deve executar o processo de consolidação.
            show_data (bool): Se deve carregar e exibir os dados consolidados.
            show_viz_data (bool): Se deve carregar e exibir os dados de visualização.
            cleanup (bool): Se deve limpar pastas vazias de simulações com falha.
        """
        print("🚀 INICIANDO FLUXO DE TRABALHO DO DATABASE CONTROLLER 🚀")
        print("=" * 60)

        if cleanup:
            self.cleanup_empty_folders()

        if consolidate:
            print("\n1️⃣ EXECUTANDO CONSOLIDAÇÃO DE RESULTADOS...")
            self.consolidate_results()

        if show_data:
            print("\n2️⃣ CARREGANDO DADOS CONSOLIDADOS...")
            df_consolidado = self.get_consolidated_data()
            if df_consolidado is not None:
                print(f"   ✅ Dados consolidados carregados. {len(df_consolidado)} linhas.")
                print("   Primeiras 5 linhas:")
                print(df_consolidado.head())
            else:
                print("   ❌ Nenhum dado consolidado encontrado.")

        if show_viz_data:
            print("\n3️⃣ CARREGANDO DADOS DE VISUALIZAÇÃO...")
            viz_data = self.get_visualization_data()
            if viz_data:
                print(f"   ✅ Dados de visualização carregados. {len(viz_data)} registros.")
                print("   Primeiros 5 registros:")
                for i, item in enumerate(viz_data[:5]):
                    print(f"     - {item}")
            else:
                print("   ❌ Nenhum dado de visualização encontrado.")

        print("\n🎯 FLUXO DE TRABALHO DO DATABASE CONTROLLER CONCLUÍDO! 🎯")
        print("=" * 60)



class ConsolidationManager:
    """
    Gerenciador especializado para consolidação de resultados.
    Funciona em conjunto com o DatabaseController original.
    """
    
    def __init__(self, base_dir: Path = None):
        if base_dir is None:
            self.base_dir = Path(__file__).resolve().parent
        else:
            self.base_dir = base_dir
            
        self.src_dir = self.base_dir 
        self.output_dir = self.src_dir / "output"
        self.consolidated_results_file = self.output_dir / "resultados_consolidados.xlsx"
        
        self.output_dir.mkdir(exist_ok=True)
    
    def get_consolidation_status(self) -> dict:
        """
        Retorna o status atual da consolidação de resultados.
        
        Returns:
            dict: Dicionário com informações sobre o status da consolidação
        """
        status = {
            'consolidated_file_exists': False,
            'consolidated_file_path': str(self.consolidated_results_file),
            'last_consolidation': None,
            'total_executions': 0,
            'total_configs': 0,
            'file_size_mb': 0,
            'needs_consolidation': False
        }
        
        try:
            # Verifica se o arquivo consolidado existe
            if self.consolidated_results_file.exists():
                status['consolidated_file_exists'] = True
                
                # Informações do arquivo
                file_info = self._get_file_info("resultados_consolidados.xlsx")
                if file_info:
                    status['last_consolidation'] = file_info['modified']
                    status['file_size_mb'] = file_info['size_mb']
                
                # Informações dos dados
                df = self._load_consolidated_data()
                if df is not None:
                    status['total_executions'] = len(df)
                    
                    # Tenta identificar colunas de configuração
                    config_cols = [col for col in df.columns if 'config' in col.lower()]
                    if config_cols:
                        status['total_configs'] = df[config_cols[0]].nunique()
                
                # Verifica se precisa de nova consolidação
                individual_files = len(glob.glob(str(self.output_dir / "*_exec_*_results.json")))
                status['needs_consolidation'] = individual_files > status['total_executions']
                
            else:
                # Se não existe arquivo consolidado, verifica se há arquivos individuais
                individual_files = len(glob.glob(str(self.output_dir / "*_exec_*_results.json")))
                status['needs_consolidation'] = individual_files > 0
                
        except Exception as e:
            status['error'] = str(e)
        
        return status
    
    def run_consolidation(self) -> bool:
        """
        Executa o processo completo de consolidação e salva em um arquivo Excel.
        
        Returns:
            bool: True se a consolidação foi bem-sucedida, False caso contrário
        """
        print("=== CONSOLIDAÇÃO DE RESULTADOS ===")
        try:
            # Verifica se o diretório de saída existe
            if not self.output_dir.exists():
                print(f"❌ Diretório de saída não encontrado: {self.output_dir}")
                return False
            
            # Executa a consolidação
            consolidar_resultados(self.output_dir)
            salvar_excel(self._gather_all_results(), self.output_dir)
            return True

        except Exception as e:
            print(f"❌ Erro durante a consolidação: {e}")
            import traceback
            traceback.print_exc()
            return False
    
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
    
    def _save_dataframe_to_excel(self, df: pd.DataFrame) -> bool:
        """
        Salva o DataFrame em um arquivo Excel com formatação.
        
        Args:
            df: DataFrame a ser salvo
            
        Returns:
            bool: True se o arquivo foi salvo com sucesso, False caso contrário
        """
        try:
            with pd.ExcelWriter(self.consolidated_results_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Resultados_Consolidados', index=False)
                worksheet = writer.sheets['Resultados_Consolidados']
                
                # Ajusta largura das colunas automaticamente
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
                
                # Adiciona informações de metadados
                metadata_sheet = writer.sheets['Resultados_Consolidados']
                metadata_sheet.sheet_properties.tabColor = "1072BA"
                
            print(f"📁 Arquivo salvo em: {self.consolidated_results_file}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar arquivo Excel: {e}")
            return False
    
    def _load_consolidated_data(self) -> pd.DataFrame | None:
        """Lê o arquivo de resultados consolidados e o retorna como um DataFrame."""
        if not self.consolidated_results_file.exists():
            print(f"Aviso: Arquivo consolidado não encontrado em {self.consolidated_results_file}")
            return None
        try:
            return pd.read_excel(self.consolidated_results_file)
        except Exception as e:
            print(f"Erro ao ler o arquivo Excel consolidado: {e}")
            return None
    
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
    
    def _get_file_info(self, file_path: str) -> dict:
        """Retorna informações detalhadas sobre um arquivo específico."""
        full_path = self.output_dir / file_path
        
        if not full_path.exists():
            return None
        
        file_stat = full_path.stat()
        
        info = {
            'name': full_path.name,
            'size_bytes': file_stat.st_size,
            'size_mb': round(file_stat.st_size / (1024 * 1024), 2),
            'created': datetime.fromtimestamp(file_stat.st_ctime),
            'modified': datetime.fromtimestamp(file_stat.st_mtime),
            'extension': full_path.suffix,
            'full_path': str(full_path)
        }
        
        return info


def run_consolidar_resultados():
    base_directory = Path(__file__).resolve().parent
    controller = DatabaseController(base_dir=base_directory)

    controller.consolidate_results()
    
#run_consolidar_resultados()

def run_controller():
    base_directory = Path(__file__).resolve().parent
    controller = DatabaseController(base_dir=base_directory)
    
    # Exemplo de uso da nova função run com todas as funcionalidades
    controller.run(
        consolidate=True,
        show_data=True,
        show_viz_data=True
    )