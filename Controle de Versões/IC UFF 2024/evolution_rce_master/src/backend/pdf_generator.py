from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt
import os


class PDFGenerator:
    def __init__(self, dados, output_dir):
        self.dados = dados
        self.output_dir = output_dir

    def criar_pdf_com_template(self, arquivo_saida):
        c = canvas.Canvas(arquivo_saida, pagesize=A4)
        largura, altura = A4

        # Adiciona o template como background
        self.adicionar_template(c, largura, altura)

        # Adiciona os dados como texto
        for chave, valor in self.dados.items():
            x, y = self.get_coordenadas(chave)
            c.drawString(x, y, f"{chave}: {valor}")

        # Salva os plots e adiciona ao PDF
        plots_sem_repop = self.salvar_plots("sem_repopulacao")
        plots_com_repop = self.salvar_plots("com_repopulacao")

        for plot in plots_sem_repop:
            c.drawImage(plot, 50, 400, width=400, height=300)
            c.showPage()

        for plot in plots_com_repop:
            c.drawImage(plot, 50, 50, width=400, height=300)
            c.showPage()

        c.save()

    def adicionar_template(self, canvas, largura, altura):
        # Aqui você pode adicionar seu próprio template como background
        # Neste exemplo, vamos apenas desenhar um retângulo preenchido
        canvas.setFillColorRGB(0, 0, 0)  # Cor preta
        canvas.rect(0, 0, largura, altura, fill=True)

    def get_coordenadas(self, chave):
        # Define as coordenadas específicas para cada chave
        # Aqui você pode definir as coordenadas com base em sua própria lógica
        coordenadas = {
            "chave1": (50, 700),
            "chave2": (50, 680),
            "chave3": (50, 660),
            # Adicione mais coordenadas conforme necessário
        }
        return coordenadas.get(chave, (50, 50))  # Retorna (50, 50) como padrão

    def salvar_plots(self, folder_name):
        plots = []
        folder_path = os.path.join(self.output_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        # Aqui você pode salvar seus plots na pasta correspondente
        # Substitua este exemplo pelo código real para salvar seus plots
        for i in range(5):  # Salvando 5 plots de exemplo
            fig, ax = plt.subplots()
            ax.plot([1, 2, 3], [4, 5, 6])
            plot_path = os.path.join(folder_path, f"plot_{i}.png")
            plt.savefig(plot_path)
            plt.close(fig)
            plots.append(plot_path)

        return plots
