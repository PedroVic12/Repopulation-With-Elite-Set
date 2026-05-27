import os
import re
import sys
import requests
from io import BytesIO
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Image,
    Frame,
    PageTemplate,
)
from reportlab.lib.units import inch
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()


def download_image(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BytesIO(response.content)
    except Exception as e:
        console.print(f"[red]Erro ao baixar imagem {url}: {e}[/red]")
        return None


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
                # Detectar imagens ![alt](url)
                img_match = re.search(r"!\[.*?\]\((.*?)\)", line)
                if img_match:
                    body.append({"type": "image", "value": img_match.group(1)})
                else:
                    body.append({"type": "text", "value": line})

        slides.append({"title": title, "body": body})

    return slides


def create_pdf(slides, output_path, bg_start=None, bg_end=None):
    doc = SimpleDocTemplate(output_path, pagesize=landscape(A4))
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "SlideTitle",
        parent=styles["Heading1"],
        fontSize=28,
        textColor=colors.HexColor("#1A3A5A"),
        alignment=1,
        spaceAfter=30,
    )
    body_style = ParagraphStyle(
        "SlideBody",
        parent=styles["Normal"],
        fontSize=16,
        leading=22,
        textColor=colors.black,
        alignment=0,
    )
    bullet_style = ParagraphStyle(
        "BulletStyle", parent=body_style, leftIndent=20, spaceBefore=10
    )

    elements = []
    total_slides = len(slides)

    def draw_background(canvas, doc):
        canvas.saveState()
        page_num = canvas.getPageNumber()
        img_path = None
        if page_num == 1 and bg_start and os.path.exists(bg_start):
            img_path = bg_start
        elif page_num == total_slides and bg_end and os.path.exists(bg_end):
            img_path = bg_end

        if img_path:
            canvas.drawImage(
                img_path, 0, 0, width=landscape(A4)[0], height=landscape(A4)[1]
            )
        canvas.restoreState()

    for i, slide in enumerate(slides):
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph(slide["title"], title_style))

        for item in slide["body"]:
            if item["type"] == "image":
                path = item["value"]
                img_data = download_image(path) if path.startswith("http") else path
                if img_data:
                    try:
                        img = Image(
                            img_data,
                            width=4 * inch,
                            height=3 * inch,
                            kind="proportional",
                        )
                        elements.append(img)
                    except:
                        elements.append(
                            Paragraph(f"[Erro ao carregar imagem: {path}]", body_style)
                        )
            else:
                line = item["value"].strip()
                if not line:
                    continue

                text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", line)
                if line.startswith(("- ", "* ")):
                    elements.append(Paragraph(f"• {text[2:]}", bullet_style))
                else:
                    elements.append(Paragraph(text, body_style))
                    elements.append(Spacer(1, 10))

        if i < total_slides - 1:
            elements.append(PageBreak())

    doc.build(elements, onFirstPage=draw_background, onLaterPages=draw_background)
    console.print(f"[green]PDF gerado: {output_path}[/green]")


def create_pptx(slides, output_path, bg_start=None, bg_end=None):
    prs = Presentation()
    # Layout 6 é "Blank"
    blank_slide_layout = prs.slide_layouts[6]

    total_slides = len(slides)

    for i, slide_data in enumerate(slides):
        slide = prs.slides.add_slide(blank_slide_layout)

        # Background template logic
        bg_path = None
        if i == 0 and bg_start and os.path.exists(bg_start):
            bg_path = bg_start
        elif i == total_slides - 1 and bg_end and os.path.exists(bg_end):
            bg_path = bg_end

        if bg_path:
            slide.shapes.add_picture(
                bg_path, 0, 0, width=prs.slide_width, height=prs.slide_height
            )

        # Title
        title_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(0.2), Inches(9), Inches(1)
        )
        tf = title_box.text_frame
        p = tf.paragraphs[0]
        p.text = slide_data["title"]
        p.font.bold = True
        p.font.size = Pt(36)
        p.alignment = PP_ALIGN.CENTER

        # Content
        left = Inches(0.5)
        top = Inches(1.5)
        width = Inches(9)
        height = Inches(5)

        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        tf.word_wrap = True

        for item in slide_data["body"]:
            if item["type"] == "image":
                path = item["value"]
                img_data = download_image(path) if path.startswith("http") else path
                if img_data:
                    try:
                        # Coloca imagem no canto se houver texto, ou centralizada
                        slide.shapes.add_picture(
                            img_data, Inches(6), top, width=Inches(3)
                        )
                    except:
                        pass
            else:
                line = item["value"].strip()
                if not line:
                    continue
                p = tf.add_paragraph()
                clean_text = line.replace("**", "")
                if line.startswith(("- ", "* ")):
                    p.text = clean_text[2:]
                    p.level = 1
                else:
                    p.text = clean_text
                p.font.size = Pt(18)

    prs.save(output_path)
    console.print(f"[green]PowerPoint gerado: {output_path}[/green]")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    console.print(Panel("[bold blue]Gerador de Apresentações ONS-PLC[/bold blue]"))

    format_choice = Prompt.ask(
        "Qual formato deseja exportar?", choices=["pdf", "pptx", "ambos"], default="pdf"
    )

    # Busca imagens de template na pasta assets se existirem
    assets_dir = os.path.join(os.getcwd(), "assets")
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)

    bg_start = os.path.join(assets_dir, "template_start.png")
    bg_end = os.path.join(assets_dir, "template_end.png")

    slides_data = parse_markdown(r"content.md")

    if not slides_data:
        console.print("[red]Erro: content.md não encontrado ou vazio.[/red]")
        sys.exit(1)

    if format_choice in ["pdf", "ambos"]:
        create_pdf(slides_data, "apresentacao_ONS_PLC.pdf", bg_start, bg_end)

    if format_choice in ["pptx", "ambos"]:
        create_pptx(slides_data, "apresentacao_ONS_PLC.pptx", bg_start, bg_end)

    console.print("[bold green]Concluído![/bold green]")
