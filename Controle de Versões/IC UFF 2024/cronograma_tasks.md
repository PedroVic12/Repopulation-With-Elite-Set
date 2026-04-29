# RCE ALG

4 reuniao (remota) Verificar se o código está funcionando, plotando o gráfico da aptidão (melhor e média) por geração. Usar população 20 indivíduos, 90% de chance de crossover e 5% de chance de mutação. Parar o algoritmo após 100 gerações.
Passos:
1 - fazer o código mínimo usando a DEAP e função rastrigin como objetivo.
2 - Implementar o elitismo simples (melhor indivíduo preservado) apenas do melhor indivíduo entre gerações.
3 - Implementar a função que faz a RCE. Chamar esta função a cada 20% do número de gerações total.

[x]

5ª Reunião (Remota)

- Sobre a visualização dos dados:
  - manter o gráfico de convergência (retirando a soma e corrigindo o Best para Max) e os dados associados
  - apresentar a melhor solução no final - valores das variáveis de decisão e valor da aptidão
  - incluir tempo de execução total

- Depois que tudo funcionar :
  - Armazenar várias execuções do algoritmo em sequencia e extrair média e desvio padrão da melhor solução (ótimo) e dos tempos de execução.

[x]

7ª Reunião (Remota)

- resolver pendências das últimas reuniões
- funcionar o RCE (em 3 etapas)
- interface beta para todos os parâmetros do AE

8ª Reunião (Remota)

- RCE - retirar a memória. o Conjunto elite é sempre novo a cada vez a RCE é chamada.- Incluir array com valores dos limites inferiores e superiores das variáveis de decisão nos dados de entrada do algoritmo.
- Utilizar estruturas do DEAP (individual) para as variáveis de decisão.
- Finalizar relatório (inclusão da tabela, explicação RCE e autoavaliação).

[x]

9ª Reunião (Remota)

- Verificar pendências
- verificar setup e ver se toolbox e create estão de acordo. Usar notebook feito pelo Rainer de referência.
- Utilizar estruturas do DEAP (individual) para as variáveis de decisão.
 Verificar se o código está funcionando, plotando o gráfico da aptidão (melhor e média) por geração. Usar população 20 indivíduos, 90% de chance de crossover e 5% de chance de mutação. Parar o algoritmo após 100 gerações.
