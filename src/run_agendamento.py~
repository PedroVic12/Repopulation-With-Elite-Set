# -*- coding: utf-8 -*-
"""
Execução do framework RCE para o problema de agendamento de manutenção.
Este script foi reestruturado usando `src/run.py` como referência para garantir
robustez e a instanciação correta dos objetos.
"""
import sys
import os
import json
import pathlib
from datetime import datetime
from itertools import product

# Adiciona o diretório raiz do projeto ao sys.path para importações corretas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Imports do framework e do projeto
from AlgEvolutivoRCE_backup.Setup import Setup
from AlgEvolutivoRCE_backup.alg_evolutivo_rce import AlgoritimoEvolutivoRCE
from config_backup import format_elapsed_time
from database_controller import run_consolidar_resultados

# Importações das funções de fitness e seus dados associados
from utils.functions_fitness.analise_contingencia.analise_contingencia_ieee14 import (
    funcao_objetivo_ieee14_analise, agendamento_df_ieee14, hashtablesize_ieee14, calcular_fitness_detalhado_ieee14_analise
)
from utils.functions_fitness.analise_contingencia.analise_contingencia_ieee30 import (
    funcao_objetivo_ieee30_analise, agendamento_df_ieee30, hashtablesize_ieee30, calcular_fitness_detalhado_ieee30_analise
)
from utils.functions_fitness.analise_contingencia.analise_contingencia_ieee118 import (
    funcao_objetivo_ieee118_analise, agendamento_df_ieee118, hashtablesize_ieee118, calcular_fitness_detalhado_ieee118_analise
)

# --- CONFIGURAÇÕES GLOBAIS ---
BASE_DIR = pathlib.Path(__file__).resolve().parent

# Mapeamentos para seleção dinâmica da função objetivo e seus parâmetros
ARRAY_FITNESS_FUNCTIONS = [funcao_objetivo_ieee14_analise, funcao_objetivo_ieee30_analise, funcao_objetivo_ieee118_analise]
HASHTABLE_SIZE_FUNCS = {
    funcao_objetivo_ieee14_analise.__name__: hashtablesize_ieee14,
    funcao_objetivo_ieee30_analise.__name__: hashtablesize_ieee30,
    funcao_objetivo_ieee118_analise.__name__: hashtablesize_ieee118,
}
AGENDAMENTO_DFS = {
    funcao_objetivo_ieee14_analise.__name__: agendamento_df_ieee14,
    funcao_objetivo_ieee30_analise.__name__: agendamento_df_ieee30,
    funcao_objetivo_ieee118_analise.__name__: agendamento_df_ieee118,
}
DETAILED_FUNCS = {
    funcao_objetivo_ieee14_analise.__name__: calcular_fitness_detalhado_ieee14_analise,
    funcao_objetivo_ieee30_analise.__name__: calcular_fitness_detalhado_ieee30_analise,
    funcao_objetivo_ieee118_analise.__name__: calcular_fitness_detalhado_ieee118_analise,
}

# --- FUNÇÕES AUXILIARES ---
def load_json(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

def convert_param_values(params):
    float_keys = {"MUTACAO", "CROSSOVER", "PORCENTAGEM"}
    for key, value in params.items():
        if isinstance(value, str) and value.strip().startswith('['):
            try:
                params[key] = json.loads(value)
            except json.JSONDecodeError:
                pass
        else:
            try:
                if key.upper() in float_keys:
                    params[key] = float(value)
                else:
                    params[key] = int(float(value))
            except (ValueError, TypeError):
                pass
    return params

# --- FUNÇÃO PRINCIPAL DE EXECUÇÃO ---
def run_agendamento(numero_funcao_objetivo: int):
    """
    Executa uma série de simulações para uma configuração de agendamento específica.
    """
    # 1. Selecionar a função objetivo
    fitness_func = ARRAY_FITNESS_FUNCTIONS[numero_funcao_objetivo]
    print(f"\nFunção objetivo selecionada: {fitness_func.__name__}")

    # 2. Carregar parâmetros e opções
    params_base = load_json(BASE_DIR / "params.json")
    options = load_json(BASE_DIR / "options.json")
    params_base = convert_param_values(params_base)

    # 3. Gerar combinações de parâmetros (mesmo que seja apenas uma)
    varying_keys = [k for k in options if isinstance(options[k], list) and len(options[k]) > 0]
    combinations = [dict(zip(varying_keys, vals)) for vals in product(*[options[k] for k in varying_keys])] if varying_keys else [{}]
    
    # 4. Configurar ambiente de execução
    repeticoes = options.get('repeticoes_por_config', 1)
    start_time = datetime.now()
    timestamp = start_time.strftime("%Y-%m-%d_%H-%M-%S")
    main_output_dir = BASE_DIR / "output" / f"run_agendamento_{timestamp}"
    os.makedirs(main_output_dir, exist_ok=True)
    print(f"Salvando resultados em: {main_output_dir}")
    print(f"Total de configurações: {len(combinations)} | Repetições por config: {repeticoes}")

    # 5. Loop através de cada combinação de parâmetros (configuração)
    for config_num, combo in enumerate(combinations, 1):
        params = params_base.copy()
        params.update(combo)
        params = convert_param_values(params)

        print(f"\n\n--- Iniciando Configuração {config_num}/{len(combinations)} ---")
        print(f"Parâmetros da configuração: {params}")

        # Ajuste dinâmico do IND_SIZE
        agendamento_df = AGENDAMENTO_DFS[fitness_func.__name__]
        params["IND_SIZE"] = len(agendamento_df)

        # Instanciar Setup UMA VEZ por configuração
        size_func = HASHTABLE_SIZE_FUNCS.get(fitness_func.__name__, lambda: 0)
        setup = Setup(params, fitness_function=fitness_func, tamanho_hash=size_func())
        
        config_dir = main_output_dir / f"config_{config_num}"
        os.makedirs(config_dir, exist_ok=True)

        # 6. Loop de execuções (repetições) para a configuração atual
        for exec_num in range(1, repeticoes + 1):
            print(f"\n--- Iniciando Execução {exec_num}/{repeticoes} ---")
            start_exec_time = datetime.now()

            # Instanciar e rodar o algoritmo
            alg = AlgoritimoEvolutivoRCE(setup, DEBUG=False)
            pop, logbook, best_individual, all_values = alg.run(RCE=True)
            best_variables = list(best_individual)

            # Obter resultados detalhados com o `setup` da execução
            detailed_func = DETAILED_FUNCS[fitness_func.__name__]
            final_results_detailed = detailed_func(individuo=best_variables, setupobj=setup)

            # Salvar resultados
            best_solution_generation, _, _, _ = alg.dashboard.visualize(logbook, pop, config_num=config_num, execution_num=exec_num)
            result = {
                "config_num": config_num,
                "exec_num": exec_num,
                "params": params,
                "best_fitness": best_individual.fitness.values[0] if best_individual.fitness.valid else float('inf'),
                "best_variables_horarios": best_variables,
                "agendamento_detalhado": final_results_detailed["ramos_selecionados"].to_dict('records'),
                "contingencias_avaliadas": final_results_detailed["contingencias"].to_dict('records'),
                "best_gen_idx": best_solution_generation,
                "time": format_elapsed_time(datetime.now() - start_exec_time),
                "fitness_function": fitness_func.__name__
            }
            output_path = config_dir / f"config_{config_num}_exec_{exec_num}_results.json"
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=4, ensure_ascii=False, default=str)
            except Exception as e:
                print(f"Erro ao salvar resultado: {e}")

    print(f"\n--- Todas as configurações foram executadas. Tempo total: {format_elapsed_time(datetime.now() - start_time)} ---")

if __name__ == "__main__":
    # Define qual função objetivo executar. Altere o número para testar outros casos.
    # 0: IEEE14, 1: IEEE30, 2: IEEE118
    NUMERO_FUNCAO_OBJETIVO = 2 # 0: IEEE14, 1: IEEE30, 2: IEEE118
    
    run_agendamento(numero_funcao_objetivo=NUMERO_FUNCAO_OBJETIVO)

    print("\nIniciando consolidação de resultados...")
    try:
        run_consolidar_resultados()
        print("Consolidação de resultados concluída com sucesso.")
    except Exception as e:
        print(f"Um erro inesperado ocorreu ao tentar consolidar os resultados: {e}")
