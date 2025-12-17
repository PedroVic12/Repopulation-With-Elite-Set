---
# Checklist de Correção de Erros — Projeto Repopulation With Elite Set 2025
---

## Requisitos RZ desde (16/10/2025)

IEEE14, IEEE30 e IEEE118 estão funcionando muito bem. IEEE57 está com o problema do modelo do pandapower e o SIN45 não está funcionando. (SIN 45 com novo código)

RZ: Erros consertados com estes arquivos a seguir 
- [x] erro no IEEE 118 - demanda com 9999 ao invés de 99
- [x] erro no SIN45 - erro de sintaxe log usando format com aspas
SIN45 sem variável de ambiente
- [x] run.py - corrigido erro de chamada das funções objetivo passando o index da func objetivo e usando os argumentos --config_num e --exec_num
- [ ] todas as funções objetivo ajustadas para funcionar com run.py da mesma maneira

Erros que continuam:
- [ ] Todas as configurações são geradas mas só uma configuração config_1 é consolidada na tabela e somente ela pode ser visualizada no dashboard para gráficos. Tabela do Dashboard mostra todas as execuções.

- [ ] Na função objetivo do SIN45 : 
[20:28:01] [ERRO] na fun��o objetivo SIN45: module 'pandapower.networks' has no attribute 'create_empty_network'
[20:28:01] Error in fitness_func: float() argument must be a string or a real number, not 'dict'

- [ ] Opção do Dashboard "População Final" mostra a mesma tabela para todas as execuções
- [ ] Dashboard : mensagem de erro sobre cálculo do tempo "Erro ao calcular tempo médio e tempo total acumulado."
- [ ] usar o launcher mais de uma vez, indo para o dashboard e voltando, pode travar o processo do launcher.
- [ ] analisar previamente a função objetivo selecionada no run.py ou permitir selecioná-la antes de executar resolveria muitos problemas, principalmente quando o número de variáveis é diferente.
- [x] Sistema Teste 57 está com muitos erros (não é no código).
- [ ] Apesar de ter duas configs e no log aparecerem duas configs, no dashboard aparece apenas config_num1 apos correção para artigo PIBIC

---

## 🧠 TODO
- [ ] Refatoração novo Lancher
- [ ] Verificar versão do repositório utilizada para análise
- [ ] Criar branch `bugfix/dec-2025` para corrigir erros listados
- [ ] Dashboard só visualiza *config_1*

---
## 🧠Testing e Qualidade

- [ ]  Criar testes unitários para cada função objetivo

- [ ]  Validar entrada/saída com asserts

- [ ]  Usar parametrização de testes (pytest)


