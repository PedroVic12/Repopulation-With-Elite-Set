import sys
import pandas as pd
import pandapower as pp
from datetime import datetime
import traceback

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Análise da Rede Elétrica - ONS</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-100 text-slate-800 font-sans">
    <div class="container mx-auto p-4 sm:p-6">
        <header class="bg-white p-5 rounded-t-lg shadow-md border-b-4 border-blue-700 flex justify-between items-center">
            <div>
                <h1 class="text-2xl font-bold text-slate-900">Relatório de Análise de Fluxo de Potência</h1>
                <p class="text-base text-slate-600">Sistema Interligado Nacional - Modelo SIN 45 Barras</p>
            </div>
            <div class="text-right">
                <p class="font-semibold text-xl text-blue-800">ONS</p>
                <p class="text-xs text-slate-500">Operador Nacional do Sistema Elétrico</p>
            </div>
        </header>
        <main class="bg-white p-6 rounded-b-lg shadow-md">
            <div class="mb-6 p-4 bg-slate-50 rounded-md border border-slate-200">
                <h2 class="text-lg font-semibold mb-2 text-slate-700">Contextualização</h2>
                <p class="text-sm leading-relaxed">Este relatório apresenta uma análise de fluxo de potência para o sistema-teste de 45 Barras, uma representação da rede de alta tensão que abrange partes das regiões Sudeste e Centro-Oeste, essencial para estudos de estabilidade e planejamento da operação do Sistema Interligado Nacional (SIN).</p>
            </div>
            <div>
                <div class="border-b border-slate-200">
                    <nav class="-mb-px flex space-x-6" id="myTab">{tab_buttons}</nav>
                </div>
                <div class="mt-4" id="myTabContent">{tab_contents}</div>
            </div>
        </main>
        <footer class="text-center mt-6 text-xs text-slate-500">
            <p>Relatório gerado em {generation_date}. Dados para fins de simulação.</p>
        </footer>
    </div>
</body>
</html>
"""

def create_report(net_file, data_file, template_file, output_file, log_file):
    try:
        with open(log_file, 'w', encoding='utf-8') as log:
            log.write(f"[{datetime.now()}] Iniciando geração do relatório.\n")
            
            log.write(f"Lendo template de: {template_file}\n")
            with open(template_file, 'r', encoding='utf-8') as f:
                template_str = f.read()
            
            log.write(f"Lendo dados da rede de: {net_file}\n")
            net = pp.from_json(net_file)
            
            log.write(f"Lendo tabelas de dados de: {data_file}\n")
            xls = pd.ExcelFile(data_file)
            all_dfs = {str(name): pd.read_excel(xls, name) for name in xls.sheet_names}
            log.write("Dados carregados com sucesso.\n")

            log.write("Sanitizando todos os dataframes para string...\n")
            sanitized_dfs = {name: df.astype(str) for name, df in all_dfs.items() if df is not None and not df.empty}
            log.write("Sanitização concluída.\n")

            log.write("Gerando gráfico interativo...\n")
            fig = pp.plotting.pf_res_plotly(net, auto_open=False)
            plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
            log.write("Gráfico gerado.\n")

            log.write("Gerando componentes HTML (legenda e abas)...\n")
            legend_data = {
                'Linhas de Transmissão': 'bg-gray-400',
                'Transformadores': 'bg-purple-500',
                'Cargas': 'bg-red-500',
                'Geradores': 'bg-green-500',
                'Grid Externo (Slack)': 'bg-orange-500',
                'Reatores (Shunt)': 'bg-cyan-400'
            }
            legend_rows = "".join([f'<tr><td class="py-2 px-3"><div class="h-4 w-4 rounded-full {c}"></div></td><td class="py-2 px-3 text-sm">{n}</td></tr>' for n, c in legend_data.items()])
            legend_table_html = f'<table class="w-full"><tbody>{legend_rows}</tbody></table>'

            table_htmls = {name: df.to_html(classes='table-auto w-full text-sm text-left', border=0, index=False) for name, df in sanitized_dfs.items()}
            
            tab_buttons = '<button data-target="#content-plot" class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm border-indigo-500 text-indigo-600">Diagrama Interativo</button>'
            tab_contents = f'<div id="content-plot" class="tab-pane active"><div class="h-[85vh]">{plot_html}</div></div>'
            for name, table_html in table_htmls.items():
                tab_name = str(name).replace("_", " ").title()
                tab_buttons += f'<button data-target="#content-{name}" class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300">{tab_name}</button>'
                tab_contents += f'<div id="content-{name}" class="tab-pane hidden">{table_html}</div>' # Usando hidden para consistência
            log.write("Componentes HTML gerados.\n")

            log.write("Preenchendo template final...\n")
            full_html = template_str.format(
                legend_table=legend_table_html,
                tab_buttons=tab_buttons,
                tab_contents=tab_contents
            )

            log.write(f"Salvando relatório em: {output_file}\n")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_html)
            
            log.write("\n--- SUCESSO ---\n")

    except Exception as e:
        # Se qualquer coisa falhar, grava o erro detalhado no log
        with open(log_file, 'a', encoding='utf-8') as log:
            log.write("\n--- FALHA CRÍTICA ---\n")
            log.write(traceback.format_exc())
        # Re-levanta a exceção para que o subprocesso retorne um código de erro
        raise

if __name__ == '__main__':
    # Argumentos: script, net_file, data_file, template_file, output_file, log_file
    if len(sys.argv) != 6:
        # Escreve o erro de uso no próprio log, que é o último argumento
        log_path = sys.argv[5] if len(sys.argv) > 5 else 'logs.txt'
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"Erro de uso do script. Esperava 5 argumentos, recebeu {len(sys.argv) - 1}\n")
            f.write(f"Argumentos: {sys.argv}\n")
        sys.exit(1)

    create_report(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])