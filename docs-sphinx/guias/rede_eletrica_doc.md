# Modelo da Rede Elétrica (`rede_eletrica.py`)

O arquivo `rede_eletrica.py` define a classe `RedeEletricaPandaPower`, que é responsável por modelar e simular sistemas de energia elétrica usando a biblioteca `pandapower`.

## Classe `RedeEletricaPandaPower`

Esta classe encapsula a rede elétrica, permitindo a manipulação de seus componentes e a execução de simulações de fluxo de potência.

### `__init__(self, network_name="", debug=False, ...)`

O construtor carrega um caso de rede elétrica da biblioteca `pandapower` (ex: '14' para o sistema IEEE 14 barras) ou cria uma rede vazia.

-   **`network_name`**: O nome do caso da rede a ser carregada.
-   **`debug`**: Ativa mensagens de depuração.

### Funcionalidades Principais

-   **Manipulação da Rede**:
    -   `desligar_elementos_agendamento(estados)`: Desliga linhas ou transformadores com base em um vetor de estados.
    -   `desligar_contingencia(ramo)`: Desliga um ramo específico para simular uma contingência.
    -   `religar_todos_os_ramos_agendamento()`: Restaura todos os ramos ao estado de serviço.
    -   `ajustar_cargas(perfil)`: Ajusta os níveis de carga da rede para simular diferentes perfis de demanda (leve, médio, pesado).

-   **Simulação**:
    -   `executar_fluxo_de_potencia()`: Executa a simulação de fluxo de potência usando o método Newton-Raphson. Retorna `True` se a simulação convergir.

-   **Avaliação de Fitness**:
    -   `calcular_violacoes_fitness()`: Após uma simulação, este método calcula as violações de tensão nos barramentos e de carregamento nas linhas e transformadores. As violações são ponderadas por pesos definidos para calcular um valor de "fitness" que representa o quão "ruim" é o estado atual da rede. Quanto menor o fitness, melhor.

-   **Hashing de Cenários**:
    -   `hashtableindex(...)`: Gera uma chave única (hash) para um cenário específico, definido pelo perfil de carga, contingência e estado dos ramos. Isso permite armazenar e reutilizar os resultados de simulações já calculadas, otimizando drasticamente o tempo de execução.
