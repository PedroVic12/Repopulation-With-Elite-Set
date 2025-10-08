# Algoritmo Evolutivo RCE (`alg_evolutivo_rce.py`)

O `alg_evolutivo_rce.py` é o coração do framework de otimização. Ele implementa o algoritmo genético com a estratégia de Repopulation-with-Elite-Set (RCE).

## Classe `AlgoritimoEvolutivoRCE`

Esta classe encapsula toda a lógica do algoritmo evolutivo.

### `__init__(self, setup, DEBUG=True)`

O construtor inicializa o algoritmo com as configurações fornecidas pelo objeto `Setup`.

-   **`setup`**: Uma instância da classe `Setup` que contém todos os parâmetros para a execução do algoritmo.
-   **`DEBUG`**: Um booleano para ativar ou desativar mensagens de depuração.

### Principais Métodos

-   **`run(self, RCE=False, num_pop=0)`**: O método principal que executa o loop do algoritmo genético por um número de gerações definido no `setup`.
    -   **`RCE`**: Booleano que ativa a estratégia de Repopulation-with-Elite-Set.
-   **`aplicar_RCE(self, generation, current_population)`**: Aplica a estratégia RCE, que consiste em substituir uma parte da população por indivíduos de uma "elite" e indivíduos aleatórios para aumentar a diversidade.
-   **`criterios_RCE(self, population)`**: Seleciona os indivíduos que farão parte do conjunto de elite com base em critérios de fitness e diversidade.
-   **`elitismoSimples(self, pop)`**: Garante que o melhor indivíduo de uma geração seja mantido na próxima.
-   **`registrarDados(self, generation)`**: Coleta e armazena estatísticas sobre a população em cada geração, como fitness mínimo, máximo e médio.

## Como Funciona

1.  **Inicialização**: A população inicial é criada com base nos parâmetros definidos no objeto `Setup`.
2.  **Loop Evolutivo**: Para cada geração:
    1.  **Seleção**: Indivíduos são selecionados para reprodução (torneio).
    2.  **Crossover**: Os indivíduos selecionados são cruzados para gerar novos descendentes.
    3.  **Mutação**: Uma pequena alteração aleatória é aplicada aos descendentes.
    4.  **Avaliação**: O fitness de cada novo indivíduo é calculado usando a função objetivo.
    5.  **RCE (se ativado)**: Em gerações específicas, a população é parcialmente substituída para introduzir diversidade e evitar a convergência prematura.
    6.  **Elitismo**: O melhor indivíduo é preservado.
3.  **Finalização**: Ao final de todas as gerações, o algoritmo retorna a população final, o logbook com as estatísticas e o melhor indivíduo encontrado.
