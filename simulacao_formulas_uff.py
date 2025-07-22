#!/usr/bin/env python3
"""
Simulação de Fórmulas UFF - Eletromagnetismo
Exemplos com SymPy, coordenadas e plots
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sympy import symbols, latex, solve, simplify, diff, integrate
from sympy.vector import CoordSys3D, gradient, divergence, curl
from IPython.display import display, Math, Latex
import math

def main():
    print("🔬 SIMULAÇÃO DE FÓRMULAS UFF - ELETROMAGNETISMO")
    print("=" * 60)
    
    # Definir símbolos
    k, q, Q, r, x, y, z = symbols('k q Q r x y z')
    mu_0, I, B, E, phi = symbols('mu_0 I B E phi')
    rho, theta, phi_sph = symbols('rho theta phi')
    
    # ========================================
    # 1. LEI DE COULOMB
    # ========================================
    print("\n1️⃣ LEI DE COULOMB")
    print("-" * 30)
    
    # Fórmula
    F_coulomb = k * q * Q / (r**2)
    display(Math(f"F = {latex(F_coulomb)}"))
    
    # Exemplo numérico
    valores_coulomb = {k: 9e9, q: 1e-6, Q: 2e-6, r: 0.1}
    resultado_coulomb = F_coulomb.subs(valores_coulomb)
    display(Math(f"Exemplo: k = {valores_coulomb[k]:.1e}, q = {valores_coulomb[q]:.1e}C, Q = {valores_coulomb[Q]:.1e}C, r = {valores_coulomb[r]}m"))
    display(Math(f"F = {latex(resultado_coulomb)} \\approx {float(resultado_coulomb):.2f} N"))
    
    # ========================================
    # 2. CAMPO ELÉTRICO - COORDENADAS RETANGULARES
    # ========================================
    print("\n2️⃣ CAMPO ELÉTRICO - COORDENADAS RETANGULARES")
    print("-" * 50)
    
    # Campo elétrico em coordenadas cartesianas
    r_cart = (x**2 + y**2 + z**2)**0.5
    E_cart = k * Q / (r_cart**2)
    
    display(Math(f"E = {latex(E_cart)}"))
    display(Math(f"r = \\sqrt{{x^2 + y^2 + z^2}}"))
    
    # Exemplo 1: Campo em (1, 2, 3)
    valores_em1 = {x: 1, y: 2, z: 3, k: 9e9, Q: 1e-6}
    E_em1 = E_cart.subs(valores_em1)
    display(Math(f"Exemplo 1 - Ponto (1, 2, 3):"))
    display(Math(f"k = {valores_em1[k]:.1e}, Q = {valores_em1[Q]:.1e}C"))
    display(Math(f"E = {latex(E_em1)} \\approx {float(E_em1):.0f} N/C"))
    
    # Exemplo 2: Campo em (0.5, 0.5, 0.5)
    valores_em2 = {x: 0.5, y: 0.5, z: 0.5, k: 9e9, Q: 2e-6}
    E_em2 = E_cart.subs(valores_em2)
    display(Math(f"Exemplo 2 - Ponto (0.5, 0.5, 0.5):"))
    display(Math(f"k = {valores_em2[k]:.1e}, Q = {valores_em2[Q]:.1e}C"))
    display(Math(f"E = {latex(E_em2)} \\approx {float(E_em2):.0f} N/C"))
    
    # ========================================
    # 3. LEI DE GAUSS - EXEMPLO 1: CARGA PONTUAL
    # ========================================
    print("\n3️⃣ LEI DE GAUSS - EXEMPLO 1: CARGA PONTUAL")
    print("-" * 45)
    
    # Fluxo elétrico
    epsilon_0 = symbols('epsilon_0')
    fluxo_gauss1 = Q / epsilon_0
    
    display(Math(f"\\Phi = {latex(fluxo_gauss1)}"))
    
    # Exemplo numérico
    valores_gauss1 = {Q: 1e-6, epsilon_0: 8.85e-12}
    resultado_gauss1 = fluxo_gauss1.subs(valores_gauss1)
    display(Math(f"Exemplo: Q = {valores_gauss1[Q]:.1e}C, \\epsilon_0 = {valores_gauss1[epsilon_0]:.1e} C²/N⋅m²"))
    display(Math(f"\\Phi = {latex(resultado_gauss1)} \\approx {float(resultado_gauss1):.0f} N⋅m²/C"))
    
    # ========================================
    # 4. LEI DE GAUSS - EXEMPLO 2: ESFERA CARREGADA
    # ========================================
    print("\n4️⃣ LEI DE GAUSS - EXEMPLO 2: ESFERA CARREGADA")
    print("-" * 45)
    
    # Densidade de carga
    rho_esfera = symbols('rho_esfera')
    R = symbols('R')  # Raio da esfera
    
    # Carga total
    Q_total = (4/3) * math.pi * R**3 * rho_esfera
    
    # Fluxo
    fluxo_gauss2 = Q_total / epsilon_0
    
    display(Math(f"Q_{{total}} = \\frac{{4\\pi R^3}}{{3}} \\rho_{{esfera}}"))
    display(Math(f"\\Phi = \\frac{{Q_{{total}}}}{{\\epsilon_0}}"))
    
    # Exemplo numérico
    valores_gauss2 = {R: 0.1, rho_esfera: 1e-6, epsilon_0: 8.85e-12}
    Q_exemplo = (4/3) * math.pi * valores_gauss2[R]**3 * valores_gauss2[rho_esfera]
    fluxo_exemplo = Q_exemplo / valores_gauss2[epsilon_0]
    
    display(Math(f"Exemplo: R = {valores_gauss2[R]}m, \\rho = {valores_gauss2[rho_esfera]}C/m³"))
    display(Math(f"Q_{{total}} = {Q_exemplo:.2e} C"))
    display(Math(f"\\Phi = {fluxo_exemplo:.2e} N⋅m²/C"))
    
    # ========================================
    # 5. LEI DE BIOT-SAVART - EXEMPLO 1: FIO RETO
    # ========================================
    print("\n5️⃣ LEI DE BIOT-SAVART - EXEMPLO 1: FIO RETO")
    print("-" * 45)
    
    # Campo magnético de fio reto
    B_biot1 = mu_0 * I / (2 * math.pi * r)
    
    display(Math(f"B = \\frac{{\\mu_0 I}}{{2\\pi r}}"))
    
    # Exemplo numérico
    valores_biot1 = {mu_0: 4*math.pi*1e-7, I: 5, r: 0.05}
    resultado_biot1 = B_biot1.subs(valores_biot1)
    display(Math(f"Exemplo: \\mu_0 = {valores_biot1[mu_0]}, I = {valores_biot1[I]}A, r = {valores_biot1[r]}m"))
    display(Math(f"B = {latex(resultado_biot1)} \\approx {float(resultado_biot1):.2e} T"))
    
    # ========================================
    # 6. LEI DE BIOT-SAVART - EXEMPLO 2: ESPIRA CIRCULAR
    # ========================================
    print("\n6️⃣ LEI DE BIOT-SAVART - EXEMPLO 2: ESPIRA CIRCULAR")
    print("-" * 45)
    
    # Campo no centro da espira
    a = symbols('a')  # Raio da espira
    B_biot2 = mu_0 * I / (2 * a)
    
    display(Math(f"B = \\frac{{\\mu_0 I}}{{2a}}"))
    
    # Exemplo numérico
    valores_biot2 = {mu_0: 4*math.pi*1e-7, I: 2, a: 0.1}
    resultado_biot2 = B_biot2.subs(valores_biot2)
    display(Math(f"Exemplo: \\mu_0 = {valores_biot2[mu_0]}, I = {valores_biot2[I]}A, a = {valores_biot2[a]}m"))
    display(Math(f"B = {latex(resultado_biot2)} \\approx {float(resultado_biot2):.2e} T"))
    
    # ========================================
    # 7. LEI DE AMPÈRE - EXEMPLO 1: FIO RETO
    # ========================================
    print("\n7️⃣ LEI DE AMPÈRE - EXEMPLO 1: FIO RETO")
    print("-" * 45)
    
    # Lei de Ampère
    B_ampere1 = mu_0 * I / (2 * math.pi * r)
    
    display(Math(f"\\oint B \\cdot dl = \\mu_0 I"))
    display(Math(f"B = \\frac{{\\mu_0 I}}{{2\\pi r}}"))
    
    # Exemplo numérico
    valores_ampere1 = {mu_0: 4*math.pi*1e-7, I: 10, r: 0.02}
    resultado_ampere1 = B_ampere1.subs(valores_ampere1)
    display(Math(f"Exemplo: \\mu_0 = {valores_ampere1[mu_0]}, I = {valores_ampere1[I]}A, r = {valores_ampere1[r]}m"))
    display(Math(f"B = {latex(resultado_ampere1)} \\approx {float(resultado_ampere1):.2e} T"))
    
    # ========================================
    # 8. LEI DE AMPÈRE - EXEMPLO 2: SOLENOIDE
    # ========================================
    print("\n8️⃣ LEI DE AMPÈRE - EXEMPLO 2: SOLENOIDE")
    print("-" * 45)
    
    # Campo dentro do solenoide
    n = symbols('n')  # Número de espiras por unidade de comprimento
    B_ampere2 = mu_0 * n * I
    
    display(Math(f"B = \\mu_0 n I"))
    
    # Exemplo numérico
    valores_ampere2 = {mu_0: 4*math.pi*1e-7, n: 1000, I: 1}  # 1000 espiras/m
    resultado_ampere2 = B_ampere2.subs(valores_ampere2)
    display(Math(f"Exemplo: \\mu_0 = {valores_ampere2[mu_0]}, n = {valores_ampere2[n]} espiras/m, I = {valores_ampere2[I]}A"))
    display(Math(f"B = {latex(resultado_ampere2)} \\approx {float(resultado_ampere2):.2e} T"))
    
    # ========================================
    # 9. COORDENADAS CILÍNDRICAS
    # ========================================
    print("\n9️⃣ COORDENADAS CILÍNDRICAS")
    print("-" * 35)
    
    # Campo elétrico em coordenadas cilíndricas
    rho, phi_cyl, z_cyl = symbols('rho phi_cyl z_cyl')
    r_cyl = (rho**2 + z_cyl**2)**0.5
    E_cyl = k * Q / (r_cyl**2)
    
    display(Math(f"E = {latex(E_cyl)}"))
    display(Math(f"r = \\sqrt{{\\rho^2 + z^2}}"))
    
    # Exemplo em coordenadas cilíndricas
    valores_cyl = {rho: 2, phi_cyl: math.pi/4, z_cyl: 1, k: 9e9, Q: 1e-6}
    E_cyl_exemplo = E_cyl.subs(valores_cyl)
    display(Math(f"Exemplo: \\rho = {valores_cyl[rho]}, \\phi = {valores_cyl[phi_cyl]}, z = {valores_cyl[z_cyl]}"))
    display(Math(f"E = {latex(E_cyl_exemplo)} \\approx {float(E_cyl_exemplo):.0f} N/C"))
    
    # ========================================
    # 10. COORDENADAS ESFÉRICAS
    # ========================================
    print("\n🔟 COORDENADAS ESFÉRICAS")
    print("-" * 30)
    
    # Campo elétrico em coordenadas esféricas
    r_sph, theta_sph, phi_sph = symbols('r_sph theta_sph phi_sph')
    E_sph = k * Q / (r_sph**2)
    
    display(Math(f"E = {latex(E_sph)}"))s
    
    # Exemplo em coordenadas esféricas
    valores_sph = {r_sph: 3, theta_sph: math.pi/3, phi_sph: math.pi/6, k: 9e9, Q: 1e-6}
    E_sph_exemplo = E_sph.subs(valores_sph)
    display(Math(f"Exemplo: r = {valores_sph[r_sph]}, \\theta = {valores_sph[theta_sph]}, \\phi = {valores_sph[phi_sph]}"))
    display(Math(f"E = {latex(E_sph_exemplo)} \\approx {float(E_sph_exemplo):.0f} N/C"))
    
    # ========================================
    # 11. PLOTS 3D
    # ========================================
    print("\n📊 PLOTS 3D")
    print("-" * 15)
    
    # Plot 1: Campo Elétrico em Coordenadas Cartesianas
    fig1 = plt.figure(figsize=(15, 5))
    
    # Subplot 1: Campo Elétrico
    ax1 = fig1.add_subplot(131, projection='3d')
    x_plot = np.linspace(-2, 2, 20)
    y_plot = np.linspace(-2, 2, 20)
    z_plot = np.linspace(-2, 2, 20)
    X, Y, Z = np.meshgrid(x_plot, y_plot, z_plot)
    
    # Calcular magnitude do campo elétrico
    k_plot = 9e9
    Q_plot = 1e-6
    R_plot = np.sqrt(X**2 + Y**2 + Z**2)
    E_mag = k_plot * Q_plot / (R_plot**2 + 1e-10)
    
    # Plotar superfície de magnitude constante
    # Corrigindo: Axes3D não possui contour3D nem set_zlabel, usar plot_surface para visualização
    # Vamos plotar algumas superfícies de nível usando plot_surface para algumas fatias de Z

    levels = np.linspace(E_mag.min(), E_mag.max(), 8)
    # Seleciona alguns índices de fatias de Z para plotar superfícies
    z_indices = np.linspace(0, Z.shape[2] - 1, 4, dtype=int)
    for idx in z_indices:
        # plot_surface é um método de Axes3D, mas precisa ser importado Axes3D explicitamente
        # Além disso, plt.cm.viridis está correto, mas pode ser necessário importar cm explicitamente
        surf = ax1.plot_surface(
            X[:, :, idx], Y[:, :, idx], Z[:, :, idx],
            facecolors=plt.get_cmap('viridis')((E_mag[:, :, idx] - E_mag.min()) / (E_mag.max() - E_mag.min())),
            rstride=1, cstride=1, alpha=0.3, linewidth=0, antialiased=False
        )

    ax1.set_xlabel('X (m)')
    ax1.set_ylabel('Y (m)')
    ax1.set_zlabel('Z (m)')  # Para compatibilidade, set_zlabel existe em Axes3D do matpslotlib
    ax1.set_title('Campo Elétrico - Cartesianas')
    
    # Subplot 2: Coordenadas Cilíndricas
    ax2 = fig1.add_subplot(132, projection='3d')
    rho_plot = np.linspace(0, 2, 20)
    phi_plot = np.linspace(0, 2*np.pi, 20)
    z_plot = np.linspace(-2, 2, 20)
    RHO, PHI, Z_CYL = np.meshgrid(rho_plot, phi_plot, z_plot)
    
    # Converter para cartesianas para plot
    X_CYL = RHO * np.cos(PHI)
    Y_CYL = RHO * np.sin(PHI)
    Z_CYL_plot = Z_CYL
    
    R_CYL = np.sqrt(RHO**2 + Z_CYL**2)
    E_CYL = k_plot * Q_plot / (R_CYL**2 + 1e-10)
    
    levels_cyl = np.linspace(E_CYL.min(), E_CYL.max(), 8)
    for level in levels_cyl:
        ax2.contour3D(X_CYL, Y_CYL, Z_CYL_plot, E_CYL, levels=[level], alpha=0.3)
    
    ax2.set_xlabel('X (m)')
    ax2.set_ylabel('Y (m)')
    ax2.set_zlabel('Z (m)')
    ax2.set_title('Campo Elétrico - Cilíndricas')
    
    # Subplot 3: Coordenadas Esféricas
    ax3 = fig1.add_subplot(133, projection='3d')
    r_plot = np.linspace(0.5, 2, 20)
    theta_plot = np.linspace(0, np.pi, 20)
    phi_plot = np.linspace(0, 2*np.pi, 20)
    R_SPH, THETA, PHI_SPH = np.meshgrid(r_plot, theta_plot, phi_plot)
    
    # Converter para cartesianas para plot
    X_SPH = R_SPH * np.sin(THETA) * np.cos(PHI_SPH)
    Y_SPH = R_SPH * np.sin(THETA) * np.sin(PHI_SPH)
    Z_SPH = R_SPH * np.cos(THETA)
    
    E_SPH = k_plot * Q_plot / (R_SPH**2 + 1e-10)
    
    levels_sph = np.linspace(E_SPH.min(), E_SPH.max(), 8)
    for level in levels_sph:
        ax3.contour3D(X_SPH, Y_SPH, Z_SPH, E_SPH, levels=[level], alpha=0.3)
    
    ax3.set_xlabel('X (m)')
    ax3.set_ylabel('Y (m)')
    ax3.set_zlabel('Z (m)')
    ax3.set_title('Campo Elétrico - Esféricas')
    
    plt.tight_layout()
    plt.show()
    
    # Plot 2: Campo Magnético
    fig2 = plt.figure(figsize=(12, 6))
    
    # Subplot 1: Fio reto
    ax4 = fig2.add_subplot(121, projection='3d')
    x_wire = np.linspace(-2, 2, 20)
    y_wire = np.linspace(-2, 2, 20)
    z_wire = np.linspace(-2, 2, 20)
    X_W, Y_W, Z_W = np.meshgrid(x_wire, y_wire, z_wire)
    
    # Campo magnético de fio reto (ao longo do eixo z)
    r_wire = np.sqrt(X_W**2 + Y_W**2)
    B_wire = 4*np.pi*1e-7 * 5 / (2*np.pi * (r_wire + 1e-10))
    
    levels_wire = np.linspace(B_wire.min(), B_wire.max(), 6)
    for level in levels_wire:
        ax4.contour3D(X_W, Y_W, Z_W, B_wire, levels=[level], alpha=0.4)
    
    ax4.set_xlabel('X (m)')
    ax4.set_ylabel('Y (m)')
    ax4.set_zlabel('Z (m)')
    ax4.set_title('Campo Magnético - Fio Reto')
    
    # Subplot 2: Solenoide
    ax5 = fig2.add_subplot(122, projection='3d')
    x_sol = np.linspace(-1, 1, 15)
    y_sol = np.linspace(-1, 1, 15)
    z_sol = np.linspace(-2, 2, 20)
    X_S, Y_S, Z_S = np.meshgrid(x_sol, y_sol, z_sol)
    
    # Campo magnético uniforme do solenoide
    B_sol = 4*np.pi*1e-7 * 1000 * 1 * np.ones_like(X_S)
    
    levels_sol = np.linspace(B_sol.min(), B_sol.max(), 6)
    for level in levels_sol:
        ax5.contour3D(X_S, Y_S, Z_S, B_sol, levels=[level], alpha=0.4)
    
    ax5.set_xlabel('X (m)')
    ax5.set_ylabel('Y (m)')
    ax5.set_zlabel('Z (m)')
    ax5.set_title('Campo Magnético - Solenoide')
    
    plt.tight_layout()
    plt.show()
    
    print("\n✅ Simulação completa finalizada!")
    print("📊 Gráficos 3D gerados com sucesso")
    print("🔬 Fórmulas calculadas em diferentes coordenadas")

if __name__ == "__main__":
    try:
        main() 
    except:
        print("Erro ao importar matplotlib.pyplot ou mpl_toolkits.mplot3d")

