
import numpy as np
import math
from deap import base, creator, tools
import random
import pandas as pd


#! WARN (04/06/2025) - Usado fora da classes para NAO ter logs no output

# Criando os individuos e uma função e minimização
#creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
#creator.create("Individual", list, fitness=creator.FitnessMin, rce=str, index=int)


#! O ideal seria importar o arquivo de configuração do projeto de forma global para o App em Streamlit também, mas como o arquivo de configuração está em outro diretório,
#from ..config import FOLDER_NAME, configuracoes_execucoes

array_decisions =  [14,15,14,18,15]

params = {
    "ARRAY_VAR": array_decisions,
    'LIMITE_VAR': [0, 31],

    'NUM_GENERATIONS': 100,
    'CROSSOVER': 0.9,
    'MUTACAO': 0.15,

    'POP_SIZE': 100,
    'IND_SIZE': 5,

    'RCE_REPOPULATION_GENERATIONS': 10,
    'NUM_VAR_DIFERENTES': 1,
    'PORCENTAGEM': 0.2,
    'DELTA_MIN': 2
  }


configuracoes_execucoes = {
        "key": True,
        "value": 5,
        "parametros_opcionais": [
             {"MUTACAO": [90,80,70, 60]},
             {"CROSSOVER": [90,80,70, 60]},
             {'NUM_GENERATIONS': [25, 50, 100, 500]},
             {'POP_SIZE': [10, 30, 50, 100]},

        ]
}



 
class Setup:
    def __init__(self, params, fitness_function, tamanho_hash = 0 ):

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
        self.config = configuracoes_execucoes


        # Criterios Rainer DEAP
        self.NUM_VAR_DIF = params["NUM_VAR_DIFERENTES"]
        self.porcentagem = params["PORCENTAGEM"]
        self.delta = params["DELTA_MIN"]

        #!Criando individuo pelo deap com seus atributos
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        self.toolbox = base.Toolbox()

        #! Parâmetros do algoritmo de Rastrigin
        self.evaluations = 0
        self.num_repopulation = int(self.NUM_GENERATIONS * (self.TAXA_GENERATION/100))

        # dict para acumular
        self.dataset = {}



        #----------------------------------------------------------------------------------------
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

        #! registrando os individuos
        self.toolbox.register("individual", tools.initRepeat, creator.Individual, self.toolbox.attribute, n=self.SIZE_INDIVIDUAL)

        #! criando e regsitrando a população de individuos (ja no type do deap)
        self.toolbox.register(
            "population", tools.initRepeat, creator.Individual, self.toolbox.individual
        )
        self.POPULATION = self.toolbox.population(n=self.POP_SIZE)

        #! paramentos evolutivos registrados
        self.toolbox.register("mate", tools.cxTwoPoint)
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

        # Teste para validar dados de entrada
        self.checkDecisionVariablesAndFitnessFunction(
            self.__fitness_function,
            self.POPULATION[0],
        )

        #! Inicializa a HashTable na instancia do Objeto Setup!
        if tamanho_hash > 0:
            self.tabela_hash = [-1] * tamanho_hash
        else:
            self.tabela_hash = None


    def avaliarFitnessIndividuos(self, pop):
        fitnesses = []  # To store fitness values for each individual
        for ind in pop:
            fitness = self.toolbox.evaluate(list(ind), self) # Assuming this calls funcao_objetivo_IEEE14
            ind.fitness.values = (fitness,)
            fitnesses.append(fitness)  # Add fitness value to the list
        return fitnesses
        #print("\nFitness individuos validados!!! ")


    def checkDecisionVariablesAndFitnessFunction(
        self, fitness_function, individual
    ):
            self.__fitness_function = fitness_function

            # Criando o esqueleto de uma funcao objetivo com uma variavel de decisao
            def fitness_func(individual,self):
                return (
                    self.funcao_objetivo(individual,self)
                    if self.funcao_objetivo
                    else self.rastrigin(individual)
                )

            #! Registrar a função de fitness no toolbox
            print("\n[DEBUG] Dados do problema = ", self.decision_variables, self.__fitness_function)
            self.toolbox.register("evaluate", fitness_func)



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


