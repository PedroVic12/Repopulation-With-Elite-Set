# Função de Aptidão para o Caso IEEE 118

Este documento descreve a função de aptidão específica para o sistema IEEE 118 barras, `funcao_objetivo_IEEE118`. A implementação segue o [template padrão de funções de aptidão](./function_IEEE_14_contigencias_doc.md) definido no projeto, mas introduz uma refatoração na sua estrutura.

## Visão Geral

O objetivo da `funcao_objetivo_IEEE118` é avaliar um cronograma de manutenção para o sistema IEEE 118, um sistema de grande porte usado para testes de metodologias de otimização. A função calcula o risco operacional (soma de violações) para que o algoritmo genético possa encontrar um agendamento seguro e eficiente.

## Customizações Específicas para o IEEE 118

As particularidades que definem esta função para o caso IEEE 118 são as seguintes:

### 1. Modelo da Rede Elétrica

A função inicializa o modelo de rede para o sistema de 118 barras:

```python
rede = RedeEletricaPandaPower("118", debug=False)
```

### 2. Dados do Problema

Os dados que definem o escopo do problema de otimização são:

-   **Agendamento de Manutenção (`agendamento_df`)**: Para este caso, são definidas **10 tarefas de manutenção** em diferentes ramos da rede.
    
-   **Lista de Contingências (`contingencia_df`)**: São avaliadas **3 contingências (N-1)**, envolvendo os seguintes ramos:
    -   Barra 48 a 49
    -   Barra 10 a 11
    -   Barra 16 a 17

### 3. Estrutura Refatorada

Uma melhoria notável neste arquivo é a separação da lógica de cálculo. A função `analise_contigencias_SEP` foi movida para o topo do arquivo, tornando-a uma função mais genérica e reutilizável. 

A função principal foi dividida em duas:
-   `calcular_fitness_detalhado_IEEE118`: Esta função executa a lógica principal de avaliação e retorna um dicionário detalhado com os resultados (DataFrames de fitness, variáveis, etc.).
-   `funcao_objetivo_IEEE118`: Atua como um "wrapper" (invólucro). Ela chama `calcular_fitness_detalhado_IEEE118` e retorna apenas o valor numérico do fitness, que é o formato esperado pelo otimizador do framework.

Essa refatoração melhora a organização do código e a separação de responsabilidades.
