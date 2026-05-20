
# -*- coding: utf-8 -*-
"""
Script de teste para validar as novas funções objetivo (SEP 3, 5 e 9 barras)
e demonstrar o uso da lógica do run.py de forma programática.
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório src ao path para os imports funcionarem
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

from run import run_framework_many_executions, ARRAY_FITNESS_FUNCTIONS

def test_sep_cases():
    print("\n" + "="*60)
    print("INICIANDO TESTES AUTOMATIZADOS DOS CASOS SEP")
    print("="*60)

    # Lista de índices das novas funções objetivo
    # 5: funcao_objetivo_SEP3
    # 6: funcao_objetivo_SEP5
    # 7: funcao_objetivo_SEP9
    sep_indices = [5, 6, 7]

    for idx in sep_indices:
        func_name = ARRAY_FITNESS_FUNCTIONS[idx].__name__
        print(f"\n>>> Testando: {func_name} (Índice {idx})")
        
        # Define o IND_SIZE correto baseado no caso
        # SEP3: 1 agendamento
        # SEP5: 2 agendamentos
        # SEP9: 2 agendamentos
        ind_size = 1 if idx == 5 else 2

        try:
            # Carrega parâmetros base e sobrescreve IND_SIZE
            import json
            params_path = current_dir / "params.json"
            with open(params_path, "r") as f:
                params = json.load(f)
            
            params["IND_SIZE"] = ind_size
            # Também ajustamos VARIAVEIS_DE_DECISAO para o tamanho correto
            params["VARIAVEIS_DE_DECISAO"] = params.get("VARIAVEIS_DE_DECISAO", params.get("ARRAY_VAR", []))[:ind_size]
            
            # Garante que NUM_VAR_DIFERENTES não seja maior que IND_SIZE
            if params.get("NUM_VAR_DIFERENTES", 0) >= ind_size:
                params["NUM_VAR_DIFERENTES"] = max(0, ind_size - 1)
            
            with open(params_path, "w") as f:
                json.dump(params, f, indent=4)
                f.flush()
                os.fsync(f.fileno())
            
            import time
            time.sleep(1) # Pequena pausa para garantir que o arquivo foi escrito
            
            run_framework_many_executions(
                function_bechmarking=False,
                config_num_arg=1,
                exec_num_arg=1,
                objective_function_index=idx
            )
            print(f"✅ Teste concluído com sucesso para {func_name}")
            
        except Exception as e:
            print(f"❌ Erro ao testar {func_name}: {e}")

if __name__ == "__main__":
    # Forçamos o modo não-CLI para o teste não parar pedindo input
    import run
    run.CLI = False
    
    test_sep_cases()
