import json
import itertools
from pathlib import Path

# Import RCE Framework
from AlgEvolutivoRCE.Setup import Setup
from AlgEvolutivoRCE.alg_evolutivo_rce import AlgoritimoEvolutivoRCE

# Utils 
from config import FOLDER_NAME, options_main_file, entrada_de_dados, load_many_executions, format_elapsed_time

import os
import pandas as pd
from datetime import datetime
from utils.functions_fitness.function_IEEE_14_contigencias import funcao_objetivo_IEEE14

# Variáveis globais
execution_times = []  # Lista para armazenar os tempos de execução
results_consolidados = []  # Corrigido para lista

def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def get_param_variaveis(options):
    # Só pega listas com mais de 1 valor (parâmetros variáveis)
    return [k for k, v in options.items() if isinstance(v, list) and len(v) > 1]

def gerar_combinacoes(options, variaveis):
    valores = [options[var] for var in variaveis]
    # Para cada combinação, monta um dicionário com os valores corretos
    return [
        {**options, **dict(zip(variaveis, comb))}
        for comb in itertools.product(*valores)
    ]

def configs_dict(configs):
    # Indexa como config 1, config 2, ...
    return {f"config {i+1}": cfg for i, cfg in enumerate(configs)}

def consulta_hashtable(setup):
    try:
        if os.path.exists("hash_table.xlsx"):
            print("\n\nFazendo consulta para setup.tabela_hash")
            hash_excel = pd.read_excel("hash_table.xlsx")
            if not hash_excel.empty and not hash_excel.isnull().values.any():
                print(hash_excel.head())
                setup.tabela_hash = hash_excel['Fitness'].to_dict()
                neg_one_count = list(setup.tabela_hash.values()).count(-1)
                if -1 in setup.tabela_hash.values():
                    print("Cenários Default = ", len(setup.tabela_hash))
                    print(neg_one_count)
                else:
                    fitness_counts = hash_excel['Fitness'].value_counts()
                    filtered_df = hash_excel[hash_excel['Fitness'] > 14]
                    print(fitness_counts.head())
            else:
                print("O arquivo hash_table.xlsx está vazio ou contém valores nulos.")
        else:
            print("Arquivo da hash table não encontrado!")
    except Exception as e:
        print(f"Erro ao ler o arquivo xlsx: {e}")

def run_framework_groups_executions(configs):
    for idx, (config_name, config) in enumerate(configs.items()):
        print(f"Combinação de Configuração {idx+1}/{len(configs)} - {config_name}")
        dados = entrada_de_dados()
        print(f"\n\nIniciando execução com os parâmetros: {config}")
        setup = Setup(config, fitness_function=funcao_objetivo_IEEE14,
                      tamanho_hash=(dados["num_contingencias"] * dados["num_carregamentos"] * (2 ** dados["num_desligamentos"])))
        consulta_hashtable(setup)
        alg = AlgoritimoEvolutivoRCE(setup, DEBUG=False)
        load_many_executions(config, setup, alg)

def load_many_executions(options, setupobj, algoritmo):
    for i in range(options.get("repeticoes_por_config", 1)):
        print("\n================================")
        print("\tExecução:", i + 1)
        print("================================\n")
        start = datetime.now()
        pop_with_repopulation, logbook_with_repopulation, best_variables = algoritmo.run(RCE=True)
        print("\n\nEvolução concluída  - 100%")
        print(f"Best variables", best_variables)
        x, y, z, fig = algoritmo.dashboard.visualize(
            logbook_with_repopulation, pop_with_repopulation,
            execution_num=i + 1
        )
        hash_df1 = pd.DataFrame(setupobj.tabela_hash, columns=['Fitness'])
        hash_df1.sort_values(by='Fitness', ascending=False, inplace=True)
        hash_df1.to_excel("hash_table.xlsx", index=False)
        print(f"\nObjective function runs : {setupobj.objectiveruns}")
        print(f"Hash table reads : {setupobj.hashtablereads}")
        end = datetime.now()
        elapsed = end - start
        formatted_time = format_elapsed_time(elapsed)
        print(f"Elapsed Time in execution : {formatted_time}")
        execution_times.append(elapsed)
        results_consolidados.append({"execution": i + 1, "solution_variables": y, "best_fitness": z, "best_generations": x, "execution_time": elapsed})

def main():
    base_dir = Path(__file__).parent
    options = load_json(base_dir / "options.json")
    params = load_json(base_dir / "params.json")
    variaveis = get_param_variaveis(options)
    configs = gerar_combinacoes(options, variaveis)
    resultado = configs_dict(configs)
    resultado = {**resultado, **params}
    print(resultado)
    with open(base_dir / "config_teste.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=4, ensure_ascii=False)
    print(f"{len(resultado)} configs salvas em config_teste.json")
    # Chama as execuções
    run_framework_groups_executions(resultado)

if __name__ == "__main__":
    main()