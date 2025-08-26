#!/usr/bin/env python3
"""
Gerenciador de Consolidação para o Framework RCE.
Arquivo separado para não modificar o database_controller.py original.
"""

import json
import pandas as pd
from pathlib import Path
import glob
from datetime import datetime
import shutil
import zipfile

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
            
        self.src_dir = self.base_dir / "src"
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
        print("=== INICIANDO CONSOLIDAÇÃO DE RESULTADOS ===")
        try:
            # Verifica se o diretório de saída existe
            if not self.output_dir.exists():
                print(f"❌ Diretório de saída não encontrado: {self.output_dir}")
                return False
            
            # Busca todos os resultados
            results_list = self._gather_all_results()
            if not results_list:
                print("❌ Nenhum resultado encontrado para consolidar!")
                print("💡 Verifique se existem arquivos *_exec_*_results.json no diretório de saída")
                return False

            print(f"📊 Processando {len(results_list)} resultados...")
            
            # Cria o DataFrame consolidado
            df = self._create_consolidated_dataframe(results_list)
            if df is None or df.empty:
                print("❌ Erro ao criar DataFrame consolidado!")
                return False
            
            print(f"📋 DataFrame criado com {len(df)} linhas e {len(df.columns)} colunas")
            
            # Salva em Excel
            success = self._save_dataframe_to_excel(df)
            if success:
                print("\n✅ Consolidação concluída com sucesso!")
                print(f"📁 Arquivo salvo em: {self.consolidated_results_file}")
                return True
            else:
                print("❌ Erro ao salvar arquivo Excel!")
                return False

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

# Para uso direto
if __name__ == '__main__':
    print("🔧 TESTE DO CONSOLIDATION MANAGER")
    print("=" * 40)
    
    manager = ConsolidationManager()
    
    # Verifica status
    status = manager.get_consolidation_status()
    print(f"📊 Status da consolidação:")
    print(f"  • Arquivo existe: {status['consolidated_file_exists']}")
    print(f"  • Precisa consolidar: {status['needs_consolidation']}")
    
    if status['needs_consolidation']:
        print("\n🔄 Executando consolidação...")
        success = manager.run_consolidation()
        if success:
            print("✅ Consolidação concluída com sucesso!")
        else:
            print("❌ Falha na consolidação!")
    else:
        print("✅ Consolidação está atualizada!") 