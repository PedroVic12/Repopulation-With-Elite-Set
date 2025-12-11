
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt


def circuito_rc():
    try:
            fig, ax = plt.subplots(figsize=(7, 5))
            t = np.linspace(0, 5, 1000)  # Tempo em segundos
            R = 1000  # Resistência em ohms
            C = 1e-6  # Capacitância em farads
            V_in = 5  # Tensão de entrada em volts
            V_out = V_in * (1 - np.exp(-t / (R * C)))  # Resposta do circuito RC

            ax.plot(t, V_out, label='Resposta RC', color='lime', linewidth=2)

            # Personalização do gráfico
            fig.patch.set_facecolor('#1a1a2e')
            ax.set_facecolor('#2b313e')
            ax.set_title("Resposta de Circuito RC", color='white')
            ax.set_xlabel("Tempo (s)", color='white')
            ax.set_ylabel("Tensão (V)", color='white')
            ax.legend()
            ax.grid(True, linestyle=':', color='gray')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            for spine in ax.spines.values():
                spine.set_edgecolor('white')

            st.pyplot(fig)
            plt.close(fig)
    except Exception as e:
            st.error(f"Erro ao gerar gráfico RC: {e}")

def sinal_pwm():
    try:
            fig, ax = plt.subplots(figsize=(7, 5))
            t = np.linspace(0, 1, 1000)
            pwm = (np.sin(2 * np.pi * 10 * t) > 0).astype(int)  # Gera um sinal PWM

            ax.plot(t, pwm, label='Sinal PWM', color='orange', linewidth=2)

            # Personalização do gráfico
            fig.patch.set_facecolor('#1a1a2e')
            ax.set_facecolor('#2b313e')
            ax.set_title("Sinal PWM", color='white')
            ax.set_xlabel("Tempo (s)", color='white')
            ax.set_ylabel("Amplitude", color='white')
            ax.legend()
            ax.grid(True, linestyle=':', color='gray')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            for spine in ax.spines.values():
                spine.set_edgecolor('white')

            st.pyplot(fig)
            plt.close(fig)
    except Exception as e:
            st.error(f"Erro ao gerar gráfico PWM: {e}")

def funcao_seno():
    try:
            fig, ax = plt.subplots(figsize=(7, 5))
            x = np.linspace(0, 2 * np.pi, 150)
            y_sin = np.sin(x)
            y_cos = np.cos(x)

            ax.plot(x, y_sin, label='Seno(x)', color='cyan', linewidth=2)
            ax.plot(x, y_cos, label='Cosseno(x)', color='magenta', linestyle='--', linewidth=2)

            # Personalização do gráfico
            fig.patch.set_facecolor('#1a1a2e')
            ax.set_facecolor('#2b313e')
            ax.set_title("Funções Seno e Cosseno", color='white')
            ax.set_xlabel("Ângulo (radianos)", color='white')
            ax.set_ylabel("Valor", color='white')
            ax.legend()
            ax.grid(True, linestyle=':', color='gray')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            for spine in ax.spines.values():
                spine.set_edgecolor('white')

            st.pyplot(fig)
            plt.close(fig)
    except Exception as e:
            st.error(f"Erro ao gerar gráfico Seno e Cosseno: {e}")