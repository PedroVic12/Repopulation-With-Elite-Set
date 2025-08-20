# -*- coding: utf-8 -*-
"""
Execução única do framework RCE
PVRV - 18/06/2025
"""

# Imports principais do framework
from AlgEvolutivoRCE_backup.Setup import Setup
from AlgEvolutivoRCE_backup.alg_evolutivo_rce import AlgoritimoEvolutivoRCE

# Utils
from config_backup import FOLDER_NAME, entrada_de_dados, format_elapsed_time, load_many_executions
from utils.functions_fitness.functions_benchmarking import rastrigin
from utils.functions_fitness.function_IEEE_14_contigencias import funcao_objetivo_IEEE14

# Bibliotecas padrão
import json
import pathlib
import pandas as pd
import os
from datetime import datetime


BASE_DIR = pathlib.Path(__file__).resolve().parent


def load_params(file_path):
    """Carrega parâmetros de um arquivo JSON."""
    with open(file_path, "r") as file:
        return json.load(file)


def convert_values_to_int(params):
    """Converte valores dos parâmetros para int, float ou listas, se aplicável."""
    float_keys = {"MUTACAO", "CROSSOVER", "PORCENTAGEM"}
    for key, value in params.items():
        # Se for uma string que parece uma lista, tenta converter
        if isinstance(value, str) and value.strip().startswith('['):
            try:
                params[key] = json.loads(value)
                continue # Pula para o próximo item
            except json.JSONDecodeError:
                # Se não for um JSON válido, ignora e mantém a string original
                pass
        
        # Lógica original para floats e ints
        try:
            if key.upper() in float_keys:
                params[key] = float(value)
            else:
                params[key] = int(float(value))
        except (ValueError, TypeError):
            # Ignora erros de conversão para valores que não são numéricos (como as listas já convertidas ou outras strings)
            pass
    return params


def run_framework_many_executions(function_bechmarking=False):
    """Função principal para executar o framework com múltiplas execuções."""

    # 1. Carrega parâmetros base e opções
    params_base = load_params(f"{BASE_DIR}/params.json")
    options = load_params(f"{BASE_DIR}/options.json")
    params_base = convert_values_to_int(params_base)

    # 2. Descobre variações e número de execuções
    varying_keys = [k for k in options if isinstance(options[k], list) and len(options[k]) > 0]
    varying_values = [options[k] for k in varying_keys]
    repeticoes = options.get('repeticoes_por_config', 1)

    # 3. Gera todas as combinações de parâmetros
    from itertools import product
    combinations = [dict(zip(varying_keys, vals)) for vals in product(*varying_values)] if varying_keys else [{}]

    print(f"Total de configurações únicas: {len(combinations)}")
    print(f"Execuções por configuração: {repeticoes}")

    # Cria um diretório de saída com timestamp para evitar sobreposições
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    main_output_dir = BASE_DIR / "output" / f"run_{timestamp}"
    os.makedirs(main_output_dir, exist_ok=True)
    print(f"Salvando resultados em: {main_output_dir}")

    config_num = 1
    for combo in combinations:
        # Cria um diretório específico para a configuração
        config_dir = main_output_dir / f"config_{config_num}"
        os.makedirs(config_dir, exist_ok=True)

        for exec_num in range(1, repeticoes + 1):
            # Monta params para esta execução
            params = params_base.copy()
            params.update(combo)
            params = convert_values_to_int(params)

            print(f"\n\nIniciando execução {exec_num}/{repeticoes} da configuração {config_num}: {params}")

            # Define função objetivo
            fitness_func = funcao_objetivo_IEEE14 if not function_bechmarking else rastrigin

            # Instancia Setup
            setup = Setup(
                params,
                fitness_function=fitness_func,
                tamanho_hash=(
                    entrada_de_dados()["num_contingencias"]
                    * entrada_de_dados()["num_carregamentos"]
                    * (2 ** entrada_de_dados()["num_desligamentos"])
                )
            )
            print("Classe Setup iniciada")

            # Consulta hash_table se existir
            if os.path.exists("hash_table.xlsx"):
                try:
                    hash_excel = pd.read_excel("hash_table.xlsx")
                    if not hash_excel.empty:
                        setup.tabela_hash = hash_excel['Fitness'].to_dict()
                        print("Tabela hash carregada com sucesso!")
                except Exception as e:
                    print(f"Erro ao carregar hash_table.xlsx: {e}")

            # Executa algoritmo
            alg = AlgoritimoEvolutivoRCE(setup, DEBUG=False)
            print("Algoritmo Evolutivo iniciado.")
            pop_with_repopulation, logbook_with_repopulation, best_variables = alg.run(RCE=True)
            print("\n\nEvolução concluída  - 100%")
            print(f"Best variables", best_variables)

            # Salva resultado individual como JSON
            result = {
                "config_num": config_num,
                "exec_num": exec_num,
                "params": params,
                "best_variables": best_variables,
            }
            
            output_path = config_dir / f"exec_{exec_num}_results.json"
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=4, ensure_ascii=False)
                print(f"Resultado salvo em: {output_path}")
            except Exception as e:
                print(f"Erro ao salvar resultado para config {config_num}, exec {exec_num}: {e}")

        config_num += 1
    
    print("\nTodas as execuções foram concluídas.")


if __name__ == "__main__":
    print("Starting execution with benchmark function...")
    run_framework_many_executions(function_bechmarking=False)
