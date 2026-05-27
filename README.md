# Repopulation-With-Elite-Set

---

## FRAMEWORK DESENVOLVIDO PARA FINS ACADÊMICOS USANDO ALGORITMOS GENÉTICOS PARA RESOLVER PROBLEMAS DE OTIMIZAÇÃO EM REDES ELÉTRICAS, FINANCIADO POR BOLSA DE INICIAÇÃO CIENTÍFICA PELA UNIVERSIDADE FEDERAL FLUMINENSE (UFF)

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

**Um framework acadêmico completo para otimização de problemas em Redes Elétricas de Potência usando Algoritmos Genéticos (AG) e a estratégia de diversificação RCE.**

---

## Atualizações e Bugs Fixes (20-05-2026)

- Novo modulo de projeto usando uma arquitetura Model-View-Controller (MVC) e integra
a funcionalidade completa de análise de sistemas de potência em um único script,
conforme solicitado.

- Model: Camada de dados e lógica de negócio.
- View: A interface gráfica.
- Controller: O orquestrador que conecta Model e View.

- **Bug Fix 18/12/25 execução única**

1) self.thread.quit(): Esta função envia um sinal para a thread indicando que ela deve encerrar seu loop de eventos. É um pedido para que a thread termine suas tarefas pendentes e saia de forma limpa. Ela não interrompe a thread imediatamente.

2) self.thread.wait(): Esta função bloqueia a thread que está chamando o wait() até que a self.thread (a thread de trabalho) tenha realmente terminado sua execução.

No nosso caso, com as mudanças que fizemos para usar Qt.QueuedConnection, o método _on_process_finished (e os outros slots que corrigimos) é executado na thread principal da sua aplicação (a thread da GUI).

Quando a thread principal chama self.thread.wait(), ela está esperando pela thread de trabalho (onde o ProcessOutputReader estava rodando) terminar.

---

## Atualização 27-05-2026

- Validação do projeto em casos de uso do SIN do ONS
- Correção e novos metodos para IEEE 30 como base de uso do lancher em Qt6
- correção e testes de AG na func obejtivo de IEEE30 com o retorno de cada ramo selecionado para desligamento por patamares de carga Leve, media e Pesada

- *Streamlit bug fixes:*

1. Exportação Detalhada (Excel): Agora, ao final de cada simulação, o run.py
      gera automaticamente o arquivo resultados_agendamento_<nome_funcao>.xlsx na
      pasta output. Esse arquivo contém o detalhamento das intervenções (ramos,
      início e duração).
2. Diferenciação de Execuções:
       *Atualizei o DatabaseController para identificar os resultados pela
         combinação de Pasta da Run + Configuração.
       * No Dashboard (RCE_Framework_Page.py), as abas agora mostram o nome da
         Run (ex: 2026-05-27_11-57-31 | Config 1), evitando que uma simulação do
         IEEE 30 sobrescreva visualmente uma do Rastrigin.
3. Timeline melhorada: O componente de linha do tempo agora lê
      preferencialmente os dados do novo Excel. Ele identifica automaticamente se
      os dados vêm de uma análise de contingência e monta as barras com o nome
      das intervenções (ex: 🛠️ Intervenção [1, 3]).
4. Consolidação Inteligente: Ajustei a lógica de busca de arquivos para que o
      Dashboard consiga localizar exatamente o JSON de cada execução dentro da
      nova estrutura de pastas, garantindo que os gráficos e métricas
      correspondam à aba selecionada.

Como verificar:

   1. Rode uma nova simulação (ex: IEEE 30).
   2. No Dashboard, você verá uma aba com o timestamp da execução.
   3. Dentro da aba "Solução", a "Linha do Tempo Interativa" estará preenchida
      com os dados carregados diretamente do Excel de agendamento.

---

## 🎯 Contexto

Este framework foi desenvolvido como parte de um projeto de Iniciação Científica (PIBIC) na Universidade Federal Fluminense (UFF). O seu objetivo é aplicar **Algoritmos Genéticos (AG)** para resolver problemas complexos de otimização em Engenharia Elétrica, especificamente o **Agendamento Ótimo de Intervenções (manutenções) em Redes Elétricas**.

A principal inovação é o uso da estratégia **RCE (Repopulação Conjunto Elite)**, uma técnica de diversificação que ajuda o algoritmo a evitar ótimos locais e a explorar melhor o espaço de busca, garantindo soluções mais robustas.

## ✨ Funcionalidades Principais

- **Algoritmo de Otimização:** Implementação de Algoritmo Genético (AG) focado no problema de agendamento, utilizando a biblioteca **DEAP**.
- **Estratégia de Diversificação:** Inclui a técnica **RCE (Repopulação Conjunto Elite)** para melhorar a qualidade e a diversidade das soluções encontradas.
- **Simulação de Redes Elétricas:** Utiliza **Pandapower** para modelar as redes (IEEE 14, 30, 118 e SIN 45) e calcular o fluxo de potência, que serve como a "função objetivo" (fitness) do AG.
- **Interface Gráfica (Desktop):** Um *Launcher* completo em **PySide6 (Qt)** para configurar todos os parâmetros do AG, definir múltiplas execuções e acompanhar os logs em tempo real.
- **Dashboard Web Interativo:** Um painel de análise de resultados em **Streamlit** para visualizar graficamente a convergência do algoritmo, comparar execuções e explorar as soluções finais.

## EXEMPLO DE USO COM O SIN DE 45 BARRAS (ONS) - REGIÃO RJ/SP

---

Uso com 20 gerações, mutação e crossover de 80%, com demandas de contingências leve, média e pesada.

<img width="1133" height="621" alt="image" src="https://github.com/user-attachments/assets/c055622a-88ca-4e12-b9bd-bf815c577b22" />

Este script utiliza um Algoritmo Genético para otimizar o agendamento de manutenções em linhas de transmissão de um sistema elétrico de potência (o SIN 45, um modelo com 45 barras).

---

## 📸 Galeria

\<table\>
\<tr\>
\<td align="center"\>\<strong\>Launcher Principal (PySide6)\</strong\>\</td\>
\<td align="center"\>\<strong\>Dashboard de Resultados (Streamlit)\</strong\>\</td\>
\</tr\>
\<tr\>
\<td\>\<img src="[https://github.com/user-attachments/assets/c055622a-88ca-4e12-b9bd-bf815c577b22](https://github.com/user-attachments/assets/c055622a-88ca-4e12-b9bd-bf815c577b22)" alt="Launcher do RCE Framework" /\>\</td\>
\<td\>\<img src="[https://github.com/user-attachments/assets/1291f753-d5c8-44b5-8cc2-460b1a6bd5ca](https://github.com/user-attachments/assets/1291f753-d5c8-44b5-8cc2-460b1a6bd5ca)" alt="Dashboard em Streamlit" /\>\</td\>
\</tr\>
\<tr\>
\<td align="center" colspan="2"\>\<strong\>Simulador para Análise de Contingências (IEEE 14 Barras)\</strong\>\</td\>
\</tr\>
\<tr\>
\<td colspan="2"\>
\<table\>
  \<tr\>
    \<td\>
\<img src="[https://github.com/PedroVic12/Repopulation-With-Elite-Set/blob/main/src/assets/newplot.png](https://github.com/PedroVic12/Repopulation-With-Elite-Set/blob/main/src/assets/newplot.png)" alt="Plot PandaPower" /\>
    \</td\>
    \<td\>
  \<img src="[https://icseg.iti.illinois.edu/files/2013/10/WSCC14.png](https://icseg.iti.illinois.edu/files/2013/10/WSCC14.png)" alt="Diagrama IEEE 14" /\>
  \</tr\>
\</table\>
\</td\>
\</tr\>
\</table\>

## 🛠️ Arquitetura do Software

O framework segue uma arquitetura desacoplada, facilitando a manutenção e o uso:

1. **`Launcher.py` (Frontend Desktop):** O utilizador configura os parâmetros da simulação (Ex: % de mutação, nº de gerações) e clica em "Executar".
2. **`run.py` (Backend/Controlador):** Este script principal recebe as configurações, instancia o algoritmo evolutivo (AG + RCE) e inicia o processo.
3. **`funcao_objetivo` (Modelo):** Para cada "indivíduo" (solução) gerado pelo AG, o `run.py` chama a função objetivo.
4. **Pandapower:** A função objetivo usa o Pandapower para simular o cenário (desligamentos + contingências) e calcular as violações (fitness).
5. **`output/` (Resultados):** O `run.py` salva os logs, gráficos e a melhor solução numa pasta de resultados.
6. **`dashboard_RCE_APP.py` (Frontend Web):** O Streamlit lê os dados da pasta `output/` e exibe os resultados de forma interativa.

## 🚀 Começo Rápido

Podes executar o framework de duas maneiras: através da interface gráfica (recomendado) ou diretamente pelo terminal.

### 1\. Instalação

Primeiro, clona o repositório e instala as dependências:

```bash
git clone https://github.com/SEU_USUARIO/Repopulation-With-Elite-Set.git
cd Repopulation-With-Elite-Set
```

**Método A (Recomendado - Windows):**

Execute o instalador que cuida de tudo para ti:

```bash
./instalador.bat
```

**Método B (Manual):**

Certifica-te de que tens o Python 3.8 (ou superior) e instala as bibliotecas necessárias:

```bash
pip install -r requirements.txt
```

---

### 2\. Execução

#### Método 1: Interface Gráfica (Recomendado)

Esta é a forma mais fácil de usar.

1. Inicia o Launcher:

    ```bash
    python app.py
    ```

2. Na aba **"Configuração e Execução"**, define os teus parâmetros:

      - **Execuções por Configuração:** Quantas vezes o AG deve rodar para cada conjunto de parâmetros (importante para resultados estatísticos).
      - **Parâmetros do Algoritmo Genético:** Podes definir valores fixos ou múltiplos valores (Modo "Variável") para `MUTACAO`, `CROSSOVER`, `NUM_GENERATIONS` e `POP_SIZE`. O framework irá testar *todas as combinações* possíveis.

3. Na aba **"Parâmetros AG - RCE"**, podes ajustar detalhes mais finos da estratégia RCE.

4. Clica em **"Salvar e Executar"**.

5. Acompanha o progresso na aba **"Dashboard e Logs"**. A partir dela, podes clicar em **"Abrir Dashboard"** para ver os resultados no Streamlit em tempo real.

#### Método 2: Direto via Terminal (Avançado)

Para utilizadores avançados que preferem scripts.

1. Edita o ficheiro de configuração principal: `src/params.json`.

2. Executa o script `run.py` (localizado dentro da pasta `src`):

    ```bash
    python src/run.py
    ```

---

### 3\. Visualizando os Resultados (Manualmente)

Se não usares o botão no Launcher, podes iniciar o dashboard do Streamlit a qualquer momento:

```bash
# Navega até à pasta do dashboard (dentro de src)
cd src/DashboardApp

# Executa o Streamlit
streamlit run dashboard_RCE_APP.py
```

## 🔧 Configurando a Otimização (`params.json`)

Para usar o framework para o *teu* problema, só precisas de te focar em duas coisas:

1. **O ficheiro `params.json` (ou a interface gráfica):**
    Aqui defines os parâmetros do teu AG.

    ```json
    {
      "ARRAY_VAR": [14, 15, 14, 18, 15],
      "LIMITE_VAR": [0, 31],
      "NUM_GENERATIONS": 100,
      "CROSSOVER": 0.8,
      "MUTACAO": 0.85,
      "POP_SIZE": 10,
      "IND_SIZE": 5,
      "RCE_REPOPULATION_GENERATIONS": 20,
      "NUM_VAR_DIFERENTES": 1,
      "PORCENTAGEM": 0.3,
      "DELTA_MIN": 0.05
    }
    ```

2. **Código 1: Exemplo de indivíduo e função objetivo**

```python
ind1 = [1,2,3,4,5,6,7,8,9,10]  # Exemplo de indivíduo de tamanho 10

def evaluate(individual):
 """Função objetivo do problema."""
 a = sum(individual)
 b = len(individual)
 return a / b
```

1. O **Código 2** ilustra o funcionamento ao instanciar os objetos do framework. Neste exemplo, são utilizados o indivíduo `ind1` e a função `evaluate`. Ao executar a função `run`, o utilizador escolhe se deseja usar a estratégia RCE. A função retorna a população final, o melhor indivíduo e gera um gráfico com os resultados.

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

## 💡 Dicas de Otimização (Estratégia RCE)

- Aumenta a **Mutação** para maior diversidade entre os valores.
- Aumenta a **PORCENTAGEM** para aumentar significativamente a quantidade de indivíduos no conjunto Elite (Critério 1).
- Altera **RCE\_REPOPULATION\_GENERATIONS** para obter mais ou menos aplicações da Estratégia de Diversificação RCE.

***Com valores altos de Mutação, Crossover e Porcentagem, é mais provável que atinja valores próximos do ótimo global.***

---

## 📚 Documentação: `RedeEletricaPandaPower`

![image](https://github.com/user-attachments/assets/1291f753-d5c8-44b5-8cc2-460b1a6bd5ca)

**Simulador de Redes Elétricas: Um software para simular o comportamento da rede em diferentes cenários, prevendo falhas e otimizando o fluxo de energia.**

Esta classe representa uma rede elétrica usando a biblioteca Pandapower. Ela fornece funcionalidades para carregar redes padrão, validar dados de agendamento e contingência, calcular violações de fitness, ajustar cargas, desligar/religar elementos da rede e executar o fluxo de carga.

**Exemplo de simulação da Rede Elétrica IEEE 14 barras com PandaPower**
<table>
  <tr>
    <td>
 <img src="https://github.com/PedroVic12/Repopulation-With-Elite-Set/blob/main/src/assets/plot_ieee14_100_generations.png" />
    </td>
    <td>
   <img src="https://icseg.iti.illinois.edu/files/2013/10/WSCC14.png" />
  </tr>
</table>

Esta é a classe central que interage com o Pandapower.

## Casos de Uso na `funcao_objetivo_IEEE14` como função Objetivo

A função `funcao_objetivo_IEEE14` usa a classe `RedeEletricaPandaPower` para simular e avaliar o desempenho de um agendamento de desligamentos na rede IEEE 14 barras.

O processo resume-se a:

1. **Inicialização:** É criada uma instância da classe `RedeEletricaPandaPower`, carregando a rede IEEE 14 barras.
2. **Configuração:** São definidos os pesos para as violações de fitness e carregados os dados de agendamento e contingência.
3. **Avaliação de Cenários:** A função `avalia_cenarios` é utilizada para gerar uma matriz de cenários, considerando os horários de início e duração dos desligamentos e os perfis de carregamento.
4. **Simulação:** Para cada cenário, o fluxo de carga é executado com `executar_fluxo_de_carga`. As cargas são ajustadas e os elementos da rede são desligados/religados conforme o cenário.
5. **Cálculo de Fitness:** As violações são calculadas com `calcular_violacoes_fitness`, e o fitness do cenário é determinado com base nos pesos atribuídos.
6. **Agregação de Resultados:** Os valores de fitness de todos os cenários são somados para obter o fitness final do agendamento.

### Por que o fluxo de potência "não converge"?

Isto é um comportamento **esperado** e correto. A não convergência do fluxo de potência é um problema clássico ao simular múltiplas falhas na rede (N-k).

Isso geralmente acontece quando um cenário de operação (um agendamento de manutenção + uma contingência) leva a uma condição fisicamente instável ou impossível na rede, como:

- **Colapso de Tensão:** As tensões em algumas barras caem para níveis tão baixos que o sistema "apaga".
- **Sobrecargas Extremas:** Linhas ou transformadores sobrecarregados.
- **Ilhamento:** A rede divide-se em "ilhas" e uma delas fica sem geração própria para se sustentar.

O nosso algoritmo de otimização *penaliza* esses indivíduos, atribuindo-lhes um fitness muito alto (penalidade por não atendimento à demanda), garantindo que o AG aprenda a evitá-los.

### Métodos Principais da Classe

- `carregar_redes_padrao()`: Carrega uma rede padrão do Pandapower (ex: "case14").
- `validar_dados()`: Valida os DataFrames de agendamento e contingência.
- `hashtableindex()`: Calcula o índice da tabela hash para um cenário (evita recálculo).
- `calcular_violacoes_fitness()`: Calcula as violações de tensão e carregamento (o *fitness*).
- `calcular_perfil()`: Determina o perfil de carregamento (leve, médio, pesado).
- `avalia_cenarios()`: Gera a matriz de cenários de operação.
- `executar_fluxo_de_carga()`: Executa o `runpp` do Pandapower.
- `ajustar_cargas()`: Ajusta as cargas da rede conforme o perfil.
- `desligar_elementos_agendamento()`: Desliga elementos com base no agendamento.
- `desligar_contingencia()`: Desliga um elemento para simular uma contingência.
- `religar_todos_os_ramos_agendamento()`: Limpa a rede para o próximo cenário.

## 🎓 Agradecimentos

Este trabalho foi desenvolvido com o fomento do **Programa Institucional de Bolsas de Iniciação Científica (PIBIC)** e o apoio da **Universidade Federal Fluminense (UFF)**, sob orientação do Prof. Dr. Rainer Zanghi.

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
  