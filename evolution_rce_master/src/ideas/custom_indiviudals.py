import random
from deap import base, creator, tools
from typing import List, Callable, Optional
import numpy as np


class CustomIndividual(list):
    def __init__(
        self,
        tipo: str,
        quantidade_var_decision: int,
        limite_var: List[Optional[float]],
        *args
    ):
        super().__init__(*args)
        self.tipo = tipo
        self.quantidade_var_decision = quantidade_var_decision
        self.limite_var = limite_var
        self.index = None
        self.rce = None


# Função de avaliação para o problema de otimização Rastrigin
def rastrigin_fitness(individual: CustomIndividual) -> float:
    rastrigin = 10 * len(individual)
    for i in range(len(individual)):
        rastrigin += individual[i] ** 2 - 10 * (np.cos(2 * np.pi * individual[i]))
    return (rastrigin,)


# Exemplo de configuração do DEAP
def configure_deap(
    tipo: str,
    quantidade_var_decision: int,
    limite_var: List[Optional[float]],
):
    creator.create("Fitness", base.Fitness, weights=(-1.0,))
    creator.create(
        "Individual", CustomIndividual, fitness=creator.Fitness, rce=str, index=int
    )

    toolbox = base.Toolbox()

    # Registro de função para inicializar os atributos dos indivíduos
    if tipo == "int":
        toolbox.register("attribute", random.randint, limite_var[0], limite_var[1])
    elif tipo == "float":
        toolbox.register("attribute", random.uniform, limite_var[0], limite_var[1])
    elif tipo == "binario":
        toolbox.register("attribute", random.randint, 0, 1)
    else:
        raise ValueError("Tipo de variável inválido")

    # Registro da função de avaliação (fitness)
    toolbox.register("evaluate", rastrigin_fitness)

    # Função para criar um indivíduo com atributos personalizados
    def create_individual(
        tipo: str, quantidade_var_decision: int, limite_var: List[Optional[float]]
    ):
        individual = creator.Individual(
            tipo,
            quantidade_var_decision,
            limite_var,
            [toolbox.attribute() for _ in range(quantidade_var_decision)],
        )
        individual.tipo = tipo
        individual.quantidade_var_decision = quantidade_var_decision
        individual.limite_var = limite_var
        return individual

    # Registro da função de criação de indivíduos
    toolbox.register(
        "individual", create_individual, tipo, quantidade_var_decision, limite_var
    )
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    return toolbox


# Exemplo de uso
tipo = "int"  # Pode ser "int", "float" ou "binario"
quantidade_var_decision = 5
limite_var = [1.0, 10]

my_toolbox = configure_deap(
    tipo,
    quantidade_var_decision,
    limite_var,
)

# Criação de um indivíduo
ind = my_toolbox.individual()
print("Indivíduo:", ind)
print("Tipo:", ind.tipo)
print("Quantidade de Variáveis de Decisão:", ind.quantidade_var_decision)
print("Limites Variáveis:", ind.limite_var)
print("Índice:", ind.index)  # Pode ser None
print("RCE:", ind.rce)  # Pode ser None

# Avaliação do indivíduo usando a função Rastrigin
fitness = my_toolbox.evaluate(ind)
print("Fitness do Indivíduo:", fitness[0])


newPop = my_toolbox.population(n=10)
print("\nPopulaçao gerada\n", newPop)
