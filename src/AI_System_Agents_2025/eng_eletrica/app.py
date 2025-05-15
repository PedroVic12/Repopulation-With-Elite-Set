import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from rlc_circuits import (SeriesRLCCircuit, ParallelRLCCircuit,
                          RCCircuit, RLCircuit, EPS)

# Configuração da página
st.set_page_config(layout="wide", page_title="Análise de Circuitos RLC")

# --- Funções de Plotagem ---
def plot_bode(omega_array, magnitude_db, phase_deg, title):
    """Plota o diagrama de Bode (Magnitude e Fase)."""
    fig, ax1 = plt.subplots(figsize=(10, 6))

    color = 'tab:red'
    ax1.set_xlabel('Frequência Angular $\omega$ (rad/s) [Escala Log]')
    ax1.set_ylabel('Magnitude $|Z(\omega)|$ (dB)', color=color)
    ax1.semilogx(omega_array, magnitude_db, color=color, linestyle='-')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, which="both", ls="-", alpha=0.5)

    ax2 = ax1.twinx() # Compartilha o mesmo eixo x
    color = 'tab:blue'
    ax2.set_ylabel('Fase $\\angle Z(\omega)$ (graus)', color=color)
    ax2.semilogx(omega_array, phase_deg, color=color, linestyle='--')
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout() # Para não cortar os labels
    plt.title(title)
    st.pyplot(fig)

def plot_time_domain(t_array, signals, labels, title, y_label):
    """Plota sinais no domínio do tempo."""
    fig, ax = plt.subplots(figsize=(10, 6))
    for signal, label in zip(signals, labels):
        ax.plot(t_array, signal, label=label)
    ax.set_xlabel('Tempo (s)')
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.legend()
    ax.grid(True, which="both", ls="-", alpha=0.5)
    st.pyplot(fig)

def plot_multiple_magnitudes(omega_array, magnitudes_db, labels, title, varying_param_name):
    """Plota múltiplas curvas de magnitude para comparação."""
    fig, ax = plt.subplots(figsize=(10, 6))
    for mag, label in zip(magnitudes_db, labels):
        ax.semilogx(omega_array, mag, label=label)

    ax.set_xlabel('Frequência Angular $\omega$ (rad/s) [Escala Log]')
    ax.set_ylabel('Magnitude $|Z(\omega)|$ (dB)')
    ax.set_title(title)
    ax.legend(title=f"Variação de {varying_param_name}")
    ax.grid(True, which="both", ls="-", alpha=0.5)
    st.pyplot(fig)

# --- Interface Streamlit ---
st.title("🐍 Análise Interativa de Circuitos RLC com Python")
st.markdown("""
Use esta aplicação para visualizar o comportamento de circuitos RLC em diferentes cenários.
Ajuste os parâmetros no painel à esquerda e observe os gráficos.
""")

# Sidebar para seleção de análise e parâmetros
st.sidebar.title("⚙️ Configurações")
analysis_type = st.sidebar.selectbox(
    "Escolha o tipo de análise:",
    [
        "Resposta em Frequência (Diagrama de Bode)",
        "Resposta ao Degrau de Tensão (Série RLC)",
        "Influência dos Componentes na Ressonância",
        "Transitórios RC e RL"
    ]
)

# --- Lógica para cada tipo de análise ---

if analysis_type == "Resposta em Frequência (Diagrama de Bode)":
    st.header("📈 Resposta em Frequência")
    circuit_type = st.sidebar.radio("Tipo de Circuito RLC:", ("Série", "Paralelo"))

    col1, col2, col3 = st.sidebar.columns(3)
    R = col1.number_input("Resistência R (Ω)", min_value=EPS, value=100.0, step=10.0, format="%.2f")
    L = col2.number_input("Indutância L (H)", min_value=EPS, value=10e-3, step=1e-3, format="%.4f")
    C = col3.number_input("Capacitância C (F)", min_value=EPS, value=100e-9, step=1e-9, format="%.10f")

    st.sidebar.markdown("---")
    f_start_hz = st.sidebar.number_input("Frequência Inicial (Hz)", min_value=EPS, value=1.0, step=1.0)
    f_end_hz = st.sidebar.number_input("Frequência Final (Hz)", min_value=f_start_hz+EPS, value=100000.0, step=1000.0)
    num_points = st.sidebar.slider("Número de Pontos (Log)", 100, 1000, 500)

    omega_start = 2 * np.pi * f_start_hz
    omega_end = 2 * np.pi * f_end_hz
    omega_array = np.logspace(np.log10(omega_start), np.log10(omega_end), num_points)

    if circuit_type == "Série":
        circuit = SeriesRLCCircuit(R, L, C)
        title_prefix = "Série"
    else: # Paralelo
        circuit = ParallelRLCCircuit(R, L, C)
        title_prefix = "Paralelo"

    magnitude_db, phase_deg = circuit.get_frequency_response(omega_array)

    st.subheader(f"Diagrama de Bode para Circuito RLC {title_prefix}")
    plot_bode(omega_array, magnitude_db, phase_deg, f"Resposta em Frequência - RLC {title_prefix}")

    st.subheader("Parâmetros Calculados:")
    f_res = circuit.resonant_frequency_hz()
    q_factor = circuit.q_factor()
    st.metric(label="Frequência de Ressonância (f₀)", value=f"{f_res:.2f} Hz")
    st.metric(label="Fator de Qualidade (Q)", value=f"{q_factor:.2f}")


elif analysis_type == "Resposta ao Degrau de Tensão (Série RLC)":
    st.header("⚡ Resposta ao Degrau de Tensão (Circuito RLC Série)")

    col1, col2, col3 = st.sidebar.columns(3)
    R = col1.number_input("Resistência R (Ω)", min_value=EPS, value=50.0, step=1.0, format="%.2f")
    L = col2.number_input("Indutância L (H)", min_value=EPS, value=20e-3, step=1e-3, format="%.4f")
    C = col3.number_input("Capacitância C (F)", min_value=EPS, value=0.1e-6, step=1e-8, format="%.10f")

    Vs = st.sidebar.number_input("Tensão do Degrau Vs (V)", min_value=0.1, value=10.0, step=0.1)

    st.sidebar.markdown("---")
    t_max_factor = st.sidebar.slider("Fator de Tempo Máx (x  1/α ou x RC)", 3.0, 15.0, 5.0, 0.1)
    num_t_points = st.sidebar.slider("Número de Pontos no Tempo", 100, 2000, 500)

    circuit = SeriesRLCCircuit(R, L, C)

    # Estimativa da constante de tempo para definir t_max
    # α = R / (2L) -> tempo característico 1/α
    # ω₀ = 1 / sqrt(LC)
    alpha = R / (2 * L) if L > EPS else EPS
    omega0_sq = 1 / (L * C) if (L*C) > EPS else EPS

    if alpha == EPS and omega0_sq == EPS: # Evita problemas se L ou C for zero
        t_max_est = 0.1
    elif alpha * alpha > omega0_sq : # Superamortecido
        s1 = -alpha + np.sqrt(alpha*alpha - omega0_sq)
        s2 = -alpha - np.sqrt(alpha*alpha - omega0_sq)
        # A constante de tempo dominante é -1/s_dominante (s mais próximo de zero)
        t_char = -1 / max(s1, s2) if max(s1,s2) < -EPS else 0.1
        t_max_est = t_max_factor * t_char
    elif abs(alpha * alpha - omega0_sq) < EPS: # Criticamente Amortecido
        t_char = 1/alpha if alpha > EPS else 0.1
        t_max_est = t_max_factor * t_char
    else: # Subamortecido
        t_char = 1/alpha if alpha > EPS else 0.1
        t_max_est = t_max_factor * t_char

    t_max_est = max(t_max_est, 0.001) # Mínimo t_max

    t_array = np.linspace(0, t_max_est, num_t_points)
    current_t, voltage_c_t = circuit.get_step_response(Vs, t_array)
    voltage_r_t = R * current_t
    # V_L = Vs - V_R - V_C (cuidado com descontinuidades em Vs para derivada de i_t)
    # Ou V_L = L * di/dt. Para evitar diferenciação numérica ruidosa, usar a lei de Kirchhoff.
    # Vs(t) para t>=0 é Vs.
    voltage_l_t = np.full_like(t_array, Vs) - voltage_r_t - voltage_c_t


    st.subheader("Formas de Onda no Domínio do Tempo")
    plot_time_domain(t_array, [current_t], ["Corrente $i(t)$"],
                     "Corrente no Circuito RLC Série", "Corrente (A)")
    plot_time_domain(t_array,
                     [np.full_like(t_array, Vs), voltage_r_t, voltage_l_t, voltage_c_t],
                     ["Tensão da Fonte $V_s(t)$", "Tensão no Resistor $V_R(t)$", "Tensão no Indutor $V_L(t)$", "Tensão no Capacitor $V_C(t)$"],
                     "Tensões nos Componentes - Circuito RLC Série", "Tensão (V)")

    f_res = circuit.resonant_frequency_hz()
    q_factor = circuit.q_factor()
    st.metric(label="Frequência de Ressonância (f₀)", value=f"{f_res:.2f} Hz")
    st.metric(label="Fator de Qualidade (Q)", value=f"{q_factor:.2f}")
    damping_ratio = R / (2 * np.sqrt(L/C)) if C > EPS and L > EPS else 0
    st.metric(label="Taxa de Amortecimento (ζ)", value=f"{damping_ratio:.3f}")
    if damping_ratio < 1: st.info("Sistema Subamortecido (oscilatório)")
    elif damping_ratio == 1: st.info("Sistema Criticamente Amortecido")
    else: st.info("Sistema Superamortecido")


elif analysis_type == "Influência dos Componentes na Ressonância":
    st.header("🔬 Influência dos Valores de R, L, C (Circuito Série)")
    st.markdown("Observe como a variação de um componente afeta a curva de magnitude da impedância, a frequência de ressonância e o fator Q de um circuito RLC Série.")

    param_to_vary = st.sidebar.selectbox(
        "Parâmetro a variar:",
        ("Resistência (R)", "Indutância (L)", "Capacitância (C)")
    )

    st.sidebar.subheader("Valores Base:")
    col1, col2, col3 = st.sidebar.columns(3)
    R_base = col1.number_input("R base (Ω)", min_value=EPS, value=50.0, format="%.2f")
    L_base = col2.number_input("L base (H)", min_value=EPS, value=10e-3, format="%.4f")
    C_base = col3.number_input("C base (F)", min_value=EPS, value=100e-9, format="%.10f")

    st.sidebar.subheader("Configuração da Variação:")
    num_steps = st.sidebar.slider("Número de Variações", 2, 10, 5)
    if param_to_vary == "Resistência (R)":
        min_val = st.sidebar.number_input("R Mínimo (Ω)", min_value=EPS, value=10.0, format="%.2f")
        max_val = st.sidebar.number_input("R Máximo (Ω)", min_value=min_val+EPS, value=200.0, format="%.2f")
        varying_values = np.linspace(min_val, max_val, num_steps)
        param_unit = "Ω"
    elif param_to_vary == "Indutância (L)":
        min_val = st.sidebar.number_input("L Mínimo (mH)", min_value=EPS*1000, value=1.0, format="%.2f") / 1000
        max_val = st.sidebar.number_input("L Máximo (mH)", min_value=min_val*1000+EPS, value=50.0, format="%.2f") / 1000
        varying_values = np.linspace(min_val, max_val, num_steps)
        param_unit = "H"
    else: # Capacitância (C)
        min_val = st.sidebar.number_input("C Mínimo (nF)", min_value=EPS*1e9, value=10.0, format="%.2f") / 1e9
        max_val = st.sidebar.number_input("C Máximo (nF)", min_value=min_val*1e9+EPS, value=500.0, format="%.2f") / 1e9
        varying_values = np.logspace(np.log10(min_val), np.log10(max_val), num_steps) # Log scale for C often better
        param_unit = "F"

    st.sidebar.markdown("---")
    f_start_hz_inf = st.sidebar.number_input("Frequência Inicial (Hz) ", min_value=EPS, value=100.0, step=1.0, key="f_start_inf")
    f_end_hz_inf = st.sidebar.number_input("Frequência Final (Hz) ", min_value=f_start_hz_inf+EPS, value=50000.0, step=1000.0, key="f_end_inf")
    num_points_inf = st.sidebar.slider("Número de Pontos (Log) ", 100, 1000, 300, key="num_points_inf")

    omega_array_inf = np.logspace(np.log10(2*np.pi*f_start_hz_inf), np.log10(2*np.pi*f_end_hz_inf), num_points_inf)

    magnitudes = []
    labels = []
    results_data = []

    for val in varying_values:
        if param_to_vary == "Resistência (R)":
            circuit = SeriesRLCCircuit(val, L_base, C_base)
            label = f"R = {val:.2f} {param_unit}"
        elif param_to_vary == "Indutância (L)":
            circuit = SeriesRLCCircuit(R_base, val, C_base)
            label = f"L = {val*1000:.2f} mH" if param_unit == "H" else f"L = {val:.2e} {param_unit}"
        else: # Capacitância (C)
            circuit = SeriesRLCCircuit(R_base, L_base, val)
            label = f"C = {val*1e9:.2f} nF" if param_unit == "F" else f"C = {val:.2e} {param_unit}"

        mag_db, _ = circuit.get_frequency_response(omega_array_inf)
        magnitudes.append(mag_db)
        labels.append(label)
        results_data.append({
            "Valor Variado": f"{val*1000 if param_unit=='H' and param_to_vary=='Indutância (L)' else (val*1e9 if param_unit=='F' and param_to_vary=='Capacitância (C)' else val):.2f} {'mH' if param_unit=='H' and param_to_vary=='Indutância (L)' else ('nF' if param_unit=='F' and param_to_vary=='Capacitância (C)' else param_unit)}",
            "f₀ (Hz)": circuit.resonant_frequency_hz(),
            "Q": circuit.q_factor()
        })

    plot_multiple_magnitudes(omega_array_inf, magnitudes, labels,
                             f"Influência de {param_to_vary} na Magnitude da Impedância (Série)",
                             param_to_vary)

    st.subheader("Resultados Tabulados")
    df_results = pd.DataFrame(results_data)
    st.dataframe(df_results.style.format({
        "f₀ (Hz)": "{:.2f}",
        "Q": "{:.2f}"
    }))


elif analysis_type == "Transitórios RC e RL":
    st.header("⏳ Comportamento Transitório (Carga e Descarga)")
    circuit_choice = st.sidebar.radio("Escolha o Circuito:", ("RC", "RL"))

    if circuit_choice == "RC":
        st.sidebar.subheader("Parâmetros do Circuito RC")
        col1, col2 = st.sidebar.columns(2)
        R_rc = col1.number_input("Resistência R (Ω)", min_value=EPS, value=10e3, format="%.2f")
        C_rc = col2.number_input("Capacitância C (µF)", min_value=EPS*1e6, value=1.0, format="%.2f") / 1e6
        V0_rc = st.sidebar.number_input("Tensão Inicial/Fonte V₀ (V)", min_value=0.1, value=5.0)

        rc_circuit = RCCircuit(R_rc, C_rc)
        tau_rc = rc_circuit.time_constant()
        t_max_rc = st.sidebar.slider("Tempo Máximo (múltiplos de τ)", 1.0, 10.0, 5.0, 0.1) * tau_rc
        t_max_rc = max(t_max_rc, EPS*1000) # Evitar t_max = 0
        t_array_rc = np.linspace(0, t_max_rc, 500)

        vc_charge = rc_circuit.voltage_charge(V0_rc, t_array_rc)
        vc_discharge = rc_circuit.voltage_discharge(V0_rc, t_array_rc)

        st.subheader("Circuito RC")
        plot_time_domain(t_array_rc, [vc_charge], ["$V_C(t)$ Carga"],
                         "Carga do Capacitor em Circuito RC", "Tensão no Capacitor (V)")
        plot_time_domain(t_array_rc, [vc_discharge], ["$V_C(t)$ Descarga"],
                         "Descarga do Capacitor em Circuito RC", "Tensão no Capacitor (V)")
        st.metric(label="Constante de Tempo (τ = RC)", value=f"{tau_rc*1000:.2f} ms")

    else: # RL
        st.sidebar.subheader("Parâmetros do Circuito RL")
        col1, col2 = st.sidebar.columns(2)
        R_rl = col1.number_input("Resistência R (Ω)", min_value=EPS, value=10.0, format="%.2f")
        L_rl = col2.number_input("Indutância L (mH)", min_value=EPS*1000, value=100.0, format="%.2f") / 1000

        st.sidebar.markdown("Para crescimento da corrente:")
        V0_rl_source = st.sidebar.number_input("Tensão da Fonte V₀ (V)", min_value=0.1, value=10.0)
        st.sidebar.markdown("Para decaimento da corrente:")
        I0_rl_initial = st.sidebar.number_input("Corrente Inicial I₀ (A)", min_value=0.01, value=1.0)


        rl_circuit = RLCircuit(R_rl, L_rl)
        tau_rl = rl_circuit.time_constant()

        if np.isinf(tau_rl) or tau_rl == 0: # Lida com R=0 ou L=0
             t_max_rl = 0.1 if L_rl > EPS else 0.01 # Um tempo arbitrário pequeno
        else:
            t_max_rl = st.sidebar.slider("Tempo Máximo (múltiplos de τ)", 1.0, 10.0, 5.0, 0.1) * tau_rl

        t_max_rl = max(t_max_rl, EPS*1000)
        t_array_rl = np.linspace(0, t_max_rl, 500)

        il_growth = rl_circuit.current_growth(V0_rl_source, t_array_rl)
        il_decay = rl_circuit.current_decay(I0_rl_initial, t_array_rl)

        st.subheader("Circuito RL")
        plot_time_domain(t_array_rl, [il_growth], ["$I_L(t)$ Crescimento"],
                         "Crescimento da Corrente no Indutor em Circuito RL", "Corrente no Indutor (A)")
        plot_time_domain(t_array_rl, [il_decay], ["$I_L(t)$ Decaimento"],
                         "Decaimento da Corrente no Indutor em Circuito RL", "Corrente no Indutor (A)")
        st.metric(label="Constante de Tempo (τ = L/R)", value=f"{tau_rl*1000:.2f} ms" if not np.isinf(tau_rl) else "Infinita (R=0)")

st.sidebar.markdown("---")
st.sidebar.info("Desenvolvido com Streamlit, Matplotlib e NumPy.")