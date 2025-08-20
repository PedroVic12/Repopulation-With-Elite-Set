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
    output_dir = Path(__file__).parent
    resultados_consolidados = []
    
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
            resultados = glob.glob(str(config_path / "exec_*_results.json"))
            
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
            # Salvar em Excel
            output_dir = Path(__file__).parent
            arquivo_salvo = salvar_excel(resultados, output_dir)
            
            print(f"\n✅ Consolidação concluída com sucesso!")
            print(f"📁 Arquivo salvo em: {arquivo_salvo}")
        else:
            print("❌ Nenhum resultado encontrado para consolidar!")
            
    except Exception as e:
        print(f"❌ Erro durante a consolidação: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 