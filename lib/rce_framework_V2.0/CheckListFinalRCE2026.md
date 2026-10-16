# Checklist — Projeto Repopulation With Elite Set 2025

\---

## 

## 1\) Requisitos RZ desde (16/10/2025)

* \[x] IEEE14, IEEE30 e IEEE118 estão funcionando muito bem. IEEE57 está com o problema do modelo do pandapower e o SIN45 não está funcionando.
* \[x] SIN 45 com novo código e mostrando os ramos desligados com os horários de intervenção

RZ: Erros consertados com estes arquivos a seguir

* \[x] erro no IEEE 118 - demanda com 9999 ao invés de 99
* \[x] erro no SIN45 - erro de sintaxe log usando format com aspas
* \[x] SIN45 sem variável de ambiente

  * Teste com variveis globais em config.py e global\_settings.py



* \[x] run.py - corrigido erro de chamada das funções objetivo passando o index da func objetivo e usando os argumentos --config\_num e --exec\_num
* \[x] todas as funções objetivo ajustadas para funcionar com run.py da mesma maneira (agora como argparse e Launcher)



* \[x] (REVER) **Apesar de ter duas configs e no log aparecerem duas configs, no dashboard aparece apenas config\_num1 apos correção para artigo PIBIC**
* \[ ] **Opção do Dashboard "População Final" mostra a mesma tabela para todas as execuções**
* \[x] **Todas as configurações são geradas mas só uma configuração config\_1 é consolidada na tabela e somente ela pode ser visualizada no dashboard para gráficos. Tabela do Dashboard mostra todas as execuções.**
* \[ ] **Dashboard : mensagem de erro sobre cálculo do tempo "Erro ao calcular tempo médio e tempo total acumulado."**
* \[ ] **Dashboard :usar o launcher mais de uma vez, indo para o dashboard e voltando, pode travar o processo do launcher.**
* \[x] Usar como base o Framework como ferramenta final antes de implementar novas telas
* \[x] Usar como base projeto em Simulink e Matlab para construir um software academico para análise de SEP

  * [https://www.youtube.com/watch?v=ftcaSp-uhtc](https://www.youtube.com/watch?v=ftcaSp-uhtc)
  * [https://www.youtube.com/watch?v=WFFDyCbCdXg](https://www.youtube.com/watch?v=WFFDyCbCdXg)







\---

### 2\) Bug Fix 18/12/25 execucao unica

"""

1. self.thread.quit(): Esta função envia um sinal para a thread indicando que ela deve encerrar seu loop de eventos. É um pedido para que a thread termine suas tarefas pendentes e saia de forma limpa. Ela não interrompe a thread imediatamente.
2. self.thread.wait(): Esta função bloqueia a thread que está chamando o wait() até que a self.thread (a thread de trabalho) tenha realmente terminado sua execução.

No nosso caso, com as mudanças que fizemos para usar Qt.QueuedConnection, o método \_on\_process\_finished (e os outros slots que corrigimos) é executado na thread principal da sua aplicação (a thread da GUI).

Quando a thread principal chama self.thread.wait(), ela está esperando pela thread de trabalho (onde o ProcessOutputReader estava rodando) terminar.





## 3\) Melhorias 2025

* \[x] Refatoração novo Lancher
* \[x] Verificar versão do repositório utilizada para análise
* \[x] Ter versão estável usada no artigo como backup no github
* \[x] Limpeza de arquivos não usados no Github
* \[x] Criação de um excel com os casos IEEE e seus ramos de contigencias para retirar o *hardcoded* dentro de cada código e ter acesso a planilha no Launcher
* \[x] Dashboard só visualiza *config\_1*. A principio corrigido em 23/12/25 após bateria de testes
* \[x] **Depurar Consolidação de Resultados (`database\_controller.py`):** Garantir que a função `run\_consolidar\_resultados` itere sobre **todas** as pastas `config\_\*` e não pare após a primeira.
* \[x] **Corrigir Filtros de Visualização (`dashboard\_RCE\_APP.py`):** Implementar ou corrigir a lógica de filtragem para que os gráficos e tabelas no Streamlit respondam corretamente à seleção do usuário (configuração, execução, etc.).



\---





## Upgrades 2026 (10/02/2026)

* \[x] Modificaçõs de caminhos de pastas na nova pasta /tools
* \[x] Tela de loading inicial
* \[x] Script ./build.sh para gerar o executáveç .exe limpo
* \[x] Novo CLI com python app.py --run 10 --config 3 --json params.json
* \[x] options.json configuracao de fluxo de potencia newthon raphson
* \[x] Novos Iframes embutidos na tela
* \[x] Usando rotas com localhost para exibir conteudo Web



## (27/09/2026)

* \[x] comandos para decks AnaRede e Pandapower e excel
* \[x] Organização e limpeza do projeto no GitHub
* \[x] Criação na versão estável em /src e projeto em desenvolvimento em /lib
* \[x] Criação de nova interface em QML usando arquivo page.ui e código backend no main.py
* \[x] Criação de novas interfaces para criar uma rede vazia usando arquivos .pwf do AnaREDE
* \[x] Melhoras na interface e migrando o projeto de Pyside6 para PyQt6
* \[x] Criação de bash script para criar programa executável e com atalho na área de trabalho



