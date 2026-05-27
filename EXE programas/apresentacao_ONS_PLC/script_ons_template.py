import os
import sys
from PyPDF2 import PdfReader, PdfWriter, PageObject
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, Paragraph, Spacer, KeepInFrame
from reportlab.lib.units import inch
from palkia_pdf_componentes import (
    get_ons_styles,
    LAYOUT_CONFIG,
    format_markdown_text,
    create_slide_content,
)
import io


def parse_markdown(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    raw_slides = content.split("---")
    slides = []
    for slide in raw_slides:
        lines = slide.strip().split("\n")
        if not lines:
            continue
        title = ""
        body = []
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
            elif line.startswith("## ") and not title:
                title = line[3:].strip()
            else:
                body.append(line)
        slides.append({"title": title, "body": body})
    return slides


def generate_slide_pdf(slide_data, config, styles, desenhar_fundo=1):
    packet = io.BytesIO()
    canv = canvas.Canvas(packet, pagesize=landscape(A4))

    elements = create_slide_content(slide_data["title"], slide_data["body"], styles)

    # KeepInFrame garante que o conteúdo não vaze para fora do frame
    kif = KeepInFrame(
        config["width"],
        config["height"],
        elements,
        mode="shrink",  # encolhe o conteúdo se for grande demais
    )

    f = Frame(
        config["x"],
        config["y"],
        config["width"],
        config["height"],
        showBoundary=desenhar_fundo,  # mude para 1 durante debug para ver a caixa!
    )

    f.addFromList([kif], canv)
    canv.save()
    packet.seek(0)
    return PdfReader(packet).pages[0]


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    content_md = "notas/content.md"
    template_pdf_path = "assets/Template PPT ONS 2026 (2).pdf"
    if not os.path.exists(template_pdf_path):
        template_pdf_path = os.path.join("assets", "Template PPT ONS 2026 (2).pdf")

    final_pdf = "assets/apresentacao_ONS_PLC_TEMPLATE.pdf"

    print(f"--- Gerador de Documentos Automatizados V5 ---")

    slides_data = parse_markdown(content_md)
    if not slides_data:
        print("Erro: content.md não encontrado.")
        return

    reader_template = PdfReader(template_pdf_path)
    writer = PdfWriter()
    styles = get_ons_styles()

    total = len(slides_data)
    for i, slide in enumerate(slides_data):
        # Selecionar config e página do template
        if i == 0:
            config = LAYOUT_CONFIG["CAPA"]
        elif i == total - 1:
            config = LAYOUT_CONFIG["ENCERRAMENTO"]
        else:
            config = LAYOUT_CONFIG["CONTEUDO"]

        # 1. Pegar fundo do template
        temp_idx = min(config["template_page"], len(reader_template.pages) - 1)
        bg_page = reader_template.pages[temp_idx]

        # 2. Gerar conteúdo em cima das coordenadas
        content_page = generate_slide_pdf(slide, config, styles)

        # 3. Merge
        new_page = PageObject.create_blank_page(
            width=bg_page.mediabox.width, height=bg_page.mediabox.height
        )
        new_page.merge_page(bg_page)
        new_page.merge_page(content_page)
        writer.add_page(new_page)
        print(f"Slide {i+1} processado.")

    with open(final_pdf, "wb") as f:
        writer.write(f)

    print(f"\n✅ SUCESSO ABSOLUTO! Arquivo gerado: {final_pdf}")
    print(f"Dica: Ajuste 'x' e 'y' em LAYOUT_CONFIG para mover o bloco de texto.")


if __name__ == "__main__":
    main()
