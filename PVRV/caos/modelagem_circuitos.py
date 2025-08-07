import numpy as np
import sympy as sp
from scipy.integrate import odeint
import matplotlib.pyplot as plt
import pandas as pd

# =============================================================================
# Classe Base para Circuitos Elétricos
# =============================================================================
class Circuito:
    def __init__(self, R, L, C, V0):
        self.R = R  # Resistência em ohms
        self.L = L  # Indutância em henrys
        self.C = C  # Capacitância em farads
        self.V0 = V0  # Tensão de entrada (pode ser função ou valor)

    def equacao_diferencial(self):
        t = sp.symbols('t')
        i = sp.Function('i')(t)
        eq = sp.Eq(self.L * i.diff(t, t) + self.R * i.diff(t) + (1 / self.C) * i, self.V0)
        return eq

    def resolver_ode(self, i0, di0, t):
        def modelo(y, t):
            i, di = y
            d2i = (self.V0 - self.R * di - (1 / self.C) * i) / self.L
            return [di, d2i]

        y0 = [i0, di0]
        sol = odeint(modelo, y0, t)
        return sol[:, 0], sol[:, 1]  # Retorna i(t) e di/dt

# =============================================================================
# Classe Específica para Circuito RLC Série
# =============================================================================
class CircuitoRlcSerie(Circuito):
    def __init__(self, R, L, C, V0):
        super().__init__(R, L, C, V0)

    def calcular_tensoes(self, i, di_dt, t):
        vR = self.R * i
        vL = self.L * di_dt
        q = np.cumsum(i * np.gradient(t))  # Integrando i(t) numericamente
        vC = q / self.C
        return vR, vL, vC

    def simular(self, i0=0, di0=0, t_max=0.1, n=1000):
        t = np.linspace(0, t_max, n)
        i, di_dt = self.resolver_ode(i0, di0, t)
        vR, vL, vC = self.calcular_tensoes(i, di_dt, t)

        df = pd.DataFrame({
            'Tempo (s)': t,
            'Corrente i(t) [A]': i,
            'Tensão R [V]': vR,
            'Tensão L [V]': vL,
            'Tensão C [V]': vC
        })

        return t, i, vR, vL, vC, df

    def plotar(self, t, i, vR, vL, vC):
        plt.figure(figsize=(12, 8))
        plt.subplot(2, 1, 1)
        plt.plot(t, i, label='Corrente i(t)', color='blue')
        plt.title('Corrente no Circuito RLC Série')
        plt.xlabel('Tempo [s]')
        plt.ylabel('Corrente [A]')
        plt.grid(True)
        plt.legend()

        plt.subplot(2, 1, 2)
        plt.plot(t, vR, label='Tensão sobre R', color='red')
        plt.plot(t, vL, label='Tensão sobre L', color='green')
        plt.plot(t, vC, label='Tensão sobre C', color='orange')
        plt.title('Tensões no Circuito RLC Série')
        plt.xlabel('Tempo [s]')
        plt.ylabel('Tensão [V]')
        plt.grid(True)
        plt.legend()

        plt.tight_layout()
        plt.show()

# =============================================================================
# Exemplo de Uso
# =============================================================================
if __name__ == '__main__':
    mestre = CircuitoRlcSerie(R=100, L=0.5, C=0.0001, V0=5)
    t, i, vR, vL, vC, df = mestre.simular(i0=0, di0=0, t_max=0.01, n=1000)
    mestre.plotar(t, i, vR, vL, vC)
    df.to_csv('resultado_rlc.csv', index=False)
