import numpy as np
import math
from deap import base, creator, tools
import random
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import json
import pandas as pd

def load_params(file_path):
    with open(file_path, "r") as file:
        params = json.load(file)
    return params

#params = load_params(     r"./parameters.json" )

array_decisions =  [14,15,14,18,15]

params = {
    "ARRAY_VAR": array_decisions,
    'LIMITE_VAR': [0, 31],

    'NUM_GENERATIONS': 100,
    'CROSSOVER': 0.9,
    'MUTACAO': 0.15,

    'POP_SIZE': 50,
    'IND_SIZE': 5,

    'RCE_REPOPULATION_GENERATIONS': 10,
    'NUM_VAR_DIFERENTES': 1,
    'PORCENTAGEM': 0.2,
    'DELTA_MIN': 2
  }



class Setup:
    def __init__(self, params,fitness_function ):

        #! Parametros JSON
        self.params = params
        self.CXPB = params["CROSSOVER"]
        self.MUTPB = params["MUTACAO"]
        self.NGEN = params["NUM_GENERATIONS"]

        # População de individuos com RCE
        self.POP_SIZE = params["POP_SIZE"]
        self.SIZE_INDIVIDUAL = params["IND_SIZE"]
        self.TAXA_GENERATION = params["RCE_REPOPULATION_GENERATIONS"]

        # Variaveis AG e AE
        self.CROSSOVER, self.MUTACAO, self.NUM_GENERATIONS, self.POPULATION_SIZE = (
            self.CXPB,
            self.MUTPB,
            self.NGEN,
            self.POP_SIZE,
        )

        #! Daodos de etrada do usuario nova
        self.limite = params["LIMITE_VAR"]
        self.decision_variables = params["ARRAY_VAR"]

        # Criterios Rainer DEAP
        self.NUM_VAR_DIF = params["NUM_VAR_DIFERENTES"]
        self.porcentagem = params["PORCENTAGEM"]
        self.delta = params["DELTA_MIN"]

        #!Criando individuo pelo deap com seus atributos
        self.toolbox = base.Toolbox()

        #! Parâmetros do algoritmo de Rastrigin
        self.evaluations = 0
        self.num_repopulation = int(self.NUM_GENERATIONS * (self.TAXA_GENERATION/100))

        # dict para acumular
        self.dataset = {}

        # Criando os individuos e uma função e minimização
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        #creator.create("Individual", list, fitness=creator.FitnessMin, rce=str, index=int                 )

        #----------------------------------------------------------------------------------------
        #! DEBUG HERE -> Verficiar as varaiveis de entrada com o type int ou float
        # --------------------------------------------------------------------------------------
        # Correção 03/04/25 - Usando as variaveis de decisao no JSON

        def checkBounds(min, max):
            def decorator(func):
                def wrapper(*args, **kargs):
                    offspring = func(*args, **kargs)
                    for child in offspring:
                        for i in range(len(child)):
                            if child[i] > max:
                                child[i] = max
                            elif child[i] < min:
                                child[i] = min

                            if type(self.decision_variables[i]) is int:
                                child[i] = int(child[i])

                            elif type(self.decision_variables[i]) is float:
                                child[i] = float(child[i])

                    return offspring
                return wrapper
            return decorator


        # No frontend em Streamlit eu quero um editor online do JSON
        if self.decision_variables is not None:
            for i in range(len(self.decision_variables)):

                if type(self.decision_variables[i]) is int:
                    #print("Verificando valores inteiros na variaveis de decisão")

                    creator.create("Individual", list, fitness=creator.FitnessMin,rce=str, index=int)

                    self.toolbox.register(
                        "attribute", random.randint, self.limite[0], self.limite[1]
                    )

                    #! Update 25/04
                    # Mutação para variáveis inteiras
                    self.toolbox.register("mutate", tools.mutUniformInt, low=self.limite[0], up=self.limite[1], indpb=1/len(self.decision_variables))
                    #self.toolbox.register("mutate", tools.mutShuffleIndexes, indpb=1/len(self.decision_variables))

                elif type(self.decision_variables[i]) is float:
                    #print("Verificando valores float na variaveis de decisão")

                    creator.create("Individual",list,fitness=creator.FitnessMin,rce=str, index=int)

                    self.toolbox.register(
                        "attribute", random.uniform, int(self.limite[0]), int(self.limite[1])
                    )

                    # Mutação para variáveis float (mantém mutGaussian)
                    self.toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.1)


        else:
            raise ValueError("No arquivo JSON as variáveis de decisão não pode ser vazia.")

        # Define os tipos de variáveis de decisão (METOOD ANTIGO)
        #self.toolbox.register("attr_float", random.uniform, self.limite[0], self.limite[1])  # x: float entre -5.12 e 5.12
        #self.toolbox.register("attr_float", random.uniform, 0.0, 31.0)
        #self.toolbox.register("attr_int", random.randint, int(self.limite[0]), int(self.limite[1]))      # entre 0 ate 31 na funcao objeitvo

        #! registrando os individuos
        #self.toolbox.register("individual", creator.Individual, self.decision_variables, self.toolbox.attribute)
        self.toolbox.register("individual", tools.initRepeat, creator.Individual, self.toolbox.attribute, n=self.SIZE_INDIVIDUAL)

        #! criando e regsitrando a população de individuos (ja no type do deap)
        self.toolbox.register(
            "population", tools.initRepeat, creator.Individual, self.toolbox.individual
        )
        self.POPULATION = self.toolbox.population(n=self.POP_SIZE)

        #! paramentos evolutivos registrados
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.1)
        self.toolbox.register("select", tools.selTournament, tournsize=3)

        # decorator
        self.toolbox.decorate("mate", checkBounds(self.limite[0], self.limite[1]))
        self.toolbox.decorate("mutate", checkBounds(self.limite[0], self.limite[1]))



        # Store the original fitness function
        self.funcao_objetivo = fitness_function

        # Use the original function if provided, otherwise use rastrigin
        self.__fitness_function = fitness_function if fitness_function is not None else self.rastrigin

        #! Register the fitness function using a lambda function, directly referencing the stored function
        self.toolbox.register("evaluate", self.funcao_objetivo if self.funcao_objetivo else self.rastrigin)
        #self.toolbox.register("evaluate", fitness_func)

        # Teste para validar dados de entrada
        self.checkDecisionVariablesAndFitnessFunction(
            self.__fitness_function,
            self.POPULATION[0],
        )



    def avaliarFitnessIndividuos(self, pop):
        fitnesses = []  # To store fitness values for each individual
        for ind in pop:
            fitness = self.toolbox.evaluate(list(ind)) # Assuming this calls funcao_objetivo_IEEE14
            ind.fitness.values = [fitness]
            fitnesses.append(fitness)  # Add fitness value to the list
        return fitnesses

        #print("\nFitness individuos validados!!! ")




    def checkDecisionVariablesAndFitnessFunction(
        self, fitness_function, individual
    ):
            self.__fitness_function = fitness_function

            # Criando o esqueleto de uma funcao objetivo com uma variavel de decisao
            def fitness_func(individual):
                return (
                    self.funcao_objetivo(individual)
                    if self.funcao_objetivo
                    else self.rastrigin(individual)
                )

            #! Registrar a função de fitness no toolbox
            print("\n[DEBUG] Dados do problema = ", self.decision_variables, self.__fitness_function)
            self.toolbox.register("evaluate", fitness_func)

            #self.toolbox.register("evaluate", self.__fitness_function)



    def gerarDataset(self, excel):
        df = pd.read_excel(excel)
        print(df.columns)
        self.dataset = {
            "CXPB": self.CROSSOVER,
            "TAXA_MUTACAO": self.MUTACAO,
            "NUM_GEN": self.NUM_GENERATIONS,
            "POP_SIZE": self.POPULATION_SIZE,
            "IND_SIZE": self.SIZE_INDIVIDUAL,
            "evaluations": self.evaluations,
            "NUM_REPOPULATION": self.num_repopulation,
        }

    def rastrigin(self, individual):
        self.evaluations += 1
        rastrigin = 10 * self.SIZE_INDIVIDUAL

        for i in range(self.SIZE_INDIVIDUAL):
            rastrigin += individual[i] * individual[i] - 10 * (
                math.cos(2 * np.pi * individual[i])
            )
        return rastrigin

    def rastrigin_decisionVariables(self, individual ):
        self.evaluations += 1
        rastrigin = 10 * len(individual)

        for i in range(len(individual)):
            rastrigin += individual[i] * individual[i] - 10 * (
                math.cos(2 * np.pi * individual[i])
            )
        return rastrigin

    def rosenbrock(self, x):

        var = np.array(x)

        return np.sum(100 * (var[1:] - var[:-1] ** 2) ** 2 + (1 - var[:-1]) ** 2)

