import streamlit as st
from fpdf import FPDF
import pandas as pd

def ler_arquivo_csv(caminho):
    """Lê um arquivo CSV e retorna um DataFrame."""
    return pd.read_csv(caminho)

class PDFGenerator(FPDF):
    """Classe para gerenciar a geração de PDF com título, subtítulo, corpo de texto, rodapé e tabelas."""

    def __init__(self):
        """Inicializa a classe sem configurações adicionais."""
        super().__init__()

    def adicionar_titulo(self, titulo, tamanho=16, cor=(0, 0, 0)):
        """Adiciona um título ao PDF."""
        self.set_text_color(*cor)
        self.set_font("helvetica", "B", tamanho)
        self.cell(0, 10, titulo, ln=True, align="C")
        self.ln(10)

    def adicionar_tabela(self, df, legenda_cima="", legenda_baixo="", tamanho=8, cor=(0, 0, 0)):
        """Adiciona uma tabela formatada ao PDF com legendas acima e abaixo."""
        if legenda_cima:
            self.set_text_color(*cor)
            self.set_font("helvetica", size=tamanho)
            self.multi_cell(0, 10, legenda_cima)
            self.ln(5)

        self.set_text_color(*cor)
        self.set_font("helvetica", size=tamanho)
        col_widths = [40, 80, 40, 30]  # Largura das colunas: ajustável

        # Cabeçalho da tabela
        self.set_fill_color(200, 200, 200)  # Cor de fundo cinza claro
        self.set_font("helvetica", "B", tamanho)
        headers = df.columns.tolist()
        for header, width in zip(headers, col_widths):
            self.cell(width, 10, header, border=1, align="C", fill=True)
        self.ln()

        # Dados da tabela
        self.set_font("Arial", size=tamanho)
        for _, row in df.iterrows():
            for value, width in zip(row, col_widths):
                # Substituir caracteres Unicode por True/False
                if value == "✔️":
                    value = "True"
                elif value == "❌":
                    value = "False"
                self.cell(width, 10, str(value), border=1, align="C")
            self.ln()

        if legenda_baixo:
            self.set_text_color(*cor)
            self.set_font("helvetica", size=tamanho)
            self.multi_cell(0, 10, legenda_baixo)
            self.ln(5)

    def gerar_pdf(self, titulo, subtitulo, texto, rodape, df, output_path):
        """Gera o PDF com os elementos fornecidos."""
        self.add_page()
        self.adicionar_titulo(titulo)
        self.adicionar_titulo(subtitulo, tamanho=12)
        self.set_font("helvetica", size=10)
        self.multi_cell(0, 10, texto)
        self.ln(10)
        self.adicionar_tabela(df, "Legenda acima da tabela", "Legenda abaixo da tabela")
        self.set_y(-15)
        self.set_font("helvetica", "I", 10)
        self.cell(0, 10, rodape, align="C")
        self.output(output_path)
        return output_path


# Streamlit Interface
def EasyPDF():
    st.title("Gerador de PDF com Unicode")
    st.markdown("---", unsafe_allow_html=True)
    st.subheader("Preencha os campos abaixo para gerar seu PDF")

    # Entradas de texto para título, subtítulo, corpo do texto e rodapé
    titulo = st.text_input("Título", "Meu PDF Gerado")
    subtitulo = st.text_input("Subtítulo", "Subtítulo do PDF")
    texto = st.text_area("Texto", "Este é o corpo do texto do PDF.")
    rodape = st.text_input("Rodapé", "Rodapé do PDF")

    # Entrada de tabela em CSV
    st.subheader("Tabela")
    texto_csv ="Coluna1,Coluna2,Coluna3,Coluna4\nValor1,Valor2,✔️,❌\nValor3,Valor4,❌,✔️"
    #texto_csv = ler_arquivo_csv("rotina.csv")
    tabela = st.text_area("Insira os dados da tabela em formato CSV", value = texto_csv, height=200)
    
    # Processar CSV e substituir vírgulas dentro das células por "+"
    linhas = tabela.split("\n")
    colunas = linhas[0].split(",")
    dados = [linha.split(",") for linha in linhas[1:]]
    dados = [[cell.replace(",", "+") for cell in linha] for linha in dados]  # Substituir vírgulas dentro das células
    df = pd.DataFrame(dados, columns=colunas)

    # Exibir DataFrame
    st.write("Tabela processada:")
    st.dataframe(df)

    # Botão para exportar Excel
    if st.button("Exportar para Excel"):
        excel_path = "tabela_exportada.xlsx"
        df.to_excel(excel_path, index=False)
        st.success(f"Tabela exportada para: {excel_path}")
        st.download_button("Baixar Excel", data=open(excel_path, "rb").read(), file_name="tabela_exportada.xlsx")

    # Botão para gerar PDF
    if st.button("Gerar PDF"):
        pdf = PDFGenerator()
        output_path = "output.pdf"
        pdf.gerar_pdf(titulo, subtitulo, texto, rodape, df, output_path)
        st.success(f"PDF gerado com sucesso: {output_path}")
        st.download_button("Baixar PDF", data=open(output_path, "rb").read(), file_name="output.pdf")


    st.rerun()
    
#EasyPDF()