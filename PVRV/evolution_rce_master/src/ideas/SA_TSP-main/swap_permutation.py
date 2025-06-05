import random
def swap_permutation(s,n):
    k = random.sample(range(1,n),2)
    s[k[0]],s[k[1]]=s[k[1]],s[k[0]]
    return(s)