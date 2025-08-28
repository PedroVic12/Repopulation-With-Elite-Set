
import sys
import pandas as pd
import pandapower as pp

def main(net_file, output_file):
    # Este script é um reprodutor de erro para depuração.
    # Ele tenta gerar o plot pf_res_plotly e salvar o HTML.
    # A saída de erro será capturada pelo processo pai.

    net = pp.from_json(net_file)
    fig = pp.plotting.pf_res_plotly(net, auto_open=False)
    plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(plot_html)

if __name__ == '__main__':
    # Argumentos: script, net_file, output_file
    if len(sys.argv) != 3:
        print(f"Uso: python {sys.argv[0]} <net_file> <output_file>", file=sys.stderr)
        sys.exit(1)
    
    main(sys.argv[1], sys.argv[2])
