# Função de Aptidão para o Caso IEEE 57

Este documento descreve a função de aptidão específica para o sistema IEEE 57 barras, `funcao_objetivo_IEEE57`. A implementação segue o [template padrão de funções de aptidão](./function_IEEE_14_contigencias_doc.md) definido no projeto.

## Visão Geral

Assim como as outras funções de aptidão, o objetivo da `funcao_objetivo_IEEE57` é avaliar um cronograma de manutenção, desta vez para o sistema IEEE 57. A função calcula um valor de "fitness" que quantifica o risco operacional (violações de tensão e carregamento) para que o algoritmo genético possa encontrar a solução ótima que minimize este risco.

## Customizações Específicas para o IEEE 57

Esta função utiliza a mesma lógica genérica de avaliação de cenários e contingências do template. As particularidades que a definem para o caso IEEE 57 são as seguintes:

### 1. Modelo da Rede Elétrica

A função inicializa o modelo de rede específico para o sistema de 57 barras, que é um sistema de maior porte e complexidade:

```python
rede = RedeEletricaPandaPower("57", debug=_debug)
```

### 2. Dados do Problema

Os dados que definem o escopo do problema de otimização para este sistema são:

-   **Agendamento de Manutenção (`agendamento_df`)**: Para este caso, são definidas **10 tarefas de manutenção** em diferentes ramos da rede, similar ao caso de 30 barras, mas em um sistema com mais componentes.
    
-   **Lista de Contingências (`contingencia_df`)**: São avaliadas **3 contingências (N-1)**, envolvendo os seguintes ramos críticos para a operação do sistema IEEE 57:
    -   Barra 1 a 2
    -   Barra 8 a 9
    -   Barra 43 a 44

### 3. Limites Operacionais

Os pesos para o cálculo das penalidades são configurados com valores padrão. Para um estudo mais aprofundado do sistema 57, estes valores poderiam ser ajustados para refletir requisitos operacionais mais específicos.

```python
rede.pesos["tensao"] = {"min": 100, "max": 100}
rede.pesos["loading_linhas"] = 100
```
