# Estrutura da Função de Aptidão para Análise de Contingências

Este documento descreve o padrão e a estrutura de uma **função de aptidão (ou função objetivo)**, usando o arquivo `function_IEEE_14_contigencias.py` como exemplo. O objetivo é que este guia sirva como um template para a criação de novas funções de aptidão para outros sistemas elétricos (como IEEE 30, 57 ou 118), destacando as partes do código que são genéricas e as que precisam de customização.

## O Papel da Função de Aptidão

A função de aptidão é o componente que avalia a qualidade de uma solução (indivíduo) proposta pelo Algoritmo Genético. No contexto deste projeto, ela recebe um **agendamento de manutenções** e retorna um **valor de fitness**, que representa o quão segura ou arriscada é aquela programação. O objetivo do algoritmo é minimizar este valor.

## Estrutura Genérica da Função

Toda função de aptidão neste framework segue um fluxo de execução padrão:

1.  **Recebe um Indivíduo**: A função aceita um `individuo` (uma lista de horários de início) e o objeto `setupobj` (que contém a tabela hash e outros parâmetros).
2.  **Cria o Modelo da Rede**: Instancia um objeto `RedeEletricaPandaPower` para o sistema elétrico em questão.
3.  **Define o Agendamento**: Atualiza a tabela de agendamentos com os horários do `individuo`.
4.  **Avalia Cenários e Contingências**: Gera uma matriz de cenários (combinações de carga e manutenções) e, para cada um, simula uma lista de contingências (falhas N-1).
5.  **Calcula o Fitness**: Executa o fluxo de potência para cada contingência, calcula as violações (tensão, carregamento) e soma tudo para obter o fitness final.
6.  **Usa Tabela Hash**: Otimiza o processo verificando se um cenário já foi calculado antes de executar uma nova simulação.

## Como Adaptar para um Novo Sistema Elétrico (Ex: IEEE 30)

Para criar uma função de aptidão para um novo sistema, você não precisa reescrever a lógica principal. Basta focar em três áreas de customização, que são os **pontos de entrada de dados específicos do problema**.

### 1. Modelo da Rede Elétrica

A primeira etapa é carregar o modelo da rede correto. A linha que faz isso é:

```python
# No caso IEEE 14:
rede = RedeEletricaPandaPower("14", debug=False)
```

-   **Ação para um novo sistema**: Para o IEEE 30, por exemplo, você precisaria garantir que a classe `RedeEletricaPandaPower` consegue carregar este novo sistema. A chamada seria algo como `rede = RedeEletricaPandaPower("30", debug=False)`.

### 2. Dados do Problema: Agendamentos e Contingências

Esta é a principal área de customização. Os DataFrames `agendamento_df` e `contingencia_df` definem o escopo do problema de otimização para um sistema específico.

```python
# Exemplo para o IEEE 14
agendamento_df = pd.DataFrame([
    {"ramo": [1, 4], "inicio": "14:00", "duracao": 6 ,"prioridade": 4},
    # ... outras manutenções
])

contingencia_df = pd.DataFrame([
    {"contingencia":1,  "from":2 , "to": 3},
    # ... outras contingências
])
```

-   **Ação para um novo sistema**: Para o IEEE 30, você deve criar novos DataFrames que contenham:
    -   `agendamento_df`: A lista de ramos (linhas de transmissão) que precisam de manutenção, com suas durações e prioridades, específicas para o estudo do caso IEEE 30.
    -   `contingencia_df`: A lista de falhas N-1 (ramos que serão desligados para simular contingências) que são consideradas críticas para a segurança do sistema IEEE 30.

### 3. Limites Operacionais (Pesos)

Os pesos e limites definem o que é considerado uma violação. Embora possam ser padronizados, eles podem variar dependendo das características de cada sistema.

```python
# Exemplo para o IEEE 14
rede.pesos["tensao"] = {"min": 100, "max": 100}
rede.pesos["loading_linhas"] = 100
```

-   **Ação para um novo sistema**: Verifique se os limites de tensão (geralmente entre 0.95 e 1.05 p.u.) e o carregamento máximo das linhas (geralmente 100%) são adequados para o novo sistema em estudo. Ajuste os valores em `rede.pesos` se necessário.

## Exemplo de Uso (Genérico)

A forma de usar a nova função de aptidão com o framework permanece a mesma, o que demonstra a modularidade do design. Você apenas precisa importar a função correta.

```python
# Supondo que você criou uma nova função para o IEEE 30
from utils.functions_fitness.function_IEEE_30_contigencias import funcao_objetivo_IEEE30, get_hash_table_size_30

# Carregue os parâmetros do AG
params = {...}

# Crie o objeto Setup, injetando a nova função de aptidão
setup = Setup(
    params,
    fitness_function=funcao_objetivo_IEEE30,
    tamanho_hash=get_hash_table_size_30()
)

# O objeto 'setup' está pronto para ser usado pelo AlgoritimoEvolutivoRCE
```