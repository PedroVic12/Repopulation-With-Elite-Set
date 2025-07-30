### Algoritmo


1) Carrega dados de entrada da tabela [Hora inicial, Duração, hora final, carregamento, ramo] de agendamentos e religa os todos os ramos do agendamento

2) Avalia cenarios retornando a matriz de cenarios (calcula perfil)

3) Condição IF para verificar todos os cenarios

4) Configuração inicial e instancia da classe

5) Ajusta o carregamento do cenario (scaling - net.load e net.gen)

6) Liga todos os ramos do agendamento

7) Identificar e desligar linhas e transformadores do cenario

8) Executar fluxo de potencia

9) Calcular as violaçoes do cenario com os pesos gerando um banco de dados dos cenarios possiveis

10) Encerra IF de verificar os cenarios possiveis

11) Calcula fitess das vioaloes com pesos

12) Retorna as amtriz violações com os resultados e graficos para debug