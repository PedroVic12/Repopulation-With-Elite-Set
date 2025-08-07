import sympy as sp
import math

# Definir a variável simbólica
x = sp.Symbol('x')

# Definir a função simbólica
f_expr = sp.pi * (300 / sp.cos(x))**2 * 0.8 / (0.5 * sp.pi * 14**2 * (1 + sp.sin(x) - 0.5 * sp.cos(x))) - 1200

# Converter a função para uma função numérica (lambdify)
f = sp.lambdify(x, f_expr, modules=['math'])

# Parâmetros iniciais
x0 = 0.0
x1 = 0.125664
e1 = 1e-3
e2 = 1e-3
NMAX = 10

print("Solução de uma equação não linear")
print(f_expr)

print("Iteração |     xn     |     f(xn)    ")
print("-------------------------------")

for i in range(1, NMAX + 1):
    f0 = f(x0)
    f1 = f(x1)
    
    if f1 - f0 == 0:
        print("Divisão por zero na iteração", i)
        break

    x2 = x1 - f1 * (x1 - x0) / (f1 - f0)
    fx2 = f(x2)
    
    print(f"   {i}     | {x2:.6f} | {fx2:.6f}")

    if abs(x2 - x1) < e1 or abs(fx2) < e2:
        print("\nSolução encontrada:")
        print(f"xn = {x2:.6f}")
        print(f"f(xn) = {fx2:.6f}")
        break

    x0, x1 = x1, x2
else:
    print("\nNúmero máximo de iterações alcançado.")
