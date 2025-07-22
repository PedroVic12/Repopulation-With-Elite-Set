#!/usr/bin/env python3
"""
Exemplo de uso da classe FormulaManager para cálculos
"""

from make_pdf_simulados_uff import FormulaManager
from sympy import symbols, latex

def main():
    # Criar instância do gerenciador de fórmulas
    fm = FormulaManager()
    
    print("=== EXEMPLOS DE CÁLCULOS ===\n")
    
    # Exemplo 1: Lei de Coulomb
    print("1. Lei de Coulomb")
    formula_coulomb = fm.formulas_em['Lei de Coulomb']['formula']
    print(f"Fórmula: ${latex(formula_coulomb.lhs)} = {latex(formula_coulomb.rhs)}$")
    print(f"Descrição: {fm.formulas_em['Lei de Coulomb']['descricao']}")
    print(f"Unidades: {fm.formulas_em['Lei de Coulomb']['unidades']}")
    
    # Calcular exemplo numérico
    k, q1, q2, r = symbols('k q1 q2 r')
    valores = {k: 9e9, q1: 1e-6, q2: 2e-6, r: 0.1}
    resultado = formula_coulomb.subs(valores)
    print(f"Exemplo: k={valores[k]}, q1={valores[q1]}C, q2={valores[q2]}C, r={valores[r]}m")
    print(f"Resultado: F = {resultado.rhs} N\n")
    
    # Exemplo 2: Campo Elétrico
    print("2. Campo Elétrico")
    formula_em = fm.formulas_em['Campo Elétrico']['formula']
    print(f"Fórmula: ${latex(formula_em.lhs)} = {latex(formula_em.rhs)}$")
    print(f"Descrição: {fm.formulas_em['Campo Elétrico']['descricao']}")
    
    valores_em = {fm.k: 9e9, fm.Q: 1e-6, fm.r: 0.05}
    resultado_em = formula_em.subs(valores_em)
    print(f"Exemplo: k={valores_em[fm.k]}, Q={valores_em[fm.Q]}C, r={valores_em[fm.r]}m")
    print(f"Resultado: E = {resultado_em.rhs} N/C\n")
    
    # Exemplo 3: Álgebra Booleana
    print("3. Álgebra Booleana")
    print("Fórmulas:")
    formulas_bool = fm.formulas_cd['Álgebra Booleana']['formula']
    for i, formula in enumerate(formulas_bool):
        if isinstance(formula, str):
            print(f"  {i+1}. {formula}")
        else:
            print(f"  {i+1}. ${latex(formula.lhs)} = {latex(formula.rhs)}$")
    print(f"Descrição: {fm.formulas_cd['Álgebra Booleana']['descricao']}")
    print("Regras:")
    for rule in fm.formulas_cd['Álgebra Booleana']['regras']:
        print(f"  • {rule}")
    print()
    
    # Exemplo 4: Leis de De Morgan
    print("4. Leis de De Morgan")
    print("Fórmulas:")
    formulas_dm = fm.formulas_cd['Leis de De Morgan']['formula']
    for i, formula in enumerate(formulas_dm):
        print(f"  {i+1}. {formula}")
    print(f"Descrição: {fm.formulas_cd['Leis de De Morgan']['descricao']}")
    print("Regras:")
    for rule in fm.formulas_cd['Leis de De Morgan']['regras']:
        print(f"  • {rule}")
    print()
    
    # Exemplo 5: Tempo de Setup
    print("5. Tempo de Setup")
    formula_timing = fm.formulas_cd['Tempo de Setup']['formula']
    print(f"Fórmula: ${latex(formula_timing.lhs)} = {latex(formula_timing.rhs)}$")
    print(f"Descrição: {fm.formulas_cd['Tempo de Setup']['descricao']}")
    print(f"Unidades: {fm.formulas_cd['Tempo de Setup']['unidades']}")
    
    valores_timing = {fm.tclk: 10e-9, fm.tcomb: 3e-9, fm.tskew: 1e-9}
    resultado_timing = formula_timing.subs(valores_timing)
    print(f"Exemplo: tclk={valores_timing[fm.tclk]}s, tcomb={valores_timing[fm.tcomb]}s, tskew={valores_timing[fm.tskew]}s")
    print(f"Resultado: tsetup = {resultado_timing.rhs} s\n")
    
    print("=== TODAS AS FÓRMULAS DISPONÍVEIS ===")
    print("\nEletromagnetismo:")
    for nome in fm.formulas_em.keys():
        print(f"  • {nome}")
    
    print("\nCircuitos Digitais:")
    for nome in fm.formulas_cd.keys():
        print(f"  • {nome}")

if __name__ == "__main__":
    main() 