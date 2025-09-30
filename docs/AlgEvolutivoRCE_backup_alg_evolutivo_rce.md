# alg_evolutivo_rce.py

```python
import numpy as np
from deap import base, creator, tools
import random
import pandas as pd
import pathlib
from .Dashboard import DashboardApp



def get_folder_path():
    BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

    # Define o caminho relativo para a pasta "output" dentro do projeto
    FOLDER_NAME = BASE_DIR / "output"

    # Cria a pasta "output" se ela não existir
    FOLDER_NAME.mkdir(parents=True, exist_ok=True)
    return FOLDER_NAME

FOLDER_NAME = get_folder_path()

class AlgoritimoEvolutivoRCE:

    def __init__(self, setup, DEBUG = True):
        self.setup = setup
        self.dashboard = DashboardApp(
            options= self.setup.config
        )
        self.DEBUG = DEBUG
        
        self.stats = tools.Statistics(key=lambda ind: ind.fitness.values)
        self.stats.register("avg", np.mean)
        self.stats.register("std", np.std)
        self.stats.register("min", np.min)
        self.stats.register("max", np.max)

        self.logbook = tools.Logbook()
        self.hof = tools.HallOfFame(1)
        self.POPULATION = self.setup.toolbox.population(n=self.setup.POP_SIZE)
        self.hof.update(self.POPULATION)

        self.pop_RCE = []
        self.best_solutions_array = []
        self.best_individual_array = []
        self.allIndividualValuesArray = []
        self.data = {}
        self.repopulation_counter = 0
        self.allFitnessValues = {}
        self.validateCounter = 0
        self.CONJUNTO_ELITE_RCE = set()

        self.decision_variables = []
        self.fitness_function  = lambda x: 0

    def registrarDados(self, generation):
        try:
            # Calculate statistics across the entire population
            fitness_values = []
            for ind in self.POPULATION:
                if ind.fitness.valid and hasattr(ind.fitness, 'values') and ind.fitness.values:
                    try:
                        fitness_values.append(float(ind.fitness.values[0]))
                    except (ValueError, TypeError, IndexError) as e:
                        print(f"Warning: Could not get fitness value for individual {ind}: {e}")
            
            # Calculate statistics
            if not fitness_values:  # If no valid fitness values, use default values
                avg_fitness = float('inf')
                std_dev = 0.0
            else:
                avg_fitness = np.mean(fitness_values)
                std_dev = np.std(fitness_values) if len(fitness_values) > 1 else 0.0
            
            # Get the best individual from the Hall of Fame
            best_individual = self.hof[0] if len(self.hof) > 0 else None
            
            # Prepare the data dictionary
            self.data = {
                "Generations": generation + 1,
                "Variaveis de Decisão": best_individual if best_individual else "N/A",
                "Evaluations": getattr(self.setup, 'evaluations', 0),
                "Ind Valido": best_individual.fitness.valid if best_individual else False,
                "Best Fitness": float(best_individual.fitness.values[0]) if best_individual and best_individual.fitness.valid else float('inf'),
                "Media": float(avg_fitness),
                "Desvio Padrao": float(std_dev),
            }

            self.best_individual_array.append(self.data)
            self.visualizarPopAtual(generation, [avg_fitness, std_dev])
            
        except Exception as e:
            print(f"Error in registrarDados: {e}")
            import traceback
            traceback.print_exc()

    def checkClonesInPop(self, ind, new_pop):
        is_clone = False
        for other_ind in new_pop:
            if (
                ind == other_ind
                and sum(ind) == sum(other_ind)
                and ind.index != other_ind.index
            ):
                is_clone = True
                break
        return is_clone

    def criterios_RCE(self, population):
        self.CONJUNTO_ELITE_RCE.clear()
        self.pop_RCE = []

        def criterio1_reduzido(population):
            #! critério 1 e obtém os N melhores com 30% do valor do melhor fitness

            best_ind = self.elitismoSimples(population)[0]
            best_fitness = best_ind.fitness.values[0]
            max_difference = (1 + self.setup.porcentagem) * best_fitness
            if self.DEBUG:
                print(
                    f"Fitness ({self.setup.porcentagem * 100})% = {round(max_difference,3)}"
                )
            return max_difference, best_ind

        if self.DEBUG:
            self.cout(
                "Criterio 1 - Pegando o valor máximo de Fitness para selecionar individuos"
            )
        max_difference, best_ind = criterio1_reduzido(population)
        self.pop_RCE.append(best_ind)

        def calculaDiff(ind, lista):
            """Critério 2 - Subrotina para calcular a difenreça entre o ind selecionado e a população do RCE."""
            count = 0

            # calcula a diferença entre o ind selecionado e o pessoal do RCE
            for i in range(0, len(lista)):
                diff = abs(np.array(ind) - np.array(lista[i]))
                array = list(diff)

                # pegando quantos valores nao sao nulos  -> caso tenha valor limite
                if sum(array) > 0.0:
                    for value in array:
                        if value > self.setup.NUM_VAR_DIF:
                            count += 1

                    # se o contador for maior que delta
                    if count >= self.setup.delta:
                        # print("\nArray diferente")

                        # print(" diff", array)

                        # print("Var decision diferentes = ", count)
                        return True

                    else:
                        return False  # sem diversidade suficiente
                else:
                    return False  # clone: Variaveis iguais

        if self.DEBUG:
            self.cout(
                f"CRITÉRIO 2 - Comparar as variáveis de decisão de cada indivíduo e verificar se existem diferenças superiores a 'delta' = {self.setup.delta}."
            )

        for ind in population:
            # criterio 1
            if ind.fitness.values[0] <= max_difference:
                # criterio 2
                diferente = calculaDiff(ind, self.pop_RCE)  # delta como valor limite
                if diferente:
                    if ind not in self.pop_RCE:
                        self.pop_RCE.append(ind)
                        self.CONJUNTO_ELITE_RCE.add(tuple(ind))

        if self.DEBUG:
            if len(self.pop_RCE) == 1:
                print("Nenhum indivíduo atende aos critérios. :( ")

            print("\nTamanho Elite = ", len(self.pop_RCE))
            #print("Tamanho Elite = ", len(self.CONJUNTO_ELITE_RCE))

        return self.pop_RCE

    def aplicar_RCE(self, generation, current_population):

        #! a - Cria uma pop aleatória (eliminando a pop aleatória criada na execução anterior do RCE)
        new_pop = self.setup.toolbox.population(
            n=self.setup.POP_SIZE
        )  # retorna uma pop com lista de individuos de var de decisão

        # Avaliar o fitness da população atual
        #?self.setup.avaliarFitnessIndividuos(current_population)
        self.calculateFitnessGeneration(current_population)

        #! Critério 1 - Coloca o elite hof da pop anterior  no topo (0)
        pop = self.elitismoSimples(current_population)

        if self.DEBUG:
            print(
                f"Elitismo HOF Index[{pop[0].index}] {pop[0]} \n Fitness = {pop[0].fitness.values} | Diversidade = {sum(pop[0])}"
            )

        new_pop[0] = self.setup.toolbox.clone(pop[0]) # pop[0] é o melhor individuo HOF

        #! Critério 1 e 2 usando este array e vai colocando os indivíduos selecionados pelo critério 2 na pop aleatória (passo a)
        ind_diferentes_var = self.criterios_RCE(
            current_population,
        )

        # COLOCANDO ATRIBUTOS HOF na tabela
        for i, ind in enumerate(ind_diferentes_var, start=0):
            new_pop[0].rce = "HOF"
            if i > 0:
                new_pop[i] = self.setup.toolbox.clone(ind)
                new_pop[i].rce = "SIM"

        #! Criterio 3 retorna pop aleatória modificada (com hof + rce + Aleatorio)
        self.calculateFitnessGeneration(new_pop)
        conjunto_elite = self.generateInfoIndividual(new_pop, generation)

        if self.DEBUG:
            self.cout(f"CRITERIO 3 - População aleatória modificada [HOF,RCE,Aleatorio] ")
        return new_pop

    def elitismoSimples(self, pop):
        self.hof.update(pop)
        pop[0] = self.setup.toolbox.clone(self.hof[0])
        return pop


    def calculateFitnessGeneration(self, new_pop):
        for ind in new_pop:
            if not ind.fitness.valid:
                try:
                    # Call the evaluate function with just the individual
                    fitness = self.setup.toolbox.evaluate(ind)
                    
                    # Ensure we have a tuple of numbers
                    if isinstance(fitness, (int, float)):
                        fitness = (float(fitness),)
                    elif isinstance(fitness, (list, tuple)):
                        fitness = tuple(float(x) for x in fitness)
                    else:
                        fitness = (float(fitness),)
                        
                    # Assign the fitness value to the individual
                    ind.fitness.values = fitness
                except Exception as e:
                    print(f"Error evaluating individual in calculateFitnessGeneration: {e}")
                    # Assign a very bad fitness value to this individual
                    ind.fitness.values = (float('inf'),)

    # def _avaliarFitnessIndividuos(self, pop):
    #     """Avaliar o fitness dos indivíduos da população atual."""
    #     fitnesses = map(self.setup.toolbox.evaluate, pop)
    #     for ind, fit in zip(pop, fitnesses):
    #         if ind.fitness.values:
    #             ind.fitness.values = [fit]


    #! Main LOOP
    def run(self,  RCE=False, num_pop=0):

        population = [self.POPULATION]

        #! Loop principal através das gerações
        for current_generation in range(self.setup.NGEN):

            if self.DEBUG:
                print(f"\nALGORITIMO EVOLUTIVO COM AG COM DEAP. Geração atual = {current_generation + 1}")


            # Selecionar os indivíduos para reprodução
            offspring = self.setup.toolbox.select(
                population[num_pop], k=len(population[num_pop])
            )

            # Clone the selected individuals
            offspring = [self.setup.toolbox.clone(ind) for ind in offspring]

            # Aplicar crossover
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < self.setup.CXPB:
                    self.setup.toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values

            # Aplicar mutação
            for mutant in offspring:
                if random.random() < self.setup.MUTPB:
                    self.setup.toolbox.mutate(mutant)
                    del mutant.fitness.values

            #  Avaliar o fitness dos novos indivíduos
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]

            #! Evaluate each individual separately
            for ind in invalid_ind:
                try:
                    # Call the evaluate function with just the individual
                    # The setup parameter is already bound in the evaluate_wrapper
                    fitness = self.setup.toolbox.evaluate(ind)
                    
                    # Ensure we have a tuple of numbers
                    if isinstance(fitness, (int, float)):
                        fitness = (float(fitness),)
                    elif isinstance(fitness, (list, tuple)):
                        fitness = tuple(float(x) for x in fitness)
                    else:
                        fitness = (float(fitness),)
                        
                    # Assign the fitness value to the individual
                    ind.fitness.values = fitness
                except Exception as e:
                    print(f"Error evaluating individual {ind}: {e}")
                    # Assign a very bad fitness value to this individual
                    ind.fitness.values = (float('inf'),)

            # # faz um map dos valores de fitness de cada individuo
            # fitnesses = map(self.setup.toolbox.evaluate, invalid_ind)
            # for ind, fit in zip(invalid_ind, list(fitnesses)):
            #     ind.fitness.values = [fit]


            #! Aplicar RCE
            if RCE and ((current_generation + 1) % self.setup.num_repopulation == 0):
                if self.DEBUG:
                    self.cout(
                        f"RCE being applied! - Generation = {current_generation + 1} ",
                    )
                #!copia pop aleatória modificada retornada para pop atual
                new_population = self.aplicar_RCE(
                    current_generation + 1, offspring
                )

                # Retorna minha nova população com RCE
                population[num_pop][:] = new_population

                # Gera o Excel com a pop com RCE em Excel
                conjunto_elite = self.generateInfoIndividual(population[num_pop][:], current_generation + 1)
                self.show_ind_df(conjunto_elite, "Individuos da nova população aleatória com RCE (Conjunto Elite)")

            else:
                population[num_pop][:] = offspring

            # Registrar estatísticas no logbook
            self.elitismoSimples(population[num_pop])
            self.registrarDados(current_generation)

            # Compila os resultados do deap
            record = self.stats.compile(population[num_pop])
            self.logbook.record(gen=current_generation, **record)


            
            if self.DEBUG:
                # Log de progresso da geração
                print(f"  - Geração {current_generation + 1:3d}/{self.setup.NGEN:3d} -> "
                  f"Min: {record['min']:.3f} | "
                  f"Avg: {record['avg']:.3f} | "
                  f"Max: {record['max']:.3f} | "
                  f"Std: {record['std']:.3f}")

        # Retornar população final, logbook e elite
        return population[num_pop], self.logbook, self.hof[0], self.allIndividualValuesArray

    def visualizarPopAtual(self, geracaoAtual, stats):
        """Atualiza as informações de visualização da população atual.
        
        Args:
            geracaoAtual (int): Número da geração atual
            stats (tuple): Tupla contendo (média, desvio_padrao) dos valores de fitness
        """
        if self.DEBUG:
            print(f"\n\nVisualizando população atual da geração {geracaoAtual + 1} com {len(self.POPULATION)} indivíduos.")
            print("TOP 3 Individuals in current population:")

        try:

            for i, ind in enumerate(self.POPULATION):
                # Get fitness value safely, default to infinity if not valid
                fitness_value = float('inf')
                if ind.fitness.valid and hasattr(ind.fitness, 'values') and ind.fitness.values:
                    fitness_value = ind.fitness.values[0]  # Get first fitness value (single-objective)
                
                dataset_individual = {
                    "Generations": geracaoAtual + 1,
                    "index": i,
                    "Variaveis de Decisão": ind,
                    "Fitness": fitness_value,
                    "Media": stats[0] if stats and len(stats) > 0 else float('inf'),
                    "Desvio Padrao": stats[1] if stats and len(stats) > 1 else 0.0,
                    "RCE": " - ",
                    "Valido": ind.fitness.valid
                }
                self.allIndividualValuesArray.append(dataset_individual)
                
                # Debug output for the first few individuals
                if self.DEBUG and i < 3:  # Only show first 3 for brevity
                    #print("TOP 3 Individuals in current population:",self.POPULATION)

                    print(f"Ind {i}: {ind} -> Fitness: {fitness_value:.2f} (Valid: {ind.fitness.valid})")
                
                    
                    
        except Exception as e:
            print(f"Error in visualizarPopAtual: {e}")
            # Log the error but don't crash the application

    def cout(self, msg):
        print(
            "\n=========================================================================================================="
        )
        print("\t", msg)
        print(
            "==========================================================================================================\n"
        )
    
    def generateInfoIndividual(self, new_pop, generation):
        ind_array = []

        for i, ind in enumerate(new_pop):
            # print(f"Index[{ind.index}] - ind_variables {ind} \n Fitness = {ind.fitness.values} ")

            ind.index = i

            ind_info = {
                "Generations": generation,
                "index": ind.index,
                "Variaveis de Decisão": ind,
                "Fitness": ind.fitness.values[0],
                "RCE": ind.rce,
                "Diversidade": np.sum(ind),
            }

            # Adicionar a informação de clone ao dicionário
            # is_clone = self.checkClonesInPop(ind, new_pop)
            # ind_info["CLONE"] = "SIM" if is_clone else "NAO"

            ind_array.append(ind_info)

        return ind_array

    def show_ind_df(self, array, text, save = True):
        df = pd.DataFrame(array)
        if save:
            df.to_excel(f"{FOLDER_NAME}/pop_final.xlsx")

        if self.DEBUG:
            print(text)
            print(df.head(10))

        # contar quantos SIM na coluna CLONE se a coluna RCE for SIM
        # display(df[df["RCE"] != ""].value_counts())

```