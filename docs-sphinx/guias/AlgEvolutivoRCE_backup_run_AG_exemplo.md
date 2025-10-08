# run_AG_exemplo.py

```python
# Imports principais do framework
from AlgEvolutivoRCE_backup.Setup import Setup, params, load_params
from AlgEvolutivoRCE_backup.alg_evolutivo_rce import AlgoritimoEvolutivoRCE


#! Importando a minha função objetivo dentro do projeto
from utils.functions_fitness.function_IEEE_14_contigencias import funcao_objetivo_IEEE14, get_hash_table_size, consultaHashTable


# Variáveis de configuração
config_num = 1
params_base = load_params(f"params.json")
options = load_params(f"options.json")
repeticoes = options.get('repeticoes_por_config', 1)

print(f"\n\nIniciando configuração {config_num} com os params.json:\n{params}\n")


# Instancia do Setup com a função objetivo
setup = Setup(
    params,
    fitness_function=funcao_objetivo_IEEE14,
    tamanho_hash=get_hash_table_size()
)
print("Classe Setup iniciada para a configuração.")


consultaHashTable()


# Loop de repetições com uma configuração Única
for exec_num in range(1, repeticoes + 1):
    print(f"\n--- Iniciando execução {exec_num}/{repeticoes} ---")

    alg = AlgoritimoEvolutivoRCE(setup, DEBUG=False)
    print("Algoritmo Evolutivo iniciado.")

    pop_with_repopulation, logbook_with_repopulation, best_individual, _ = alg.run(RCE=True)

    print("\nEvolução concluída  - 100%")

    best_solution_generation, best_solution_variables, best_solution_fitness, grafico_RCE = alg.dashboard.visualize(
        logbook_with_repopulation,
        pop_with_repopulation,
        config_num=config_num,
        execution_num=exec_num,
    )
    
    print(f"Objective functions runs: {setup.objectiveruns}")
    print(f"Consultas HashTable: {setup.hashtablereads}\n")
    
    print(f"\nMelhores horários de agendamento (melhor indivíduo):")
    print(best_solution_variables)
    print(f"Na melhor geração encontrada = {best_solution_generation} de {setup.params['NUM_GENERATIONS']} ")
    print("="*80)
```