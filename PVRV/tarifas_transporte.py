from datetime import datetime

preco_metro = 6.90
preco_barcas = 4.50
salario_atual = 700

data_atual = datetime.today()
data_inicio_estagio = datetime(2025, 6, 17)

# Calcula o número de dias desde o início do estágio até hoje
dias_passados = (data_atual - data_inicio_estagio).days

# Considerando 2 dias por semana, vamos calcular quantas semanas se passaram
dias_trabalho = 7

# Custo diário (ida e volta, 2 meios de transporte)
custo_diario = 2 * (preco_metro + preco_barcas)

# Gasto total
gasto_total = dias_trabalho * custo_diario

print(f"Dias desde o início do estágio: {dias_passados} dias")
print(f"Gasto total com transporte: R$ {gasto_total:.2f}")


def porcentual_gasto_salario(gasto, salario):
    """Calcula o percentual do gasto em relação ao salário."""
    return (gasto / salario) * 100

# Calcula o percentual do gasto em relação ao salário
percentual_gasto = porcentual_gasto_salario(gasto_total, salario_atual)
print(f"Percentual do gasto com transporte em relação ao salário: {percentual_gasto:.2f}%")
