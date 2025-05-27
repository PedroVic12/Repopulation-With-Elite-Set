import streamlit as st
from fpdf import FPDF
import pandas as pd

class PDFGenerator(FPDF):
    """Classe para gerenciar a geração de PDF com título, subtítulo, corpo de texto, rodapé, imagens e tabelas."""

    def __init__(self):
        """Inicializa a classe sem configurações adicionais."""
        super().__init__()

    def adicionar_titulo(self, titulo, tamanho=16, cor=(0, 0, 0)):
        """Adiciona um título ao PDF."""
        self.set_text_color(*cor)
        self.set_font("Arial", "B", tamanho)
        self.cell(0, 10, titulo, ln=True, align="C")
        self.ln(10)

    def adicionar_subtitulo(self, subtitulo, tamanho=12, cor=(0, 0, 0)):
        """Adiciona um subtítulo ao PDF."""
        self.set_text_color(*cor)
        self.set_font("Arial", "B", tamanho)
        self.cell(0, 10, subtitulo, ln=True, align="C")
        self.ln(10)

    def adicionar_corpo_texto(self, texto, tamanho=12, cor=(0, 0, 0)):
        """Adiciona o corpo de texto ao PDF."""
        self.set_text_color(*cor)
        self.set_font("Arial", size=tamanho)
        self.multi_cell(0, 10, texto)
        self.ln(10)

    def adicionar_imagem(self, imagem_path, x=10, y=None, w=100):
        """Adiciona uma imagem ao PDF."""
        self.image(imagem_path, x=x, y=y, w=w)
        self.ln(10)

    def adicionar_tabela(self, df, legenda_cima="", legenda_baixo="", tamanho=12, cor=(0, 0, 0)):
        """Adiciona uma tabela formatada ao PDF com legendas acima e abaixo."""
        if legenda_cima:
            self.adicionar_corpo_texto(legenda_cima, tamanho=tamanho, cor=cor)

        self.set_text_color(*cor)
        self.set_font("Arial", size=tamanho)
        col_widths = [40, 80, 40, 30]  # Largura das colunas: ajustável

        # Cabeçalho da tabela
        self.set_fill_color(200, 200, 200)  # Cor de fundo cinza claro
        self.set_font("Arial", "B", tamanho)
        headers = df.columns.tolist()
        for header, width in zip(headers, col_widths):
            self.cell(width, 10, header, border=1, align="C", fill=True)
        self.ln()

        # Dados da tabela
        self.set_font("Arial", size=tamanho)
        for _, row in df.iterrows():
            for value, width in zip(row, col_widths):
                # Substituir caracteres Unicode
                value = str(value).replace("✔️", "X").replace("❌", "-")
                self.cell(width, 10, value, border=1, align="C")
            self.ln()

        if legenda_baixo:
            self.adicionar_corpo_texto(legenda_baixo, tamanho=tamanho, cor=cor)

    def adicionar_rodape(self, rodape, tamanho=10, cor=(0, 0, 0)):
        """Adiciona um rodapé ao PDF."""
        self.set_y(-15)
        self.set_text_color(*cor)
        self.set_font("Arial", "I", tamanho)
        self.cell(0, 10, rodape, align="C")

    def gerar_pdf(self, titulo, subtitulo, texto, rodape, imagem_path, df, legenda_cima, legenda_baixo, output_path):
        """Gera o PDF com os elementos fornecidos."""
        self.add_page()
        self.adicionar_titulo(titulo)
        self.adicionar_subtitulo(subtitulo)
        self.adicionar_corpo_texto(texto)
        if imagem_path:
            self.adicionar_imagem(imagem_path, x=10, y=None, w=100)
        if df is not None:
            self.adicionar_tabela(df, legenda_cima, legenda_baixo)
        self.adicionar_rodape(rodape)
        self.output(output_path)
        return output_path


# Interface Streamlit
def EasyPDF():
    st.title("Gerador de PDF")
    st.subheader("Preencha os campos abaixo para gerar seu PDF")

    # Entrada de dados
    titulo = st.text_input("Título", "Meu PDF Gerado")
    subtitulo = st.text_input("Subtítulo", "Subtítulo do PDF")
    texto = st.text_area("Corpo de Texto", "Este é o corpo do texto do PDF.")
    rodape = st.text_input("Rodapé", "Rodapé do PDF")
    imagem = st.file_uploader("Carregar Imagem", type=["png", "jpg", "jpeg"])

    # Tabela
    st.subheader("Tabela")
    tabela = st.text_area("Insira os dados da tabela (separados por vírgula)", "Horário,Atividade,Duração,Status\n08h30-08h40,Aquecimento mental,10 min,✔️\n08h40-09h10,Simulado 1,30 min,❌")
    legenda_cima = st.text_input("Legenda acima da tabela", "Legenda acima da tabela")
    legenda_baixo = st.text_input("Legenda abaixo da tabela", "Legenda abaixo da tabela")

    # Botão para gerar PDF
    if st.button("Gerar PDF"):
        # Processar tabela
        linhas = tabela.split("\n")
        colunas = linhas[0].split(",")
        dados = [linha.split(",") for linha in linhas[1:]]
        df = pd.DataFrame(dados, columns=colunas)

        pdf = PDFGenerator()
        imagem_path = None
        if imagem:
            imagem_path = f"temp_image.{imagem.name.split('.')[-1]}"
            with open(imagem_path, "wb") as f:
                f.write(imagem.getbuffer())

        output_path = "output.pdf"
        pdf.gerar_pdf(titulo, subtitulo, texto, rodape, imagem_path, df, legenda_cima, legenda_baixo, output_path)

        st.success(f"PDF gerado com sucesso! Arquivo salvo em: {output_path}")
        st.download_button("Baixar PDF", data=open(output_path, "rb").read(), file_name="output.pdf")

        # Remover imagem temporária
        if imagem_path:
            import os
            os.remove(imagem_path)


EasyPDF()  # Instancia a classe PDFGenerator para uso posterior