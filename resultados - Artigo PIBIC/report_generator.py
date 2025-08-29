import sys
import pandas as pd
import pandapower as pp
from datetime import datetime
import traceback
import os
import argparse

def create_report(net_file, data_file, template_file, output_file, log_file):
    """
    Gera um relatório HTML a partir de uma rede pandapower, dados do Excel e um template HTML.

    Args:
        net_file (str): Caminho para o ficheiro JSON da rede pandapower.
        data_file (str): Caminho para o ficheiro Excel com dados suplementares.
        template_file (str): Caminho para o ficheiro de template HTML.
        output_file (str): Caminho para o relatório HTML gerado.
        log_file (str): Caminho para o ficheiro de log.
    """
    try:
        with open(log_file, 'w', encoding='utf-8') as log:
            log.write(f"[{datetime.now()}] A iniciar a geração do relatório.\n")
            log.write(f"Argumentos recebidos:\n")
            log.write(f"  net_file: {net_file}\n")
            log.write(f"  data_file: {data_file}\n")
            log.write(f"  template_file: {template_file}\n")
            log.write(f"  output_file: {output_file}\n")
            log.write(f"  log_file: {log_file}\n\n")
            
            # --- 1. Verificar Ficheiros de Entrada ---
            log.write("--- A verificar ficheiros de entrada ---\n")
            # (O resto do código permanece igual)
            for file_path, file_desc in [
                (net_file, "Ficheiro de rede"),
                (data_file, "Ficheiro de dados"),
                (template_file, "Template HTML")
            ]:
                if os.path.exists(file_path):
                    log.write(f"✓ {file_desc} encontrado: {file_path}\n")
                else:
                    log.write(f"✗ {file_desc} NÃO encontrado: {file_path}\n")
            
            # --- 2. Ler Template HTML ---
            log.write(f"\n--- A ler template de: {template_file} ---\n")
            with open(template_file, 'r', encoding='utf-8') as f:
                template_str = f.read()
            log.write(f"Template carregado, tamanho: {len(template_str)} caracteres\n")
            
            # --- 3. Carregar Rede Pandapower ---
            log.write(f"\n--- A ler dados da rede de: {net_file} ---\n")
            net = pp.from_json(net_file)

            if net is None or len(net.bus) == 0:
                log.write(f"✗ ERRO CRÍTICO: A rede não foi carregada ou está vazia. Verifique o ficheiro '{net_file}'.\n")
                return

            log.write(f"Rede carregada com sucesso:\n")
            log.write(f"  - Barras: {len(net.bus)}\n")
            log.write(f"  - Linhas: {len(net.line)}\n")
            
            # --- 4. Carregar Dados do Excel ---
            log.write(f"\n--- A ler tabelas de dados de: {data_file} ---\n")
            all_dfs = {}
            if os.path.exists(data_file):
                try:
                    xls = pd.ExcelFile(data_file)
                    log.write(f"Folhas encontradas no Excel: {xls.sheet_names}\n")
                    for sheet_name in xls.sheet_names:
                        df = pd.read_excel(xls, sheet_name, index_col=0)
                        all_dfs[str(sheet_name)] = df
                    log.write("Dados do Excel carregados com sucesso.\n")
                except Exception as e:
                    log.write(f"Erro ao carregar ficheiro Excel: {e}\n")
            else:
                log.write("Ficheiro Excel não encontrado.\n")

            # --- 5. Limpar DataFrames ---
            log.write("\n--- A limpar DataFrames ---\n")
            sanitized_dfs = {}
            for name, df in all_dfs.items():
                if df is not None and not df.empty:
                    try:
                        sanitized_dfs[name] = df.round(4).fillna('N/A').astype(str)
                        log.write(f"  ✓ {name}: limpo\n")
                    except Exception as e:
                        log.write(f"  ✗ Erro ao limpar {name}: {e}\n")
            
            # --- 6. Gerar Gráfico Interativo ---
            log.write("\n--- A gerar gráfico interativo do Pandapower ---\n")
            plot_html = ""
            try:
                # CORREÇÃO: Prioriza pf_res_plotly se os resultados existirem
                if hasattr(net, 'res_bus') and net.res_bus is not None and not net.res_bus.empty:
                    log.write("Resultados de fluxo de potência encontrados. A usar pf_res_plotly().\n")
                    fig = pp.plotting.pf_res_plotly(net, auto_open=False)
                    plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
                    log.write("✓ Gráfico de resultados (Plotly) gerado com sucesso.\n")
                else:
                    log.write("⚠️ Rede não tem resultados de fluxo de potência. A usar simple_plotly() como fallback.\n")
                    fig = pp.plotting.simple_plotly(net, auto_open=False)
                    plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
                    log.write("✓ Gráfico de topologia básica gerado com sucesso.\n")
            except Exception as e:
                log.write(f"✗ Erro ao gerar gráfico Plotly: {e}\n")
                log.write(traceback.format_exc())
                plot_html = f'<div class="text-red-500 p-4 bg-red-100 rounded">❌ Erro ao gerar gráfico: {str(e)}</div>'

            # --- 7. Gerar Componentes HTML ---
            log.write("\n--- A gerar componentes HTML para a interface com separadores ---\n")
            tab_buttons_html = ""
            tab_contents_html = ""

            tab_buttons_html += '<button class="tab-button active" data-target="#content-plot">Diagrama Interativo</button>'
            tab_contents_html += f'<div id="content-plot" class="tab-pane active"><div class="h-[85vh]">{plot_html}</div></div>'

            legend_data = {
                'Linhas de Transmissão': 'bg-gray-400', 'Transformadores': 'bg-purple-500',
                'Cargas': 'bg-red-500', 'Geradores': 'bg-green-500',
                'Rede Externa (Slack)': 'bg-orange-500', 'Reatores (Shunt)': 'bg-cyan-400'
            }
            legend_rows = "".join([f'<tr><td class="py-2 px-3"><div class="h-4 w-4 rounded-full {c}"></div></td><td class="py-2 px-3 text-sm">{n}</td></tr>' for n, c in legend_data.items()])
            legend_table_html = f'<div class="p-4"><h2 class="text-xl font-semibold mb-4">Legenda</h2><table class="w-full md:w-1/2"><tbody>{legend_rows}</tbody></table></div>'
            tab_buttons_html += '<button class="tab-button" data-target="#content-legend">Legenda</button>'
            tab_contents_html += f'<div id="content-legend" class="tab-pane">{legend_table_html}</div>'

            for name, df in sanitized_dfs.items():
                tab_name = str(name).replace("_", " ").title()
                table_html = df.to_html(classes='table-auto w-full text-sm text-left', border=0, index=True)
                tab_buttons_html += f'<button class="tab-button" data-target="#content-{name}">{tab_name}</button>'
                tab_contents_html += f'<div id="content-{name}" class="tab-pane"><div class="p-4">{table_html}</div></div>'
            log.write("Componentes HTML gerados.\n")

            # --- 8. Montar e Escrever Relatório Final ---
            log.write("\n--- A montar e a escrever o relatório final ---\n")
            report_content = template_str.replace('{{TAB_BUTTONS}}', tab_buttons_html)
            report_content = report_content.replace('{{TAB_CONTENTS}}', tab_contents_html)
            report_content = report_content.replace('{{GENERATION_DATE}}', datetime.now().strftime("%d de %B de %Y, %H:%M:%S"))

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            log.write(f"✓ Relatório gerado com sucesso em: {output_file}\n")

    except Exception as e:
        error_message = f"[{datetime.now()}] Ocorreu um erro crítico: {e}\n{traceback.format_exc()}"
        print(error_message, file=sys.stderr)
        try:
            with open(log_file, 'a', encoding='utf-8') as log:
                log.write(error_message)
        except:
            pass
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Gerar um relatório HTML para uma rede pandapower.")
    parser.add_argument("--net_file", required=True, help="Caminho para o ficheiro JSON da rede pandapower.")
    parser.add_argument("--data_file", required=True, help="Caminho para o ficheiro Excel com tabelas de dados.")
    parser.add_argument("--template_file", required=True, help="Caminho para o ficheiro de template HTML.")
    parser.add_argument("--output_file", default="report.html", help="Caminho para o relatório HTML de saída.")
    parser.add_argument("--log_file", default="report_generator.log", help="Caminho para o ficheiro de log.")
    
    args = parser.parse_args()
    
    create_report(
        net_file=args.net_file,
        data_file=args.data_file,
        template_file=args.template_file,
        output_file=args.output_file,
        log_file=args.log_file
    )
