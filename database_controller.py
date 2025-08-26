import json
import pandas as pd
from pathlib import Path
import glob
from datetime import datetime
import subprocess
import sys
import shutil
import zipfile
from abc import ABC, abstractmethod

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
        
        # Inicializa o orquestrador de arquivos de saída
        self._file_orchestrator = FileOutputOrchestrator(self.output_dir)

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

    def get_consolidated_data(self) -> pd.DataFrame | None:
        """Lê o arquivo de resultados consolidados e o retorna como um DataFrame."""
        if not self.consolidated_results_file.exists():
            print(f"Aviso: Arquivo consolidado não encontrado em {self.consolidated_results_file}")
            return None
        try:
            return pd.read_excel(self.consolidated_results_file)
        except Exception as e:
            print(f"Erro ao ler o arquivo Excel consolidado: {e}")
            return None

    def consolidar_script_button(self):
        """Executa o processo de consolidação. Mantido para compatibilidade com launchers existentes."""
        self.run_consolidation()

    def get_consolidated_data(self):
        df = pd.read_excel("/home/pedrov12/Documentos/GitHub/Repopulation-With-Elite-Set/src/output/resultados_consolidados.xlsx")
        return df

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

    # --- Métodos de Orquestração de Arquivos de Saída ---
    
    def get_execution_summary(self) -> dict:
        """Retorna um resumo organizado de todas as execuções."""
        return self._file_orchestrator.get_execution_summary()
    
    def get_all_output_files(self, file_type: str = None) -> dict:
        """Retorna um dicionário organizado com todos os arquivos de saída."""
        return self._file_orchestrator.get_all_output_files(file_type)
    
    def find_files_by_pattern(self, pattern: str) -> list:
        """Busca arquivos por padrão específico."""
        return self._file_orchestrator.find_files_by_pattern(pattern)
    
    def organize_outputs_by_config(self, target_dir: str = None) -> bool:
        """Organiza os arquivos de saída por configuração em diretórios separados."""
        return self._file_orchestrator.organize_outputs_by_config(target_dir)
    
    def create_output_report(self, output_file: str = None) -> bool:
        """Cria um relatório detalhado de todos os arquivos de saída."""
        return self._file_orchestrator.create_output_report(output_file)
    
    def cleanup_old_runs(self, keep_last_n: int = 5) -> bool:
        """Remove execuções antigas, mantendo apenas as N mais recentes."""
        return self._file_orchestrator.cleanup_old_runs(keep_last_n)
    
    def export_run_to_zip(self, run_name: str, output_zip: str = None) -> bool:
        """Exporta uma execução específica para um arquivo ZIP."""
        return self._file_orchestrator.export_run_to_zip(run_name, output_zip)
    
    def get_file_info(self, file_path: str) -> dict:
        """Retorna informações detalhadas sobre um arquivo específico."""
        return self._file_orchestrator.get_file_info(file_path)


class FileOutputOrchestrator:
    """
    Orquestrador especializado para gerenciar e organizar todos os arquivos de saída
    (.json, .html, .pkl, .xlsx) gerados pelas execuções do framework.
    
    Implementa o Strategy Pattern para separar a responsabilidade de orquestração
    de arquivos da lógica principal do DatabaseController.
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self._run_directories = self._discover_run_directories()
    
    def _discover_run_directories(self) -> list:
        """Descobre todos os diretórios de execução baseados no padrão run_YYYY-MM-DD_HH-MM-SS"""
        run_pattern = str(self.output_dir / "run_*")
        run_dirs = glob.glob(run_pattern)
        return sorted(run_dirs, reverse=True)  # Mais recentes primeiro
    
    def get_execution_summary(self) -> dict:
        """Retorna um resumo organizado de todas as execuções."""
        summary = {
            'total_runs': len(self._run_directories),
            'run_directories': [],
            'file_counts': {},
            'latest_execution': None
        }
        
        for run_dir in self._run_directories:
            run_path = Path(run_dir)
            run_name = run_path.name
            
            # Conta arquivos por tipo
            file_counts = {
                'json': len(list(run_path.glob("*.json"))),
                'html': len(list(run_path.glob("*.html"))),
                'pkl': len(list(run_path.glob("*.pkl"))),
                'xlsx': len(list(run_path.glob("*.xlsx")))
            }
            
            run_info = {
                'name': run_name,
                'path': str(run_path),
                'file_counts': file_counts,
                'total_files': sum(file_counts.values())
            }
            
            summary['run_directories'].append(run_info)
            
            # Identifica a execução mais recente
            if summary['latest_execution'] is None:
                summary['latest_execution'] = run_info
        
        # Conta arquivos totais por tipo
        all_files = self.get_all_output_files('all')
        summary['file_counts'] = {k: len(v) for k, v in all_files.items()}
        
        return summary
    
    def get_all_output_files(self, file_type: str = None) -> dict:
        """
        Retorna um dicionário organizado com todos os arquivos de saída.
        
        Args:
            file_type: Filtro opcional ('json', 'html', 'pkl', 'xlsx', 'all')
        """
        files_by_type = {
            'json': [],
            'html': [],
            'pkl': [],
            'xlsx': [],
            'other': []
        }
        
        # Busca recursiva por todos os arquivos
        all_files = glob.glob(str(self.output_dir / "**/*"), recursive=True)
        
        for file_path in all_files:
            if Path(file_path).is_file():
                file_ext = Path(file_path).suffix.lower()
                rel_path = Path(file_path).relative_to(self.output_dir)
                
                if file_ext == '.json':
                    files_by_type['json'].append(str(rel_path))
                elif file_ext == '.html':
                    files_by_type['html'].append(str(rel_path))
                elif file_ext == '.pkl':
                    files_by_type['pkl'].append(str(rel_path))
                elif file_ext == '.xlsx':
                    files_by_type['xlsx'].append(str(rel_path))
                else:
                    files_by_type['other'].append(str(rel_path))
        
        if file_type and file_type in files_by_type:
            return {file_type: files_by_type[file_type]}
        elif file_type == 'all':
            return files_by_type
        else:
            return files_by_type
    
    def find_files_by_pattern(self, pattern: str) -> list:
        """
        Busca arquivos por padrão específico.
        
        Args:
            pattern: Padrão de busca (ex: '*config1*', '*best*', etc.)
        """
        search_pattern = str(self.output_dir / "**" / pattern)
        matching_files = glob.glob(search_pattern, recursive=True)
        
        # Converte para caminhos relativos
        relative_files = [Path(f).relative_to(self.output_dir) for f in matching_files]
        return [str(f) for f in relative_files]
    
    def organize_outputs_by_config(self, target_dir: str = None) -> bool:
        """
        Organiza os arquivos de saída por configuração em diretórios separados.
        
        Args:
            target_dir: Diretório de destino (padrão: output/organized_by_config)
        """
        if target_dir is None:
            target_dir = self.output_dir / "organized_by_config"
        else:
            target_dir = Path(target_dir)
        
        target_dir.mkdir(exist_ok=True)
        
        try:
            # Busca todos os arquivos de resultado
            result_files = glob.glob(str(self.output_dir / "*_exec_*_results.json"))
            
            for result_file in result_files:
                data = self._load_json(Path(result_file))
                if not data:
                    continue
                
                config_num = data.get('config_num')
                exec_num = data.get('exec_num')
                
                if config_num is None:
                    continue
                
                # Cria diretório para a configuração
                config_dir = target_dir / f"config_{config_num}"
                config_dir.mkdir(exist_ok=True)
                
                # Move arquivos relacionados
                base_pattern = f"config_{config_num}_exec_{exec_num}"
                related_files = glob.glob(str(self.output_dir / f"{base_pattern}*"))
                
                for file_path in related_files:
                    file_path = Path(file_path)
                    if file_path.exists():
                        dest_path = config_dir / file_path.name
                        shutil.copy2(file_path, dest_path)
            
            print(f"✅ Arquivos organizados por configuração em: {target_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao organizar arquivos: {e}")
            return False
    
    def create_output_report(self, output_file: str = None) -> bool:
        """
        Cria um relatório detalhado de todos os arquivos de saída.
        
        Args:
            output_file: Arquivo de saída (padrão: output/output_report.xlsx)
        """
        if output_file is None:
            output_file = self.output_dir / "output_report.xlsx"
        else:
            output_file = Path(output_file)
        
        try:
            summary = self.get_execution_summary()
            
            # Cria DataFrames para o relatório
            run_summary_df = pd.DataFrame(summary['run_directories'])
            
            # Lista detalhada de arquivos
            all_files = self.get_all_output_files('all')
            files_df = pd.DataFrame([
                {'file_type': file_type, 'file_path': file_path}
                for file_type, files in all_files.items()
                for file_path in files
            ])
            
            # Salva relatório em Excel
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Resumo geral
                summary_df = pd.DataFrame([{
                    'Total de Execuções': summary['total_runs'],
                    'Total de Arquivos JSON': summary['file_counts']['json'],
                    'Total de Arquivos HTML': summary['file_counts']['html'],
                    'Total de Arquivos PKL': summary['file_counts']['pkl'],
                    'Total de Arquivos XLSX': summary['file_counts']['xlsx']
                }])
                summary_df.to_excel(writer, sheet_name='Resumo_Geral', index=False)
                
                # Detalhes das execuções
                run_summary_df.to_excel(writer, sheet_name='Execucoes', index=False)
                
                # Lista de arquivos
                files_df.to_excel(writer, sheet_name='Arquivos', index=False)
            
            print(f"✅ Relatório criado em: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar relatório: {e}")
            return False
    
    def cleanup_old_runs(self, keep_last_n: int = 5) -> bool:
        """
        Remove execuções antigas, mantendo apenas as N mais recentes.
        
        Args:
            keep_last_n: Número de execuções mais recentes para manter
        """
        try:
            if len(self._run_directories) <= keep_last_n:
                print(f"✅ Apenas {len(self._run_directories)} execuções encontradas. Nenhuma limpeza necessária.")
                return True
            
            runs_to_remove = self._run_directories[keep_last_n:]
            
            for run_dir in runs_to_remove:
                run_path = Path(run_dir)
                if run_path.exists():
                    shutil.rmtree(run_path)
                    print(f"🗑️ Removido: {run_path.name}")
            
            # Atualiza lista de diretórios
            self._run_directories = self._discover_run_directories()
            
            print(f"✅ Limpeza concluída. Mantidas {keep_last_n} execuções mais recentes.")
            return True
            
        except Exception as e:
            print(f"❌ Erro durante limpeza: {e}")
            return False
    
    def export_run_to_zip(self, run_name: str, output_zip: str = None) -> bool:
        """
        Exporta uma execução específica para um arquivo ZIP.
        
        Args:
            run_name: Nome da execução (ex: 'run_2025-08-25_21-46-02')
            output_zip: Nome do arquivo ZIP de saída
        """
        run_path = self.output_dir / run_name
        if not run_path.exists():
            print(f"❌ Execução não encontrada: {run_name}")
            return False
        
        if output_zip is None:
            output_zip = f"{run_name}.zip"
        
        try:
            with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in run_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(run_path)
                        zipf.write(file_path, arcname)
            
            print(f"✅ Execução exportada para: {output_zip}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao exportar execução: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> dict:
        """
        Retorna informações detalhadas sobre um arquivo específico.
        
        Args:
            file_path: Caminho relativo do arquivo
        """
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


# Para permitir a execução direta do script para consolidação
if __name__ == '__main__':
    # O diretório base é o diretório pai do diretório onde o script está
    # Ex: /path/to/project/database_controller.py -> /path/to/project
    base_directory = Path(__file__).resolve().parent
    controller = DatabaseController(base_dir=base_directory)
    
    print("🚀 DATABASE CONTROLLER + FILE ORCHESTRATOR")
    print("=" * 50)
    
    # 1. Executa consolidação tradicional
    print("\n1️⃣ EXECUTANDO CONSOLIDAÇÃO...")
    controller.run_consolidation()
    
    # 2. Demonstra novas funcionalidades de orquestração
    print("\n2️⃣ DEMONSTRANDO ORQUESTRAÇÃO DE ARQUIVOS...")
    
    # Resumo geral
    summary = controller.get_execution_summary()
    print(f"   📁 Total de execuções: {summary['total_runs']}")
    print(f"   📊 Total de arquivos: {sum(summary['file_counts'].values())}")
    
    # Lista arquivos por tipo
    all_files = controller.get_all_output_files('all')
    for file_type, files in all_files.items():
        if files:
            print(f"   📋 {file_type.upper()}: {len(files)} arquivos")
    
    # 3. Cria relatório de saída
    print("\n3️⃣ CRIANDO RELATÓRIO DE SAÍDA...")
    if controller.create_output_report():
        print("   ✅ Relatório criado com sucesso!")
    
    # 4. Organiza arquivos por configuração
    print("\n4️⃣ ORGANIZANDO ARQUIVOS...")
    if controller.organize_outputs_by_config():
        print("   ✅ Arquivos organizados por configuração!")
    
    print("\n🎯 Processo completo concluído!")
    print("\n💡 DICAS DE USO:")
    print("   • controller.get_execution_summary() - Resumo das execuções")
    print("   • controller.find_files_by_pattern('*config1*') - Busca por padrão")
    print("   • controller.cleanup_old_runs(3) - Mantém apenas 3 execuções")
    print("   • controller.export_run_to_zip('run_2025-08-25_21-46-02') - Exporta execução")