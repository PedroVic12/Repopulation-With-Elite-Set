# cython: language_level=3
# distutils: language=c++
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

import numpy as np
cimport numpy as np
from libcpp.vector cimport vector
from libcpp.pair cimport pair
from libcpp.unordered_map cimport unordered_map
from libcpp.algorithm cimport sort, min_element, max_element
from libcpp.math cimport sqrt, pow, exp, log
from cython.operator cimport dereference as deref
from cpython cimport array

# Tipos de dados
ctypedef np.float64_t DTYPE_t
ctypedef vector[DTYPE_t] vec_t
ctypedef vector[vec_t] matrix_t
ctypedef pair[DTYPE_t, int] fitness_pair_t

cdef class FastGeneticAlgorithm:
    """Algoritmo Genético Otimizado em C++"""
    
    cdef:
        int population_size
        int chromosome_length
        double mutation_rate
        double crossover_rate
        matrix_t population
        vec_t fitness_values
        vec_t best_fitness_history
        int current_generation
        
    def __init__(self, int pop_size, int chrom_length, double mutation_rate, double crossover_rate):
        self.population_size = pop_size
        self.chromosome_length = chrom_length
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.current_generation = 0
        
        # Inicializa população
        self._initialize_population()
    
    cdef void _initialize_population(self):
        """Inicializa população com valores aleatórios"""
        cdef int i, j
        cdef vec_t individual
        
        self.population.clear()
        self.fitness_values.resize(self.population_size)
        
        for i in range(self.population_size):
            individual.clear()
            for j in range(self.chromosome_length):
                individual.push_back(np.random.uniform(0.0, 1.0))
            self.population.push_back(individual)
    
    def evaluate_fitness(self, object fitness_function):
        """Avalia fitness de toda a população"""
        cdef int i
        cdef vec_t individual
        
        for i in range(self.population_size):
            individual = self.population[i]
            # Converte para numpy array para compatibilidade
            np_individual = np.array(individual, dtype=np.float64)
            self.fitness_values[i] = fitness_function(np_individual)
    
    def selection(self):
        """Seleção por torneio"""
        cdef int i, j, tournament_size = 3
        cdef int winner, competitor
        cdef matrix_t new_population
        cdef vec_t selected_individual
        
        new_population.clear()
        
        for i in range(self.population_size):
            # Torneio
            winner = np.random.randint(0, self.population_size)
            for j in range(1, tournament_size):
                competitor = np.random.randint(0, self.population_size)
                if self.fitness_values[competitor] < self.fitness_values[winner]:
                    winner = competitor
            
            selected_individual = self.population[winner]
            new_population.push_back(selected_individual)
        
        self.population = new_population
    
    def crossover(self):
        """Crossover uniforme"""
        cdef int i, j
        cdef double rand_val
        cdef vec_t parent1, parent2, child1, child2
        
        for i in range(0, self.population_size - 1, 2):
            if np.random.random() < self.crossover_rate:
                parent1 = self.population[i]
                parent2 = self.population[i + 1]
                
                child1.clear()
                child2.clear()
                
                for j in range(self.chromosome_length):
                    rand_val = np.random.random()
                    if rand_val < 0.5:
                        child1.push_back(parent1[j])
                        child2.push_back(parent2[j])
                    else:
                        child1.push_back(parent2[j])
                        child2.push_back(parent1[j])
                
                self.population[i] = child1
                self.population[i + 1] = child2
    
    def mutation(self):
        """Mutação gaussiana"""
        cdef int i, j
        cdef double mutation_value
        
        for i in range(self.population_size):
            for j in range(self.chromosome_length):
                if np.random.random() < self.mutation_rate:
                    mutation_value = np.random.normal(0.0, 0.1)
                    self.population[i][j] += mutation_value
                    # Mantém valores entre 0 e 1
                    if self.population[i][j] < 0.0:
                        self.population[i][j] = 0.0
                    elif self.population[i][j] > 1.0:
                        self.population[i][j] = 1.0
    
    def get_best_individual(self):
        """Retorna o melhor indivíduo"""
        cdef int best_idx = 0
        cdef double best_fitness = self.fitness_values[0]
        cdef int i
        
        for i in range(1, self.population_size):
            if self.fitness_values[i] < best_fitness:
                best_fitness = self.fitness_values[i]
                best_idx = i
        
        return np.array(self.population[best_idx], dtype=np.float64), best_fitness
    
    def evolve(self, object fitness_function, int generations):
        """Evolui a população por várias gerações"""
        cdef int gen
        cdef double best_fitness
        
        self.best_fitness_history.clear()
        
        for gen in range(generations):
            self.evaluate_fitness(fitness_function)
            best_individual, best_fitness = self.get_best_individual()
            self.best_fitness_history.push_back(best_fitness)
            
            self.selection()
            self.crossover()
            self.mutation()
            
            self.current_generation += 1
        
        return np.array(self.best_fitness_history, dtype=np.float64)
    
    def get_population(self):
        """Retorna população atual como numpy array"""
        cdef int i
        cdef np.ndarray[DTYPE_t, ndim=2] pop_array
        
        pop_array = np.zeros((self.population_size, self.chromosome_length), dtype=np.float64)
        
        for i in range(self.population_size):
            for j in range(self.chromosome_length):
                pop_array[i, j] = self.population[i][j]
        
        return pop_array

cdef class FastRCEOptimizer:
    """Otimizador RCE em C++"""
    
    cdef:
        int elite_size
        double repopulation_rate
        int repopulation_generations
        FastGeneticAlgorithm ga
        matrix_t elite_population
        vec_t elite_fitness
    
    def __init__(self, int pop_size, int chrom_length, double mutation_rate, 
                 double crossover_rate, int elite_size, double repopulation_rate, 
                 int repopulation_generations):
        self.elite_size = elite_size
        self.repopulation_rate = repopulation_rate
        self.repopulation_generations = repopulation_generations
        
        self.ga = FastGeneticAlgorithm(pop_size, chrom_length, mutation_rate, crossover_rate)
        self.elite_population.clear()
        self.elite_fitness.clear()
    
    def update_elite_population(self):
        """Atualiza população de elite"""
        cdef int i, j
        cdef np.ndarray[DTYPE_t, ndim=2] current_pop
        cdef vec_t fitness_values
        cdef vector[pair[double, int]] fitness_indices
        
        current_pop = self.ga.get_population()
        fitness_values = self.ga.fitness_values
        
        # Cria pares (fitness, índice)
        fitness_indices.clear()
        for i in range(len(fitness_values)):
            fitness_indices.push_back(pair[double, int](fitness_values[i], i))
        
        # Ordena por fitness
        sort(fitness_indices.begin(), fitness_indices.end())
        
        # Atualiza elite
        self.elite_population.clear()
        self.elite_fitness.clear()
        
        for i in range(min(self.elite_size, len(fitness_indices))):
            j = fitness_indices[i].second
            self.elite_population.push_back(self.ga.population[j])
            self.elite_fitness.push_back(fitness_values[j])
    
    def repopulate_from_elite(self):
        """Repopula usando indivíduos de elite"""
        cdef int i, j, elite_idx
        cdef vec_t new_individual, elite_individual
        cdef double mutation_value
        
        # Seleciona indivíduos de elite para repopulação
        for i in range(self.ga.population_size):
            if np.random.random() < self.repopulation_rate:
                elite_idx = np.random.randint(0, len(self.elite_population))
                elite_individual = self.elite_population[elite_idx]
                
                new_individual.clear()
                for j in range(self.ga.chromosome_length):
                    mutation_value = np.random.normal(0.0, 0.05)
                    new_individual.push_back(elite_individual[j] + mutation_value)
                    
                    # Mantém valores entre 0 e 1
                    if new_individual[j] < 0.0:
                        new_individual[j] = 0.0
                    elif new_individual[j] > 1.0:
                        new_individual[j] = 1.0
                
                self.ga.population[i] = new_individual
    
    def run_rce_optimization(self, object fitness_function, int main_generations, int repopulation_cycles):
        """Executa otimização RCE completa"""
        cdef int cycle
        cdef np.ndarray[DTYPE_t, ndim=1] main_history, repop_history
        cdef vector[double] all_history
        
        all_history.clear()
        
        for cycle in range(repopulation_cycles):
            # Fase principal do GA
            main_history = self.ga.evolve(fitness_function, main_generations)
            
            # Adiciona ao histórico
            for i in range(len(main_history)):
                all_history.push_back(main_history[i])
            
            # Atualiza elite
            self.update_elite_population()
            
            # Repopulação
            self.repopulate_from_elite()
            
            # Fase de repopulação
            repop_history = self.ga.evolve(fitness_function, self.repopulation_generations)
            
            # Adiciona ao histórico
            for i in range(len(repop_history)):
                all_history.push_back(repop_history[i])
        
        return np.array(all_history, dtype=np.float64)
    
    def get_best_solution(self):
        """Retorna a melhor solução encontrada"""
        return self.ga.get_best_individual()

# Funções de benchmark otimizadas
def fast_rastrigin(np.ndarray[DTYPE_t, ndim=1] x):
    """Função Rastrigin otimizada"""
    cdef int n = len(x)
    cdef double result = 10.0 * n
    cdef int i
    cdef double xi
    
    for i in range(n):
        xi = x[i]
        result += xi * xi - 10.0 * cos(2.0 * M_PI * xi)
    
    return result

def fast_sphere(np.ndarray[DTYPE_t, ndim=1] x):
    """Função Sphere otimizada"""
    cdef double result = 0.0
    cdef int i
    
    for i in range(len(x)):
        result += x[i] * x[i]
    
    return result

def fast_rosenbrock(np.ndarray[DTYPE_t, ndim=1] x):
    """Função Rosenbrock otimizada"""
    cdef double result = 0.0
    cdef int i
    cdef double xi, xi_plus_1
    
    for i in range(len(x) - 1):
        xi = x[i]
        xi_plus_1 = x[i + 1]
        result += 100.0 * pow(xi_plus_1 - xi * xi, 2) + pow(xi - 1.0, 2)
    
    return result 