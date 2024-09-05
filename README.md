# Repopulation-With-Elite-Set
 
---
##  EXEMPLO DE USO DO FRAMEWORK:
---

O usuário do framework encontrará na pasta compartilhada onde possui três arquivos com extensão jupyter notebook que podem ser abertos diretamente no Google Colab. O Notebook 1 pode ser utilizado para apenas uma execução do AE. Para este fim, o usuário deverá seguir os seguintes passos:

1) Crie um arquivo chamado `parameters.json`

2) Pegue o exemplo dos valores no arquivo localizado em:
https://drive.google.com/drive/folders/1j8Hia_ofFMzTyzUUv27oqj1Nq5lLskSg?usp=drive_link

3) Copie e cole esses valores no arquivo de parâmetros criado.

4) Adapte a função objetivo e as variáveis de decisão para o seu problema de otimização. Crie um array multidimensional de valores float ou int e crie uma função em Python que represente o problema. No trecho de Código 1, é ilustrada a definição de um array ind1 para as variáveis de decisão e uma função evaluate que representa a função objetivo.

Código 1: Exemplo de indivíduo e função objetivo 
```python
ind1 = [1,2,3,4,5,6,7,8,9,10]  # Exemplo de individuo de tamanho 10

def evaluate(individual):
	"""Função objetivo do problema """
a = sum(individual)
b = len(individual)
return a / b
```

5) No trecho de Código 2, é ilustrado o funcionamento ao instanciar os objetos criados das três classes do framework. Neste exemplo são utilizados o array ind1 e a função evaluate, criados anteriormente. Ao executar a função run, o usuário escolhe se deseja usar a estratégia RCE [1]. Esta função retorna a população final gerada e o melhor indivíduo da geração, gerando seu gráfico com esses mesmos parâmetros.


Código 2: Código Main para execução do framework

```python
if __name__ == "__main__":
    # Instancia dos objetos	
    setup = Setup(params)
    alg = AlgoritimoEvolutivoRCE(setup)
    data_visual = DataExploration()

 # Função que executa o algoritmo evolutivo
    pop_with_repopulation, logbook_with_repopulation, best_variables = alg.run(
        RCE=True,
        fitness_function=evaluate, # Nome da função objetivo do problema
        decision_variables=(ind1), # Nome do array das variaveis de decisão
    )
    print("\n\nEvolução concluída  - 100%")

    # Visualização dos resultados
    data_visual.show_rastrigin_benchmark(logbook_with_repopulation, best_variables)

    best_solution_generation, best_solution_variables, best_fitness = data_visual.visualize(
        logbook_with_repopulation, pop_with_repopulation, repopulation=True
    )
```


6) Execute todas as células desse Notebook.

7) Para obter resultados e gráficos diferentes, modifique os parâmetros evolutivos do arquivo JSON, salve e execute novamente.

8) É possivel baixar em arquivo .xlsx a população final gerada



### **Dicas**:

1) Aumente **Mutação** para maior GAP entre os valores

2) Aumente **PORCENTAGEM** para aumentar signitificamente a quantidade de individuos para entrar no conjunto Elite (Criterio 1)

3) Altere **RCE_REPOPULATION_GENERATIONS** para obter mais ou menos aplicações da Estrategia de Diversitifiação RCE

***Com os valores de Mutação, Crossover e Porcentagem altos é bem capaz de voce atingir valores proximos ao valor global 0,0 da função Rastrigin***
