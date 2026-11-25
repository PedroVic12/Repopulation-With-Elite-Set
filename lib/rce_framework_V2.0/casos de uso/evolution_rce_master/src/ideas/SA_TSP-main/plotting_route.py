import matplotlib.pyplot as plt

def plotting_route(n,s,P):
    for i in range (n):
        plt.scatter(P[i][0],P[i][1])

        for i in range (n):
            if (i<n-1):    
                p1= [P[s[i]][0],P[s[i+1]][0]]
                p2= [P[s[i]][1],P[s[i+1]][1]]
                plt.plot(p1,p2, color='b')
            else:
                p1= [P[s[i]][0],P[s[0]][0]]
                p2= [P[s[i]][1],P[s[0]][1]]
                plt.plot(p1,p2, color='b')