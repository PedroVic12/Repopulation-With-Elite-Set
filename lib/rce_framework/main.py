# -*- coding: utf-8 -*-
import json
import itertools
import os
import pandas as pd
from pathlib import Path
from datetime import datetime

# Import RCE Framework
from components.setup import Setup
from components.alg_evolutivo import AlgoritimoEvolutivoRCE
from utils.functions_fitness.function_IEEE_14_contigencias import funcao_objetivo_IEEE14

# Variáveis globais
execution_times = []
results_consolidados = []
BASE_DIR = Path(__file__).resolve().parent.parent.parent # Goes up to the project root

def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def format_elapsed_time(elapsed_time):
    parts = str(elapsed_time).split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    formatted_time = ""
    if hours > 0:
        formatted_time += f"{hours} horas "
    if minutes > 0:
        formatted_time += f"{minutes} minutos "
    formatted_time += f"{int(round(seconds))} segundos"
    return formatted_time.strip()

def entrada_de_dados():
    agendamento_df = pd.DataFrame([
        {"ramo": [1, 4], "inicio": "14:00", "duracao": 6, "prioridade": 4},
        {"ramo": [1, 3], "inicio": "15:00", "duracao": 5, "prioridade": 1},
        {"ramo": [3, 6], "inicio": "14:00", "duracao": 6, "prioridade": 1},
        {"ramo": [11, 12], "inicio": "18:00", "duracao": 6, "prioridade": 1},
        {"ramo": [9, 10], "inicio": "15:00", "duracao": 4, "prioridade": 1}
    ])
    contingencia_df = pd.DataFrame([
        {"contingencia": 1, "from": 2, "to": 3},
        {"contingencia": 2, "from": 5, "to": 12},
        {"contingencia": 3, "from": 12, "to": 13},
    ])
    contingencias = contingencia_df['contingencia'].to_list()
    return {
        "contigencias": contingencias,
        "num_carregamentos": 3,
        "num_contingencias": len(contingencias),
        "num_desligamentos": len(agendamento_df),
        "horarios_agendamento": agendamento_df,
    }

def get_param_variaveis(options):
    return [k for k, v in options.items() if isinstance(v, list) and len(v) > 1]

def gerar_combinacoes(options, variaveis):
    valores = [options[var] for var in variaveis]
    return [
        {**options, **dict(zip(variaveis, comb))}
        for comb in itertools.product(*valores)
    ]

def flatten_config(config):
    ALWAYS_LIST = {"ARRAY_VAR", "LIMITE_VAR"}
    return {
        k: (v if k in ALWAYS_LIST else (v[0] if isinstance(v, list) and len(v) == 1 else v))
        for k, v in config.items()
    }

def merge_dicts(base, override):
    merged = base.copy()
    merged.update(override)
    return merged

def run_single_config(config_ag, repeticoes, config_name, idx):
    all_results = []
    for rep in range(repeticoes):
        print(f"Execução {rep+1}/{repeticoes} para {config_name}")
        start = datetime.now()
        dados = entrada_de_dados()
        
        setup = Setup(config_ag, fitness_function=lambda ind: funcao_objetivo_IEEE14(ind, setup),
                      tamanho_hash=(dados["num_contingencias"] * dados["num_carregamentos"] * (2 ** dados["num_desligamentos"])))
        
        if os.path.exists("hash_table.xlsx"):
            hash_excel = pd.read_excel("hash_table.xlsx")
            if not hash_excel.empty and not hash_excel.isnull().values.any():
                setup.tabela_hash = hash_excel['Fitness'].tolist()

        alg = AlgoritimoEvolutivoRCE(setup, DEBUG=False)
        pop, logbook, best_variables = alg.run(RCE=True)
        
        # Certifique-se que o diretório de output existe
        output_dir = BASE_DIR / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        x, y, z, fig = alg.dashboard.visualize(logbook, pop, execution_num=rep + 1, output_dir=output_dir)
        
        elapsed = datetime.now() - start
        print(f"Best variables: {best_variables}")
        print(f"Elapsed Time: {format_elapsed_time(elapsed)}")
        
        all_results.append({
            "config_exec_num": idx,
            "config_name": config_name,
            "config": config_ag.copy(),
            "execution": rep + 1,
            "solution_variables": y,
            "best_fitness": z,
            "best_generations": x,
            "execution_time": str(elapsed)
        })
    return all_results

def main():
    src_dir = BASE_DIR / "src"
    options = load_json(src_dir / "options.json")
    params_base = load_json(src_dir / "params.json")

    variaveis = get_param_variaveis(options)
    configs_list = gerar_combinacoes(options, variaveis)
    
    configs_dict = {f"config_{i+1}": flatten_config(merge_dicts(params_base, cfg)) for i, cfg in enumerate(configs_list)}
    
    print(f"Total de configs: {len(configs_dict)}\n\n")
    
    all_results = []
    for idx, (config_name, config) in enumerate(configs_dict.items(), 1):
        print(f"\n=== INICIANDO A EXECUÇÃO {config_name} ===")
        repeticoes = config.get("repeticoes_por_config", 1)
        results = run_single_config(config, repeticoes, config_name, idx)
        all_results.extend(results)

    df = pd.DataFrame(all_results)
    output_dir = BASE_DIR / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_dir / "resultados_execucoes.xlsx", index=False)
    print(f"\nResultados salvos em {output_dir / 'resultados_execucoes.xlsx'}")

if __name__ == "__main__":
    main()
