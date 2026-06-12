---

# RCE Lancher AG - Desktop Simulator for SEP usando Algoritimos Evolutivos

---



- [x] Novo exemplo de Documentação de otimizacao

- [x] Novo template APP

- [x] Novo Iframes em cada Tab dentro do meu app template

- [x] Pegar tudo de util utilizado nos 2 artigos e colocar na documentação 

- [x] Destaque para cargas leve, média e pesada segundo ONS

- [x] Destaque para algoritmo avalia_cenarios() e analise_contigencias_sep()

- [x] Setup, AlgEvolutivoRCE, RedeEletricaPandaPower e SmartGrid_SIN (modelagem de dados para cada classe)

- [x] Documetação caso SIN 45

- [x] 04/12/25 - Nova versão no Github








## Projetos 2024/2025 com GUI

- [x] RCE Lancher Menu TAB

- [x] RCE Lancher CLI Menu Tab

- [x] Perdas Duplas ETL Iframe

- [ ] MUST Dekstop Access DB/SQLite (CRUD)- fora ponta - AI - Big O - Aprova/Ressalva - Consolidados e Pendentes com Word Template

- [x] SIN 45 Analise Contigencias xlsx/.PWF Pandapower PowerFLow

- [x] Electrical-IEEE-Systems-PandaPower

- [x] App Template - /src /gui /app 

  - [x] SideMenuComponent

  - header nav bar component

  - AppBar ToolBox PandaPower

  - [x] Open/Close Tabs and Iframes

  - Dark/Light mode

  - PySignal + Slot + Worker + MVC or MVVM desktop




---

# Checklist de Correção de Erros — Projeto Repopulation With Elite Set 2025

---



## 1) Requisitos RZ desde (16/10/2025)



- [x] IEEE14, IEEE30 e IEEE118 estão funcionando muito bem. IEEE57 está com o problema do modelo do pandapower e o SIN45 não está funcionando. 



- [x] SIN 45 com novo código e mostrando os ramos desligados com os horários de intervenção



RZ: Erros consertados com estes arquivos a seguir 

- [x] erro no IEEE 118 - demanda com 9999 ao invés de 99

- [x] erro no SIN45 - erro de sintaxe log usando format com aspas




- [x] run.py - corrigido erro de chamada das funções objetivo passando o index da func objetivo e usando os argumentos --config_num e --exec_num



- [x] todas as funções objetivo ajustadas para funcionar com run.py da mesma maneira (agora como argparse e Launcher)



- [x] (REVER COM URGENCIA) __Apesar de ter duas configs e no log aparecerem duas configs, no dashboard aparece apenas config_num1 apos correção para artigo PIBIC__



- [ ] __Opção do Dashboard "População Final" mostra a mesma tabela para todas as execuções__



- [ ] __Todas as configurações são geradas mas só uma configuração config_1 é consolidada na tabela e somente ela pode ser visualizada no dashboard para gráficos. Tabela do Dashboard mostra todas as execuções.__



- [x] __Dashboard : mensagem de erro sobre cálculo do tempo "Erro ao calcular tempo médio e tempo total acumulado."__



- [ ] __Dashboard :usar o launcher mais de uma vez, indo para o dashboard e voltando, pode travar o processo do launcher.__



- [x] Usar como base o Framework como ferramenta final antes de implementar novas telas



- [ ] Usar como base projeto em Simulink e Matlab para construir um software academico para análise de SEP 

    - https://www.youtube.com/watch?v=ftcaSp-uhtc

    - https://www.youtube.com/watch?v=WFFDyCbCdXg


---
### 3) Bug Fix 18/12/25 execucao unica
"""

1) self.thread.quit(): Esta função envia um sinal para a thread indicando que ela deve encerrar seu loop de eventos. É um pedido para que a thread termine suas tarefas pendentes e saia de forma limpa. Ela não interrompe a thread imediatamente.



2) self.thread.wait(): Esta função bloqueia a thread que está chamando o wait() até que a self.thread (a thread de trabalho) tenha realmente terminado sua execução.



No nosso caso, com as mudanças que fizemos para usar Qt.QueuedConnection, o método _on_process_finished (e os outros slots que corrigimos) é executado na thread principal da sua aplicação (a thread da GUI).



Quando a thread principal chama self.thread.wait(), ela está esperando pela thread de trabalho (onde o ProcessOutputReader estava rodando) terminar.


---

 

## 4) TODO PVRV

- [x] Refatoração novo Lancher

- [x] Verificar versão do repositório utilizada para análise

- [x] Ter versão estável usada no artigo como backup no github

- [x] Limpeza de arquivos não usados no Github

- [ ] Criação de um excel com os casos IEEE e seus ramos de contigencias para retirar o *hardcoded* dentro de cada código e ter acesso a planilha no Launcher

- [x] Criar branch `bugfix/dec-2025` para corrigir erros listados

- [x] Dashboard só visualiza *config_1*. A principio corrigido em 23/12/25 após bateria de testes



---

## 5) Testing e Qualidade



- [x]  Criar testes unitários para cada função objetivo 

    - [x] Test benchmarking (rastrigin)

    - [x] Test run.py

- [x]  Validar entrada/saída com options e params com pasta output em variaveis globais

- [x]  Usar parametrização de testes (pytest)



---


