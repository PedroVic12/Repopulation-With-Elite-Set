# Função Objetivo para o Caso IEEE 14 (`function_IEEE_14_contigencias.py`)

Este arquivo define a função objetivo específica para o problema de otimização de agendamento de manutenções no sistema IEEE 14 barras, considerando contingências.

## Função `funcao_objetivo_IEEE14`

Esta é a função que o algoritmo genético tentará minimizar. Ela recebe um `individuo` (que representa uma solução candidata, ou seja, um conjunto de horários de início para as manutenções) e um objeto `setupobj`.

### Como Usar

Para utilizar esta função, você deve passá-la como argumento para a classe `Setup` ao inicializar o seu problema de otimização.

```python
from AlgEvolutivoRCE_backup.Setup import Setup
from utils.functions_fitness.function_IEEE_14_contigencias import funcao_objetivo_IEEE14, get_hash_table_size

# Carregue seus parâmetros
params = {...}

# Crie o objeto Setup
setup = Setup(
    params,
    fitness_function=funcao_objetivo_IEEE14,
    tamanho_hash=get_hash_table_size()
)

# Agora, o objeto 'setup' está pronto para ser usado pelo AlgoritimoEvolutivoRCE
```

### O que a Função Faz?

1.  **Recebe um Indivíduo**: O `individuo` é uma lista de números que representam os horários de início para cada tarefa de manutenção agendada.
2.  **Cria o Modelo da Rede**: Instancia a `RedeEletricaPandaPower` para o caso IEEE 14.
3.  **Define o Agendamento**: Atualiza o DataFrame de agendamento com os horários do `individuo`.
4.  **Avalia Cenários**:
    -   Gera uma matriz de cenários que combina diferentes perfis de carga (leve, médio, pesado) com os estados de desligamento dos ramos da rede em cada hora.
    -   Para cada cenário, simula uma lista de contingências (desligamento de outros ramos).
5.  **Calcula o Fitness**:
    -   Para cada combinação de cenário e contingência, executa um fluxo de potência.
    -   Calcula as violações de tensão e carregamento.
    -   Soma todas as violações (ponderadas) para obter o valor de fitness total do agendamento.
6.  **Usa Tabela Hash**: Antes de calcular o fitness de um cenário, verifica se ele já foi calculado e está na tabela hash (fornecida pelo `setupobj`). Se sim, reutiliza o resultado; se não, calcula e armazena o resultado na tabela.
7.  **Retorna o Fitness**: O valor final, que é a soma das violações de todos os cenários, é retornado. O objetivo do algoritmo é encontrar um `individuo` que minimize este valor.
