import math


def calcular_numero_clientes(montante, valor_venda, taxa_juros, tempo):
    """
    Calcula o número mínimo de clientes para alcançar um rendimento desejado com juros compostos.

    Argumentos:
      montante: Valor final desejado (rendimento).
      valor_venda: Valor inicial de cada venda.
      taxa_juros: Taxa de juros compostos anual.
      tempo: Número de meses.

    Retorna:
      Número mínimo de clientes.
    """

    taxa_por_periodo = taxa_juros / 12 / 100
    numero_clientes = math.log(montante / valor_venda) / math.log(1 + taxa_por_periodo)
    return math.ceil(numero_clientes)


def gerar_grafico(montante_minimo, montante_maximo, valor_venda, taxa_juros, tempo):
    """
    Gera um gráfico mostrando o número de clientes necessário para alcançar diferentes rendimentos.

    Argumentos:
      montante_minimo: Valor mínimo do rendimento.
      montante_maximo: Valor máximo do rendimento.
      valor_venda: Valor inicial de cada venda.
      taxa_juros: Taxa de juros compostos anual.
      tempo: Número de meses.

    Retorna:
      None.
    """

    import matplotlib.pyplot as plt

    montantes = list(range(montante_minimo, montante_maximo + 1))
    numero_clientes = [
        calcular_numero_clientes(montante, valor_venda, taxa_juros, tempo)
        for montante in montantes
    ]

    plt.plot(montantes, numero_clientes)
    plt.xlabel("Rendimento Desejado (R$)")
    plt.ylabel("Número Mínimo de Clientes")
    plt.show()


def jurosCompostos(VP, i, n):
    return VP * (1 + i) ** n


def jurosSimples(VP, i, n):
    return VP * (1 + i * n)


anos = list(range(15))

VP = 100
i = 0.12

VF_compostos = [jurosCompostos(VP, i, n) for n in anos]
VF_simples = [jurosSimples(VP, i, n) for n in anos]

print(VF_compostos)
print(VF_simples)


montante_desejado = 2600
salario_minimo = 1500
valor_venda = 450
taxa_juros = 0.12
tempo = 12
numClientes = 5
cal_vendas = numClientes * valor_venda
