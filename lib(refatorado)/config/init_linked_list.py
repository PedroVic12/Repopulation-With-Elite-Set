import json
import itertools
from pathlib import Path

# Import RCE Framework
from AlgEvolutivoRCE.Setup import Setup
from AlgEvolutivoRCE.alg_evolutivo_rce import AlgoritimoEvolutivoRCE

# Utils 
from config import FOLDER_NAME, options_main_file, entrada_de_dados, format_elapsed_time

import os
import pandas as pd
from datetime import datetime
from utils.functions_fitness.function_IEEE_14_contigencias import funcao_objetivo_IEEE14

# Variáveis globais
execution_times = []
results_consolidados = []

# --- Lista Encadeada Simples para Eficiência ---
class Node:
    def __init__(self, key, value, next=None):
        self.key = key
        self.value = value
        self.next = next

class LinkedConfigList:
    def __init__(self):
        self.head = None
        self.size = 0

    def append(self, key, value):
        new_node = Node(key, value)
        if not self.head:
            self.head = new_node
        else:
            curr = self.head
            while curr.next:
                curr = curr.next
            curr.next = new_node
        self.size += 1

    def __iter__(self):
        curr = self.head
        while curr:
            yield curr.key, curr.value
            curr = curr.next

    def __len__(self):
        return self.size

def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def get_param_variaveis(options):
    return [k for k, v in options.items() if isinstance(v, list) and len(v) > 1]

def gerar_combinacoes(options, variaveis):
    valores = [options[var] for var in variaveis]
    return [
        {**options, **dict(zip(variaveis, comb))}
        for comb in itertools.product(*valores)
    ]

def configs_linked_list(configs):
    ll = LinkedConfigList()
    for i, cfg in enumerate(configs):
        ll.append(f"config_{i+1}", cfg)
    return ll

def consulta_hashtable(setup):
    try:
        if os.path.exists("hash_table.xlsx"):
            hash_excel = pd.read_excel("hash_table.xlsx")
            if not hash_excel.empty and not hash_excel.isnull().values.any():
                setup.tabela_hash = hash_excel['Fitness'].to_dict()
    except Exception as e:
        print(f"Erro ao ler o arquivo xlsx: {e}")
        
def tratamento_dados_json(config):
    config["POP_SIZE"] = int(config["POP_SIZE"][0])  # Convertendo para inteiro
    config["NUM_GENERATIONS"] = int(config["NUM_GENERATIONS"][0])  # Convertendo para inteiro
    print(f"POP_SIZE: {config['POP_SIZE']}")
    print("======================")
    print(f"Iniciando execução com os parâmetros: {config}")
    print("======================")


def run_framework_groups_executions(configs_ll):
    for idx, (config_name, config) in enumerate(configs_ll):
        print(f"Configuração {idx+1}/{len(configs_ll)} - {config_name}")
        dados = entrada_de_dados()
        
        tratamento_dados_json(config)
        
        
        setup = Setup(config, fitness_function=funcao_objetivo_IEEE14,
                      tamanho_hash=(dados["num_contingencias"] * dados["num_carregamentos"] * (2 ** dados["num_desligamentos"])))
        consulta_hashtable(setup)
        alg = AlgoritimoEvolutivoRCE(setup, DEBUG=False)
        load_many_executions(config, setup, alg)

def load_many_executions(options, setupobj, algoritmo):
    for i in range(options.get("repeticoes_por_config", 1)):
        print(f"\n=== Execução: {i + 1} ===")
        start = datetime.now()
        pop_with_repopulation, logbook_with_repopulation, best_variables = algoritmo.run(RCE=True)
        print("Evolução concluída - 100%")
        x, y, z, fig = algoritmo.dashboard.visualize(
            logbook_with_repopulation, pop_with_repopulation,
            execution_num=i + 1
        )
        hash_df1 = pd.DataFrame(setupobj.tabela_hash, columns=['Fitness'])
        hash_df1.sort_values(by='Fitness', ascending=False, inplace=True)
        hash_df1.to_excel("hash_table.xlsx", index=False)
        print(f"Objective function runs : {setupobj.objectiveruns}")
        print(f"Hash table reads : {setupobj.hashtablereads}")
        end = datetime.now()
        elapsed = end - start
        print(f"Elapsed Time: {format_elapsed_time(elapsed)}")
        execution_times.append(elapsed)
        results_consolidados.append({
            "execution": i + 1,
            "solution_variables": y,
            "best_fitness": z,
            "best_generations": x,
            "execution_time": elapsed
        })

def main():
    base_dir = Path(__file__).parent
    options = load_json(base_dir / "options.json")
    params = load_json(base_dir / "params.json")
    variaveis = get_param_variaveis(options)
    configs = gerar_combinacoes(options, variaveis)
    configs_ll = configs_linked_list(configs)
    print(f"{len(configs_ll)} configs geradas.")
    # Salva configs em arquivo para referência
    configs_dict = {k: v for k, v in configs_ll}
    with open(base_dir / "config_teste.json", "w", encoding="utf-8") as f:
        json.dump(configs_dict, f, indent=4, ensure_ascii=False)
    print(f"{len(configs_dict)} configs salvas em config_teste.json")
    # Executa as configurações
    run_framework_groups_executions(configs_ll)

if __name__ == "__main__":
    main()