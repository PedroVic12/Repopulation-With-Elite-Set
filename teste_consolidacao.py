#!/usr/bin/env python3
"""
Script de teste para verificar a consolidação
"""

import json
from pathlib import Path

def testar_estrutura():
    """Testa se a estrutura dos arquivos está correta"""
    output_dir = Path(__file__).parent / "src" / "output"
    
    print(f"Verificando estrutura em: {output_dir}")
    
    # Encontrar pastas run_*
    pastas_run = list(output_dir.glob("run_*"))
    print(f"Pastas encontradas: {len(pastas_run)}")
    
    for pasta in pastas_run:
        print(f"\n📁 {pasta.name}:")
        
        # Encontrar configurações
        configs = list(pasta.glob("config_*"))
        print(f"  Configurações: {len(configs)}")
        
        for config in configs:
            print(f"    📂 {config.name}:")
            
            # Encontrar arquivos de resultados
            resultados = list(config.glob("*_exec_*_results.json"))
            print(f"      Resultados: {len(resultados)}")
            
            for resultado in resultados:
                try:
                    with open(resultado, 'r') as f:
                        dados = json.load(f)
                    
                    # Verificar campos obrigatórios
                    campos_obrigatorios = ['config_num', 'exec_num', 'params', 'best_variables', 'best_fitness', 'best_gen_idx']
                    campos_faltando = [campo for campo in campos_obrigatorios if campo not in dados]
                    
                    if campos_faltando:
                        print(f"        ❌ {resultado.name}: campos faltando: {campos_faltando}")
                    else:
                        print(f"        ✅ {resultado.name}: OK")
                        print(f"          Fitness: {dados.get('best_fitness')}")
                        print(f"          Geração: {dados.get('best_gen_idx')}")
                        print(f"          Variáveis: {dados.get('best_variables')}")
                        
                except Exception as e:
                    print(f"        ❌ {resultado.name}: erro ao ler: {e}")

if __name__ == "__main__":
    testar_estrutura() 