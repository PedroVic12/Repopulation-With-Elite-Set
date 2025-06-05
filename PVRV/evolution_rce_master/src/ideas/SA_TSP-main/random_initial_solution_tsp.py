import numpy as np
def random_initial_solution_tsp (n):
    s = [0 for i in range(n)]
    s = np.random.permutation(n)
    return(s)