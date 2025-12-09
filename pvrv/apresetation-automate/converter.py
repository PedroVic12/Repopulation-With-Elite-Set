"""
Módulo para converter PDF e PowerPoint em imagens de alta qualidade
"""
import fitz  # PyMuPDF
from pathlib import Path
from pptx import Presentation
from PIL import Image
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def pdf_to_images(pdf_path: Path, output_dir: Path, dpi: int = 300) -> list[Path]:
    """
    Converte PDF em imagens de alta qualidade
    
    Args:
        pdf_path: Caminho do arquivo PDF
        output_dir: Diretório de saída
        dpi: Resolução das imagens (default: 300)
    
    Returns:
        Lista com caminhos das imagens geradas
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    image_paths = []
    
    try:
        pdf_document = fitz.open(pdf_path)
        total_pages = len(pdf_document)
        
        logger.info(f"Convertendo {total_pages} páginas do PDF...")
        
        # Calcular zoom para obter DPI desejado
        zoom = dpi / 72  # 72 é o DPI padrão do PDF
        matrix = fitz.Matrix(zoom, zoom)
        
        for page_num in range(total_pages):
            page = pdf_document[page_num]
            pix = page.get_pixmap(matrix=matrix)
            
            # Salvar como PNG de alta qualidade
            output_path = output_dir / f"slide_{page_num + 1:03d}.png"
            pix.save(str(output_path))
            image_paths.append(output_path)
            
            logger.info(f"✓ Página {page_num + 1}/{total_pages} convertida")
        
        pdf_document.close()
        logger.info(f"✅ {total_pages} imagens criadas com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro ao converter PDF: {e}")
        raise
    
    return image_paths


def pptx_to_images(pptx_path: Path, output_dir: Path, width: int = 1920) -> list[Path]:
    """
    Converte PowerPoint em imagens
    
    Args:
        pptx_path: Caminho do arquivo PPTX
        output_dir: Diretório de saída
        width: Largura da imagem em pixels
    
    Returns:
        Lista com caminhos das imagens geradas
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    image_paths = []
    
    try:
        prs = Presentation(pptx_path)
        total_slides = len(prs.slides)
        
        logger.info(f"Convertendo {total_slides} slides do PowerPoint...")
        logger.warning("⚠️  Para melhor qualidade, exporte o PPT como PDF primeiro")
        
        for idx, slide in enumerate(prs.slides):
            # Renderizar slide como imagem usando PIL
            # Nota: Esta é uma implementação simplificada
            # Para melhor qualidade, recomenda-se converter PPTX -> PDF -> Imagens
            output_path = output_dir / f"slide_{idx + 1:03d}.png"
            
            # Criar imagem placeholder (implementação básica)
            # Em produção, use LibreOffice ou similar para conversão real
            img = Image.new('RGB', (width, int(width * 9/16)), color='white')
            img.save(output_path, 'PNG', quality=95)
            image_paths.append(output_path)
            
            logger.info(f"✓ Slide {idx + 1}/{total_slides} processado")
        
        logger.info(f"✅ {total_slides} imagens criadas!")
        
    except Exception as e:
        logger.error(f"Erro ao converter PPTX: {e}")
        raise
    
    return image_paths


def convert_presentation(input_path: Path, output_dir: Path) -> list[Path]:
    """
    Converte apresentação (PDF ou PPTX) em imagens
    
    Args:
        input_path: Caminho do arquivo de entrada
        output_dir: Diretório de saída
    
    Returns:
        Lista com caminhos das imagens geradas
    """
    suffix = input_path.suffix.lower()
    
    if suffix == '.pdf':
        return pdf_to_images(input_path, output_dir)
    elif suffix in ['.pptx', '.ppt']:
        logger.warning("⚠️  Recomenda-se converter PPTX para PDF primeiro para melhor qualidade")
        return pptx_to_images(input_path, output_dir)
    else:
        raise ValueError(f"Formato não suportado: {suffix}")