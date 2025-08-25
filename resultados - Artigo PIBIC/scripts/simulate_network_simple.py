import pandapower as pp
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from IPython.display import display


def simulate_NEW_network():
    # Criando a rede elétrica vazia
    net = pp.create_empty_network()


    # Dados fictícios para as barras (12 barras: 6 à esquerda, 6 à direita)
    barras = [
        {"id": 0, "nome": "Barra 1E", "tensao": 1.05},  # Barra de referência (Slack)
        {"id": 1, "nome": "Barra 2E", "tensao": 1.02},
        {"id": 2, "nome": "Barra 3E", "tensao": 20.0},
        {"id": 3, "nome": "Barra 4E", "tensao": 20.0},
        {"id": 4, "nome": "Barra 5E", "tensao": 20.0},
        {"id": 5, "nome": "Barra 6E", "tensao": 20.0},
        {"id": 6, "nome": "Barra 1D", "tensao": 20.0},
        {"id": 7, "nome": "Barra 2D", "tensao": 20.0},
        {"id": 8, "nome": "Barra 3D", "tensao": 20.0},
        {"id": 9, "nome": "Barra 4D", "tensao": 20.0},
        {"id": 10, "nome": "Barra 5D", "tensao": 20.0},
        {"id": 11, "nome": "Barra 6D", "tensao": 20.0},
    ]

    # Linhas conectando as barras em dois ramos (esquerdo e direito) e uma ligação central
    linhas = [
        # Lado Esquerdo (E)
        {"de": 0, "para": 1, "r_ohm_per_km": 0.01, "x_ohm_per_km": 0.03, "c_nf_per_km": 10, "max_i_ka": 0.2, "comprimento_km": 1.0},
        {"de": 1, "para": 2, "r_ohm_per_km": 0.01, "x_ohm_per_km": 0.03, "c_nf_per_km": 10, "max_i_ka": 0.2, "comprimento_km": 1.0},
        {"de": 2, "para": 3, "r_ohm_per_km": 0.01, "x_ohm_per_km": 0.03, "c_nf_per_km": 10, "max_i_ka": 0.2, "comprimento_km": 1.0},
        {"de": 3, "para": 4, "r_ohm_per_km": 0.01, "x_ohm_per_km": 0.03, "c_nf_per_km": 10, "max_i_ka": 0.2, "comprimento_km": 1.0},
        {"de": 4, "para": 5, "r_ohm_per_km": 0.01, "x_ohm_per_km": 0.03, "c_nf_per_km": 10, "max_i_ka": 0.2, "comprimento_km": 1.0},
        # Lado Direito (D)
        {"de": 6, "para": 7, "r_ohm_per_km": 0.01, "x_ohm_per_km": 0.03, "c_nf_per_km": 10, "max_i_ka": 0.2, "comprimento_km": 1.0},
        {"de": 7, "para": 8, "r_ohm_per_km": 0.01, "x_ohm_per_km": 0.03, "c_nf_per_km": 10, "max_i_ka": 0.2, "comprimento_km": 1.0},
        {"de": 8, "para": 9, "r_ohm_per_km": 0.01, "x_ohm_per_km": 0.03, "c_nf_per_km": 10, "max_i_ka": 0.2, "comprimento_km": 1.0},
        {"de": 9, "para": 10, "r_ohm_per_km": 0.01, "x_ohm_per_km": 0.03, "c_nf_per_km": 10, "max_i_ka": 0.2, "comprimento_km": 1.0},
        {"de": 10, "para": 11, "r_ohm_per_km": 0.01, "x_ohm_per_km": 0.03, "c_nf_per_km": 10, "max_i_ka": 0.2, "comprimento_km": 1.0},
        # Ligação central entre os dois lados
        {"de": 2, "para": 8, "r_ohm_per_km": 0.02, "x_ohm_per_km": 0.04, "c_nf_per_km": 15, "max_i_ka": 0.2, "comprimento_km": 1.5},
        {"de": 5, "para": 11, "r_ohm_per_km": 0.02, "x_ohm_per_km": 0.04, "c_nf_per_km": 15, "max_i_ka": 0.2, "comprimento_km": 1.5},
    ]

    # Criando as barras
    for barra in barras:
        pp.create_bus(net, name=barra["nome"], vn_kv=barra["tensao"], index=barra["id"])

    # Criando a barra de referência (Slack)
    pp.create_ext_grid(net, bus=0, vm_pu=1.0, name="Slack")


    # Criando as linhas
    for linha in linhas:
        pp.create_line_from_parameters(
            net,
            from_bus=linha["de"],
            to_bus=linha["para"],
            length_km=linha["comprimento_km"],
            r_ohm_per_km=linha["r_ohm_per_km"],
            x_ohm_per_km=linha["x_ohm_per_km"],
            c_nf_per_km=linha["c_nf_per_km"],
            max_i_ka=linha["max_i_ka"],
            name=f"Linha {linha['de']} -> {linha['para']}",
        )

    # Dados fictícios para as cargas
    cargas = [
        {"bus": 1, "p_mw": 0.02, "q_mvar": 0.01, "nome": "Carga 1"},
        {"bus": 2, "p_mw": 0.03, "q_mvar": 0.015, "nome": "Carga 2"},
    ]

    # Criando as cargas
    for carga in cargas:
        pp.create_load(net, bus=carga["bus"], p_mw=carga["p_mw"], q_mvar=carga["q_mvar"], name=carga["nome"])

    # Dados fictícios para os geradores
    geradores = [
        {"bus": 3, "p_mw": 0.05, "vm_pu": 1.02, "nome": "Gerador PV"},
    ]

    # Criando os geradores
    for gerador in geradores:
        pp.create_sgen(net, bus=gerador["bus"], p_mw=gerador["p_mw"], vm_pu=gerador["vm_pu"], name=gerador["nome"])

    # Executando o fluxo de potência
    pp.runpp(net)

    # Exibindo os resultados
    print(f"Resultados de Sistema Elétrico de Potencia com {len(barras)} Barras:")
    print("""
        VM_PU = Tensões em pu em cada barra
        va_degree = Angulo de fase em graus
        p_mw  = Potencia Aparente em MW
        q_mvar = Potencia Reativa em MW

        + -> Potencia Demandada
        - -> Potencia Gerada
        """)
    display(net.res_bus)

    print("\nResultados das Linhas:")
    display(net.res_line)

    print("\nResultados das Cargas:")
    display(net.res_load)

    return net


def plot_results(net):
    # Plot das tensões nas barras
    fig = go.Figure()
    fig.add_trace(go.Bar(x=net.res_bus.index, y=net.res_bus.vm_pu, name="Tensão (pu)"))
    #fig.add_trace(go.Pie(x=net.res_line, y=net.res_bus.vm_pu, name="Ângulo (graus)", textinfo='label+percent'))
    fig.update_layout(title="Tensões nas Barras", xaxis_title="Barras", yaxis_title="Tensão (pu)")
    fig.show()

    # Plot das correntes nas linhas
    fig = go.Figure()
    fig.add_trace(go.Bar(x=net.res_line.index, y=net.res_line.i_ka, name="Corrente (kA)"))
    fig.update_layout(title="Correntes nas Linhas", xaxis_title="Linhas", yaxis_title="Corrente (kA)")
    fig.show()

    # Plot das potências nas cargas
    fig = go.Figure()
    fig.add_trace(go.Bar(x=net.res_load.index, y=net.res_load.p_mw, name="Potência Ativa (MW)"))
    fig.update_layout(title="Potências Ativas nas Cargas", xaxis_title="Cargas", yaxis_title="Potência Ativa (MW)")
    fig.show()

    
    fig.to_html("./network_results.html")



def main_simulate():
    net = simulate_NEW_network()
    plot_results(net)

main_simulate()
