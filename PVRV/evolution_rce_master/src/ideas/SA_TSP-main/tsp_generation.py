from random import randint 

n=20
m=1

for k in range(m):
    str_file_name = "TSP-"
    file_name = str_file_name + str(k+1)+ ".txt"
    file = open(file_name, "w")
    
    for i in range(n):
        r1=randint(-10*n,10*n)
        r2=randint(-10*n,10*n)
        file.write("%i" %(r1))
        file.write("  ")
        file.write("%i" %(r2))
        file.write("\n") 

    file.close()