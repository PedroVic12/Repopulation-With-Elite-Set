
import numpy as np
import pandas as pd
import streamlit as st

# Import RCE Framework
from AlgEvolutivoRCE.Setup import Setup, params
from AlgEvolutivoRCE.alg_evolutivo_rce import AlgoritimoEvolutivoRCE
from AlgEvolutivoRCE.Dashboard import DashboardApp
from utils.functions_fitness.functions_benchmarking import rosenbrock_benchmark,esfera_benchmark,rastrigin, evaluate
from RedeEletrica.rede_eletrica import RedeEletricaPandaPower


# Utils 
from config import FOLDER_NAME, options_main_file
import json
import pathlib
import time
from IPython.display import display


execution_times = []  # Lista para armazenar os tempos de execução
results_consolidados = []  # Lista para armazenar os resultados consolidadosimport pandas as pd
import pandapower as pp
import pandapower.networks as ppnets
import pandapower.plotting as ppl
from pandapower.plotting.plotly import pf_res_plotly

import matplotlib.pyplot as mplt
import numpy as np

# Supondo que RedeEletricaPandaPower seja uma classe definida
network_name = "14"
rede = RedeEletricaPandaPower(network_name, debug=True)
net = rede.net
exibir_tabelas = False

# Aumentar o estresse na rede significa que mais linhas se tornam críticas,
# o que é bom para fins de demonstração da análise de contingência.

# Desativar a subestação externa (external grid)
net.ext_grid['in_service'] = False

# Aumentar a carga padrão para estressar ainda mais a rede:
net.load.scaling = 1.5

# Ajustar as tensões terminais dos geradores para que as tensões dos barramentos e estejam dentro de uma faixa mais prática, de 0.95 pu a 1.05 pu.
net.gen['vm_pu'] = 1.045

# Realizar um despacho simples de geradores maximizando os três primeiros geradores e definindo o quarto como slack.
net.gen.loc[0, 'p_mw'] = 120
net.gen.loc[1, 'p_mw'] = 100
net.gen.loc[2, 'p_mw'] = 100
net.gen.loc[3, 'slack'] = True

# Executar o Fluxo de Potência na condição base
pp.runpp(net, numba=False)
print("Fluxo de Potencia executado!")

# Imprimir a Geração Total e a Carga como uma Verificação Rápida
gen_mw_total = net.res_gen['p_mw'].sum()
imports_mw_total = net.res_ext_grid['p_mw'].sum()

print('Geração total em MW:', gen_mw_total + imports_mw_total)
print('Geração total importada em MW:', imports_mw_total)
print('Geração total local em MW:', gen_mw_total)
print('Carga total em MW:', net.res_load['p_mw'].sum())

# Exibir tabelas se solicitado
if exibir_tabelas:
                print("\n--- Tabelas Detalhadas da Rede ---")
                print(f"Nome da Rede: IEEE {network_name}")
                print("\nEstrutura Completa da Rede (Objeto 'net'):")
                print(net)

                if 'gen' in net:
                    print("\nTabela de Geradores ('net.gen'):")
                    display(net.gen)


                if 'load' in net:
                    print("\nTabela de Cargas ('net.load'):")
                    display(net.load)


                if 'res_gen' in net:
                     print("\nTabela de Resultados dos Geradores ('net.res_gen'):")
                     display(net.res_gen)


                if 'res_bus' in net:
                    print("\nTabela de Resultados dos Barramentos ('net.res_bus'):")
                    display(net.res_bus)


                # Adicionar outras tabelas comuns se existirem na sua rede
                if 'line' in net:
                     print("\nTabela de Linhas ('net.line'):")
                     display(net.line)


                if 'res_line' in net:
                     print("\nTabela de Resultados das Linhas ('net.res_line'):")
                     display(net.res_line)


                if 'trafo' in net:
                     print("\nTabela de Transformadores ('net.trafo'):")
                     display(net.trafo)

                if 'res_trafo' in net:
                     print("\nTabela de Resultados dos Transformadores ('net.res_trafo'):")
                     display(net.res_trafo)


                print("\n--- Fim das Tabelas ---")


# --- Análise de Contingência para encontrar linhas críticas ---

def realizar_analise_contingencia(rede, vmax=1.05, vmin=0.95, line_loading_max=100):
    """
    Realiza a análise de contingência para cada linha na rede
    e retorna os índices das linhas críticas.
    """
    linhas = rede.line.index
    indices_linhas_criticas = []

    print("\nRealizando análise de contingência para as linhas...")
    for l in linhas:
        # Temporariamente desativar a linha (simulando a contingência)
        rede.line.loc[l, 'in_service'] = False
        try:
            # Executar o fluxo de potência com a contingência
            pp.runpp(rede, numba=False)

            # Verificar violações (limites de tensão e carregamento de linha)
            if rede.res_bus.vm_pu.max() > vmax or rede.res_bus.vm_pu.min() < vmin or rede.res_line.loading_percent.max() > line_loading_max:
                indices_linhas_criticas.append(l)

        except pp.LoadflowNotConverged:
            print(f"Fluxo de potência não convergiu para a contingência da linha {l}. Considerada crítica.")
            indices_linhas_criticas.append(l)
        except Exception as e:
            print(f"Ocorreu um erro durante o fluxo de potência para a contingência da linha {l}: {e}")
            # Dependendo dos requisitos da sua análise, você pode querer tratar outros erros como críticos
            # indices_linhas_criticas.append(l)
        finally:
            # Sempre retornar a linha ao serviço
            rede.line.loc[l, 'in_service'] = True
            # Executar o fluxo de potência na condição base novamente se o fluxo de potência falhou durante a contingência
            pp.runpp(rede, numba=False)

    return list(set(indices_linhas_criticas)) # Remover duplicatas



# --- Plotagem com cores de status ---
def plotar_rede_com_status(rede, indices_linhas_criticas):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    bus_color = ['green' if status else 'gray' for status in rede.bus.in_service]

    line_color = []

    for i in rede.line.index:
        if not rede.line.at[i, 'in_service'] or i in indices_linhas_criticas:
            line_color.append('orange')
        else:
            line_color.append('blue')

    trafo_color = ['green' if status else 'gray' for status in rede.trafo.in_service] if not rede.trafo.empty else None



    ax = ppl.simple_plot(
        rede,

        bus_color=bus_color,
        line_color=line_color,
        trafo_color=trafo_color,
        ext_grid_color='black',


        ext_grid_size=3.0,
        line_width=2.0,
        bus_size=3,
        trafo_size=4,
        switch_size = 4,
        bus_dc_size = 4,

        plot_sgens = True,
        plot_line_switches=True,
        plot_loads = True,
        respect_switches = True,


    )

    legenda = [
        Line2D([0], [0], marker='o', color='w', label='Barramento Ativo',
               markerfacecolor='green', markersize=10),
        Line2D([0], [0], color='blue', lw=2, label='Linha Normal'),
        Line2D([0], [0], color='orange', lw=2, linestyle='--', label='Linha Crítica/Inativa'),
        Line2D([0], [0], color='green', lw=2, label='Trafo Ativo'),
        Line2D([0], [0], color='gray', lw=2, linestyle='--', label='Trafo Inativo'),
    ]

    ax.legend(handles=legenda, loc='best')
    ax.set_title("Status da Rede Elétrica IEEE 14 - Inclusiva")
    ax.set_xlabel("Eixo X")
    ax.set_ylabel("Eixo Y")
    ax.grid(True)

    plt.show()



# Executar a análise de contingência
critical_lines_indx = realizar_analise_contingencia(net)
print(f"Índices das linhas críticas = {critical_lines_indx} ")

# Executar a plotagem
plotar_rede_com_status(net, critical_lines_indx)

print("\n\nPlot da Rede com cores de status pela tensão nos barramentos")
ppl.pf_res_plotly(net,  line_width= 5, bus_size= 40)


def load_many_executions(dict_key_value, dashboard, algoritmo):
    if dict_key_value["key"]:

        for i in range(dict_key_value["value"]):
            print("\nExecução", i + 1)

            start_time = time.time()  # Inicia a contagem do tempo para cada execução

            # Loop principal do Algoritmo Evolutivo
            pop_with_repopulation, logbook_with_repopulation, best_variables = algoritmo.run(RCE=True)
            print("\n\nEvolução concluída  - 100%")

            # Resultados
            x, y, z, grafico = dashboard.visualize(logbook_with_repopulation, pop_with_repopulation, execution_num=i + 1)

            grafico.show()

            end_time = time.time()  # Finaliza a contagem do tempo para cada execução
            execution_time = end_time - start_time
            execution_times.append(execution_time)  # Armazena o tempo de execução

            # Append results to the list
            results_consolidados.append({"execution": i + 1, "solution_variables": y, "best_fitness": z, "best_generations": x,"execution_time": execution_time})

    else: # Use st.pyplot with stash=False to prevent overwriting
        print("False! Rodando o framework uma unica vez!")
        start_time = time.time()  # Inicia a contagem do tempo para a execução única

        # Loop principal do Algoritmo Evolutivo
        pop_with_repopulation, logbook_with_repopulation, best_variables = algoritmo.run(RCE=True)
        print("\n\nEvolução concluída  - 100%")

        # Resultados
        x, y, z, fig = dashboard.visualize(logbook_with_repopulation, pop_with_repopulation)

        end_time = time.time()  # Finaliza a contagem do tempo para a execução única
        execution_time = end_time - start_time

        # Append results to the list (for single execution)
        results_consolidados.append({"execution": i + 1, "solution_variables": y, "best_fitness": z, "best_generations": x,"execution_time": execution_time})

        print(f"Tempo de execução: {execution_time:.2f} segundos")

    # Calcula a média e o desvio padrão dos tempos de execução
    avg_execution_time = np.mean(execution_times)
    std_execution_time = np.std(execution_times)

    print(f"Tempo médio de execução: {avg_execution_time:.2f} segundos")
    print(f"Desvio padrão do tempo de execução: {std_execution_time:.2f} segundos")


    # Create the DataFrame
    results_consolidados_df = pd.DataFrame(results_consolidados)

    results_consolidados_df["execution_time"] = results_consolidados_df["execution_time"].apply(lambda x: f"{x:.2f} segundos")

    # exportar para excel
    results_consolidados_df.to_excel("results_consolidados.xlsx", index=False)

     # Display or use the results
    print("\nResultados Consolidados:")
    display(results_consolidados_df)
    results_consolidados_df.sort_values(by="best_fitness", inplace=True)
    results_consolidados_df.describe()
    
    
if __name__ == "__main__":
    import pandas as pd
    import numpy as np
    from IPython.display import display

    configuracoes_execucoes = {
            "key": True,
            "value": 5,
            "parametros_opcionais": [
                {"MUTACAO": [90,80,70]},
                {"CROSSOVER": [90,80,70]},
                {'NUM_GENERATIONS': [100, 200, 300]},

            ]
    }


    # Inicializa a configuração do algoritmo
    configuracao_algoritmo = Setup(params, rastrigin)

    # Inicializa o algoritmo
    algoritmo_evolutivo = AlgoritimoEvolutivoRCE(configuracao_algoritmo, DEBUG=False)

    # Inicializa o dashboard
    painel_controle = DashboardApp(configuracao_algoritmo)

    # Carrega dados de execuções
    load_many_executions(configuracoes_execucoes, painel_controle, algoritmo_evolutivo)