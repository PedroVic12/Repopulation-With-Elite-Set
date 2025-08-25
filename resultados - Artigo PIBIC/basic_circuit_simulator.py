import streamlit as st
import schemdraw
import schemdraw.elements as elm
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import io
import base64

# --- Funções de Desenho (SchemDraw) ---

def draw_rlc_circuit(R, L, C, f):
    with schemdraw.Drawing() as d:
        d.config(unit=3)
        V = d.add(elm.SourceSin().label(f'{f} Hz'))
        d.add(elm.Resistor().right().label(f'{R} Ω', loc='bottom'))
        d.add(elm.Inductor().right().label(f'{L*1e3:.1f} mH', loc='bottom'))
        d.add(elm.Capacitor().right().label(f'{C*1e6:.1f} μF', loc='bottom'))
        d.add(elm.Line().left().to(V.start))
        d.add(elm.Ground())
    svg_data = d.get_imagedata('svg')
    b64 = base64.b64encode(svg_data).decode("utf-8")
    return f"data:image/svg+xml;base64,{b64}"

def draw_rc_circuit(R, C, f):
    with schemdraw.Drawing() as d:
        d.config(unit=3)
        V = d.add(elm.SourceSin().label(f'{f} Hz'))
        d.add(elm.Resistor().right().label(f'{R} Ω', loc='bottom'))
        d.add(elm.Capacitor().right().label(f'{C*1e6:.1f} μF', loc='bottom'))
        d.add(elm.Line().left().to(V.start))
        d.add(elm.Ground())
    svg_data = d.get_imagedata('svg')
    b64 = base64.b64encode(svg_data).decode("utf-8")
    return f"data:image/svg+xml;base64,{b64}"


# --- Funções de Análise (SymPy & NumPy) ---

def analyze_rlc_frequency_domain(R, L, C, f):
    s, R_sym, L_sym, C_sym, omega_sym = sp.symbols('s R L C omega', real=True, positive=True)
    Z_total_s = R_sym + L_sym * s + 1 / (C_sym * s)
    Z_total_jw = Z_total_s.subs(s, sp.I * omega_sym)
    
    omega = 2 * np.pi * f
    XL = omega * L
    XC = 1 / (omega * C) if omega * C > 0 else np.inf
    Z_complex = R + 1j * (XL - XC)
    
    return {
        "Z_total_symbolic": Z_total_jw,
        "Z_magnitude": np.abs(Z_complex),
        "Z_phase_deg": np.rad2deg(np.angle(Z_complex)),
        "XL": XL, "XC": XC, "Z_complex": Z_complex
    }

def analyze_rc_frequency_domain(R, C, f):
    s, R_sym, C_sym, omega_sym = sp.symbols('s R C omega', real=True, positive=True)
    Z_total_s = R_sym + 1 / (C_sym * s)
    Z_total_jw = Z_total_s.subs(s, sp.I * omega_sym)

    omega = 2 * np.pi * f
    XC = 1 / (omega * C) if omega * C > 0 else np.inf
    Z_complex = R - 1j * XC

    return {
        "Z_total_symbolic": Z_total_jw,
        "Z_magnitude": np.abs(Z_complex),
        "Z_phase_deg": np.rad2deg(np.angle(Z_complex)),
        "XC": XC, "Z_complex": Z_complex
    }

def solve_time_domain(Z_complex, V_peak, f):
    t, omega, phi, I_peak_sym, V_peak_sym = sp.symbols('t omega phi I_peak V_peak', real=True)
    
    omega_val = 2 * np.pi * f
    Z_mag = np.abs(Z_complex)
    phi_val = np.angle(Z_complex)
    I_peak = V_peak / Z_mag if Z_mag > 0 else 0
    
    v_source_expr = V_peak * sp.cos(omega_val * t)
    i_t_expr = I_peak * sp.cos(omega_val * t - phi_val)
    
    v_source_func = sp.lambdify(t, v_source_expr, 'numpy')
    i_t_func = sp.lambdify(t, i_t_expr, 'numpy')

    i_t_eq_latex = sp.latex(I_peak_sym * sp.cos(omega * t - phi))
    v_s_t_eq_latex = sp.latex(V_peak_sym * sp.cos(omega * t))

    return {
        "v_source_func": v_source_func, "i_t_func": i_t_func,
        "v_s_t_eq_latex": v_s_t_eq_latex, "i_t_eq_latex": i_t_eq_latex,
        "I_peak": I_peak, "phi_deg": np.rad2deg(phi_val)
    }


# --- Funções de Plot (Matplotlib) ---

def plot_phasor_diagram(vectors, labels, colors, title):
    fig, ax = plt.subplots(figsize=(5, 5))
    max_val = max(np.abs(v) for v in vectors) * 1.3
    if max_val == 0: max_val = 1
    ax.set_xlim(-max_val, max_val); ax.set_ylim(-max_val, max_val)
    ax.axhline(0, color='grey', lw=0.5); ax.axvline(0, color='grey', lw=0.5)

    for i, (vec, label, color) in enumerate(zip(vectors, labels, colors)):
        start_point = sum(vectors[:i])
        ax.arrow(start_point.real, start_point.imag, vec.real, vec.imag, 
                 head_width=max_val*0.05, head_length=max_val*0.1, fc=color, ec=color, label=label)
    
    # Desenha o vetor resultante (total) da origem
    total_vec = sum(vectors)
    ax.arrow(0, 0, total_vec.real, total_vec.imag, 
             head_width=max_val*0.05, head_length=max_val*0.1, fc='yellow', ec='yellow', label='$Z_{total}$')

    ax.set_title(title); ax.set_xlabel("Eixo Real (Resistência)"); ax.set_ylabel("Eixo Imaginário (Reatância)")
    ax.grid(True, linestyle='--', alpha=0.6); ax.set_aspect('equal', adjustable='box'); ax.legend()
    return fig

def plot_time_domain(t_vals, v_vals, i_vals, V_peak, I_peak, f):
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(t_vals, v_vals, 'b-', label='Tensão da Fonte $V(t)$')
    ax1.set_xlabel(f"Tempo (s) - Exibindo 3 ciclos")
    ax1.set_ylabel("Tensão (V)", color='b'); ax1.tick_params(axis='y', labelcolor='b')
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.set_ylim(-(V_peak * 1.2), V_peak * 1.2) if V_peak > 0 else ax1.set_ylim(-1, 1)

    ax2 = ax1.twinx()
    ax2.plot(t_vals, i_vals, 'r-', label='Corrente $I(t)$')
    ax2.set_ylabel("Corrente (A)", color='r'); ax2.tick_params(axis='y', labelcolor='r')
    ax2.set_ylim(-(I_peak * 1.2), I_peak * 1.2) if I_peak > 0 else ax2.set_ylim(-1, 1)

    fig.suptitle("Formas de Onda no Domínio do Tempo", fontsize=16)
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper right')
    return fig


# --- Interface Principal (Streamlit) ---

st.set_page_config(page_title="Simulador de Circuitos CA", layout="wide")
st.title("⚡ Simulador Interativo de Circuitos CA")

# --- Menu Lateral de Configuração ---
with st.sidebar:
    st.header("Parâmetros do Circuito")
    V_peak = st.slider("Tensão de Pico da Fonte (V)", 1.0, 220.0, 10.0, 0.5)
    f_val = st.slider("Frequência (f) [Hz]", 1.0, 1000.0, 60.0, 1.0)
    R_val = st.slider("Resistência (R) [Ω]", 1.0, 1000.0, 100.0, 1.0)
    L_val = st.slider("Indutância (L) [mH]", 1.0, 1000.0, 100.0, 1.0) / 1000 # H
    C_val = st.slider("Capacitância (C) [μF]", 0.1, 100.0, 10.0, 0.1) / 1e6 # F

# --- Abas para cada circuito ---
tab_rlc, tab_rc = st.tabs(["🔌 Circuito RLC", "💡 Circuito RC"])

# --- Aba RLC ---
with tab_rlc:
    st.header("Análise do Circuito RLC Série")
    
    col_diagram, col_freq_analysis = st.columns([1, 2])
    with col_diagram:
        st.subheader("Diagrama (SchemDraw)")
        st.image(draw_rlc_circuit(R_val, L_val, C_val, f_val))

    with col_freq_analysis:
        st.subheader("Análise no Domínio da Frequência")
        rlc_freq = analyze_rlc_frequency_domain(R_val, L_val, C_val, f_val)
        st.metric("Impedância Total |Z|", f"{rlc_freq['Z_magnitude']:.2f} Ω")
        st.metric("Ângulo de Fase (φ)", f"{rlc_freq['Z_phase_deg']:.2f}°")
        st.latex(f"Z_{{total}} = {R_val} \\Omega + j({rlc_freq['XL']:.2f} \\Omega - {rlc_freq['XC']:.2f} \\Omega)")

    st.subheader("Diagrama Fasorial de Impedância")
    rlc_phasor_fig = plot_phasor_diagram(
        [R_val, 1j * rlc_freq['XL'], -1j * rlc_freq['XC']],
        ['$Z_R$', '$Z_L$', '$Z_C$'],
        ['cyan', 'magenta', 'orange'],
        "Fasores de Impedância (RLC)"
    )
    st.pyplot(rlc_phasor_fig)

    st.divider()
    st.header("Análise no Domínio do Tempo (RLC)")
    if st.button("Calcular e Plotar Tensão/Corrente (RLC)"):
        time_analysis = solve_time_domain(rlc_freq['Z_complex'], V_peak, f_val)
        t_vals = np.linspace(0, 3 / f_val, 500)
        v_vals = time_analysis["v_source_func"](t_vals)
        i_vals = time_analysis["i_t_func"](t_vals)
        
        with st.expander("Resultados e Gráficos", expanded=True):
            st.pyplot(plot_time_domain(t_vals, v_vals, i_vals, V_peak, time_analysis['I_peak'], f_val))
            st.metric("Pico de Corrente (I_peak)", f"{time_analysis['I_peak']:.3f} A")


# --- Aba RC ---
with tab_rc:
    st.header("Análise do Circuito RC Série")

    col_diagram_rc, col_freq_analysis_rc = st.columns([1, 2])
    with col_diagram_rc:
        st.subheader("Diagrama (SchemDraw)")
        st.image(draw_rc_circuit(R_val, C_val, f_val))

    with col_freq_analysis_rc:
        st.subheader("Análise no Domínio da Frequência")
        rc_freq = analyze_rc_frequency_domain(R_val, C_val, f_val)
        st.metric("Impedância Total |Z|", f"{rc_freq['Z_magnitude']:.2f} Ω")
        st.metric("Ângulo de Fase (φ)", f"{rc_freq['Z_phase_deg']:.2f}°")
        st.latex(f"Z_{{total}} = {R_val} \\Omega - j({rc_freq['XC']:.2f} \\Omega)")

    st.subheader("Diagrama Fasorial de Impedância")
    rc_phasor_fig = plot_phasor_diagram(
        [R_val, -1j * rc_freq['XC']],
        ['$Z_R$', '$Z_C$'],
        ['cyan', 'orange'],
        "Fasores de Impedância (RC)"
    )
    st.pyplot(rc_phasor_fig)

    st.divider()
    st.header("Análise no Domínio do Tempo (RC)")
    if st.button("Calcular e Plotar Tensão/Corrente (RC)"):
        time_analysis_rc = solve_time_domain(rc_freq['Z_complex'], V_peak, f_val)
        t_vals_rc = np.linspace(0, 3 / f_val, 500)
        v_vals_rc = time_analysis_rc["v_source_func"](t_vals_rc)
        i_vals_rc = time_analysis_rc["i_t_func"](t_vals_rc)

        with st.expander("Resultados e Gráficos", expanded=True):
            st.pyplot(plot_time_domain(t_vals_rc, v_vals_rc, i_vals_rc, V_peak, time_analysis_rc['I_peak'], f_val))
            st.metric("Pico de Corrente (I_peak)", f"{time_analysis_rc['I_peak']:.3f} A")

