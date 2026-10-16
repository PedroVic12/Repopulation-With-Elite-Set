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
- [x] analisar previamente a função objetivo selecionada no run.py ou permitir selecioná-la antes de executar resolveria muitos problemas, principalmente quando o número de variáveis é diferente.

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


---

# Melhorias Rainer Zanghi (28/02/2026)

- [ ] A tabela hash é preservada entre execuções de diferentes configurações? Poderia ser um ganho interessante no custo computacional.

- [ ] Uma boa visualização do resultado, dentro do contexto do problema de agendamento de intervenções, deveria estar em outra página contendo :

a - linha do tempo interativa com os cenários - os cenários podem ser obtidos com a reexecução da função que calcula os cenários para um conjunto de variáveis de decisão e configuração
b - desligamentos efetuados em cada cenário - já estão na tabela hash
c - violações de cada cenário - já estão na tabela hash

- [ ] DESAFIO : No Streamlit, permitir que o usuário selecione a configuração e a execução mostradas na visualização, quando clicar na linha correspondente da tabela inicial de resultados consolidados. Essa funcionalidade facilita a navegação entre execuções.

- [ ] Na guia Setup, seria importante ter um texto de explicação dos parâmetros. Isso também ajudaria o usuário nos casos de funções objetivo com outros números de variáveis de decisão e na escolha de variáveis de decisão inteiras ou com ponto flutuante.

- [ ] Através de um botão no Launcher, deve ser possível realizar o backup em zip da planilha "resultados_consolidados.xlsx" com as pastas run que estão cadastradas na planilha e a tabela hash. Ao final do backup, a planilha, as pastas e a tabela hash devem ser apagadas. Usar uma guia de setup ou manutenção para colocar este botão e explicar o que foi feito, informando o caminho completo do arquivo de backup. Isso facilita o uso do software com diferentes funções objetivo.

- [ ] A ordem das tabs de visualização das configurações deve seguir apenas a ordem do número da configuração e não a ordem alfabética por caractere. Logo, Config 1 não deve ser sucedida por Config 10, caso as duas existam.



## Testes realizados (28/02/2026)

config única - ok
config com 2 valores em um atributo - ok
config com 2 valores em dois atributos - ok
ajuste de parâmetros da opção "Setup" (persistência entre execuções e efetividade) - ok 
ajuste de parâmetros na guia "Parâmetros AG" (persistência entre execuções e efetividade)  - ok
seleção de função objetivo - ok
testes anteriores com IEEE30 - ok
teste config única com IEEE14 - ok


Erros:
Mensagem da janela de conclusão : "Execução da bateria de testes concluída com código 0." Trocar "código 0" por "sucesso".
Instalar o pacote numba. Incluir na lista de dependências. É possível executar o aplicativo sem o numba, mas diversas mensagens de warning aparecem no console e a execução fica lenta.
A consolidação de resultados não é executada automaticamente ao final da execução. Se é ativada manualmente através do botão "Consolidar Resultados", a planilha de consolidação "resultados_consolidados.xlsx" é gerada ou atualizada. Mensagem de console ao final da execução : 
[16:39:17] Todas as execuções foram concluídas.
[16:39:17] 
[16:39:17] Iniciando consolidação de resultados em segundo plano...
[16:39:18] [0m
A população final analizada em todos os casos é aquela gravada no arquivo "\APPPATH\rce_framework\src\output\pop_final.xlsx". O applicativo deveria gerar uma população final para cada execução de cada configuração e o streamlit deveria selecionar a adequada. Sugestão: usar a pasta run para guardar o arquivo com nome indexado a cada execução e usar estes (caminho e nome) no streamlit.
Na tela do Streamlit, devem ser retiradas referências diretas ao problema de agendamento : 
1 - "Melhores Variáveis de Decisão (Horários)" retirar texto entre parênteses
2 - "Solução de melhores horários de agendamento para o SEP" trocar para "Solução do problema de otimização"
A tabela de visualização da população final possui duas colunas que não devem ser mostradas pois não tem informação relevante : "Unnamed:0" e "index".
A mensagem "Erro ao calcular tempo médio e tempo total acumulado." é apresentada e estas informações não são mostradas no Streamlit.
Ao executar a partir de uma IDE, o botão de fechar (X) janela faz o launcher travar. Acontece depois de tentar executar uma vez e interromper a execução através do botão "Parar Bateria" - msg de erro : "\APPPATH\rce_framework\src\LauncherGUI\app\controllers\main_controller.py:254: RuntimeWarning: Failed to disconnect (None) from signal "clicked()".
  tab.start_stop_btn.clicked.disconnect()"
No código do launcher, ao gerar a planilha "resultados_consolidados.xlsx" algumas verificações devem ser feitas sobre a planilha existente, para evitar problemas no Streamlit:
1 - Se a função objetivo escolhida for diferente daquela registrada nas simulações da planilha, uma nova planilha deve ser gerada e a planilha anterior guardada em uma pasta backup dentro de output. Isto deve ser observado a cada nova bateria de testes.
2 - A coluna config_num deve ser incremental e só repetir números se estes pertencerem à mesma configuração. Isto deve ser observado a cada nova bateria de testes. Isso não é feito na versão atual, fazendo com o Streamlit só mostre os detalhes dos resultados das configurações criadas na última bateria de teste, mesmo que a tabela inicial seja populada corretamente.
3 - Verificar o código no Streamlit que usa a informação da configuração para coletar as informações de gráfico. Os gráficos de baterias diferentes da última bateria não são mostrados (msg "Dados de visualização não disponíveis para o gráfico de estatísticas."). Garantir que o código use config_num para todos os objetos e cruze esta informação com as colunas 'configuracao' e 'execucao' para obter as informações corretas nas pastas run.
Preservar a escolha de função objetivo entre execuções do launcher.



---


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


