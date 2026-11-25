import numpy as np
import math
from deap import base, creator, tools
import random
import matplotlib.pyplot as plt

# GA parameters
CXPB, MUTPB, NGEN, POP_SIZE = 0.9, 0.05, 100, 100
IND_SIZE = 10  # number of decision variables

class AlgoritmoEvolutivo:
    def __init__(self):
        self.setup_deap()

    def setup_deap(self):
        # Create fitness and individual classes
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMin)

        # Register toolbox with necessary functions
        self.toolbox = base.Toolbox()
        self.toolbox.register("attribute", random.random)
        self.toolbox.register("individual", tools.initRepeat, creator.Individual, self.toolbox.attribute, n=IND_SIZE)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)

        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.1)
        self.toolbox.register("select", tools.selTournament, tournsize=3)
        self.toolbox.register("evaluate", self.evaluate)

    def evaluate(self, individual):
        rastrigin = 10 * IND_SIZE
        for i in range(IND_SIZE):
            rastrigin += (individual[i] * individual[i] - 10 * (math.cos(2 * np.pi * individual[i])))
        return rastrigin,

def criarIndividuo(toolbox):
    return toolbox.individual()

def avaliarIndividuo(toolbox, individual):
    return toolbox.evaluate(individual)

def selecionarInidividuo(toolbox, population, k):
    return toolbox.select(population, k=k)

def cruzamento(toolbox, parent1, parent2):
    child1, child2 = toolbox.mate(parent1, parent2)
    del child1.fitness.values
    del child2.fitness.values
    return child1, child2

def mutacao(toolbox, individual):
    mutated_ind = toolbox.mutate(individual)
    del mutated_ind.fitness.values
    return mutated_ind

def main():
    # Setup DEAP
    alg_evolution = AlgoritmoEvolutivo()

    # Store statistics of all generations
    stats = tools.Statistics(key=lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("std", np.std)
    stats.register("min", np.min)
    stats.register("max", np.max)
    logbook = tools.Logbook()

    # GA initial population
    pop = alg_evolution.toolbox.population(n=POP_SIZE)

    # Store best individual
    hof = tools.HallOfFame(1)
    hof.update(pop)

    # Generational loop until stop criteria
    for g in range(NGEN):
        # Select the next generation individuals
        offspring = selecionarInidividuo(alg_evolution.toolbox, pop, k=len(pop))
        # Clone the selected individuals
        offspring = [alg_evolution.toolbox.clone(ind) for ind in offspring]

        # Apply crossover and mutation on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < CXPB:
                child1, child2 = cruzamento(alg_evolution.toolbox, child1, child2)

        for mutant in offspring:
            if random.random() < MUTPB:
                mutant = mutacao(alg_evolution.toolbox, mutant)

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = map(avaliarIndividuo, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # The population is entirely replaced by the offspring
        pop[:] = offspring

        # Elitism - update best with new pop
        hof.update(pop)

        # Save each generation record in the logbook
        record = stats.compile(pop)
        logbook.record(gen=g, **record)

    # Read the logbook
    gen = logbook.select("gen")
    fit_avg = logbook.select("avg")
    fit_std = logbook.select("std")
    fit_min = logbook.select("min")
    fit_max = logbook.select("max")

    # Print best individual
    print("Best solution variables:")
    print(hof[0])

    # Print best fitness
    print("Best solution fitness:")
    print(hof[0].fitness)

    # Plot fitness over generations
    fig, ax1 = plt.subplots()
    line1 = ax1.plot(gen, fit_min, "*b-", label="Minimum Fitness")
    line2 = ax1.plot(gen, fit_avg, "+r-", label="Average Fitness")
    line3 = ax1.plot(gen, fit_max, "og-", label="Maximum Fitness")
    ax1.set_xlabel("Generation")
    ax1.set_ylabel("Fitness")
    lns = line1 + line2 + line3
    labs = [l.get_label() for l in lns]
    ax1.legend(lns, labs, loc="upper right")
    plt.show()

if __name__ == "__main__":
    main()
