# Repopulation-With-Elite-Set

---
#### FRAMEWORK DESENVOLVIDO PARA FINS ACADÊMICOS USANDO ALGORITMOS GENÉTICOS PARA RESOLVER PROBLEMAS DE OTIMIZAÇÃO EM REDES ELÉTRICAS, FINANCIADO POR BOLSA DE INICIAÇÃO CIENTÍFICA PELA UNIVERSIDADE FEDERAL FLUMINENSE (UFF)
---

<table>
  <tr>
    <td>
	    <img src="https://github.com/user-attachments/assets/21e2218a-3df3-4757-8234-eb59c91490c3" alt="Descrição Imagem 1">
    </td>
    <td>
	    <img src="https://github.com/user-attachments/assets/5e46cfe2-c669-42ef-9dd5-4f526a82753b" alt="Descrição Imagem 1">
	</td>
  </tr>
</table>


## Update - 16/09/25

- O projeto está sendo refatorado para a pasta `/lib` com arquitetura MVC para facilitar a manutenção do código.

- A versão estável encontra-se na pasta `/src`.

## INTRODUÇÃO

Algoritmos Evolutivos (EAs) são algoritmos de otimização global inspirados na evolução natural e biológica, como reprodução, cruzamento, mutação e seleção, simulando a "sobrevivência do mais apto". Isso os torna muito intuitivos. Eles se enquadram no termo mais amplo de Algoritmos Meta-heurísticos ou, simplesmente, Meta-heurísticas.

Vamos implementar o Algoritmo Genético (GA), e os seguintes passos básicos devem fornecer clareza para avançar:

1.  O GA começa com uma população de soluções (indivíduos) selecionadas aleatoriamente, distribuídas por todo o espaço de busca, em vez de um único ponto de partida, como em algoritmos de busca local (ex: Hill Climbing) ou baseados em gradiente (ex: Gradient Descent).

2.  Os valores de aptidão (fitness) de cada indivíduo são então calculados.
3.  Os melhores indivíduos (os mais aptos) são selecionados usando uma estratégia baseada no seu valor de aptidão (“sobrevivência do mais apto”).
4.  Indivíduos selecionados produzem descendentes (filhos) ao final de cada geração, transmitindo seus genes. O processo é conhecido como Reprodução, Cruzamento ou Recombinação.
5.  Os descendentes sofrem mutações aleatórias (com base numa probabilidade), de forma semelhante ao que ocorre na natureza.

6.  Os descendentes da geração anterior tornam-se a população da próxima geração.
7.  O processo repete-se por um número definido de gerações (iterações).
8.  O indivíduo mais apto de todas as gerações é a solução ótima encontrada.
    
   
## EXEMPLO DE USO COM O SIN DE 45 BARRAS (ONS) - REGIÃO RJ/SP
---

Uso com 20 gerações, mutação e crossover de 80%, com demandas de contingências leve, média e pesada.

<img width="1133" height="621" alt="image" src="https://github.com/user-attachments/assets/c055622a-88ca-4e12-b9bd-bf815c577b22" />

Este script utiliza um Algoritmo Genético para otimizar o agendamento de manutenções em linhas de transmissão de um sistema elétrico de potência (o SIN 45, um modelo com 45 barras).

---


Na pasta partilhada, existem três ficheiros Jupyter Notebook que podem ser abertos diretamente no Google Colab. Para isso, o utilizador deverá seguir os seguintes passos:

1.  Crie um ficheiro chamado `params.json` para configurar os parâmetros do AG:

```python
array_decisions =  [14,15,14,18,15]

params = {
    "ARRAY_VAR": array_decisions,
    'LIMITE_VAR': [0, 31],

    'NUM_GENERATIONS': 100,
    'CROSSOVER': 0.8,
    'MUTACAO': 0.85,

    'POP_SIZE': 10,
    'IND_SIZE': 5,

    'RCE_REPOPULATION_GENERATIONS': 20,
    'NUM_VAR_DIFERENTES': 1,
    'PORCENTAGEM': 0.3,
    'DELTA_MIN': 0.05
  }
```

2.  Adapte a função objetivo e as variáveis de decisão para o seu problema. Crie um array de valores e uma função em Python que represente o problema. O **Código 1** ilustra a definição de um indivíduo (`ind1`) e uma função objetivo (`evaluate`).

**Código 1: Exemplo de indivíduo e função objetivo**
```python
ind1 = [1,2,3,4,5,6,7,8,9,10]  # Exemplo de indivíduo de tamanho 10

def evaluate(individual):
	"""Função objetivo do problema."""
	a = sum(individual)
	b = len(individual)
	return a / b
```

3.  O **Código 2** ilustra o funcionamento ao instanciar os objetos do framework. Neste exemplo, são utilizados o indivíduo `ind1` e a função `evaluate`. Ao executar a função `run`, o utilizador escolhe se deseja usar a estratégia RCE. A função retorna a população final, o melhor indivíduo e gera um gráfico com os resultados.

**Código 2: Código `main` para execução do framework**

```python
# Import RCE Framework
from AlgEvolutivoRCE.Setup import Setup, params
from AlgEvolutivoRCE.alg_evolutivo_rce import AlgoritimoEvolutivoRCE
from AlgEvolutivoRCE.Dashboard import DashboardApp

# Import functions benchmark
from utils.functions_fitness.functions_benchmarking import rosenbrock_benchmark

if __name__ == "__main__":

    # Instanciando os Objetos
    setup = Setup(params, fitness_function=funcao_objetivo_IEEE14)
    alg = AlgoritimoEvolutivoRCE(setup, DEBUG=False)

    # Loop do Algoritmo Evolutivo
    pop_with_repopulation, logbook_with_repopulation, best_variables = alg.run(
        RCE=False,
    )

    print("\n\nEvolução concluída - 100%")

    # Resultados
    x, y, z, fig = alg.dashboard.visualize(
        logbook_with_repopulation, pop_with_repopulation,
    )
```

4.  Para obter resultados e gráficos diferentes, modifique os parâmetros no ficheiro `params.json`, guarde e execute novamente.

5.  É possível baixar a população final gerada em formato `.xlsx`.

6.  A versão frontend dos resultados está localizada em:

    `/src/DashboardApp/dashboard_RCE_APP.py`

7.  Execute o ficheiro do frontend:

```bash
streamlit run dashboard_RCE_APP.py
```

8.  A versão atual está em desenvolvimento desde 10/04/2025 e continua a receber melhorias, incluindo contribuições para construir uma interface em Streamlit e programação funcional que suporte múltiplas execuções com tabelas e gráficos dos resultados do algoritmo.


### **Dicas**:

1.  Aumente a **Mutação** para maior diversidade entre os valores.

2.  Aumente a **PORCENTAGEM** para aumentar significativamente a quantidade de indivíduos no conjunto Elite (Critério 1).

3.  Altere **RCE_REPOPULATION_GENERATIONS** para obter mais ou menos aplicações da Estratégia de Diversificação RCE.

***Com valores altos de Mutação, Crossover e Porcentagem, é mais provável que atinja valores próximos do ótimo global (0,0 na função Rastrigin).***

---
# Documentação da Classe `RedeEletricaPandaPower` e o seu uso na `funcao_objetivo_IEEE14`
---


![image](https://github.com/user-attachments/assets/1291f753-d5c8-44b5-8cc2-460b1a6bd5ca)

**Simulador de Redes Elétricas: Um software para simular o comportamento da rede em diferentes cenários, prevendo falhas e otimizando o fluxo de energia.**

Esta classe representa uma rede elétrica usando a biblioteca Pandapower. Ela fornece funcionalidades para carregar redes padrão, validar dados de agendamento e contingência, calcular violações de fitness, ajustar cargas, desligar/religar elementos da rede e executar o fluxo de carga.

**Exemplo de simulação da Rede Elétrica IEEE 14 barras com PandaPower**
<table>
  <tr>
    <td>
	<img src="https://github.com/PedroVic12/Repopulation-With-Elite-Set/blob/main/src/assets/newplot.png" />
    </td>
    <td>
	  <img src="https://icseg.iti.illinois.edu/files/2013/10/WSCC14.png" />
  </tr>
</table>

A não convergência do fluxo de potência é um problema clássico e esperado, especialmente ao simular múltiplas falhas na rede (N-2), que é o que o código faz (uma manutenção + uma contingência).

**Por que não converge?**

Isso geralmente acontece quando um cenário de operação (um agendamento + uma contingência) leva a uma condição fisicamente instável ou impossível na rede, como:

*   **Colapso de Tensão:** As tensões em algumas barras caem para níveis tão baixos que o sistema "apaga".
*   **Sobrecargas Extremas:** Linhas ou transformadores sobrecarregados a níveis absurdos.
*   **Ilhamento:** A rede divide-se em "ilhas" e uma delas fica sem geração própria para se sustentar.


## Classe `RedeEletricaPandaPower`

### Atributos

*   `net`: Objeto Pandapower que representa a rede elétrica.
*   `debug`: Flag para ativar ou desativar o modo de depuração.
*   `console`: Objeto Logger para registar mensagens.
*   `mapeamento_ramos`: Dicionário que mapeia pares de barramentos para índices de linhas e transformadores.
*   `pesos`: Dicionário que define os pesos para as violações de fitness.
*   `agendamento`: DataFrame que armazena os dados de agendamento.
*   `contingencia`: DataFrame que armazena os dados de contingência.

### Métodos

*   `carregar_redes_padrao()`: Carrega uma rede padrão do Pandapower.
*   `criar_mapeamento_ramos()`: Cria um mapeamento de ramos para facilitar o acesso aos elementos.
*   `validar_dados()`: Valida os dados de agendamento e contingência.
*   `hashtableindex()`: Calcula o índice da tabela hash para um cenário.
*   `log()`: Regista uma mensagem.
*   `show_status()`: Exibe o estado atual da rede.
*   `calcular_violacoes_fitness()`: Calcula as violações de tensão e carregamento.
*   `calcular_perfil()`: Determina o perfil de carregamento (leve, médio, pesado).
*   `avalia_cenarios()`: Gera uma matriz de cenários de operação.
*   `executar_fluxo_de_carga()`: Executa o fluxo de carga na rede.
*   `ajustar_cargas()`: Ajusta as cargas da rede conforme o perfil.
*   `desligar_elementos_agendamento()`: Desliga elementos com base no agendamento.
*   `desligar_contingencia()`: Desliga um elemento para simular uma contingência.
*   `desligar_elementos()`: Desliga os elementos especificados.
*   `religar_todos_os_ramos_agendamento()`: Religa todos os ramos da rede.
*   `imprimir_resultados()`: Imprime e guarda os resultados do fluxo de carga.
*   `calcular_potencia_aparente_trafos()`: Calcula a potência aparente nos transformadores.
*   `calcular_potencia_aparente_linhas()`: Calcula a potência aparente nas linhas.


## Uso na `funcao_objetivo_IEEE14`

A função `funcao_objetivo_IEEE14` usa a classe `RedeEletricaPandaPower` para simular e avaliar o desempenho de um agendamento de desligamentos na rede IEEE 14 barras.

O processo resume-se a:

1.  **Inicialização:** É criada uma instância da classe `RedeEletricaPandaPower`, carregando a rede IEEE 14 barras.
2.  **Configuração:** São definidos os pesos para as violações de fitness e carregados os dados de agendamento e contingência.
3.  **Avaliação de Cenários:** A função `avalia_cenarios` é utilizada para gerar uma matriz de cenários, considerando os horários de início e duração dos desligamentos e os perfis de carregamento.
4.  **Simulação:** Para cada cenário, o fluxo de carga é executado com `executar_fluxo_de_carga`. As cargas são ajustadas e os elementos da rede são desligados/religados conforme o cenário.
5.  **Cálculo de Fitness:** As violações são calculadas com `calcular_violacoes_fitness`, e o fitness do cenário é determinado com base nos pesos atribuídos.
6.  **Agregação de Resultados:** Os valores de fitness de todos os cenários são somados para obter o fitness final do agendamento.


## 👨‍💻 Desenvolvedor

**Pedro Victor Rodrigues Veras**

## 📄 Licença

Projeto educacional desenvolvido para UFF e PIBIC.

## 📚 Recursos Adicionais

- [Next.js Documentation](https://nextjs.org/docs)


---

**Data de Criação**: 20 de Outubro de 2025
**Versão**: 5.1.2
**Ultimas atualizações**:
- RCE Lancher
- Pyintaller com instalar.bat
- AG - Análise de Contigencaias + FLuxPlot com Pandapower e Pyside6
- Dashboard Streamlit com pastas /outputs com correções no lancher
  

