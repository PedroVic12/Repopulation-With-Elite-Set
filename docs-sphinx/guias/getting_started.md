# getting_started.py

```python
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

    x,y,z, fig = dashboard.visualize(
        logbook_with_repopulation, pop_with_repopulation
    )

    # Print the best variables found
    print(f"Best variables: {best_variables}")
    # Print the best fitness value
    print(f"Best fitness: {z}")
    # Print the generations
    print(f"Best generations: {x}")

    fig.show()

    
    print("\n\nEvolução concluída  - 100%")

```