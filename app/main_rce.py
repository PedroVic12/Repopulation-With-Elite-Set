import json
from src.models.AlgEvolution import AlgoritimoEvolutivoRCE
from src.models.Setup_rce import SetupRCE
from src.models.DataExploration import Dashboard
from pathlib import Path


def load_params(file_path):
    with open(file_path, "r") as file:
        params = json.load(file)
    return params


def main():
    # Setup
    params = {'type': 'rastrigin',
 'CROSSOVER': 0.6,
 'MUTACAO': 0.15,
 'NUM_GENERATIONS': 100,
 'POP_SIZE': 100,
 'IND_SIZE': 10,
 'funcao objetivo': 'rastrigin',
 'RCE_REPOPULATION_GENERATIONS': 20,
 'NUM_VAR_DIFERENTES': 1,
 'PORCENTAGEM': 30,
 'VALOR_LIMITE': 3}
    setup = SetupRCE(params)


    #! Exemplo de uso
    tipo = "float"  # Pode ser "int", "float" ou "binario"
    quantidade_var_decision = 5
    limite_var = [-5.12, 5.12]

    my_toolbox = setup.configure_deap(tipo, quantidade_var_decision, limite_var)

    newPop = my_toolbox.population(n=100)

    alg = AlgoritimoEvolutivoRCE(setup)

    data_visual = Dashboard()

    pop_with_repopulation, logbook_with_repopulation, best_variables = alg.run(
        RCE=True,
        #fitness_function=rastrigin_decisionVariables,
        #decision_variables=(X, y, data_hora, curva, vento),
    )

    print("\n\nEvolução concluída  - 100%")

    # Visualização dos resultados
    alg.cout("VISUALIZANDO OS RESULTADOS")
    data_visual.show_rastrigin_benchmark(logbook_with_repopulation, best_variables)
    data_visual.visualize(
        logbook_with_repopulation, pop_with_repopulation, repopulation=True
    )
    data_visual.statistics_per_generation_df(logbook_with_repopulation)


if __name__ == "__main__":
    main()