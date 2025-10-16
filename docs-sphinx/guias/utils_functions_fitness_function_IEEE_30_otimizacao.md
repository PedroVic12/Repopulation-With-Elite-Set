# Função de Aptidão para o Caso IEEE 30

Este documento descreve a função de aptidão específica para o sistema IEEE 30 barras, `funcao_objetivo_IEEE30`. Ela segue o [template padrão de funções de aptidão](./function_IEEE_14_contigencias_doc.md) definido no projeto.

## Visão Geral

O objetivo desta função é avaliar um cronograma de manutenção para o sistema IEEE 30, considerando a segurança da rede sob contingências. A função calcula um valor de "fitness" que representa o risco operacional (soma de violações de tensão e carregamento), que o algoritmo genético tentará minimizar.

## Customizações Específicas para o IEEE 30

Seguindo o template padrão, esta função implementa a lógica genérica de avaliação de cenários. As customizações que a tornam específica para o caso IEEE 30 são as seguintes:

### 1. Modelo da Rede Elétrica

A função inicializa o modelo de rede específico para o sistema de 30 barras:

```python
rede = RedeEletricaPandaPower("30", debug=_debug)
```

### 2. Dados do Problema

Os dados que definem o escopo do problema de otimização são carregados diretamente no arquivo:

-   **Agendamento de Manutenção (`agendamento_df`)**: Para este caso, são definidas **10 tarefas de manutenção** em diferentes ramos da rede.
    
-   **Lista de Contingências (`contingencia_df`)**: São avaliadas **3 contingências (N-1)**, envolvendo os seguintes ramos:
    -   Barra 1 a 3
    -   Barra 11 a 14
    -   Barra 14 a 17

Esses DataFrames fornecem os dados de entrada que caracterizam o desafio de otimização para o sistema IEEE 30.

### 3. Limites Operacionais

Os pesos para o cálculo das penalidades são configurados com valores padrão, que podem ser ajustados se necessário para refletir requisitos operacionais específicos deste sistema:

```python
rede.pesos["tensao"] = {"min": 100, "max": 100}
rede.pesos["loading_linhas"] = 100
```
