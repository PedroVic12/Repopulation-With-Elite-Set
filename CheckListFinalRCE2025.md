---
# Checklist de Correção de Erros — Projeto Repopulation With Elite Set 2025
---

## 1) Requisitos RZ desde (16/10/2025)

- [x] IEEE14, IEEE30 e IEEE118 estão funcionando muito bem. IEEE57 está com o problema do modelo do pandapower e o SIN45 não está funcionando. 

- [x] SIN 45 com novo código e mostrando os ramos desligados com os horários de intervenção

RZ: Erros consertados com estes arquivos a seguir 
- [x] erro no IEEE 118 - demanda com 9999 ao invés de 99
- [x] erro no SIN45 - erro de sintaxe log usando format com aspas
- [ ] SIN45 sem variável de ambiente (nao importante ainda)
    - Teste com variveis globais em config.py e global_settings.py

- [x] run.py - corrigido erro de chamada das funções objetivo passando o index da func objetivo e usando os argumentos --config_num e --exec_num

- [x] todas as funções objetivo ajustadas para funcionar com run.py da mesma maneira (agora como argparse e Launcher)

- [x] (REVER COM URGENCIA) __Apesar de ter duas configs e no log aparecerem duas configs, no dashboard aparece apenas config_num1 apos correção para artigo PIBIC__

- [ ] __Opção do Dashboard "População Final" mostra a mesma tabela para todas as execuções__

- [ ] __Todas as configurações são geradas mas só uma configuração config_1 é consolidada na tabela e somente ela pode ser visualizada no dashboard para gráficos. Tabela do Dashboard mostra todas as execuções.__

- [ ] __Dashboard : mensagem de erro sobre cálculo do tempo "Erro ao calcular tempo médio e tempo total acumulado."__

- [ ] __Dashboard :usar o launcher mais de uma vez, indo para o dashboard e voltando, pode travar o processo do launcher.__

- [ ] Usar como base o Framework como ferramenta final antes de implementar novas telas

- [ ] Usar como base projeto em Simulink e Matlab para construir um software academico para análise de SEP 
    - https://www.youtube.com/watch?v=ftcaSp-uhtc
    - https://www.youtube.com/watch?v=WFFDyCbCdXg


## 2) __Erros que continuam:__

- [x] Na função objetivo do SIN45 : 
[20:28:01] [ERRO] na fun��o objetivo SIN45: module 'pandapower.networks' has no attribute 'create_empty_network' 
    - Erro acontece por erro de sintaxe do pandapower mas a classe de Rede Elétrica já possui este método encapsulado

- [x] [20:28:01] Error in fitness_func: float() argument must be a string or a real number, not 'dict'


- [x] analisar previamente a função objetivo selecionada no run.py ou permitir selecioná-la antes de executar resolveria muitos problemas, principalmente quando o número de variáveis é diferente.

- [x] Sistema Teste 57 está com muitos erros (não é no código e sim a biblioteca pandapower).


---

### 3) Bug Fix 18/12/25 execucao unica
"""
1) self.thread.quit(): Esta função envia um sinal para a thread indicando que ela deve encerrar seu loop de eventos. É um pedido para que a thread termine suas tarefas pendentes e saia de forma limpa. Ela não interrompe a thread imediatamente.

2) self.thread.wait(): Esta função bloqueia a thread que está chamando o wait() até que a self.thread (a thread de trabalho) tenha realmente terminado sua execução.

No nosso caso, com as mudanças que fizemos para usar Qt.QueuedConnection, o método _on_process_finished (e os outros slots que corrigimos) é executado na thread principal da sua aplicação (a thread da GUI).

Quando a thread principal chama self.thread.wait(), ela está esperando pela thread de trabalho (onde o ProcessOutputReader estava rodando) terminar.
"""
 
## 4) TODO PVRV
- [x] Refatoração novo Lancher
- [x] Verificar versão do repositório utilizada para análise
- [x] Ter versão estável usada no artigo como backup no github
- [x] Limpeza de arquivos não usados no Github
- [ ] Criação de um excel com os casos IEEE e seus ramos de contigencias para retirar o *hardcoded* dentro de cada código e ter acesso a planilha no Launcher
- [ ] Criar branch `bugfix/dec-2025` para corrigir erros listados
- [x] Dashboard só visualiza *config_1*. A principio corrigido em 23/12/25 após bateria de testes

### 2. Correção do Dashboard e Consolidação de Dados
- [x] **Depurar Consolidação de Resultados (`database_controller.py`):** Garantir que a função `run_consolidar_resultados` itere sobre **todas** as pastas `config_*` e não pare após a primeira.
- [ ] **Corrigir Filtros de Visualização (`dashboard_RCE_APP.py`):** Implementar ou corrigir a lógica de filtragem para que os gráficos e tabelas no Streamlit respondam corretamente à seleção do usuário (configuração, execução, etc.).

### 3. Correção de Estabilidade do Launcher
- [X] **Gerenciar Subprocesso do Dashboard (`main_launcher.py`):** Implementado mecanismo para `src/run.py` utilizar um diretório de output compartilhado, passado pelo launcher. (Ainda pendente: Implementar a finalização explícita do subprocesso do Streamlit ao fechar o dashboard ou o launcher).
s

---
## 5) Testing e Qualidade

- [ ]  Criar testes unitários para cada função objetivo 
    - [x] Test benchmarking (rastrigin)
    - [x] Test run.py

- [ ]  Validar entrada/saída com options e params com pasta output em variaveis globais

- [ ]  Usar parametrização de testes (pytest)

---
