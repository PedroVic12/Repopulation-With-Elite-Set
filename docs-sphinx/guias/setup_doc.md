# Configuração do Algoritmo (`Setup.py`)

O arquivo `Setup.py` é fundamental para configurar o ambiente do algoritmo genético. A classe `Setup` é responsável por inicializar todos os parâmetros, operadores e a estrutura de dados necessários para a execução da otimização com a biblioteca `DEAP`.

## Classe `Setup`

### `__init__(self, params, fitness_function, tamanho_hash=0)`

O construtor da classe `Setup` recebe os parâmetros da simulação e a função de fitness a ser utilizada.

-   **`params`**: Um dicionário contendo todos os parâmetros do algoritmo, como:
    -   `POP_SIZE`: Tamanho da população.
    -   `NUM_GENERATIONS`: Número de gerações.
    -   `CROSSOVER`: Taxa de crossover.
    -   `MUTACAO`: Taxa de mutação.
    -   `IND_SIZE`: Tamanho do indivíduo (número de variáveis de decisão).
    -   `ARRAY_VAR`: Valores iniciais para as variáveis de decisão.
    -   `LIMITE_VAR`: Limites inferior e superior para as variáveis de decisão.
-   **`fitness_function`**: A função objetivo que o algoritmo tentará minimizar.
-   **`tamanho_hash`**: O tamanho da tabela hash para armazenar resultados de cenários já calculados.



### Funcionalidades

-   **Criação de Indivíduos e População**: Define a estrutura de um "indivíduo" (uma lista de variáveis de decisão) e de uma "população" (uma coleção de indivíduos).
-   **Registro de Operadores Genéticos**:
    -   `toolbox.register("mate", ...)`: Registra o operador de **crossover** (cruzamento), que combina dois indivíduos para gerar descendentes.
    -   `toolbox.register("mutate", ...)`: Registra o operador de **mutação**, que introduz pequenas alterações aleatórias nos indivíduos.
    -   `toolbox.register("select", ...)`: Registra o método de **seleção** (ex: torneio), que escolhe os indivíduos que irão para a próxima geração.
    -   `toolbox.register("evaluate", ...)`: Registra a **função de avaliação** (fitness), que mede a qualidade de cada indivíduo.
-   **Controle de Limites (`checkBounds`)**: Utiliza um decorador para garantir que as variáveis de decisão dos indivíduos permaneçam dentro dos limites definidos após as operações de crossover e mutação.
-   **Tabela Hash**: Inicializa uma tabela hash (se `tamanho_hash > 0`) para armazenar os resultados de fitness de cenários já avaliados, evitando recálculos desnecessários.

