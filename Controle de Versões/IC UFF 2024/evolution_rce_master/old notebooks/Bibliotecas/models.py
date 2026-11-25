import random
from faker import Faker
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

fake = Faker("pt_BR")


class Individual:
    def __init__(self, nome, idade, sexo, peso, altura):
        self.nome = nome
        self.idade = idade
        self.sexo = sexo
        self.peso = peso
        self.altura = altura
        self.QI = random.randint(20, 130)

        self.imc = self.calculate_imc()
        self.fitness = self.calculate_fitness()

    def calculate_imc(self):
        return round(self.peso / (self.altura**2), 2)

    # Example fitness function
    def calculate_fitness(self):
        # Define os pesos para cada critério
        peso_imc = 0.4  # 40% do fitness vem do IMC
        peso_idade = 0.2  # 20% do fitness vem da idade
        peso_qi = 0.4  # 40% do fitness vem do QI

        # Calcula o score do IMC (considera-se o IMC normal como mais saudável)
        imc_score = (24.9 - abs(self.calculate_imc() - 24.9)) / 24.9

        # Calcula o score da idade (considera-se 50 anos como pico de 'saúde')
        idade_score = max(0, 1 - abs(self.idade - 50) / 50)

        # Calcula o score do QI (considera-se 130 como QI máximo para pontuação máxima)
        qi_score = self.QI / 130

        # Calcula o fitness geral
        fitness_total = (
            imc_score * peso_imc + idade_score * peso_idade + qi_score * peso_qi
        )

        # Normaliza o fitness_total para estar no intervalo de 0 a 100
        fitness_normalizado = round(max(0, min(100, fitness_total * 100)), 1)

        return fitness_normalizado


class Population:
    def __init__(self, size):
        self.conjunto_elite = []
        self.used_names = set()
        self.individuals = [self.create_individual() for _ in range(size)]

    def create_individual(self):
        while True:
            sexo = random.choice(["M", "F"])
            if sexo == "M":
                nome = (
                    fake.unique.first_name_male() + " " + fake.unique.last_name_male()
                )
            else:
                nome = (
                    fake.unique.first_name_female()
                    + " "
                    + fake.unique.last_name_female()
                )
            if nome not in self.used_names:
                self.used_names.add(nome)
                break

        idade = fake.random_int(min=18, max=80)
        peso = fake.random_int(min=45, max=150)
        altura = round(random.uniform(1.20, 2.10), 2)

        return Individual(nome, idade, sexo, peso, altura)

    def get_elite_set(self):
        elite_set = []
        for ind in self.individuals:
            if (18.5 < ind.imc <= 25) and (ind.altura >= 1.75) and (ind.QI >= 120):
                elite_set.append(ind)
        return elite_set

    def getConjuntoElite(self):
        for ind in self.individuals:
            if (18.5 < ind.imc <= 25) and (ind.altura >= 1.75):
                self.conjunto_elite.append(ind)
                return ind

    def evaluate(self):
        for individual in self.individuals:
            individual.fitness = individual.calculate_fitness()
            individual.imc = individual.calculate_imc()

            # Critério de IMC
            if (individual.imc >= 18.5) and (individual.imc <= 25):
                #!print(f"Nome: {individual.nome}, imc = {individual.imc}, idade = {individual.idade}, data: {individual.peso}KG x {individual.altura}m ")
                self.conjunto_elite.append(individual)

    def selection(self):
        """Esta função é responsável por selecionar os indivíduos mais aptos da população para reprodução. Ao classificar os indivíduos com base em seu desempenho (fitness) e escolher os melhores, a seleção direciona o algoritmo para soluções de maior qualidade. A ideia é simular o processo natural em que os indivíduos mais adaptados ao ambiente têm maiores chances de sobreviver e se reproduzir."""
        # Simple selection: sort by fitness and take the top half
        self.individuals.sort(key=lambda x: x.fitness, reverse=True)
        self.individuals = self.individuals[: len(self.individuals) // 2]

    def crossover(self):
        """A função de cruzamento imita a reprodução sexual na natureza, onde dois indivíduos (pais) combinam partes de seus genomas para criar descendentes. Essa mistura de material genético pode produzir novos indivíduos com características únicas, potencialmente mais aptos que seus pais. Isso introduz diversidade genética na população, o que é crucial para explorar o espaço de solução em busca de ótimos globais."""
        new_generation = []
        for _ in range(len(self.individuals) // 2):
            parent1 = random.choice(self.individuals)
            parent2 = random.choice(self.individuals)
            child1 = Individual(
                parent1.nome,
                (parent1.idade + parent2.idade) // 2,
                parent1.sexo,
                parent1.peso,
                parent1.altura,
            )
            child2 = Individual(
                parent2.nome,
                (parent1.idade + parent2.idade) // 2,
                parent2.sexo,
                parent2.peso,
                parent2.altura,
            )
            new_generation.extend([child1, child2])
        self.individuals.extend(new_generation)

    def mutation(self):
        """A mutação introduz variações aleatórias nos genomas dos indivíduos. Isso simula as mutações aleatórias no DNA que ocorrem na natureza. O objetivo da mutação em algoritmos evolutivos é manter a diversidade genética na população, prevenindo a convergência prematura para ótimos locais. Alterações pequenas e aleatórias nos genes podem levar a descobertas de novas e melhores soluções."""
        # Simple mutation: randomly change the age
        for individual in self.individuals:
            if random.random() < 0.1:  # 10% chance to mutate
                individual.idade = fake.random_int(min=18, max=80)
                individual.fitness = individual.calculate_fitness()
