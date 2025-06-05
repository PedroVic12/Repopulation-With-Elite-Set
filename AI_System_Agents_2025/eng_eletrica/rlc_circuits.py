import numpy as np
from scipy.integrate import odeint

# Constante para evitar divisão por zero ou log de zero
EPS = np.finfo(float).eps

class Circuit:
    """Classe base para circuitos."""
    def __init__(self, R, L, C):
        self.R = max(R, EPS) # Evitar R=0 em alguns cálculos de Q
        self.L = max(L, EPS)
        self.C = max(C, EPS)

    def resonant_frequency_rad(self):
        """Frequência de ressonância em rad/s."""
        if self.L == EPS or self.C == EPS:
            return 0
        return 1 / np.sqrt(self.L * self.C)

    def resonant_frequency_hz(self):
        """Frequência de ressonância em Hz."""
        return self.resonant_frequency_rad() / (2 * np.pi)

class SeriesRLCCircuit(Circuit):
    """Representa um circuito RLC em série."""
    def __init__(self, R, L, C):
        super().__init__(R, L, C)

    def impedance(self, omega):
        """Calcula a impedância Z(ω) = R + j(ωL - 1/(ωC))."""
        omega = np.maximum(omega, EPS) # Evitar omega = 0 para 1/omegaC
        Xc = 1 / (omega * self.C)
        Xl = omega * self.L
        return self.R + 1j * (Xl - Xc)

    def get_frequency_response(self, omega_array):
        """Calcula a magnitude (dB) e fase (graus) da impedância."""
        Z = self.impedance(omega_array)
        magnitude_db = 20 * np.log10(np.abs(Z) + EPS)
        phase_rad = np.angle(Z)
        phase_deg = np.degrees(phase_rad)
        return magnitude_db, phase_deg

    def q_factor(self):
        """Calcula o Fator de Qualidade Q = ω₀L / R."""
        omega0 = self.resonant_frequency_rad()
        if self.R == EPS or omega0 == 0:
            return np.inf # Ou um valor grande, ou tratar como indefinido
        return (omega0 * self.L) / self.R

    def get_step_response(self, Vs, t_array):
        """
        Calcula a resposta a um degrau de tensão usando odeint.
        Retorna corrente i(t) e tensão no capacitor Vc(t).
        Estado: [q, i] onde q é a carga no capacitor, i é a corrente.
        V_L + V_R + V_C = Vs
        L(di/dt) + Ri + q/C = Vs
        dq/dt = i
        """
        def model(state, t, R, L, C, Vs_func):
            q, i = state
            V_s_t = Vs_func(t) # Permite Vs ser uma função do tempo se necessário (aqui é degrau)
            dqdt = i
            didt = (1/L) * (V_s_t - R*i - q/C)
            return [dqdt, didt]

        # Condições iniciais: q(0)=0, i(0)=0
        initial_state = [0, 0]

        # Para um degrau de tensão Vs em t=0
        Vs_step_func = lambda t_val: Vs if t_val >= 0 else 0

        solution = odeint(model, initial_state, t_array, args=(self.R, self.L, self.C, Vs_step_func))
        q_t = solution[:, 0]
        i_t = solution[:, 1]
        Vc_t = q_t / self.C
        return i_t, Vc_t

class ParallelRLCCircuit(Circuit):
    """Representa um circuito RLC em paralelo."""
    def __init__(self, R, L, C):
        super().__init__(R, L, C)

    def admittance(self, omega):
        """Calcula a admitância Y(ω) = 1/R + j(ωC - 1/(ωL))."""
        omega = np.maximum(omega, EPS)
        Bc = omega * self.C
        Bl = 1 / (omega * self.L)
        G = 1 / self.R
        return G + 1j * (Bc - Bl)

    def impedance(self, omega):
        """Calcula a impedância Z(ω) = 1 / Y(ω)."""
        Y = self.admittance(omega)
        return 1 / (Y + EPS) # Adicionar EPS para evitar divisão por zero se Y for zero

    def get_frequency_response(self, omega_array):
        """Calcula a magnitude (dB) e fase (graus) da impedância."""
        Z = self.impedance(omega_array)
        magnitude_db = 20 * np.log10(np.abs(Z) + EPS)
        phase_rad = np.angle(Z)
        phase_deg = np.degrees(phase_rad)
        return magnitude_db, phase_deg

    def q_factor(self):
        """Calcula o Fator de Qualidade Q = R / (ω₀L) = R * ω₀C."""
        omega0 = self.resonant_frequency_rad()
        if omega0 == 0 or self.L == EPS: # ou self.R * omega0 * self.C
             return np.inf # Ou um valor grande
        return self.R / (omega0 * self.L)


class RCCircuit:
    """Representa um circuito RC simples para transitórios."""
    def __init__(self, R, C):
        self.R = max(R, EPS)
        self.C = max(C, EPS)

    def time_constant(self):
        return self.R * self.C

    def voltage_charge(self, V0, t_array):
        """Tensão no capacitor durante a carga: Vc(t) = V₀(1 - e^(-t/RC))."""
        tau = self.time_constant()
        if tau == 0: return np.full_like(t_array, V0) # Carga instantânea se tau=0
        return V0 * (1 - np.exp(-t_array / tau))

    def voltage_discharge(self, V0, t_array):
        """Tensão no capacitor durante a descarga: Vc(t) = V₀e^(-t/RC)."""
        tau = self.time_constant()
        if tau == 0: return np.full_like(t_array, 0) # Descarga instantânea
        return V0 * np.exp(-t_array / tau)

class RLCircuit:
    """Representa um circuito RL simples para transitórios."""
    def __init__(self, R, L):
        self.R = max(R, EPS)
        self.L = max(L, EPS)

    def time_constant(self):
        if self.R == EPS: return np.inf # Constante de tempo infinita se R=0
        return self.L / self.R

    def current_growth(self, V0, t_array):
        """Corrente no indutor durante o crescimento: I(t) = (V₀/R)(1 - e^(-Rt/L))."""
        tau = self.time_constant()
        I_final = V0 / self.R if self.R != EPS else np.inf # Corrente final
        if I_final == np.inf : return np.full_like(t_array, np.inf) # Rampa linear se R=0
        if tau == 0 : return np.full_like(t_array, I_final) # Crescimento instantâneo
        if tau == np.inf: return (V0/self.L) * t_array # Rampa para R=0
        return I_final * (1 - np.exp(-t_array / tau))

    def current_decay(self, I0, t_array):
        """Corrente no indutor durante o decaimento: I(t) = I₀e^(-Rt/L)."""
        tau = self.time_constant()
        if tau == 0 : return np.full_like(t_array, 0) # Decaimento instantâneo
        if tau == np.inf: return np.full_like(t_array, I0) # Corrente constante se R=0
        return I0 * np.exp(-t_array / tau)