from objective_function_tsp import objective_function_tsp
def two_opt_best_improvement(n,s,f,D):
    s_best = s
    f_best = f
    for i in range(n-1):
        for j in range(1,n):
            s_0 = s
            s[i],s[j]=s[j],s[i]
            f_new = objective_function_tsp(n,s,D)
            if f_new < f_best:
                s_best = s
                f_best = f_new
            else:
                s = s_0
    return(s_best,f_best)

