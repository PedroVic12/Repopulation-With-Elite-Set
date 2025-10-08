# create_new_network_from_excel.py

```python
import pandapower as pp
import pandas as pd
import plotly.graph_objects as go

def read_excel_network(file_path):
    colunas = pd.ExcelFile(file_path).sheet_names
    if 'barras' not in colunas or 'linhas' not in colunas or 'cargas' not in colunas or 'geradores' not in colunas:
        raise ValueError("O arquivo Excel deve conter as folhas 'barras', 'linhas', 'cargas' e 'geradores'.")
    
    # Lê as folhas do Excel
    df_barras = pd.read_excel(file_path, sheet_name='barras')
    df_linhas = pd.read_excel(file_path, sheet_name='linhas')
    

    #df_cargas = pd.read_excel(file_path, sheet_name='cargas')
    #df_geradores = pd.read_excel(file_path, sheet_name='geradores')
    return df_barras, df_linhas

def read_network_pandapower(file_path):
    net = pp.from_excel(file_path)
    return net




def create_network(df_barras, df_linhas, df_cargas, df_geradores):
    net = pp.create_empty_network()
    for _, row in df_barras.iterrows():
        pp.create_bus(net, name=row['nome'], vn_kv=row['tensao'], index=row['id'])
    pp.create_ext_grid(net, bus=0, vm_pu=1.0, name="Slack")
    for _, row in df_linhas.iterrows():
        pp.create_line_from_parameters(
            net,
            from_bus=row['de'],
            to_bus=row['para'],
            length_km=row['comprimento_km'],
            r_ohm_per_km=row['r_ohm_per_km'],
            x_ohm_per_km=row['x_ohm_per_km'],
            c_nf_per_km=row['c_nf_per_km'],
            max_i_ka=row['max_i_ka'],
            name=row['nome']
        )
    for _, row in df_cargas.iterrows():
        pp.create_load(net, bus=row['bus'], p_mw=row['p_mw'], q_mvar=row['q_mvar'], name=row['nome'])
    for _, row in df_geradores.iterrows():
        pp.create_sgen(net, bus=row['bus'], p_mw=row['p_mw'], vm_pu=row['vm_pu'], name=row['nome'])
    return net

def run_power_flow(net):
    pp.runpp(net)
    return net

def analyze_contingency_pandapower(net):
    linhas_criticas = []

    # Desativa cada linha e verifica se o sistema ainda opera dentro dos limites
    net.line['in_service'] = True  # Garante que todas as linhas estão inicialmente ativas
    for linha in net.line.index:

        # Desativa a linha
        net.line.loc[linha, 'in_service'] = False
        
        try:
            # Executa o fluxo de Potencia
            pp.runpp(net )

            # Verifica se as tensões estão dentro dos limites e se as linhas estão sobrecarregadas
            if net.res_bus.vm_pu.max() > 1.05 or net.res_bus.vm_pu.min() < 0.95 or net.res_line.loading_percent.max() > 100:
                linhas_criticas.append(linha)
        except:
            print(f"Erro ao calcular o fluxo de carga com a linha {linha} desativada.")
        
        finally:
            # Reativa a linha para o próximo teste
            net.line.loc[linha, 'in_service'] = True
    
    
    return linhas_criticas

def plot_results(net, linhas_criticas):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=net.res_bus.index, y=net.res_bus.vm_pu, name="Tensão (pu)"))
    fig.update_layout(title="Tensões nas Barras", xaxis_title="Barras", yaxis_title="Tensão (pu)")
    fig.show()

    fig = go.Figure()
    fig.add_trace(go.Bar(x=net.res_line.index, y=net.res_line.i_ka, name="Corrente (kA)"))
    fig.update_layout(title="Correntes nas Linhas", xaxis_title="Linhas", yaxis_title="Corrente (kA)")
    fig.show()

    fig = go.Figure()
    fig.add_trace(go.Bar(x=net.res_load.index, y=net.res_load.p_mw, name="Potência Ativa (MW)"))
    fig.update_layout(title="Potências Ativas nas Cargas", xaxis_title="Cargas", yaxis_title="Potência Ativa (MW)")
    fig.show()

    if linhas_criticas:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=linhas_criticas, y=[net.res_line.loc[i, 'loading_percent'] for i in linhas_criticas], name="Linhas Críticas (%)"))
        fig.update_layout(title="Linhas Críticas", xaxis_title="Linhas", yaxis_title="Carregamento (%)")
        fig.show()

def main():
    file_path = r'assets/sistema_4_barras.xlsx'
    excel_path = r"C:\Users\pedrovictor.veras\Documents\GitHub\Repopulation-With-Elite-Set\src\RedeEletrica\assets\sistema_14_barras.xlsx"
    
    
    
    net_pandapower = read_network_pandapower(excel_path)
    print(net_pandapower)
    df_barras, df_linhas, df_cargas, df_geradores = read_excel_network(excel_path)
    net = create_network(df_barras, df_linhas, df_cargas, df_geradores)
    
    
    # fluxo de potencia
    net = run_power_flow(net)
    
    
    # Linhas criticas
    linhas_criticas = analyze_contingency_pandapower(net)
    plot_results(net, linhas_criticas)

if __name__ == "__main__":
    main()

```