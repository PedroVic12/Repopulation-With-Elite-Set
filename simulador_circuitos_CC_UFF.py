import numpy as np
import matplotlib.pyplot as plt

# Constantes do circuito (exemplo)
R = 100      # Ohms
L = 0.1      # Henry
C = 100e-6   # Farads
V0 = 5       # Tensão de entrada (volts)
f = 50       # Frequência em Hz
omega = 2 * np.pi * f
t = np.linspace(0, 0.2, 1000)  # tempo em segundos

# Tensão de entrada (senoidal)
Vin = V0 * np.sin(omega * t)

# Corrente no circuito série RLC (resposta forçada senoidal)
Z = np.sqrt(R**2 + (omega - 1/(omega))**2)  # Impedância total
I = V0 / Z * np.sin(omega * t)  # Corrente senoidal

# Tensão em cada componente
V_R = I * R
V_L = I * omega * L
V_C = I / (omega * C)

# Plot
plt.figure(figsize=(12, 8))
plt.subplot(3, 1, 1)
plt.plot(t, Vin, label='Vin (Fonte)', color='blue')
plt.ylabel("Tensão (V)")
plt.legend()

plt.subplot(3, 1, 2)
plt.plot(t, V_R, label='VR (Resistor)', color='red')
plt.plot(t, V_L, label='VL (Indutor)', color='green')
plt.plot(t, V_C, label='VC (Capacitor)', color='purple')
plt.ylabel("Tensão (V)")
plt.legend()

plt.subplot(3, 1, 3)
plt.plot(t, I, label='Corrente (I)', color='orange')
plt.xlabel("Tempo (s)")
plt.ylabel("Corrente (A)")
plt.legend()

plt.tight_layout()
plt.show()


print("Fim da simulção")

