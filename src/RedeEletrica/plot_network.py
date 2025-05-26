from rede_eletrica import RedeEletricaPandaPower
from pandapower.plotting import simple_plot, simple_plotly, pf_res_plotly
import pandas as pd


# YouTube Tutorial: https://www.youtube.com/watch?v=4LQLZQWPaPM
import pandapower.networks as nw
import pandapower.plotting as plot
import matplotlib.pyplot as plt
import seaborn

colors = seaborn.color_palette()


#! 1) Criar a rede elétrica IEEE 14 barras, Inicializar a classe com a rede e carrega a tabela de agendamento
rede = RedeEletricaPandaPower("14", debug=True)
net = rede.net
net = nw.mv_oberrhein()

print(net)


bc = plot.create_bus_collection(net, buses=net.bus.index, color=colors[0], size=80, zorder=1)
lc = plot.create_line_collection(net, lines=net.line.index, color='grey', zorder=2)

long_lines = net.line.loc[net.line.length_km > 2.].index
lcl = plot.create_line_collection(net, lines=long_lines, color=colors[2], zorder=2)
plot.draw_collections([lc, bc, lcl])
plt.show()



def funcao_objetivo_IEEE14(individuo, _debug = False):

    #! 1) Criar a rede elétrica IEEE 14 barras, Inicializar a classe com a rede e carrega a tabela de agendamento
    rede = RedeEletricaPandaPower("14", debug=_debug)

    #=====================================================

    #! Colocando pesos como input do usuario e os dados de entrada do agendamento
    rede.pesos["tensao"] = {"min": 100, "max": 100}
    rede.pesos["loading_linhas"] = 100
    rede.pesos["loading_trafos"] = 100

    #=====================================================

    # Tabela agendamentos em xlsx hardcoded
    agendamento_df = pd.DataFrame([
        {"ramo": [1, 4], "inicio": "14:00", "duracao": 6 ,"prioridade": 4},
        {"ramo": [1, 3], "inicio": "15:00", "duracao": 5, "prioridade": 1},
        {"ramo": [3, 6], "inicio": "14:00", "duracao": 6, "prioridade": 1},
        {"ramo": [11, 12], "inicio": "18:00", "duracao": 6, "prioridade": 1},
        {"ramo": [9, 10], "inicio": "15:00", "duracao": 4, "prioridade": 1}
    ])

    contingencia_df = pd.DataFrame([
            {"contingencia":1,  "from":2 , "to": 3},
            {"contingencia":2,  "from":5 , "to": 12},
            {"contingencia":3,  "from":12 , "to": 13},
    ])

    # Converter horários de início para horas do dia
    agendamento_df['inicio'] = agendamento_df['inicio'].apply(lambda x: int(x.split(':')[0]))

    # Calcular horário de término em horas do dia
    agendamento_df['final'] = agendamento_df.apply(lambda row: (row['inicio'] + row['duracao']) % 24, axis=1)

    # Calcular a duração total do agendamento em horas
    duracao_total_agendamento = (agendamento_df['inicio']+agendamento_df['duracao']).max()
    rede.validar_dados(agendamento_df, contingencia_df)


    # passando a variavel de decisão na função objetivo
    agendamento_df["inicio"] = individuo

    # TODO -> Corrgir a coluna final com a duração para cada cenarios
    #display(agendamento_df)
    #agendamento_df["final"] = agendamento_df.apply(lambda row: (row['inicio'] + row['duracao']) % 24, axis=1)

    # Calcular a duração total do agendamento em horas
    #duracao_total_agendamento = (agendamento_df['inicio']+agendamento_df['duracao']).max()

    #=====================================================

    # 2)  Avaliar cenários e criar matriz de cenários
    matriz_cenarios = rede.avalia_cenarios(
            horas = duracao_total_agendamento,
            hora_inicio=agendamento_df['inicio'],
            duracao=agendamento_df['duracao'],
            ls=0, le=8,
            ms=8, me=18,
            hs=18, he=24
        )
    #=====================================================

    #! Calculo  de otimização para achar o fitness de cada cenario
    violacoes_total = []
    violacoes_hash_table = {}

    # Generate hash key (teste 01)
    contingencias = contingencia_df['contingencia'].to_list()
    num_carregamentos = 3
    num_contingencias = len(contingencias) # 3
    num_desligamentos = len(agendamento_df) # 5

    # FAZENDO UM BANCO EM MEMORIA DE EXECUÇÃO
    bd_aptidao_cenario =[-1.0]*(num_contingencias* num_carregamentos*(2**num_desligamentos) )

    try:
        # 3) Processar cada cenário da matriz de cenários
        for cenario in matriz_cenarios:
            perfil = cenario[0]
            estado_ramos = cenario[1:]

            # 4) Ajustar carregamento para o perfil do cenário
            rede.ajustar_cargas(perfil)

            # Loop through contingencies before calculating violations for the scenario
            for contingencia_atual in range(num_contingencias):
                contingencia_atual += 1

                #5)  Ligar todos os ramos antes de aplicar mudanças
                rede.religar_todos_os_ramos_agendamento()

                # 6) Fazendo os deligamentos com base na tabela em .xlsx e nos cenários calculados
                rede.desligar_elementos_agendamento(estado_ramos)

                # 7) Identifica ramos afetados pela contingência
                ramo_contingencia = list(contingencia_df.loc[contingencia_df['contingencia'] == contingencia_atual, ['from', 'to']].values[0])
                rede.log(f"\n{contingencia_atual}) Ramo da contingencia = { ramo_contingencia}\n")

                # 8) Desliga os ramos afetados
                rede.desligar_contingencia(ramo_contingencia)

                # 9) Executar fluxo de potência para o cenário com contingência
                if rede.executar_fluxo_de_carga():

                    # 10) Calcular violações com pesos e armazenar os resultados
                    fitness, violacoes_df = rede.calcular_violacoes_fitness()
                    violacoes_total.append(fitness)

                else:
                    fitness = rede.pesos["demanda"] # penalidade com valor default de 99


                #02/05/25 - Testar hashtable mais generica fora do for loop

                #! 11) Store violation in the hash table
                hash_key = rede.hashtableindex(perfil, num_carregamentos, contingencia_atual, num_contingencias, estado_ramos)
                violacoes_hash_table[hash_key] = fitness
                bd_aptidao_cenario[hash_key] = fitness
                rede.log(f"Hash key = { hash_key}\n")


            #! Ver apenas o true in service de barras e transformadores
            rede.show_status()

        #! Usando dicionario nos temos os valores acumulando tirando os valores nulos
        hash_df2 = pd.DataFrame(violacoes_hash_table.items(), columns=['Hash Key', 'Fitness'])

        # Passando os valores do array direto no dataframe com os index como chave (hash = chave, valor)
        hash_df = pd.DataFrame(bd_aptidao_cenario, columns=[ 'Fitness'])
        filtered_hash_table = hash_df.loc[hash_df['Fitness'] > 0]

        hash_df.to_excel("hash_table.xlsx", index=False)

        # 12) Calcular fitness final com somatorio das vioações com pesos de todos os cenarios
        fitness_final = sum(violacoes_total)
        rede.log(f"\nFitness do agendamento = {fitness_final:.2f}\n")
        return fitness_final

    except Exception as e:
        print(f"\nErro: {e}")