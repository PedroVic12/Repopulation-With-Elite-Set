# Repopulation-With-Elite-Set
 
---
##      EXEMPLO DE USO DO FRAMEWORK:
---
O usuário do framework encontrará na pasta compartilhada onde possui três arquivos com extensão jupyter notebook que podem ser abertos diretamente no Google Colab. O Notebook 1 pode ser utilizado para apenas uma execução do AE. Para este fim, o usuário deverá seguir os seguintes passos:


1) Crie um arquivo chamado `parameters.json`

2) Pegue o exemplo dos valores no arquivo localizado em:
https://drive.google.com/drive/folders/1j8Hia_ofFMzTyzUUv27oqj1Nq5lLskSg?usp=drive_link

3) Copie e cole esses valores no arquivo de parâmetros criado.

4) Adapte a função objetivo e as variáveis de decisão para o seu problema de otimização. Crie um array multidimensional de valores float ou int e crie uma função em Python que represente o problema. 

5) Execute todas as células desse Notebook.

6) Para obter resultados e gráficos diferentes, modifique os parâmetros evolutivos do arquivo JSON, salve e execute novamente.


7) É possivel baixar em arquivo .xlsx a população final gerada

Para obter resultados e graficos diferentes, modifique os parametros Evolutivos do arquivo JSON, salve e execute novamente.


### **Dicas**:

1) Aumente **Mutação** para maior GAP entre os valores

2) Aumente **PORCENTAGEM** para aumentar signitificamente a quantidade de individuos para entrar no conjunto Elite (Criterio 1)

3) Altere **RCE_REPOPULATION_GENERATIONS** para obter mais ou menos aplicações da Estrategia de Diversitifiação RCE

***Com os valores de Mutação, Crossover e Porcentagem altos é bem capaz de voce atingir valores proximos ao valor global 0,0 da função Rastrigin***
