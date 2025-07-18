import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import os

# Importes do seu framework
from AlgEvolutivoRCE.Setup import Setup
from AlgEvolutivoRCE.alg_evolutivo_rce import AlgoritimoEvolutivoRCE
from config import entrada_de_dados, format_elapsed_time
from utils.functions_fitness.function_IEEE_14_contigencias import funcao_objetivo_IEEE14


"""
Lê o config.json e o params.json.
Mescla os dois para cada execução.
Mantém arrays importantes como listas e tratamento dos dados que estao variando
Executa o AG para cada configuração e repetição instanciando Setup e AlgoritimoEvolutivoRCE
Salva todo resultado de todas as execuções em Excel.
"""
# Parâmetros que DEVEM continuar como array/lista
ALWAYS_LIST = {"ARRAY_VAR", "LIMITE_VAR"}

def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def flatten_config(config):
    # Converte listas de tamanho 1 para escalares, exceto para os que devem ser listas
    return {
        k: (v if k in ALWAYS_LIST else (v[0] if isinstance(v, list) and len(v) == 1 else v))
        for k, v in config.items()
    }

def merge_dicts(base, override):
    # base: params.json, override: config do config.json
    merged = base.copy()
    merged.update(override)
    return merged

def run_all_configs(configs_dict, params_base):
    all_results = []
    for idx, (config_name, config) in enumerate(configs_dict.items(), 1):
        print(f"\n=== INICIANDO A EXECUÇÃO {config_name} ===")
        repeticoes = config.get("repeticoes_por_config", 1)
        # Mescla params.json (fixos) com config do config.json (variáveis e fixos)
        merged_config = merge_dicts(params_base, config)
        config_ag = flatten_config(merged_config)
        for rep in range(repeticoes):
            print(f"Execução {rep+1}/{repeticoes} para {config_name}")
            start = datetime.now()
            dados = entrada_de_dados()

            print("Iniciando as instâncias dos meus objetos")
            print(config_ag)

            setup = Setup(config_ag, fitness_function=funcao_objetivo_IEEE14,
                          tamanho_hash=(dados["num_contingencias"] * dados["num_carregamentos"] * (2 ** dados["num_desligamentos"])))
            if os.path.exists("hash_table.xlsx"):
                hash_excel = pd.read_excel("hash_table.xlsx")
                if not hash_excel.empty and not hash_excel.isnull().values.any():
                    setup.tabela_hash = hash_excel['Fitness'].tolist()
            alg = AlgoritimoEvolutivoRCE(setup, DEBUG=False)
            pop, logbook, best_variables = alg.run(RCE=True)
            x, y, z, fig = alg.dashboard.visualize(logbook, pop, execution_num=rep+1)
            elapsed = datetime.now() - start
            print(f"Best variables: {best_variables}")
            print(f"Elapsed Time: {format_elapsed_time(elapsed)}")
            all_results.append({
                "config_exec_num": idx,
                "config_name": config_name,
                "config": config_ag.copy(),
                "execution": rep+1,
                "solution_variables": y,
                "best_fitness": z,
                "best_generations": x,
                "execution_time": str(elapsed)
            })
    return all_results

def main():
    base_dir = Path(__file__).parent
    configs_dict = load_json(base_dir / "options.json")
    params_base = load_json(base_dir / "params.json")
    print("Configs:", configs_dict)
    print("--------------------------------")
    print("DEBUG HERE ACIMA\n\n")
    print("Params:", params_base)
    results = run_all_configs(configs_dict, params_base)
    df = pd.DataFrame(results)
    df.to_excel(base_dir / "resultados_execucoes.xlsx", index=False)
    print(f"\nResultados salvos em {base_dir / 'resultados_execucoes.xlsx'}")

if __name__ == "__main__":
    main()