import json
import itertools
from pathlib import Path
from typing import List, Dict, Any
import streamlit as st
import pandas as pd
import os
from .AlgEvolutivoRCE.alg_evolutivo_rce import AlgoritimoEvolutivoRCE
from .AlgEvolutivoRCE.Setup import Setup
from .utils.functions_fitness.function_IEEE_14_contigencias import funcao_objetivo_IEEE14





# --- 1. SchemaModel (opcional, só para clareza) ---
class SchemaModel:
    def __init__(self, base: dict, variaveis: List[str]):
        self.base = base
        self.variaveis = variaveis

    def gerar_combinacoes(self) -> List[Dict[str, Any]]:
        valores = [self.base[var] for var in self.variaveis]
        combinacoes = list(itertools.product(*valores))
        configs = []
        for idx, valores_comb in enumerate(combinacoes, 1):
            config = self.base.copy()
            for i, var in enumerate(self.variaveis):
                config[var] = valores_comb[i]
            configs.append(config)
        return configs

import itertools

def export_all_configs_to_json(parametros):
    # parametros: dict com os 4 parâmetros, cada um sendo uma lista de valores possíveis
    keys = list(parametros.keys())
    values = [parametros[k] if isinstance(parametros[k], list) else [parametros[k]] for k in keys]
    configs = {}
    for idx, combination in enumerate(itertools.product(*values), 1):
        config_dict = dict(zip(keys, combination))
        configs[f"config {idx}"] = config_dict
    # Salva no arquivo
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(configs, f, indent=4, ensure_ascii=False)
    st.success(f"{len(configs)} configurações exportadas para config.json!")

def convert_values_to_int(params):
    """Converte os valores de um dicionário para int, exceto para as chaves especificadas."""
    float_keys = {"MUTACAO", "CROSSOVER", "PORCENTAGEM"}
    for key, value in params.items():
        if key.upper() in float_keys:
            #print(key,value)
            params[key] = float(value)
        elif isinstance(value, list):
            print(f"Valor da chave {key} é uma lista, não será convertido para int.")
        else:
            params[key] = int(value)
    return params


# --- 2. Lê os arquivos JSON ---
def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

BASE_DIR = Path(__file__).parent
#BASE_DIR = BASE_DIR / "src" / "DashboardApp" / "views" / 
print(BASE_DIR) 

options = load_json(BASE_DIR / "options.json")
params = load_json(BASE_DIR / "params.json")

# --- 3. Defina os parâmetros variáveis (os que são listas) ---
# Você pode mudar aqui conforme o que está variando no seu app!
parametros_variaveis = []
for k, v in options.items():
    if isinstance(v, list) and len(v) > 1:
        parametros_variaveis.append(k)

# Exemplo fixo (se quiser forçar):
# parametros_variaveis = ["CROSSOVER", "MUTACAO", "POP_SIZE", "NUM_GENERATIONS"]

# --- 4. Crie o SchemaModel e gere as combinações ---
schema = SchemaModel(options, parametros_variaveis)
execucoes = schema.gerar_combinacoes()

# --- 5. Salve o array de dicionários em um novo JSON ---
with open(BASE_DIR / "execucoes_configs.json", "w", encoding="utf-8") as f:
    json.dump(execucoes, f, indent=4, ensure_ascii=False)

print(f"Geradas {len(execucoes)} combinações e salvas em execucoes_configs.json")

# --- 6. (Opcional) Como rodar cada execução no seu run_framework.py ---
# for config in execucoes:
#     # Passe config para o seu framework
#     # Exemplo:
#     # setup = Setup(config, ...)
#     # alg = AlgoritimoEvolutivoRCE(setup, ...)
#     print(config)




def run_framework_groups_executions():
    """Função para executar o framework com múltiplas execuções baseadas em grupos de parâmetros."""
    
    # Parâmetros que devem ser float/int
    float_params = {"MUTACAO", "CROSSOVER", "PORCENTAGEM"}
    int_params = {"NUM_GENERATIONS", "POP_SIZE"}
    
    # Carrega os parâmetros default do AG (params.json)
    params = load_params(f"{BASE_DIR}/params.json")
    config = load_params(f"{BASE_DIR}/options.json")
    
    # Convert values to int, except for specified float keys
    params = convert_values_to_int(params)
    #options = convert_values_to_int(options)

    # Defina os nomes dos parâmetros variáveis
    param_names = ["MUTACAO", "CROSSOVER", "NUM_GENERATIONS", "POP_SIZE"]
    param_values = [config[name] for name in param_names]

    # Gera todas as combinações possíveis dos parâmetros variáveis
    combinacoes = list(itertools.product(*param_values))
    repeticoes = config.get('repeticoes_por_config', 1)
    
    print(f"Combinação = {combinacoes} | Repetição = {repeticoes}")

    for idx, valores in enumerate(combinacoes):
        params_exec = params.copy()
        

        for rep in range(repeticoes):
            
            print(f"Execução da configuração: {idx} = {rep}")
            
            # Atualiza mensagem na tela do Streamlit
            print(f"\n\nIniciando execução com a combinação: {dict(zip(param_names, valores))}")
            print(f"Combinação de Configuração {idx+1}/{len(combinacoes)} - Execução {rep+1}/{repeticoes}")

            dados = entrada_de_dados()
            print(f"\n\nIniciando execução com os parâmetros: {config}")
            setup = Setup(params_exec, fitness_function=funcao_objetivo_IEEE14,
                          tamanho_hash=(dados["num_contingencias"] * dados["num_carregamentos"] * (2 ** dados["num_desligamentos"])))
            
            #TODO for loop para conjunto de configurações de parametros_opcionais
            def consulta_hashtable():
                #! TODO para melhor performace
                try:
                    # Ler xlsx no início da run_framework e verificar logo depois de instanciar o setup se o xlsx existe e caso exista, coloca o conteúdo do xlsx no setup.tabela_hash.
                    if os.path.exists(f"hash_table.xlsx"):
                        print("\n\nFazendo consulta para setup.tabela_hash")

                        hash_excel = pd.read_excel("hash_table.xlsx")

                        if not hash_excel.empty and not hash_excel.isnull().values.any():
                            print(hash_excel.head())

                            setup.tabela_hash = hash_excel['Fitness'].to_dict()
                            neg_one_count = list(setup.tabela_hash.values()).count(-1)

                            if -1 in setup.tabela_hash.values():
                                print("Cenários Default = ",len(setup.tabela_hash))
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
            consulta_hashtable()

            
            # Usando o algoritimo Genetico do DEAP
            alg = AlgoritimoEvolutivoRCE(setup, DEBUG = False)

            # Run the utility function to load many executions
            load_many_executions(config, setup, alg)
