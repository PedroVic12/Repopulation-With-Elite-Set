from Setup import Setup, params
from alg_evolutivo_rce import AlgoritimoEvolutivoRCE
from Dashboard import DashboardApp


import math
import numpy as np

if __name__ == "__main__":
    
    # Instanciando os Objetos
    setup = Setup(params)
    alg = AlgoritimoEvolutivoRCE(setup,DEBUG= False)
    dashboard = DashboardApp()


    # Variaveis de decisao e função objetivo
    #! Por padrao do JSON ta criando um individuo de tamanho 5
    X = [5.0, 4.0, 3.0, 2.0, 1.0]
    Y = [1, 2]

    def func_aptidao(ind):
        return ind[0]**2 + ind[1]**2
    
    def rastrigin_decisionVariables( individual ):
            rastrigin = 10 * len(individual)

            for i in range(len(individual)):
                rastrigin += individual[i] * individual[i] - 10 * (
                    math.cos(2 * np.pi * individual[i])
                )
            return rastrigin

    def rosenbrock( x):

        var = np.array(x)

        return np.sum(100 * (var[1:] - var[:-1] ** 2) ** 2 + (1 - var[:-1]) ** 2)
    

    # Loop Algoritmo Evolutivo podendo receber a função objetivo e as variaveis do problema
    pop_with_repopulation, logbook_with_repopulation, best_variables = alg.run(
        RCE=True,
        fitness_function=rastrigin_decisionVariables,
        decision_variables=(X),
    )

    print("\n\nEvolução concluída  - 100%")

    #! Resultados  - Terminal normal
    #generation, best_solution_variables, fitness_result = dashboard.visualize(
    #    logbook_with_repopulation, pop_with_repopulation,
    #)

    #! Resultados - Dashboard
        # Validar os resultados
    if logbook_with_repopulation and pop_with_repopulation and best_variables:
        best_fitness = min(logbook_with_repopulation.select("min"))
        
        #print("best_fitness", best_fitness)
        #print("best_variables", best_variables)
        #print("pop_with_repopulation", pop_with_repopulation)
        #print("logbook_with_repopulation", logbook_with_repopulation)

        dashboard.run(
            logbook=logbook_with_repopulation,
            pop=pop_with_repopulation,
            
        )

        print("Dashboard gerado com sucesso.")
    else:
        print("Erro: Dados do algoritmo evolutivo estão incompletos.")

