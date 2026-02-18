using Plots

println("\n" * "="^60)
println("CAMPO ELÉTRICO DE UMA CARGA PONTUAL")
println("="^60)
println("\nEquação: E = k × q / r²")
println("Onde:")
println("  k = 9 × 10⁹ N⋅m²/C² (constante de Coulomb)")
println("  q = carga (C)")
println("  r = distância (m)")
println("  E = campo elétrico (N/C)")

k = 9e9
q = 1e-6
r = 0.1:0.01:2

E = k * q ./ r .^ 2

println("\n--- Parâmetros ---")
println("k = $k N⋅m²/C²")
println("q = $(q * 1e6) μC = $q C")
println("r varia de $(first(r)) m até $(last(r)) m")

println("\n--- Alguns Resultados ---")
for i in 1:10:length(r)
    println("r = $(r[i]) m  →  E = $(round(E[i]; digits=2)) N/C")
end

plot(r, E,
    xlabel="Distância (m)",
    ylabel="Campo Elétrico (N/C)",
    title="Campo Elétrico de Carga Pontual",
    legend=false)

savefig("campo_eletrico.png")
println("\n✓ Gráfico salvo em 'campo_eletrico.png'")


println("\n" * "="^60)
println("CAMPO MAGNÉTICO DE UM FIO RETILÍNEO")
println("="^60)
println("\nEquação: B = μ₀ × I / (2π × r)")
println("Onde:")
println("  μ₀ = 4π × 10⁻⁷ H/m (permeabilidade do vácuo)")
println("  I = corrente (A)")
println("  r = distância do fio (m)")
println("  B = campo magnético (T)")

μ0 = 4π * 1e-7
I = 10
r = 0.01:0.001:0.5

B = μ0 * I ./ (2π .* r)

println("\n--- Parâmetros ---")
println("μ₀ = $(round(μ0; sigdigits=3)) H/m")
println("I = $I A")
println("r varia de $(first(r)) m até $(last(r)) m")

println("\n--- Alguns Resultados ---")
for i in 1:50:length(r)
    b_value = B[i]
    b_micro = round(b_value * 1e6; digits=2)
    println("r = $(round(r[i]; digits=4)) m  →  B = $b_micro μT")
end

plot(r, B,
    xlabel="r (m)",
    ylabel="B (T)",
    title="Campo Magnético de um Fio",
    legend=false)

savefig("campo_magnetico.png")
println("\n✓ Gráfico salvo em 'campo_magnetico.png'")


println("\n" * "="^60)
println("CALCULADORA COM FUNÇÕES MATEMÁTICAS")
println("="^60)
println("\nEquações implementadas:")
println("  1. f(x, y, z) = x² + y² + z²")
println("  2. soma(a, b) = a + b")
println("  3. mult(a, b) = a × b")

mutable struct Calculadora
end

function f(calc::Calculadora, x, y, z)
    return x^2 + y^2 + z^2
end

function soma(calc::Calculadora, a, b)
    a + b
end

function mult(calc::Calculadora, a, b)
    a * b
end

calc = Calculadora()

# println("\n--- Testando as Funções ---")
# println("\n1. f(x, y, z) = x² + y² + z²")
# x, y, z = 1, 2, 3
# resultado = f(calc, x, y, z)
# println("   f($x, $y, $z) = $x² + $y² + $z² = $resultado unidades²")

# println("\n2. soma(a, b)")
# a, b = 2, 3
# resultado = soma(calc, a, b)
# println("   soma($a, $b) = $a + $b = $resultado")

# println("\n3. mult(a, b)")
# a, b = 4, 5
# resultado = mult(calc, a, b)
# println("   mult($a, $b) = $a × $b = $resultado")

# println("\n" * "="^60)
# println("✓ Cálculos concluídos com sucesso!")
# println("="^60 * "\n")


struct LinhaTransmissao
    de::Int
    para::Int
    r_km::Float64
    x_km::Float64
    km::Float64
end

impedancia(l::LinhaTransmissao) = (l.r_km + im * l.x_km) * l.km
println("\n" * "="^60)
println("LINHA DE TRANSMISSÃO ELÉTRICA")
println("="^60)
println("\nEquação: Z = (r + jx) × km")
println("Onde:")
println("  r = resistência por km (Ω/km)")
println("  x = reatância por km (Ω/km)")
println("  km = comprimento da linha (km)")
println("  Z = impedância total (Ω)")

linha = LinhaTransmissao(1, 2, 0.5, 1.0, 100)
Z = impedancia(linha)
println("\n--- Parâmetros ---")
println("De: $(linha.de)  →  Para: $(linha.para)")
println("r = $(linha.r_km) Ω/km")
println("x = $(linha.x_km) Ω/km")
println("km = $(linha.km) km")
println("\n--- Impedância Total ---")
println("Z = $(round(Z; sigdigits=3)) Ω")
println("\n" * "="^60)
println("✓ Cálculo de impedância concluído com sucesso!")
println("="^60 * "\n")