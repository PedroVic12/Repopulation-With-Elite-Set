
from pathlib import Path
import sys
import os

# Define o diretório raiz do projeto
PROJ_DIR = Path(__file__).resolve().parent.parent.parent

# Obtém o caminho absoluto para o arquivo de parâmetros
PARAMS_FILE = Path(PROJ_DIR, "params.json")
OPTIONS_FILE = Path(PROJ_DIR, "options.json")

# Adiciona o diretório raiz ao path para encontrar os módulos
PROJ_DIR_PATH = str(PROJ_DIR)

sys.path.append(PROJ_DIR_PATH)
#print(f"PROJ_DIR_PATH: {PROJ_DIR_PATH}")
#print(f"PARAMS_FILE: {PARAMS_FILE}")
#print(f"OPTIONS_FILE: {OPTIONS_FILE}")
DEFAULT_PARAMS_FILE = PARAMS_FILE


# Imports principais do framework
from AlgEvolutivoRCE.Setup import Setup, params, load_params
from AlgEvolutivoRCE.alg_evolutivo_rce import AlgoritimoEvolutivoRCE


#! Importando a minha função objetivo dentro do projeto
from utils.functions_fitness.function_IEEE_14_contigencias import (
    funcao_objetivo_IEEE14,
    hashtablesize,
    HASH_TABLE_PATH
)

def consultaHashTable():
    # Consulta hash_table se existir (sub rotina)
    if os.path.exists(HASH_TABLE_PATH):
        try:

            # Read from Excel, using the first column as the index (our hash key)
            hash_excel = pd.read_excel(
                HASH_TABLE_PATH, index_col=0
            )
            if not hash_excel.empty:

                # Update the list-based hash table from the loaded dictionary
                for key, value in hash_excel["Fitness"].items():

                    if isinstance(key, int) and key < len(setup.tabela_hash):
                        setup.tabela_hash[key] = value

                print(
                    f"Tabela hash carregada e atualizada com {len(hash_excel)} registros!"
                )
        except Exception as e:
            print(f"Erro ao carregar hash_table.xlsx: {e}")
    else:
        # If the file doesn't exist, create it from the initial hash table
        hash_df = pd.DataFrame(data=setup.tabela_hash, columns=["Fitness"])
        hash_df.to_excel(HASH_TABLE_PATH, index=False)
        print(
            f"Tabela hash INICIAL com {len(setup.tabela_hash)} posições não existia e foi criada! - PVRV"
        )



# Variáveis de configuração
config_num = 1
params_base = load_params(DEFAULT_PARAMS_FILE)
options = load_params(OPTIONS_FILE)
repeticoes = options.get("repeticoes_por_config", 1)

print(f"\n\nIniciando configuração {config_num} com os params.json:\n{params}\n")


# Instancia do Setup com a função objetivo
setup = Setup(
    params, fitness_function=funcao_objetivo_IEEE14, tamanho_hash=hashtablesize()
)
print("Classe Setup iniciada para a configuração.")


consultaHashTable()


# Loop de repetições com uma configuração Única
for exec_num in range(1, repeticoes + 1):
    print(f"\n--- Iniciando execução {exec_num}/{repeticoes} ---")

    alg = AlgoritimoEvolutivoRCE(setup, DEBUG=False)
    print("Algoritmo Evolutivo iniciado.")

    pop_with_repopulation, logbook_with_repopulation, best_individual, _ = alg.run(
        RCE=True
    )

    print("\nEvolução concluída  - 100%")

    (
        best_solution_generation,
        best_solution_variables,
        best_solution_fitness,
        grafico_RCE,
    ) = alg.dashboard.visualize(
        logbook_with_repopulation,
        pop_with_repopulation,
        config_num=config_num,
        execution_num=exec_num,
    )

    print(f"Objective functions runs: {setup.objectiveruns}")
    print(f"Consultas HashTable: {setup.hashtablereads}\n")

    print(f"\nMelhores horários de agendamento (melhor indivíduo):")
    print(best_solution_variables)
    print(
        f"Na melhor geração encontrada = {best_solution_generation} de {setup.params['NUM_GENERATIONS']} "
    )
    print("=" * 80)
