import math
def distance_matrix(n,P):
    D = [[0 for j in range (n)] for i in range (n)]
    for i in range(n):
        for j in range(n):
            if (i==j):
                D[i][j]=-1
            else:
                D[i][j]=math.sqrt(((P[i][0]-P[j][0])**2)+(P[i][1]-P[j][1])**2)
        
    return(D)