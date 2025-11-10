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




\<table\>
  \<tr\>
    \<td\>
    \<img src="[https://github.com/user-attachments/assets/21e2218a-3df3-4757-8234-eb59c91490c3](https://github.com/user-attachments/assets/21e2218a-3df3-4757-8234-eb59c91490c3)" alt="Logo PIBIC"\>
    \</td\>
    \<td\>
    \<img src="[https://github.com/user-attachments/assets/5e46cfe2-c669-42ef-9dd5-4f526a82753b](https://github.com/user-attachments/assets/5e46cfe2-c669-42ef-9dd5-4f526a82753b)" alt="Logo UFF"\>
\</td\>
  \</tr\>
\</table\>

**Um framework acadêmico completo para otimização de problemas em Redes Elétricas de Potência usando Algoritmos Genéticos (AG) e a estratégia de diversificação RCE.**

-----

## ⚠️ Status do Projeto

  * O projeto está a ser refatorado para a pasta `/lib` com arquitetura MVC para facilitar a manutenção do código.
  * A versão estável encontra-se na pasta `/src`.

## 🎯 Contexto

Este framework foi desenvolvido como parte de um projeto de Iniciação Científica (PIBIC) na Universidade Federal Fluminense (UFF). O seu objetivo é aplicar **Algoritmos Genéticos (AG)** para resolver problemas complexos de otimização em Engenharia Elétrica, especificamente o **Agendamento Ótimo de Intervenções (manutenções) em Redes Elétricas**.

A principal inovação é o uso da estratégia **RCE (Repopulação Conjunto Elite)**, uma técnica de diversificação que ajuda o algoritmo a evitar ótimos locais e a explorar melhor o espaço de busca, garantindo soluções mais robustas.

## ✨ Funcionalidades Principais

  * **Algoritmo de Otimização:** Implementação de Algoritmo Genético (AG) focado no problema de agendamento, utilizando a biblioteca **DEAP**.
  * **Estratégia de Diversificação:** Inclui a técnica **RCE (Repopulação Conjunto Elite)** para melhorar a qualidade e a diversidade das soluções encontradas.
  * **Simulação de Redes Elétricas:** Utiliza **Pandapower** para modelar as redes (IEEE 14, 30, 118 e SIN 45) e calcular o fluxo de potência, que serve como a "função objetivo" (fitness) do AG.
  * **Interface Gráfica (Desktop):** Um *Launcher* completo em **PySide6 (Qt)** para configurar todos os parâmetros do AG, definir múltiplas execuções e acompanhar os logs em tempo real.
  * **Dashboard Web Interativo:** Um painel de análise de resultados em **Streamlit** para visualizar graficamente a convergência do algoritmo, comparar execuções e explorar as soluções finais.

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

1.  **`Launcher.py` (Frontend Desktop):** O utilizador configura os parâmetros da simulação (Ex: % de mutação, nº de gerações) e clica em "Executar".
2.  **`run.py` (Backend/Controlador):** Este script principal recebe as configurações, instancia o algoritmo evolutivo (AG + RCE) e inicia o processo.
3.  **`funcao_objetivo` (Modelo):** Para cada "indivíduo" (solução) gerado pelo AG, o `run.py` chama a função objetivo.
4.  **Pandapower:** A função objetivo usa o Pandapower para simular o cenário (desligamentos + contingências) e calcular as violações (fitness).
5.  **`output/` (Resultados):** O `run.py` salva os logs, gráficos e a melhor solução numa pasta de resultados.
6.  **`dashboard_RCE_APP.py` (Frontend Web):** O Streamlit lê os dados da pasta `output/` e exibe os resultados de forma interativa.

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

-----

### 2\. Execução

#### Método 1: Interface Gráfica (Recomendado)

Esta é a forma mais fácil de usar.

1.  Inicia o Launcher:

    ```bash
    python launcher.py
    ```

2.  Na aba **"Configuração e Execução"**, define os teus parâmetros:

      * **Execuções por Configuração:** Quantas vezes o AG deve rodar para cada conjunto de parâmetros (importante para resultados estatísticos).
      * **Parâmetros do Algoritmo Genético:** Podes definir valores fixos ou múltiplos valores (Modo "Variável") para `MUTACAO`, `CROSSOVER`, `NUM_GENERATIONS` e `POP_SIZE`. O framework irá testar *todas as combinações* possíveis.

3.  Na aba **"Parâmetros AG - RCE"**, podes ajustar detalhes mais finos da estratégia RCE.

4.  Clica em **"Salvar e Executar"**.

5.  Acompanha o progresso na aba **"Dashboard e Logs"**. A partir dela, podes clicar em **"Abrir Dashboard"** para ver os resultados no Streamlit em tempo real.

#### Método 2: Direto via Terminal (Avançado)

Para utilizadores avançados que preferem scripts.

1.  Edita o ficheiro de configuração principal: `src/params.json`.

2.  Executa o script `run.py` (localizado dentro da pasta `src`):

    ```bash
    python src/run.py
    ```

-----

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

1.  **O ficheiro `params.json` (ou a interface gráfica):**
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

2.  **A tua Função Objetivo (Fitness):**
    No `run.py`, vais passar a tua própria função de avaliação para o `Setup`. O framework foi desenhado para aceitar qualquer função que receba um "indivíduo" (lista de valores) e retorne um "fitness" (um número).

    **Exemplo (Código 1 do `README.md` original):**

    ```python
    def evaluate(individual):
        """Função objetivo de exemplo."""
        a = sum(individual)
        b = len(individual)
        return a / b,  # DEAP espera uma tupla

    # ... no teu main ...
    # setup = Setup(params, fitness_function=evaluate) 
    ```

## 💡 Dicas de Otimização (Estratégia RCE)

  * Aumenta a **Mutação** para maior diversidade entre os valores.
  * Aumenta a **PORCENTAGEM** para aumentar significativamente a quantidade de indivíduos no conjunto Elite (Critério 1).
  * Altera **RCE\_REPOPULATION\_GENERATIONS** para obter mais ou menos aplicações da Estratégia de Diversificação RCE.

***Com valores altos de Mutação, Crossover e Porcentagem, é mais provável que atinja valores próximos do ótimo global.***

## 📚 Documentação: `RedeEletricaPandaPower`

Esta é a classe central que interage com o Pandapower.

#### Por que o fluxo de potência "não converge"?

Isto é um comportamento **esperado** e correto. A não convergência do fluxo de potência é um problema clássico ao simular múltiplas falhas na rede (N-k).

Isso geralmente acontece quando um cenário de operação (um agendamento de manutenção + uma contingência) leva a uma condição fisicamente instável ou impossível na rede, como:

  * **Colapso de Tensão:** As tensões em algumas barras caem para níveis tão baixos que o sistema "apaga".
  * **Sobrecargas Extremas:** Linhas ou transformadores sobrecarregados.
  * **Ilhamento:** A rede divide-se em "ilhas" e uma delas fica sem geração própria para se sustentar.

O nosso algoritmo de otimização *penaliza* esses indivíduos, atribuindo-lhes um fitness muito alto (penalidade por não atendimento à demanda), garantindo que o AG aprenda a evitá-los.

### Métodos Principais da Classe

  * `carregar_redes_padrao()`: Carrega uma rede padrão do Pandapower (ex: "case14").
  * `validar_dados()`: Valida os DataFrames de agendamento e contingência.
  * `hashtableindex()`: Calcula o índice da tabela hash para um cenário (evita recálculo).
  * `calcular_violacoes_fitness()`: Calcula as violações de tensão e carregamento (o *fitness*).
  * `calcular_perfil()`: Determina o perfil de carregamento (leve, médio, pesado).
  * `avalia_cenarios()`: Gera a matriz de cenários de operação.
  * `executar_fluxo_de_carga()`: Executa o `runpp` do Pandapower.
  * `ajustar_cargas()`: Ajusta as cargas da rede conforme o perfil.
  * `desligar_elementos_agendamento()`: Desliga elementos com base no agendamento.
  * `desligar_contingencia()`: Desliga um elemento para simular uma contingência.
  * `religar_todos_os_ramos_agendamento()`: Limpa a rede para o próximo cenário.

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
  

