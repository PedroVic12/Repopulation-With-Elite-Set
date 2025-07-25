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
execution_times = []
results_consolidados = []

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
    return {f"config {i+1}": cfg for i, cfg in enumerate(configs)}

def consulta_hashtable(setup):
    try:
        if os.path.exists("hash_table.xlsx"):
            hash_excel = pd.read_excel("hash_table.xlsx")
            if not hash_excel.empty and not hash_excel.isnull().values.any():
                setup.tabela_hash = hash_excel['Fitness'].to_dict()
    except Exception as e:
        print(f"Erro ao ler o arquivo xlsx: {e}")

def tratamento_dados_json(config):
    # Para todos os parâmetros que são listas, pega só o valor da combinação (primeiro valor)
    for k, v in config.items():
        if isinstance(v, list) and len(v) == 1:
            config[k] = v[0]
    print("Configuração tratada:", config)
    
    
    #! codigo acima feito por IA e ta com versao estavel roando sme mostrar o tempo mas com concfig 2/10 com exec = 3
    
    #! cada config faz uma instancia no setup. ta certo isso?dar
    
    # Exemplo: sempre força POP_SIZE e NUM_GENERATIONS para int
    if isinstance(config.get("POP_SIZE"), list):
        config["POP_SIZE"] = int(config["POP_SIZE"][0])
    if isinstance(config.get("NUM_GENERATIONS"), list):
        config["NUM_GENERATIONS"] = int(config["NUM_GENERATIONS"][0])
        
    int_keys = ["CROSSOVER", "MUTACAO"]
    
    for key in int_keys:
        if key in config and isinstance(config[key], list) and len(config[key]) > 0:
            config[key] = config[key][0]
            
            
    print("iniciando as configuração pelo usuario =\n")
    print(config)


    #!tenho que pensar em um caso com lista de 4 crossover variando NA MESMA EXECUÇÃO
    #else:
    #    cross_dict = {f"crossover_{i}": val for i, val in enumerate(config["CROSSOVER"])}

def run_framework_groups_executions(configs):
    for idx, (config_name, config) in enumerate(configs.items()):
        print(f"Configuração {idx+1}/{len(configs)} - {config_name}")
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
        
        # aqrui preciso passar a varaivel contador de config para passar para salvar os graficos em html
        x, y, z, fig = algoritmo.dashboard.visualize(
            logbook_with_repopulation, pop_with_repopulation,
            execution_num=i + 1
        )
        hash_df1 = pd.DataFrame(setupobj.tabela_hash, columns=['Fitness'])
        hash_df1.sort_values(by='Fitness', ascending=False, inplace=True)
        hash_df1.to_excel("hash_table.xlsx", index=False)
        end = datetime.now()
        elapsed = end - start
        formatted_time = format_elapsed_time(elapsed)
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

    # --- Defina manualmente de onde cada parâmetro deve vir ---
    prioridade_param = {
        "ARRAY_VAR": "params",  # sempre do params.json
        "LIMITE_VAR": "params",
        "POP_SIZE": "params",  # sempre do options.json
        "NUM_GENERATIONS": "params",
        # ...adicione outros se quiser...
    }

    variaveis = get_param_variaveis(options)
    configs = gerar_combinacoes(options, variaveis)
    resultado = configs_dict(configs)

    # Atualiza cada config conforme prioridade_param
    for cfg in resultado.values():
        for param, origem in prioridade_param.items():
            if origem == "params" and param in params:
                cfg[param] = params[param]
            elif origem == "options" and param in options:
                cfg[param] = options[param]

    with open(base_dir / "config_teste.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=4, ensure_ascii=False)
    print(f"{len(resultado)} configs salvas em config_teste.json")

    run_framework_groups_executions(resultado)

if __name__ == "__main__":
    main()