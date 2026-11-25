import matplotlib.pyplot as plt
import random
import math
import numpy as np

from random_initial_solution_tsp import random_initial_solution_tsp
from tsp_reading import tsp_reading
from distance_matrix import distance_matrix
from objective_function_tsp import objective_function_tsp
from swap_permutation import swap_permutation
from plotting_route import plotting_route
from two_opt_best_improvement import two_opt_best_improvement

# Input
file_name = "TSP-1.txt"
P = tsp_reading(file_name)
n = len(P)
D = distance_matrix(n, P)

# Parameters
T_0 = 1000
T_f = 1.5
alpha = 0.95

# Initial setting
num_iter = 0
max_iter = 2000
best_solution_found = np.array([0 for j in range(max_iter)])
T = T_0
s_0 = random_initial_solution_tsp(n)
f_0 = objective_function_tsp(n, s_0, D)

s_best = s_0
f_best = f_0

print("Initial solution: ", s_best, f_best)


while num_iter < max_iter:
    s_1 = swap_permutation(s_0, n)
    f_1 = objective_function_tsp(n, s_0, D)
    if (f_1 - f_0 < 0) or (random.random() < math.exp((f_1 - f_0) / T)):
        s_0 = s_1
        f_0 = f_1
    if f_0 < f_best:
        f_best = f_0
        s_best = s_0
    if T <= T_f:
        T = T_0
    else:
        T = alpha * T

    best_solution_found[num_iter] = f_best
    num_iter += 1


print(s_best, f_best)

plt.xlabel("Iterations")
plt.xlabel("Objective function values")
plt.plot(best_solution_found)
plt.savefig("best_solutions.jpg")  # save as jpg

print("Simulated annealing found a solution: ", s_best)
