# File: Repopulation-With-Elite-Set/lib/domain/models/utils/functions_fitness/function_IEEE_14_contigencias.py

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt  # Import matplotlib
import io
import base64

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from RedeEletrica.rede_eletrica import RedeEletricaPandaPower
from AlgEvolutivoRCE.Setup import Setup


#! TODO -> (10/07/25) Função implementada em Março mas precisa de paralelismo para ficar mais eficiente e melhor uso da hash table
def funcao_objetivo_IEEE14(individuo, setupobj, _debug = False):
    
    """    
    # Esta função avalia o agendamento de desligamentos e contingências na rede elétrica, calculando o fitness baseado em violações de tensões e carregamentos.
    # A função utiliza a classe RedeEletricaPandaPower para simular o fluxo de carga e calcular as violações com base em um agendamento fornecido.
    # a função retorna o fitness total do agendamento, que é a soma das violações de todos os cenários avaliados.
    ## A função também utiliza uma tabela hash para armazenar os resultados de cenários já avaliados, evitando cálculos redundantes.
    # 


    Returns:
        float/int: fitness_result
    """
    # Função objetivo para o problema de otimização da rede elétrica IEEE 14 barras

    #! 1) Criar a rede elétrica IEEE 14 barras, Inicializar a classe com a rede e carrega a tabela de agendamento
    rede = RedeEletricaPandaPower("14", debug=_debug)


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
   ] )

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

    violacoes_total = []
    violacoes_hash_table = {}

    # Generate hash key values
    #! Variáveis de Calculo  de otimização para achar o fitness de cada cenario
    contingencias = contingencia_df['contingencia'].to_list()
    num_carregamentos = 3
    num_contingencias = len(contingencias) # 3
    num_desligamentos = len(agendamento_df) # 5
    
    #bd_aptidao_cenario = [-1.0]*(num_contingencias* num_carregamentos*(2**num_desligamentos) )

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
                
                # Uso da hash key para ja utilizar cenarios calculados
                hash_key = rede.hashtableindex(perfil, num_carregamentos, contingencia_atual, num_contingencias, estado_ramos)
                
                if _debug:
                    print("minha tabela hash:", len(setupobj.tabela_hash))
                #setupobj.tamanho_hash = hash_key
                
                #! RZ_01jun2025 - verifica se o cenário já foi calculado na tabela hash
                if setupobj.tabela_hash[hash_key] < 0.0:
                    #!DEBUG = Cenario 288 calculado, ai calcula o cenario 235 e da erro (porque ainda nao existe!)
                    
                    #! Simulação e modelagem usando pandapower com metodos da RedeEleticaPandawer em subtorinas
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
                    if rede.executar_fluxo_de_potencia():                            
                            # 10) Calcular violações com pesos e armazenar os resultados
                            fitness, violacoes_df = rede.calcular_violacoes_fitness()

                    else:
                            fitness = rede.pesos["demanda"] # penalidade com valor default de 99



                    # 11) Store violation in the hash table
                    #!debug = Ele esta salvando primeiro cenario, o hashtable existe mas o proximo cenario ainda nao foi calculado... 
                    setupobj.tabela_hash[hash_key] = fitness
                    rede.log(f"Hash key = { hash_key}\n")
                    
                    # incrementa contador de execuções da função objetivo
                    setupobj.objectiveruns += 1

                    #save hash key in excel
                    #pd.DataFrame(list(setupobj.tabela_hash.items())).to_excel("hash_table.xlsx", index=False)
                        
                        

                #! 12) Retorna o valores calculados de fluxo de potencia na variavel fitness
                else:
                  fitness = setupobj.tabela_hash[hash_key]
                  if _debug:
                      print("Fitness do cenario = ", fitness)
                  setupobj.hashtablereads += 1

                violacoes_total.append(fitness)

            #! Ver apenas o true in service de barras e transformadores
            rede.show_status()

        # 12) Calcular fitness final com somatorio das vioações com pesos de todos os cenarios
        fitness_final = sum(violacoes_total)
        rede.log(f"\nFitness do agendamento = {fitness_final:.2f}\n", level = "success")
        return fitness_final

    except Exception as e:
        print(f"\nErro ao calcular a função objetivo: {e}")

def generate_chart(data, chart_type='bar'):
    """
    Generates a chart of the specified type from the given data.

    Args:
        data (list): A list of tuples, where each tuple contains a label and a value.
        chart_type (str): The type of chart to generate ('bar', 'line', 'pie').

    Returns:
        str: A base64 encoded PNG image of the chart, or None if an error occurs.
    """
    try:
        # Prepare data for plotting
        labels, values = zip(*data)

        # Create the plot
        fig, ax = plt.subplots()

        if chart_type == 'bar':
            ax.bar(labels, values)
            ax.set_ylabel('Values')
            ax.set_title('Bar Chart')
        elif chart_type == 'line':
            ax.plot(labels, values, marker='o')
            ax.set_ylabel('Values')
            ax.set_title('Line Chart')
        elif chart_type == 'pie':
            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.set_title('Pie Chart')
        else:
            print(f"Error: Unknown chart type '{chart_type}'.")
            return None

        # Save the plot to a BytesIO object
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)

        # Encode the image to base64
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return image_base64

    except Exception as e:
        print(f"Error generating chart: {e}")
        return None

def simulate_IEEE_14_cenario(chart_type='bar'):
    """
    Simulates an IEEE 14 scenario and generates a chart of the fitness values.

    Args:
        chart_type (str): The type of chart to generate ('bar', 'line', 'pie').
    """
    horarios = [14,16,18,20,25]
    
    params_json = {
    "NUM_GENERATIONS": 40,
    "CROSSOVER": 0.95,
    "MUTACAO": 0.25,
    "POP_SIZE": 5,
    "IND_SIZE": 5,
    "RCE_REPOPULATION_GENERATIONS": 50,
    "NUM_VAR_DIFERENTES": 1,
    "PORCENTAGEM": 0.2,
    "DELTA_MIN": 2,
    "ARRAY_VAR": [
        14,
        15,
        14,
        18,
        15
    ],
    "LIMITE_VAR": [
        0,
        31
    ]
}
    
    setup_obj = Setup(
            params = params_json,
            fitness_function = funcao_objetivo_IEEE14,
        )
    
    # Collect fitness values for chart
    fitness_values = []
    num_simulations = 5  # Number of simulations
    
    for i in range(num_simulations):
        fitness = funcao_objetivo_IEEE14(
            individuo=horarios,
            setupobj= setup_obj,
            _debug = True
        )
        fitness_values.append(fitness)

    # Prepare data for chart
    chart_data = [(f"Simulation {i+1}", fitness) for i, fitness in enumerate(fitness_values)]

    # Generate chart
    chart_image = generate_chart(chart_data, chart_type)
    
    if chart_image:
        # The chart_image variable now contains the base64 encoded PNG image
        # You can save this to a file, display it in a web page, etc.
        # For example, to print it to the console:
        print(f"Chart image (base64): {chart_image}")

        # Alternatively, to save it to an HTML file to display it in a web browser:
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Fitness Chart</title>
        </head>
        <body>
            <h1>Fitness Chart</h1>
            <img src="data:image/png;base64,{chart_image}" alt="Fitness Chart">
        </body>
        </html>
        '''
        with open("fitness_chart.html", "w") as f:
            f.write(html_content)
        print("Chart saved to fitness_chart.html")
    else:
        print("Failed to generate chart.")
    
# Example usage
simulate_IEEE_14_cenario(chart_type='bar')  # You can change 'bar' to 'line' or 'pie'