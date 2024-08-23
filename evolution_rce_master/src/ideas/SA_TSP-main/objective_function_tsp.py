def objective_function_tsp(n,s,D):
    d = 0
    for i in range(n-1):
        d += D[s[i]][s[i+1]]

    d+=D[s[n-1]][s[0]]

    return(d)