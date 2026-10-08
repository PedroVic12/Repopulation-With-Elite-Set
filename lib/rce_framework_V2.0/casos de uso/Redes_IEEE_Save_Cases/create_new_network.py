import pandapower as pp
import pandapower.plotting as plot
import pandas as pd
import plotly.graph_objects as go
from IPython.display import display
import os
from pandapower.plotting import simple_plot, simple_plotly, pf_res_plotly

def simulate_NEW_network():
    net = pp.create_empty_network()

    barras = [
        {"id": 0, "nome": "Barra 1E", "tensao": 1.05},
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
        {"id": 12, "nome": "Barra 7D", "tensao": 20.0},
        {"id": 13, "nome": "Barra 8D", "tensao": 20.0},
        {"id": 14, "nome": "Barra 9D", "tensao": 20.0},
        {"id": 15, "nome": "Barra 10D", "tensao": 20.0},
        {"id": 16, "nome": "Barra 11D", "tensao": 20.0},
        {"id": 17, "nome": "Barra 12D", "tensao": 20.0},
        {"id": 18, "nome": "Barra 13D", "tensao": 20.0},
        {"id": 19, "nome": "Barra 14D", "tensao": 20.0},
        {"id": 20, "nome": "Barra 15D", "tensao": 20.0},
        {"id": 21, "nome": "Barra 16D", "tensao": 20.0},
        {"id": 22, "nome": "Barra 17D", "tensao": 20.0},
        {"id": 23, "nome": "Barra 18D", "tensao": 20.0},
    ]

    linhas = [
        {"de": 0, "para": 1}, {"de": 1, "para": 2}, {"de": 2, "para": 3},
        {"de": 3, "para": 4}, {"de": 4, "para": 5}, {"de": 6, "para": 7},
        {"de": 7, "para": 8}, {"de": 8, "para": 9}, {"de": 9, "para": 10},
        {"de": 10, "para": 11}, {"de": 2, "para": 8}, {"de": 5, "para": 11},
        {"de": 12, "para": 13}, {"de": 13, "para": 14}, {"de": 14, "para": 15},
        {"de": 15, "para": 16}, {"de": 16, "para": 17}, {"de": 18, "para": 19},
        {"de": 19, "para": 20}, {"de": 20, "para": 21}, {"de": 21, "para": 22},
        {"de": 22, "para": 23}, {"de": 23, "para": 12}, {"de": 1, "para": 6},
        {"de": 3, "para": 9}, {"de": 5, "para": 11}, {"de": 7, "para": 13},
        {"de": 8, "para": 14}, {"de": 10, "para": 16}, {"de": 12, "para": 18},
    ]

    for barra in barras:
        pp.create_bus(net, name=barra["nome"], vn_kv=barra["tensao"], index=barra["id"])
        # Criando a barra de referência (Slack)
        # A barra 0 é a barra de referência, com tensão de 1.05 
            


    pp.create_ext_grid(net, bus=0, vm_pu=1.0, name="Slack")

    for linha in linhas:
        pp.create_line_from_parameters(
            net, from_bus=linha["de"], to_bus=linha["para"],
            length_km=1.0, r_ohm_per_km=0.01, x_ohm_per_km=0.03,
            c_nf_per_km=10, max_i_ka=0.2, name=f"Linha {linha['de']}->{linha['para']}"
        )

    pp.create_load(net, bus=1, p_mw=0.02, q_mvar=0.01, name="Carga 1")
    pp.create_load(net, bus=2, p_mw=0.03, q_mvar=0.015, name="Carga 2")
    # Criando um gerador fotovoltaico na barra 3
    # com potência ativa de 0.05 MW e tensão de 1.02 pu

    

    pp.create_sgen(net, bus=3, p_mw=0.05, vm_pu=1.02, name="Gerador PV")

    pp.runpp(net)
    return net


def plot_result_type(df, coluna, tipo="barras", titulo="", eixo_x="", eixo_y=""):
    fig = go.Figure()

    if tipo == "barras":
        fig.add_trace(go.Bar(x=df.index, y=df[coluna], name=coluna))
    elif tipo == "linhas":
        fig.add_trace(go.Scatter(x=df.index, y=df[coluna], mode='lines+markers', name=coluna))
    elif tipo == "pizza":
        fig = go.Figure(data=[go.Pie(labels=df.index.astype(str), values=df[coluna])])
    else:
        raise ValueError("Tipo inválido: escolha entre 'barras', 'linhas' ou 'pizza'.")

    fig.update_layout(title=titulo, xaxis_title=eixo_x, yaxis_title=eixo_y)
    return fig


def carregar_diagrama(net):
    fig = pf_res_plotly(net)
    return fig

def gerar_dashboard_html(net):
    figs = []

    # plot 0: Desenho da rede
    display(pf_res_plotly(net))
    figs.append(pf_res_plotly(net))

    # Plot 1: Tensões nas barras
    figs.append(plot_result_type(net.res_bus, "vm_pu", tipo="barras", titulo="Tensões nas Barras", eixo_x="Barra", eixo_y="Tensão (pu)"))

    # Plot 2: Correntes nas linhas
    figs.append(plot_result_type(net.res_line, "i_ka", tipo="linhas", titulo="Correntes nas Linhas", eixo_x="Linha", eixo_y="Corrente (kA)"))

    # Plot 3: Potência nas cargas
    figs.append(plot_result_type(net.res_load, "p_mw", tipo="pizza", titulo="Potência nas Cargas", eixo_x="Carga", eixo_y="Potência (MW)"))

    # Plot 4: Diagrama da rede
    #plot.simple_plot(net, respect_switches=True)
    simple_plotly(net, respect_switches=True)

    # Estatísticas do sistema
    info = f"""
    <h2>Resumo do Sistema Elétrico</h2>
    <ul>
        <li><b>{len(net.bus)}</b> Barras</li>
        <li><b>{len(net.line)}</b> Linhas</li>
        <li><b>{len(net.load)}</b> Cargas</li>
        <li><b>{len(net.sgen)}</b> Geradores</li>
        <li><b>{len(net.trafo)}</b> Transformadores</li>
    </ul>
    """

    # Checagem simples de violações
    violacoes = ""
    tensoes_invalidas = net.res_bus[(net.res_bus.vm_pu < 0.95) | (net.res_bus.vm_pu > 1.05)]
    if not tensoes_invalidas.empty:
        violacoes += "<p><b>Atenção:</b> Violações de tensão detectadas nas barras:</p>"
        violacoes += tensoes_invalidas.to_html()
    else:
        violacoes += "<p>✅ Nenhuma violação de tensão detectada.</p>"

    # Salvar tudo num HTML
    html_path = "dashboard_result.html"
    with open(html_path, "w") as f:
        f.write("<html><head><title>Relatório do Sistema</title></head><body>")
        f.write(info + violacoes)
        f.write("<h3>Resultados Numéricos</h3>")
        f.write("<h3>Tensões nas Barras</h3>")
        f.write(net.res_bus.to_html())
        f.write("<h3>Potencia nas Linhas</h3>")
        f.write(net.res_line.to_html())
        f.write("<h3>Potencia nas Cargas</h3>")
        f.write(net.res_load.to_html())
        for fig in figs:
            f.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))
        f.write("</body></html>")

    print(f"✅ Relatório gerado: {html_path}")


def main_simulate():
    net = simulate_NEW_network()
    gerar_dashboard_html(net)


# --- EXECUTA ---
main_simulate()
