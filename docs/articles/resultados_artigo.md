# Análise de Resultados da Simulação do Framework RCE

**Data:** 01 de Agosto de 2025

## 1. Objetivo

Este documento apresenta os resultados consolidados de uma série de 7 execuções do framework RCE (Repopulation with Elite Set). O objetivo foi avaliar a performance e a consistência do algoritmo na resolução do problema de otimização de agendamento de manutenção para a rede IEEE 14 barras, considerando múltiplas contingências e perfis de carga.

## 2. Parâmetros da Simulação

A configuração utilizada para o Algoritmo Genético foi a seguinte:

- **Número de Gerações:** 40
- **Tamanho da População:** 5
- **Taxa de Crossover:** 0.95
- **Taxa de Mutação:** 0.25
- **Número de Execuções (Repetições):** 7
- **Função Objetivo:** `funcao_objetivo_IEEE14` (minimização de violações na rede)

## 3. Resultados Consolidados

A tabela abaixo resume os resultados obtidos em cada uma das 7 execuções independentes:

| Execução | Melhor Fitness | Melhor Geração | Melhor Solução (Variáveis) | Tempo de Execução |
|:---:|:---:|:---:|:---|:---:|
| 1   | 59.43         | 37              | `[24, 2, 24, 14, 7]`        | 56.38s            |
| 2   | 65.08         | 37              | `[9, 10, 3, 28, 10]`        | 50.25s            |
| 3   | 76.53         | 23              | `[0, 4, 13, 30, 6]`         | 49.86s            |
| 4   | 65.10         | 8               | `[16, 1, 14, 6, 16]`        | 51.17s            |
| 5   | 70.60         | 24              | `[27, 27, 2, 15, 21]`       | 48.51s            |
| 6   | 64.10         | 22              | `[3, 9, 11, 3, 31]`         | 50.26s            |
| 7   | 52.51         | 0               | `[7, 31, 0, 0, 23]`         | 49.98s            |

## 4. Análise Preliminar

- **Convergência e Qualidade da Solução:** Os valores de fitness variaram entre **52.51** e **76.53**, o que é esperado para um algoritmo estocástico. A execução 7 encontrou a melhor solução (menor violação), demonstrando a capacidade do algoritmo de explorar diferentes regiões do espaço de busca. Notavelmente, a melhor solução nem sempre é encontrada na última geração, indicando que a estratégia de elitismo preserva boas soluções encontradas no início do processo.

- **Eficiência Computacional (Destaque do Artigo):** O uso da tabela hash (memoização) mostrou-se extremamente eficaz. Em cada execução, o número de chamadas à função objetivo (que executa o custoso fluxo de potência) foi da ordem de **~200**, enquanto as leituras da tabela hash chegaram a mais de **18.000**. Isso representa uma **redução de quase 99%** no número de cálculos pesados, viabilizando a análise de um grande número de cenários em um tempo computacional viável (cerca de 50 segundos por execução).

## 5. Artefatos Gerados

Para cada execução, os seguintes arquivos foram gerados na pasta `src/output/`:

- `dashboard_data_*.pkl`: Arquivo de dados contendo o logbook completo, a melhor solução e os parâmetros da execução.
- `grafico_execucao_*.html`: Gráfico interativo da evolução do fitness (mínimo, médio, máximo) ao longo das gerações.
- `results_consolidados.xlsx`: Planilha com a tabela de resultados consolidada.

Esses artefatos garantem a reprodutibilidade e permitem uma análise mais aprofundada dos resultados.
