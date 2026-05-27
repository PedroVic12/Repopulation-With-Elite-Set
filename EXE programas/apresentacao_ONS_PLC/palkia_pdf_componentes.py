import os
import re
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, PageBreak, Image
from reportlab.lib.units import inch

# =============================================================================
# 🛠️ MAPEAMENTO DO TEMPLATE ONS (9 PÁGINAS)
# =============================================================================
# Página 1: Capa Principal
# Página 2: Template de Transição ou Agenda (Branco com detalhes)
# Página 3-8: Templates de Conteúdo Padrão
# Página 9: Contra-capa / Encerramento
# =============================================================================

# =============================================================================
# 🛠️ COORDENADAS ABSOLUTAS (Pontos: 0,0 é o canto inferior esquerdo)
# A4 Paisagem: 842 de largura x 595 de altura
# =============================================================================
LAYOUT_CONFIG = {
    "CAPA": {
        "x": 50,
        "y": 100,
        "width": 470,
        "height": 300,
        "template_page": 0,
    },
    "CONTEUDO": {
        "x": 80,
        "y": 80,
        "width": 750,
        "height": 350,
        "template_page": 2,
    },
    "ENCERRAMENTO": {
        "x": 100,
        "y": 100,
        "width": 600,
        "height": 300,
        "template_page": 8,
    },
}


# Cores e Estilos ONS
ONS_COLORS = {
    "primary": colors.HexColor("#072B50"),
    "secondary": colors.HexColor("#05cde7"),
    "accent": colors.HexColor("#2e7d32"),
    "text": colors.black,
    "muted": colors.grey,
}


def get_ons_styles():
    styles = getSampleStyleSheet()

    ons_styles = {
        "title": ParagraphStyle(
            "ONSTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=ONS_COLORS["primary"],
            alignment=1,  # Center
            spaceAfter=40,
            fontName="Helvetica-Bold",
        ),
        "subtitle": ParagraphStyle(
            "ONSSubtitle",
            parent=styles["Heading2"],
            fontSize=18,
            textColor=ONS_COLORS["secondary"],
            alignment=0,  # Left
            spaceBefore=15,
            spaceAfter=10,
            fontName="Helvetica-Bold",
        ),
        "body": ParagraphStyle(
            "ONSBody",
            parent=styles["Normal"],
            fontSize=16,
            leading=22,
            textColor=ONS_COLORS["text"],
            alignment=0,  # Left
        ),
        "bullet": ParagraphStyle(
            "ONSBullet",
            parent=styles["Normal"],
            fontSize=14,
            leading=22,
            leftIndent=25,
            firstLineIndent=0,
            spaceBefore=10,
            textColor=ONS_COLORS["text"],
        ),
    }
    return ons_styles


def format_markdown_text(text):
    """Converte negrito e itálico markdown para tags reportlab."""
    # Bold: **text** -> <b>text</b>
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    # Italic: *text* -> <i>text</i>
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)
    # Italic: _text_ -> <i>text</i>
    text = re.sub(r"_(.*?)_", r"<i>\1</i>", text)
    return text


def create_slide_content(title, body_lines, styles):
    elements = []
    # Título do slide
    elements.append(Paragraph(format_markdown_text(title), styles["title"]))
    elements.append(Spacer(1, 0.4 * inch))

    for line in body_lines:
        line = line.strip()
        if not line:
            continue

        # Detectar imagens
        img_match = re.search(r"!\[.*?\]\((.*?)\)", line)
        if img_match:
            img_path = img_match.group(1)
            try:
                elements.append(
                    Image(
                        img_path, width=4 * inch, height=3 * inch, kind="proportional"
                    )
                )
            except:
                elements.append(
                    Paragraph(
                        f"<i>[Imagem não encontrada: {img_path}]</i>", styles["body"]
                    )
                )
        elif line.startswith("## "):
            # Subtítulo (Header nível 2)
            text = format_markdown_text(line[3:])
            elements.append(Paragraph(text, styles["subtitle"]))
        else:
            text = format_markdown_text(line)
            if line.startswith(("- ", "* ")):
                elements.append(Paragraph(f"• {text[2:]}", styles["bullet"]))
            else:
                elements.append(Paragraph(text, styles["body"]))
                elements.append(Spacer(1, 12))

    return elements


def draw_ons_template(canvas, doc, template_path=None):
    """
    Desenha o template de fundo.
    Se template_path for um PDF, precisaremos de pdfrw para importar.
    Por enquanto, suporta imagens.
    """
    canvas.saveState()
    if template_path and os.path.exists(template_path):
        # Nota: Para desenhar PDF dentro de PDF no ReportLab nativo é complexo.
        # Geralmente se usa imagens de fundo ou se importa com pdfrw.
        if template_path.lower().endswith((".png", ".jpg", ".jpeg")):
            canvas.drawImage(
                template_path, 0, 0, width=landscape(A4)[0], height=landscape(A4)[1]
            )
    canvas.restoreState()
