#!/usr/bin/env python3
"""
Script simplificado para consolidar resultados - sempre salva como 'resultados_consolidados.xlsx'
"""

import json
import pandas as pd
from pathlib import Path
import glob

def consolidar():
    output_dir = Path(__file__).parent
    resultados = []
    
    # Encontrar todas as pastas run_*
    for pasta_run in glob.glob(str(output_dir / "run_*")):
        pasta_run_path = Path(pasta_run)
        nome_run = pasta_run_path.name
        
        # Encontrar configurações
        for config in glob.glob(str(pasta_run_path / "config_*")):
            config_path = Path(config)
            nome_config = config_path.name
            
            # Encontrar resultados
            for resultado in glob.glob(str(config_path / "exec_*_results.json")):
                try:
                    with open(resultado, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                    
                    linha = {
                        'pasta_run': nome_run,
                        'configuracao': nome_config,
                        'execucao': dados.get('exec_num', 'N/A'),
                        'config_num': dados.get('config_num', 'N/A')
                    }
                    
                    # Parâmetros
                    params = dados.get('params', {})
                    for param, valor in params.items():
                        if isinstance(valor, list):
                            for i, v in enumerate(valor):
                                linha[f'{param}_{i+1}'] = v
                        else:
                            linha[f'param_{param}'] = valor
                    
                    # Melhores variáveis
                    best_vars = dados.get('best_variables', [])
                    for i, var in enumerate(best_vars):
                        linha[f'best_var_{i+1}'] = var
                    
                    resultados.append(linha)
                    
                except Exception as e:
                    print(f"Erro em {resultado}: {e}")
    
    if resultados:
        df = pd.DataFrame(resultados)
        
        # Reorganizar colunas
        colunas = ['pasta_run', 'configuracao', 'execucao', 'config_num']
        colunas.extend([col for col in df.columns if col.startswith('param_')])
        colunas.extend([col for col in df.columns if col.startswith('best_var_')])
        
        df = df[colunas]
        
        # Salvar
        arquivo_saida = output_dir / "resultados_consolidados.xlsx"
        df.to_excel(arquivo_saida, index=False)
        
        print(f"✅ Consolidados {len(resultados)} resultados em {arquivo_saida}")
        print(f"📊 {df['pasta_run'].nunique()} pastas, {df['configuracao'].nunique()} configs")
    else:
        print("❌ Nenhum resultado encontrado")

if __name__ == "__main__":
    consolidar() 