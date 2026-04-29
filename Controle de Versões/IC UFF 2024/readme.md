# Algoritimos Geneticos

---

## Algoritimos Evolutivos

algoritmo de otimização inspirado pela seleção natural e outros mecanismos biológicos. Aqui está um resumo da importância de cada função:

- Seleção (selection): Esta função é responsável por selecionar os indivíduos mais aptos da população para reprodução. Ao classificar os indivíduos com base em seu desempenho (fitness) e escolher os melhores, a seleção direciona o algoritmo para soluções de maior qualidade. A ideia é simular o processo natural em que os indivíduos mais adaptados ao ambiente têm maiores chances de sobreviver e se reproduzir.

- Cruzamento (crossover): A função de cruzamento imita a reprodução sexual na natureza, onde dois indivíduos (pais) combinam partes de seus genomas para criar descendentes. Essa mistura de material genético pode produzir novos indivíduos com características únicas, potencialmente mais aptos que seus pais. Isso introduz diversidade genética na população, o que é crucial para explorar o espaço de solução em busca de ótimos globais.

- Mutação (mutation): A mutação introduz variações aleatórias nos genomas dos indivíduos. Isso simula as mutações aleatórias no DNA que ocorrem na natureza. O objetivo da mutação em algoritmos evolutivos é manter a diversidade genética na população, prevenindo a convergência prematura para ótimos locais. Alterações pequenas e aleatórias nos genes podem levar a descobertas de novas e melhores soluções.

- A função de cálculo de aptidão (calculate_fitness) avalia o desempenho de cada indivíduo. No contexto de programação linear, essa função pode medir quão bem uma solução candidata satisfaz um conjunto de restrições ou atinge um objetivo específico, como minimizar custos ou maximizar lucros.

Em algoritmos evolutivos aplicados à programação linear, os principais pontos incluem:

Representação: Definir como as soluções candidatas (indivíduos) são representadas (por exemplo, vetores de variáveis de decisão).
Inicialização: Gerar uma população inicial de soluções de maneira aleatória ou heurística.
Seleção: Escolher os indivíduos que participarão do processo de reprodução com base em sua aptidão.
Operadores Genéticos: Aplicar operações de cruzamento e mutação para criar novas soluções.
Avaliação: Calcular a aptidão de cada solução com base em um modelo de programação linear.
Substituição: Decidir quais soluções serão mantidas para a próxima geração.
A combinação desses componentes permite que os algoritmos evolutivos busquem soluções ótimas ou quase ótimas para problemas complexos de programação linear, adaptando-se e melhorando ao longo de várias gerações.

## SOLID

Single Responsibility Principle: Cada classe tem uma única responsabilidade. Individuo lida com as propriedades do indivíduo e o cálculo da aptidão, Populacao gerencia a população de indivíduos, e AlgoritmoEvolutivo controla o fluxo do algoritmo genético.
Open/Closed Principle: O código está aberto para extensão, mas fechado para modificação. Se você precisar alterar o cálculo de aptidão, você pode estender a classe Individuo sem alterar as classes existentes.
Liskov Substitution Principle: Este princípio é respeitado, pois não há subclasses. Todas as classes podem ser usadas conforme esperado.
Interface Segregation Principle: Não há interfaces complexas que as classes precisam implementar, cada uma tem métodos simples e específicos.
Dependency Inversion Principle: O algoritmo depende de abstrações e não de detalhes concretos das classes.
