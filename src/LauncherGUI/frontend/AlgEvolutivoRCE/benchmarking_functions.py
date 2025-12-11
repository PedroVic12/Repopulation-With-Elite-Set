"""
Standard benchmarking functions for genetic algorithms.
"""
import numpy as np
import math

def rastrigin(individual):
    """Rastrigin function for benchmarking.

    Args:
        individual (list or np.ndarray): An individual in the population.

    Returns:
        float: The fitness value.
    """
    return 10 * len(individual) + np.sum(
        [x**2 - 10 * np.cos(2 * np.pi * x) for x in individual]
    )


# funções Benchmarking
def evaluate(individual):
	"""Função objetivo do problema """
	a = sum(individual)
	b = len(individual)
	return b / a


def rastrigin(individual ):
    """Calcula o valor da função Rastrigin para uma única variável."""
    rastrigin = 10 * len(individual)

    for i in range(len(individual)):
        rastrigin += individual[i] * individual[i] - 10 * (
            math.cos(2 * np.pi * individual[i])
        )
    return rastrigin