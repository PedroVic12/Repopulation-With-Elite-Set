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

#!/usr/bin/env python3
"""
Script para consolidar todos os resultados das execuções em um único arquivo Excel.
Consolida dados de todas as pastas run_* e suas configurações.
"""

import os
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import glob

def consolidar_resultados():
    """
    Consolida todos os resultados das execuções em um único DataFrame
    """
    # Usando caminho relativo ao diretório do script
    output_dir = Path(__file__).parent /  "output"
    resultados_consolidados = []

    print(f"Pasta de saída definida como: {output_dir.resolve()}")

    # Encontrar todas as pastas de execução
    pastas_run = glob.glob(str(output_dir / "run_*"))

    print(f"Encontradas {len(pastas_run)} pastas de execução:")
    
    for pasta_run in pastas_run:
        pasta_run_path = Path(pasta_run)
        nome_run = pasta_run_path.name
        
        # Encontrar todas as configurações dentro da pasta run
        configs = glob.glob(str(pasta_run_path / "config_*"))
        
        print(f"  {nome_run}: {len(configs)} configurações")
        
        for config in configs:
            config_path = Path(config)
            nome_config = config_path.name
            
            # Encontrar todos os arquivos de resultados
            resultados = glob.glob(str(config_path / "*_exec_*_results.json"))
            
            for resultado in resultados:
                try:
                    with open(resultado, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                    
                    # Extrair informações básicas
                    linha_resultado = {
                        'pasta_run': nome_run,
                        'configuracao': nome_config,
                        'execucao': dados.get('exec_num', 'N/A'),
                        'config_num': dados.get('config_num', 'N/A')
                    }
                    
                    # Extrair parâmetros
                    params = dados.get('params', {})
                    for param, valor in params.items():
                        if isinstance(valor, list):
                            # Para arrays, criar colunas separadas
                            for i, v in enumerate(valor):
                                linha_resultado[f'{param}_{i+1}'] = v
                        else:
                            linha_resultado[f'param_{param}'] = valor
                    
                    # Extrair melhores variáveis
                    best_vars = dados.get('best_variables', [])
                    for i, var in enumerate(best_vars):
                        linha_resultado[f'best_var_{i+1}'] = var
                    
                    # Extrair fitness e geração
                    linha_resultado['best_fitness'] = dados.get('best_fitness', 'N/A')
                    linha_resultado['best_gen_idx'] = dados.get('best_gen_idx', 'N/A')
                    
                    resultados_consolidados.append(linha_resultado)
                    
                except Exception as e:
                    print(f"    Erro ao processar {resultado}: {e}")
    
    return resultados_consolidados

def salvar_excel(resultados, output_dir):
    """
    Salva os resultados consolidados em um arquivo Excel
    """
    if not resultados:
        print("Nenhum resultado encontrado para consolidar!")
        return
    
    # Criar DataFrame
    df = pd.DataFrame(resultados)
    
    # Reorganizar colunas para melhor visualização
    colunas_ordenadas = []
    
    # Colunas de identificação primeiro
    colunas_ordenadas.extend(['pasta_run', 'configuracao', 'execucao', 'config_num'])
    
    # Parâmetros
    colunas_params = [col for col in df.columns if col.startswith('param_')]
    colunas_params.sort()
    colunas_ordenadas.extend(colunas_params)
    
    # Melhores variáveis
    colunas_best = [col for col in df.columns if col.startswith('best_var_')]
    colunas_best.sort()
    colunas_ordenadas.extend(colunas_best)
    
    # Fitness e geração
    colunas_fitness = ['best_fitness', 'best_gen_idx']
    colunas_ordenadas.extend(colunas_fitness)
    
    # Reordenar DataFrame
    df = df[colunas_ordenadas]
    
    # Nome do arquivo com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"resultados_consolidados.xlsx"
    caminho_arquivo = output_dir / nome_arquivo
    
    # Salvar Excel
    with pd.ExcelWriter(caminho_arquivo, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Resultados_Consolidados', index=False)
        
        # Ajustar largura das colunas
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
    
    # Mostrar estatísticas
    print(f"\nEstatísticas:")
    print(f"  - Pastas de execução: {df['pasta_run'].nunique()}")
    print(f"  - Configurações: {df['configuracao'].nunique()}")
    print(f"  - Execuções: {df['execucao'].nunique()}")
    
    return caminho_arquivo

def main():
    """
    Função principal
    """
    print("=== CONSOLIDADOR DE RESULTADOS ===")
    print("Iniciando consolidação...\n")
    
    try:
        # Consolidar resultados
        resultados = consolidar_resultados()
        
        if resultados:
            # Salvar em Excel na pasta output
            output_dir = Path(__file__).parent  / "output"
            arquivo_salvo = salvar_excel(resultados, output_dir)
            
            print(f"Consolidação concluída com sucesso!")
            print(f"Arquivo salvo em: {arquivo_salvo}")
        else:
            print("Nenhum resultado encontrado para consolidar!")
            
    except Exception as e:
        print(f"❌ Erro durante a consolidação: {e}")
        import traceback
        traceback.print_exc()

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
        main()

        try:

            print(f"Resultados consolidados salvos com sucesso em: {self.consolidated_results_file}")
        except Exception as e:
            print(f"Erro ao salvar o arquivo Excel consolidado: {e}")


main()  # Executa a consolidação ao rodar este script diretamente