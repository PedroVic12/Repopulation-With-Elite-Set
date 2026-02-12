import streamlit as st
import schemdraw
import schemdraw.elements as elm
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import io
import base64

# --- Funções de Desenho (SchemDraw) ---

def draw_circuit(type, R, L, C, source=False, f=None):
    """Função unificada para desenhar circuitos RLC e RC."""
    with schemdraw.Drawing() as d:
        d.config(unit=3.5)
        
        if source:
            V = d.add(elm.SourceSin().label(f'{f} Hz' if f else 'V(t)'))
        else:
            d.add(elm.Line().right())

        if type == 'RLC':
            L_elm = d.add(elm.Inductor().down().label(f'{L*1e3:.1f} mH'))
            d.add(elm.Resistor().left().label(f'{R} Ω'))
            
            # Adiciona o capacitor e a sua etiqueta de tensão
            C_elm_label = f'{C*1e6:.1f} μF'
            if not source:
                C_elm = d.add(elm.Capacitor().up().label(C_elm_label).label(('+', '$v_C(t)$', '-'), loc='bottom'))
            else:
                C_elm = d.add(elm.Capacitor().up().label(C_elm_label))

            d.add(elm.Line().right().to(L_elm.start))
            if not source:
                d.add(elm.CurrentLabel(top=False).at(L_elm).label('$i(t)$'))
        
        elif type == 'RC':
            d.add(elm.Resistor().down().label(f'{R} Ω'))

            # Adiciona o capacitor e a sua etiqueta de tensão
            C_elm_label = f'{C*1e6:.1f} μF'
            if not source:
                 C_elm = d.add(elm.Capacitor().left().label(C_elm_label).label(('+', '$v_C(t)$', '-'), loc='bottom'))
            else:
                 C_elm = d.add(elm.Capacitor().left().label(C_elm_label))

            if source:
                d.add(elm.Line().up().to(V.start))
            else:
                d.add(elm.Line().up().to(C_elm.start))

        if source:
            d.add(elm.Ground())

    svg_data = d.get_imagedata('svg')
    b64 = base64.b64encode(svg_data).decode("utf-8")
    return f"data:image/svg+xml;base64,{b64}"


# --- Funções de Análise de Resposta Natural (EDO com SymPy) ---

def solve_rlc_natural_response(R, L, C, V0, I0):
    t, s = sp.symbols('t s', real=True)
    v = sp.Function('v')(t)
    
    # EDO para display
    edo = sp.Eq(v.diff(t, 2) + (R/L) * v.diff(t, 1) + (1/(L*C)) * v, 0)
    
    # Parâmetros calculados numericamente
    alpha = R / (2 * L)
    omega0 = 1 / np.sqrt(L * C) if L * C > 0 else 0
    dv0 = I0 / C

    # Resolve a equação característica numericamente para robustez
    coeffs = [1, 2 * alpha, omega0**2]
    roots = np.roots(coeffs)
    s1, s2 = roots[0], roots[1]

    # Determina o tipo de amortecimento e resolve para as constantes simbolicamente
    if alpha > omega0:
        damping_type = "Superamortecida"
        A1, A2 = sp.symbols('A1 A2')
        # Usa as raízes numéricas na forma da solução simbólica
        solution_form = A1 * sp.exp(s1*t) + A2 * sp.exp(s2*t)
        constants = sp.solve([sp.Eq(solution_form.subs(t, 0), V0), sp.Eq(solution_form.diff(t).subs(t, 0), dv0)], (A1, A2))
    elif abs(alpha - omega0) < 1e-9:
        damping_type = "Amortecimento Crítico"
        D1, D2 = sp.symbols('D1 D2')
        # Usa alpha para a raiz repetida
        solution_form = (D1 + D2 * t) * sp.exp(-alpha * t)
        constants = sp.solve([sp.Eq(solution_form.subs(t, 0), V0), sp.Eq(solution_form.diff(t).subs(t, 0), dv0)], (D1, D2))
    else: # Subamortecida
        damping_type = "Subamortecida"
        omega_d = np.sqrt(omega0**2 - alpha**2)
        B1, B2 = sp.symbols('B1 B2')
        solution_form = sp.exp(-alpha*t) * (B1 * sp.cos(omega_d*t) + B2 * sp.sin(omega_d*t))
        constants = sp.solve([sp.Eq(solution_form.subs(t, 0), V0), sp.Eq(solution_form.diff(t).subs(t, 0), dv0)], (B1, B2))
    
    # Substitui as constantes na forma da solução correta
    final_solution = solution_form.subs(constants)
    v_func = sp.lambdify(t, final_solution, 'numpy')
    
    # Equação característica simbólica para exibição
    alpha_sym, omega0_sym = sp.symbols('alpha omega_0')
    char_eq_display = sp.Eq(s**2 + 2*alpha_sym*s + omega0_sym**2, 0)

    return {
        "edo": edo, "char_eq": char_eq_display, "alpha": alpha, "omega0": omega0,
        "damping_type": damping_type, "roots": (s1, s2),
        "v_t_symbolic": final_solution, "v_t_func": v_func
    }

def solve_rc_natural_response(R, C, V0):
    t = sp.symbols('t', real=True)
    v = sp.Function('v')(t)
    tau = R * C
    edo = sp.Eq(v.diff(t) + (1/tau) * v, 0)
    final_solution = V0 * sp.exp(-t / tau)
    v_func = sp.lambdify(t, final_solution, 'numpy')
    return {"edo": edo, "tau": tau, "v_t_symbolic": final_solution, "v_t_func": v_func}

# --- Funções de Análise de Resposta Forçada (Fasores) ---

def analyze_frequency_domain(type, R, L, C, f):
    omega = 2 * np.pi * f
    Z_R = R
    Z_L = 1j * omega * L
    Z_C = -1j / (omega * C) if omega * C > 0 else -1j * np.inf
    
    if type == 'RLC':
        Z_total = Z_R + Z_L + Z_C
    else: # RC
        Z_total = Z_R + Z_C
        
    return {"Z_total": Z_total, "Z_R": Z_R, "Z_L": Z_L, "Z_C": Z_C}

# --- Funções de Plot (Matplotlib) ---

def plot_natural_response(t_vals, v_vals, title, ylabel="Tensão V(t) [V]"):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(t_vals, v_vals, '#00aaff', lw=2)
    ax.set_title(title, fontsize=16); ax.set_xlabel("Tempo (s)"); ax.set_ylabel(ylabel)
    ax.grid(True, linestyle='--', alpha=0.7); ax.axhline(0, color='black', lw=0.5)
    return fig

def plot_phasor_diagram(vectors, labels, colors, title):
    fig, ax = plt.subplots(figsize=(6, 6))
    # Calcula o valor máximo para ajustar os limites do gráfico
    max_val = max(np.abs(v) for v in vectors + [sum(vectors)]) * 1.4
    if max_val == 0: max_val = 1
    ax.set_xlim(-max_val, max_val); ax.set_ylim(-max_val, max_val)
    ax.axhline(0, color='grey', lw=0.5); ax.axvline(0, color='grey', lw=0.5)

    # Plota vetores individuais da origem
    for vec, label, color in zip(vectors, labels, colors):
        ax.arrow(0, 0, vec.real, vec.imag, 
                 head_width=max_val*0.05, head_length=max_val*0.1, fc=color, ec=color, label=label, length_includes_head=True)
    
    # Plota o vetor resultante (total)
    total_vec = sum(vectors)
    ax.arrow(0, 0, total_vec.real, total_vec.imag,
             head_width=max_val*0.05, head_length=max_val*0.1, fc='yellow', ec='yellow', label='$Z_{total}$', length_includes_head=True)

    ax.set_title(title); ax.set_xlabel("Eixo Real (Ω)"); ax.set_ylabel("Eixo Imaginário (Ω)")
    ax.grid(True, linestyle='--', alpha=0.6); ax.set_aspect('equal', adjustable='box'); ax.legend()
    return fig

# --- Interface Principal (Streamlit) ---

st.set_page_config(page_title="Simulador de Circuitos", layout="wide")
st.title("⚡ Simulador de Circuitos: Análise de Resposta Natural e Forçada")

# --- Menu Lateral de Configuração ---
with st.sidebar:
    st.header("Parâmetros Gerais")
    R_val = st.slider("Resistência (R) [Ω]", 1.0, 200.0, 10.0, 0.5)
    L_val = st.slider("Indutância (L) [mH]", 1.0, 100.0, 25.0, 0.1) / 1000 # H
    C_val = st.slider("Capacitância (C) [μF]", 10.0, 1000.0, 100.0, 1.0) / 1e6 # F
    
    st.header("Condições Iniciais (Resposta Natural)")
    V0 = st.slider("Tensão Inicial Vc(0) [V]", -50.0, 50.0, 10.0, 0.5)
    I0 = st.slider("Corrente Inicial iL(0) [A]", -10.0, 10.0, 0.0, 0.1)

    st.header("Fonte CA (Resposta Forçada)")
    f_val = st.slider("Frequência (f) [Hz]", 1.0, 500.0, 60.0, 1.0)

# --- Abas Principais de Análise ---
tab_natural, tab_forced = st.tabs(["**Análise de Resposta Natural (EDO)**", "**Análise de Resposta Forçada (Fasores)**"])

# --- Análise de Resposta Natural ---
with tab_natural:
    st.header("Análise da Resposta do Circuito Sem Fonte Externa")
    tab_rlc_nat, tab_rc_nat = st.tabs(["🔌 Circuito RLC Série", "💡 Circuito RC"])

    with tab_rlc_nat:
        st.subheader("Resposta Natural do Circuito RLC")
        st.image(draw_circuit('RLC', R_val, L_val, C_val, source=False))
        rlc_analysis = solve_rlc_natural_response(R_val, L_val, C_val, V0, I0)
        
        st.markdown("##### 1. Equação Diferencial e Característica")
        st.latex(sp.latex(rlc_analysis['edo']))
        col1, col2, col3 = st.columns(3)
        alpha_val, omega0_val = float(rlc_analysis['alpha']), float(rlc_analysis['omega0'])
        col1.metric("Fator de Amort. (α)", f"{alpha_val:.2f} Np/s")
        col2.metric("Freq. Natural (ω₀)", f"{omega0_val:.2f} rad/s")
        col3.info(f"**Resposta: {rlc_analysis['damping_type']}**")
        s1_val, s2_val = rlc_analysis['roots']
        st.latex(f"s^2 + {2*alpha_val:.2f}s + {omega0_val**2:.2f} = 0 \\implies s_1={sp.latex(round(s1_val, 2))}, s_2={sp.latex(round(s2_val, 2))}")
        
        st.markdown("##### 2. Solução e Gráfico para Vc(t)")
        st.latex(sp.latex(rlc_analysis['v_t_symbolic']))
        if rlc_analysis['damping_type'] == "Subamortecida":
            omega_d_val = np.sqrt(omega0_val**2 - alpha_val**2)
            t_max = 5 * (2 * np.pi / omega_d_val if omega_d_val > 0 else 1)
        else:
            # Para crítico e superamortecido, baseia-se na raiz de decaimento mais lenta
            slowest_decay = min(abs(s.real) for s in rlc_analysis['roots'])
            t_max = 5 / slowest_decay if slowest_decay > 0 else 1
        t_vals = np.linspace(0, float(t_max), 500)
        v_vals = rlc_analysis["v_t_func"](t_vals)
        st.pyplot(plot_natural_response(t_vals, v_vals, f"Resposta {rlc_analysis['damping_type']}"))

    with tab_rc_nat:
        st.subheader("Resposta Natural do Circuito RC")
        st.image(draw_circuit('RC', R_val, L_val, C_val, source=False))
        rc_analysis = solve_rc_natural_response(R_val, C_val, V0)
        
        st.markdown("##### 1. Equação Diferencial e Constante de Tempo")
        st.latex(sp.latex(rc_analysis['edo']))
        st.metric("Constante de Tempo (τ = RC)", f"{rc_analysis['tau']:.4f} s")
        
        st.markdown("##### 2. Solução e Gráfico para Vc(t)")
        st.latex(sp.latex(rc_analysis['v_t_symbolic']))
        t_max_rc = 5 * rc_analysis['tau']
        t_vals_rc = np.linspace(0, float(t_max_rc), 500)
        v_vals_rc = rc_analysis["v_t_func"](t_vals_rc)
        st.pyplot(plot_natural_response(t_vals_rc, v_vals_rc, "Descarga do Capacitor"))

# --- Análise de Resposta Forçada ---
with tab_forced:
    st.header("Análise da Resposta em Regime Permanente Senoidal")
    tab_rlc_forced, tab_rc_forced = st.tabs(["🔌 Circuito RLC Série", "💡 Circuito RC"])

    with tab_rlc_forced:
        st.subheader("Análise Fasorial do Circuito RLC")
        st.image(draw_circuit('RLC', R_val, L_val, C_val, source=True, f=f_val))
        
        rlc_freq_analysis = analyze_frequency_domain('RLC', R_val, L_val, C_val, f_val)
        Z_total = rlc_freq_analysis['Z_total']
        
        st.markdown("##### 1. Cálculo de Impedâncias")
        col1, col2, col3 = st.columns(3)
        col1.metric("Z Resistor", f"{rlc_freq_analysis['Z_R']:.2f} Ω")
        col2.metric("Z Indutor", f"{rlc_freq_analysis['Z_L'].imag:.2f}j Ω")
        col3.metric("Z Capacitor", f"{rlc_freq_analysis['Z_C'].imag:.2f}j Ω")
        
        st.metric("Impedância Total (Z)", f"{Z_total.real:.2f} + {Z_total.imag:.2f}j Ω")
        st.metric("Módulo |Z| e Fase ∠Z", f"{np.abs(Z_total):.2f} Ω ∠ {np.rad2deg(np.angle(Z_total)):.2f}°")

        st.markdown("##### 2. Diagrama Fasorial de Impedância")
        st.pyplot(plot_phasor_diagram([complex(rlc_freq_analysis['Z_R']), rlc_freq_analysis['Z_L'], rlc_freq_analysis['Z_C']],
                                      ['$Z_R$', '$Z_L$', '$Z_C$'], ['cyan', 'magenta', 'orange'], "Fasores de Impedância (RLC)"))

    with tab_rc_forced:
        st.subheader("Análise Fasorial do Circuito RC")
        st.image(draw_circuit('RC', R_val, L_val, C_val, source=True, f=f_val))
        
        rc_freq_analysis = analyze_frequency_domain('RC', R_val, 0, C_val, f_val)
        Z_total_rc = rc_freq_analysis['Z_total']

        st.markdown("##### 1. Cálculo de Impedâncias")
        col1, col2 = st.columns(2)
        col1.metric("Z Resistor", f"{rc_freq_analysis['Z_R']:.2f} Ω")
        col2.metric("Z Capacitor", f"{rc_freq_analysis['Z_C'].imag:.2f}j Ω")

        st.metric("Impedância Total (Z)", f"{Z_total_rc.real:.2f} + {Z_total_rc.imag:.2f}j Ω")
        st.metric("Módulo |Z| e Fase ∠Z", f"{np.abs(Z_total_rc):.2f} Ω ∠ {np.rad2deg(np.angle(Z_total_rc)):.2f}°")

        st.markdown("##### 2. Diagrama Fasorial de Impedância")
        st.pyplot(plot_phasor_diagram([complex(rc_freq_analysis['Z_R']), rc_freq_analysis['Z_C']],
                                      ['$Z_R$', '$Z_C$'], ['cyan', 'orange'], "Fasores de Impedância (RC)"))
