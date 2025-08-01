
import math
import numpy as np
from RedeEletrica.rede_eletrica import RedeEletricaPandaPower
import pandas as pd





# funções Benchmakrin
def evaluate(individual):
	"""Função objetivo do problema """
	a = sum(individual)
	b = len(individual)
	return b / a


def rastrigin(individual ):
        rastrigin = 10 * len(individual)

        for i in range(len(individual)):
            rastrigin += individual[i] * individual[i] - 10 * (
                math.cos(2 * np.pi * individual[i])
            )
        return rastrigin

def rosenbrock_benchmark(individual):
    """Calcula o valor da função Rosenbrock para uma única variável."""
    fitness = 0  # Inicializa o valor da função objetivo
    num_vars = len(individual)  # Número de variáveis de decisão

    for i in range(num_vars - 1):  # Itera até a penúltima variável
        fitness += 100 * (individual[i + 1] - individual[i]**2)**2 + (1 - individual[i])**2

    return fitness

def esfera_benchmark(individual):
    fitness = 0  # Inicializa o valor da função objetivo
    num_vars = len(individual)  # Número de variáveis de decisão

    for i in range(num_vars):
        fitness += individual[i]**2  # Acessa cada variável de decisão usando indexação

    return fitness

