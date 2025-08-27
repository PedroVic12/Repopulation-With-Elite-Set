import os

def generate_html_report():
    image_files = [
        "grafico_1_topologia_rede.png",
        "grafico_2_fluxo_base.png",
        "grafico_3_tensoes_base.png",
        "grafico_4_fluxo_contingencia.png",
        "grafico_5_tensoes_contingencia.png",
        "grafico_6_comparativo_tensoes.png",
        "grafico_7_comparativo_carregamento.png"
    ]

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Análise da Rede Elétrica Inteligente</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; text-align: center; }
            .plots-grid-container {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(450px, 1fr)); /* 2 columns, responsive */
                gap: 20px;
                margin-top: 30px;
            }
            .plot-container {
                border: 1px solid #ddd;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
                background-color: #fff;
            }
            img { max-width: 100%; height: auto; display: block; margin: 0 auto; }
            .plot-title { text-align: center; font-size: 1.2em; margin-bottom: 10px; color: #555; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>Relatório de Análise da Rede Elétrica Inteligente</h1>
        <div class="plots-grid-container">
    """

    plot_titles = {
        "grafico_1_topologia_rede.png": "Gráfico 1: Topologia da Rede 'Canarinho' (16 Barras)",
        "grafico_2_fluxo_base.png": "Gráfico 2: Fluxo de Potência - Caso Base",
        "grafico_3_tensoes_base.png": "Gráfico 3: Perfil de Tensão - Caso Base",
        "grafico_4_fluxo_contingencia.png": "Gráfico 4: Fluxo de Potência - Contingência",
        "grafico_5_tensoes_contingencia.png": "Gráfico 5: Perfil de Tensão - Contingência",
        "grafico_6_comparativo_tensoes.png": "Gráfico 6: Comparativo de Perfil de Tensão",
        "grafico_7_comparativo_carregamento.png": "Gráfico 7: Comparativo de Carregamento das Linhas"
    }

    for img_file in image_files:
        if os.path.exists(img_file):
            html_content += f"""
            <div class="plot-container">
                <div class="plot-title">{plot_titles.get(img_file, img_file)}</div>
                <img src="{img_file}" alt="{plot_titles.get(img_file, img_file)}">
            </div>
            """
        else:
            html_content += f"""
            <div class="plot-container">
                <p>Erro: Imagem {img_file} não encontrada.</p>
            </div>
            """

    html_content += """
        </div> <!-- Close plots-grid-container -->
    </body>
    </html>
    """

    with open("analise_smartgrid_report.html", "w") as f:
        f.write(html_content)
    print("Relatório HTML 'analise_smartgrid_report.html' gerado com sucesso.")

if __name__ == "__main__":
    generate_html_report()