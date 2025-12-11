# -*- coding: utf-8 -*-
"""
Execução do framework RCE com configuração de várias execuções e variações de parâmetros.
PVRV - 20/08/2025
"""

# Imports principais do framework
from AlgEvolutivoRCE_backup.Setup import Setup
from AlgEvolutivoRCE_backup.alg_evolutivo_rce import AlgoritimoEvolutivoRCE
#from RedeEletrica_backup.rede_eletrica import RedeEletricaPandaPower

# Utils - Trazer esses codigos para esse unico arquivo
from config_backup import FOLDER_NAME, entrada_de_dados, format_elapsed_time


#! Importando a minha função objetivo dentro do projeto
from utils.functions_fitness.functions_benchmarking import rastrigin
from utils.functions_fitness.function_IEEE_14_contigencias import funcao_objetivo_IEEE14, HASH_TABLE_PATH
from utils.functions_fitness.function_IEEE_118_otimizacao import funcao_objetivo_IEEE118, HASH_TABLE_PATH
from utils.functions_fitness.function_IEEE_30_otimizacao import funcao_objetivo_IEEE30, HASH_TABLE_PATH
from utils.functions_fitness.function_IEEE_57_otimizacao import funcao_objetivo_IEEE57, HASH_TABLE_PATH

# Bibliotecas padrão
import json
import pathlib
import pandas as pd
import numpy as np
import os
from datetime import datetime




# VARIAVEIS GLOBAIS
ARRAY_FITNESS_FUNCTIONS = [funcao_objetivo_IEEE14,funcao_objetivo_IEEE30, funcao_objetivo_IEEE57, funcao_objetivo_IEEE118]

BASE_DIR = pathlib.Path(__file__).resolve().parent

# variaveis de controle
CLI = False
DEBUG_MODE = False
BECHMARKING_MODE = False
SHOW_SETTINGS = False

NUMERO = 1

# Entrada de dados do usuario
print("\nNo arquivo:", BASE_DIR / "utils" / "functions_fitness")
print("\nSELECIONE O SEU CASO DE SIMULAÇÃO DE AGENDAMENTO DE DESLIGAMENTOS DE CONTINGENCIAS E OTIMIZAÇÃO PARA REDES ELÉTRICAS")
print("--------------------------------")
for i in range(len(ARRAY_FITNESS_FUNCTIONS)):
    print(f"{i} - {ARRAY_FITNESS_FUNCTIONS[i].__name__}")
print("--------------------------------\n")


if CLI:
    print("Responda no terminal onde o seu laucher.py esta sendo executado")
    choice = input("Digite o número da funcao objetivo: ")
    NUMERO = int(choice)
    print("\n")
    choice_benchmarking = input("Deseja usar o modo benchmarking? (S/N): default (N) ")
    BECHMARKING_MODE = True if choice_benchmarking.lower() == "s" else False
    print("\n")
    debug_mode = input("Deseja usar o modo debug? (S/N): default (N) ")
    DEBUG_MODE = True if debug_mode.lower() == "s" else False


print("\nLet's rock!\n")

# Funções auxiliares
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

# Função principal para executar o framework com múltiplas execuções
def run_framework_many_executions(function_bechmarking=False):


    if function_bechmarking:
        print("Função objetivo selecionada: Rastrigin")
    else:
        print(f"Função objetivo selecionada: {ARRAY_FITNESS_FUNCTIONS[NUMERO]}")

    print("Função principal para executar o framework com múltiplas execuções.")

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
    
    #! Inicia o contador de tempo de execução
    start = datetime.now()

    # Exibe informações das configurações
    print(f"\nTotal de configurações únicas: {len(combinations)}")
    print(f"Execuções por configuração: {repeticoes}")

    # Cria um diretório de saída com timestamp para evitar sobreposições
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    main_output_dir = BASE_DIR / "output" / f"run_{timestamp}"
    os.makedirs(main_output_dir, exist_ok=True)
    #print(f"\nSalvando resultados em: {main_output_dir}")

    config_num = 1
    for combo in combinations:

        # Cria um diretório específico para a configuração
        config_dir = main_output_dir / f"config_{config_num}"
        os.makedirs(config_dir, exist_ok=True)

        # Monta params para esta configuração
        params = params_base.copy()
        params.update(combo)
        params = convert_values_to_int(params)

        #! 4) Define função objetivo
        fitness_func = ARRAY_FITNESS_FUNCTIONS[NUMERO] if not function_bechmarking else rastrigin

        #! 5) Instancia Setup uma vez por configuração
        print(f"\n\nIniciando configuração {config_num}: {params}")
        setup = Setup(
            params,
            fitness_function=fitness_func,
            tamanho_hash=(
                entrada_de_dados()["num_contingencias"]
                * entrada_de_dados()["num_carregamentos"]
                * (2 ** entrada_de_dados()["num_desligamentos"])
            )
        )

        # Reseta contadores para a nova execução
        # if hasattr(setup, 'objectiveruns'):
        #     setup.objectiveruns = 0
        # if hasattr(setup, 'hashtablereads'):
        #     setup.hashtablereads = 0

        print("Classe Setup iniciada para a configuração.")

        if SHOW_SETTINGS:
            print("\n")
            print("--- [INICIO] ATRIBUTOS DO OBJETO SETUP ---")
            try:
                # Usando json.dumps para uma visualização bonita e segura
                print(json.dumps(vars(setup), indent=4, default=str))
            except Exception as e:
                print(f"Nao foi possivel serializar o objeto Setup: {e}")
            print("--- [FIM] ATRIBUTOS DO OBJETO SETUP ---")


        def consultaHashTable():
            # Consulta hash_table se existir (sub rotina)
            if os.path.exists(HASH_TABLE_PATH):
                try:
                    hash_excel = pd.read_excel(HASH_TABLE_PATH)
                    if not hash_excel.empty:
                        setup.tabela_hash = hash_excel['Fitness'].to_dict()
                        print("Tabela hash carregada!")
                except Exception as e:
                    print(f"Erro ao carregar hash_table.xlsx: {e}")
        consultaHashTable()

        for exec_num in range(1, repeticoes + 1):
            print(f"\n--- Iniciando execução {exec_num}/{repeticoes} ---")


            #! 6) Executa algoritmo
            alg = AlgoritimoEvolutivoRCE(setup, DEBUG=DEBUG_MODE)
            print("Algoritmo Evolutivo iniciado.")
            pop_with_repopulation, logbook_with_repopulation, best_individual, all_individual_values = alg.run(RCE=True)
            best_variables = list(best_individual)

            #! 7) Visualize os Resultados do Primeiro Dashboard do Alg.dashbord aqui
            print("\nEvolução concluída  - 100%")

            best_solution_generation, best_solution_variables, best_solution_fitness, grafico_RCE = alg.dashboard.visualize(
                logbook_with_repopulation,
                pop_with_repopulation,
                config_num=config_num,
                execution_num=exec_num,
            )



            # Passando os valores do array direto no dataframe com os index como chave (hash = chave, valor)
            hash_df1 = pd.DataFrame(setup.tabela_hash, columns=['Fitness'])
            hash_df1.sort_values(by='Fitness', ascending=False, inplace=True)
            hash_df1.to_excel(HASH_TABLE_PATH, index=False)

            # Verificação de velocidade com hashtable
            print(f"\nObjective function runs : {setup.objectiveruns}")
            print(f"Hash table reads : {setup.hashtablereads}")

            end = datetime.now()
            elapsed = end - start
            formatted_time = format_elapsed_time(elapsed)
            print(f"\nElapsed Time in execution : {formatted_time}\n\n")


            #! 8) Salva os dados de  cada visualização
            vis_output_path = config_dir / f"config_{config_num}_exec_{exec_num}_visualization.json"
            try:
                # Convert individuals to lists for JSON serialization
                for item in all_individual_values:
                    if 'Variaveis de Decisão' in item and hasattr(item['Variaveis de Decisão'], 'tolist'):
                        item['Variaveis de Decisão'] = item['Variaveis de Decisão'].tolist()
                    elif isinstance(item['Variaveis de Decisão'], np.ndarray):
                        item['Variaveis de Decisão'] = item['Variaveis de Decisão'].tolist()
                    elif not isinstance(item['Variaveis de Decisão'], (list, str)):
                        item['Variaveis de Decisão'] = list(item['Variaveis de Decisão'])


                with open(vis_output_path, 'w', encoding='utf-8') as f:
                    json.dump(all_individual_values, f, indent=4, ensure_ascii=False)
                print(f"\nDados de visualização salvos em: {vis_output_path}")
            except Exception as e:
                print(f"Erro ao salvar dados de visualização para config {config_num}, exec {exec_num}: {e}")

            #! 9) Salva resultado individual como JSON
            best_fitness = best_individual.fitness.values[0] if best_individual.fitness.valid else float('inf')
            best_gen_idx = logbook_with_repopulation.select("gen")[-1] if logbook_with_repopulation else 'N/A'

            result = {
                "config_num": config_num,
                "exec_num": exec_num,
                "params": params,
                "best_variables": best_variables,
                "best_fitness": best_fitness,
                "best_gen_idx": best_solution_generation,
                "time":formatted_time,
                "fitness_function": fitness_func.__name__
            }
            
            output_path = config_dir / f"config_{config_num}_exec_{exec_num}_results.json"
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=4, ensure_ascii=False)
                print(f"Resultado salvo em: {output_path}")
            except Exception as e:
                print(f"Erro ao salvar resultado para config {config_num}, exec {exec_num}: {e}")

        config_num += 1
    
    print("\nTodas as execuções foram concluídas.")
    
    # Consolidar resultados automaticamente
    try:
        import subprocess
        import sys
        def run_sript_consolidar_resultados():
            # Caminho para o script de consolidação
            consolidar_script = BASE_DIR.parent / "consolidar_resultados.py"
            
            if consolidar_script.exists():
                print(f"Executando consolidação: {consolidar_script}")
                result = subprocess.run([sys.executable, str(consolidar_script)], 
                                        capture_output=True, text=True, cwd=str(BASE_DIR.parent))
                
                if result.returncode == 0:
                    print("✅ Consolidação executada com sucesso!")
                    if result.stdout:
                        print("Saída da consolidação:\n")
                        print(result.stdout)
                else:
                    print(f"❌ Erro na consolidação: {result.stderr}")
            else:
                print(f"⚠️ Script de consolidação não encontrado em: {consolidar_script}")
        run_sript_consolidar_resultados()
            
    except Exception as e:
        print(f"❌ Erro ao executar consolidação: {e}")
        print("Execute manualmente: python3 consolidar_resultados.py")


if __name__ == "__main__":
    run_framework_many_executions(function_bechmarking=BECHMARKING_MODE)


