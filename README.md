# Repopulation-With-Elite-Set
 
---
#### FRAMEWORK DESENVOLVIDO PARA FINS ACADEMICOS USANDO ALGORITIMOS GENÉTICOS PARA RESOLVER PROBLEMAS DE OTIMIZAÇÃO EM REDES ELÉTRICAS POR BOLSA CIENTÍFICA PELA UNIVERSIDADE FEDERAL FLUMINENSE (UFF) 
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

- O projeto esta sendo refatorado para a pasta /lib com arquitetura MVC com facil manutenção de código.

- Versão estavél na pasta /src

## INTRODUÇÃO

EAs são problemas de algoritmos de otimização global inspirados na evolução natural/biológica por seleção natural, como reprodução/recombinação/cruzamento, mutação e seleção, semelhantes à sobrevivência do mais apto na vida real. Isso os torna muito intuitivos de entender. Eles se enquadram no termo mais amplo de Algoritmos Metaheurísticos ou simplesmente Metaheurísticas .

Vamos implementar o Algoritmo Genético e esperamos que os seguintes passos básicos forneçam clareza suficiente para avançar:

1) O GA começa inicialmente com soluções selecionadas aleatoriamente (ou indivíduos , todos eles combinados formam a população ) que são distribuídos aleatoriamente por toda a função, em vez de apenas um ponto de partida aleatório como em algoritmos de busca baseados em vizinhança (por exemplo: Hill Climbing) ou gradiente (por exemplo: Gradient Descent).

2) Os valores de aptidão ou aptidão dos indivíduos ou soluções são então calculados
3) Os melhores ou mais aptos indivíduos são então selecionados usando uma estratégia de seleção baseada no valor de aptidão (leia “Sobrevivência do mais apto” ).
4)  Indivíduos selecionados da população produzem descendentes (ou filhos ) ao final de cada geração (ou iteração ), transmitindo assim seus genes aptos aos seus descendentes. O processo é conhecido como Reprodução, Cruzamento ou Recombinação .
5)  Os descendentes são semelhantes aos pais e sofrem mutações aleatórias (com base na probabilidade), muito parecidas com o que vemos na vida real entre pais e filhos.

6)  Os descendentes da geração anterior se tornam população (ou pais ) para a próxima geração .
7)   O processo continua pelo número dado de gerações ou iterações .
8)   O indivíduo mais apto é registrado no final de todas as gerações; o mais apto de todos é a solução ótima .
    
   
## EXEMPLO DE USO COM SIN 45 BARRAS (ONS) REGIAO RJ/SP
---

Uso com 20 gerações e mutacao e crossover em 80& com demandas de contigencias leve, média e pesada. 

<img width="1133" height="621" alt="image" src="https://github.com/user-attachments/assets/c055622a-88ca-4e12-b9bd-bf815c577b22" />


Na pasta compartilhada onde possui três arquivos com extensão jupyter notebook que podem ser abertos diretamente no Google Colab.Para este fim, o usuário deverá seguir os seguintes passos:

1) Crie um arquivo chamado `params.json` para configurar os parametros AG

```´py
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


2) Adapte a função objetivo e as variáveis de decisão para o seu problema de otimização. Crie um array multidimensional de valores float ou int e crie uma função em Python que represente o problema. No trecho de Código 1, é ilustrada a definição de um array ind1 para as variáveis de decisão e uma função evaluate que representa a função objetivo.

Código 1: Exemplo de indivíduo e função objetivo 
```python
ind1 = [1,2,3,4,5,6,7,8,9,10]  # Exemplo de individuo de tamanho 10 e inteiro

def evaluate(individual):
	"""Função objetivo do problema """
	a = sum(individual)
	b = len(individual)
	return a / b
```

3) No trecho de Código 2, é ilustrado o funcionamento ao instanciar os objetos criados das três classes do framework. Neste exemplo são utilizados o array ind1 e a função evaluate, criados anteriormente. Ao executar a função run, o usuário escolhe se deseja usar a estratégia RCE [1]. Esta função retorna a população final gerada e o melhor indivíduo da geração, gerando seu gráfico com esses mesmos parâmetros.


Código 2: Código Main para execução do framework

```python
# Import RCE Framework
from AlgEvolutivoRCE.Setup import Setup, params
from AlgEvolutivoRCE.alg_evolutivo_rce import AlgoritimoEvolutivoRCE
from AlgEvolutivoRCE.Dashboard import DashboardApp


# Import functions benchmark
from utils.functions_fitness.functions_benchmarking import rosenbrock_benchmark


if __name__ == "__main__":

    # Instanciando os Objetos
    setup = Setup(params, fitness_function= funcao_objetivo_IEEE14)
    alg = AlgoritimoEvolutivoRCE(setup,DEBUG= False)

    # Loop Algoritmo Evolutivo podendo receber a função objetivo e as variaveis do problema
    pop_with_repopulation, logbook_with_repopulation, best_variables = alg.run(
        RCE=False,
    )

    print("\n\nEvolução concluída  - 100%")

    # Resultados
    x, y, z, fig = alg.dashboard.visualize(
        logbook_with_repopulation, pop_with_repopulation,
    )

```

4) Para obter resultados e gráficos diferentes, modifique os parâmetros evolutivos do arquivo JSON, salve e execute novamente.

5) É possivel baixar em arquivo .xlsx a população final gerada

6) A versão frontend dos resultados ficam localizados em:

   		/src/DashboardApp/dashboard_RCE_APP.py

7) Excute o arquivo do frontend

```py
streamlit run dashboard_RCE_APP.py
```


8) A versão esta em desenvolvimento desde 10/04/2025 e segue buscando melhorias e contribuições em outros programadores para construir uma interface em Streamlit e programação funcional para obter um sistema que surporte diferentes execuções com tabelas e graficos dos resultados do algoritimo evolutivo com ou sem a estrategia RCE


### **Dicas**:

1) Aumente **Mutação** para maior GAP entre os valores

2) Aumente **PORCENTAGEM** para aumentar signitificamente a quantidade de individuos para entrar no conjunto Elite (Criterio 1)

3) Altere **RCE_REPOPULATION_GENERATIONS** para obter mais ou menos aplicações da Estrategia de Diversitifiação RCE

***Com os valores de Mutação, Crossover e Porcentagem altos é bem capaz de voce atingir valores proximos ao valor global 0,0 da função Rastrigin***

---
# Documentação da Classe RedeEletricaPandaPower e seu uso na funcao_objetivo_IEEE14
---


![image](https://github.com/user-attachments/assets/1291f753-d5c8-44b5-8cc2-460b1a6bd5ca)

**Simulador de Redes Elétricas: Um software para simular o comportamento da rede em diferentes cenários, prevendo falhas e otimizando o fluxo de energia.**

Esta classe representa uma rede elétrica usando a biblioteca Pandapower. Ela fornece funcionalidades para carregar redes padrão, validar dados de agendamento e contingência, calcular violações de fitness, ajustar cargas, desligar/religar elementos da rede e executar o fluxo de carga.

Exemplo de simulação da Rede Eletrica IEEE 14 barras com PandaPower
<table>
  <tr>
    <td>
	<img src="https://github.com/PedroVic12/Repopulation-With-Elite-Set/blob/main/src/assets/newplot.png" />
    </td>
    <td>
	  <img src="https://icseg.iti.illinois.edu/files/2013/10/WSCC14.png" />
  </tr>
</table>


## Classe RedeEletricaPandaPower

### Atributos

* `net`: Objeto Pandapower que representa a rede elétrica.
* `debug`: Flag para ativar ou desativar o modo de depuração.
* `console`: Objeto Logger para registrar mensagens.
* `mapeamento_ramos`: Dicionário que mapeia pares de barramentos para índices de linhas e trafos.
* `pesos`: Dicionário que define os pesos para as violações de fitness.
* `agendamento`: DataFrame que armazena os dados de agendamento.
* `contingencia`: DataFrame que armazena os dados de contingência.

### Métodos

* `carregar_redes_padrao()`: Carrega uma rede padrão do Pandapower com base no nome fornecido.
* `criar_mapeamento_ramos()`: Cria um mapeamento de ramos (linhas e trafos) para facilitar o acesso aos elementos da rede.
* `validar_dados()`: Valida os dados de agendamento e contingência antes de processá-los.
* `hashtableindex()`: Calcula o índice da tabela hash correspondente a um cenário específico.
* `log()`: Registra uma mensagem com o nível especificado.
* `show_status()`: Exibe o status atual da rede elétrica, incluindo informações sobre linhas, transformadores e barramentos.
* `calcular_violacoes_fitness()`: Calcula as violações de fitness, como violações de tensão e carregamento de linhas e transformadores.
* `calcular_perfil()`: Determina o perfil de carregamento (leve, médio ou pesado) para uma determinada hora.
* `avalia_cenarios()`: Avalia os cenários de agendamento e contingência, gerando uma matriz de cenários.
* `executar_fluxo_de_carga()`: Executa o fluxo de carga na rede elétrica usando o algoritmo Newton-Raphson.
* `ajustar_cargas()`: Ajusta as cargas da rede de acordo com o perfil de carregamento especificado.
* `desligar_elementos_agendamento()`: Desliga elementos da rede (linhas e trafos) com base no cenário de agendamento.
* `desligar_contingencia()`: Desliga elementos da rede com base no cenário de contingência.
* `desligar_elementos()`: Desliga os elementos especificados (linhas e trafos) da rede.
* `religar_todos_os_ramos_agendamento()`: Religa todos os ramos da rede que foram desligados durante o agendamento.
* `imprimir_resultados()`: Imprime os resultados do fluxo de carga e salva os dados em um arquivo Excel.
* `calcular_potencia_aparente_trafos()`: Calcula a potência aparente nos transformadores.
* `calcular_potencia_aparente_linhas()`: Calcula a potência aparente nas linhas.


## Uso na funcao_objetivo_IEEE14

A função `funcao_objetivo_IEEE14` usa a classe `RedeEletricaPandaPower` para simular e avaliar o desempenho de um agendamento de desligamentos na rede elétrica IEEE 14 barras. 

Aqui está um resumo de como a classe é utilizada na função:

1. **Inicialização:** Uma instância da classe `RedeEletricaPandaPower` é criada, carregando a rede IEEE 14 barras.
2. **Configuração:** Os pesos para as violações de fitness são definidos, e os dados de agendamento e contingência são carregados.
3. **Avaliação de Cenários:** A função `avalia_cenarios` da classe é utilizada para gerar uma matriz de cenários, considerando os horários de início e duração dos desligamentos, bem como os perfis de carregamento.
4. **Simulação:** Para cada cenário, o fluxo de carga é executado usando a função `executar_fluxo_de_carga` da classe. Antes da execução, as cargas são ajustadas de acordo com o perfil de carregamento do cenário, e os elementos da rede são desligados/religados conforme definido no cenário.
5. **Cálculo de Fitness:** As violações de fitness são calculadas usando a função `calcular_violacoes_fitness` da classe. O fitness do cenário é então determinado com base nos pesos atribuídos a cada tipo de violação.
6. **Agregação de Resultados:** Os fitness de todos os cenários são somados para obter o fitness final do agendamento.


