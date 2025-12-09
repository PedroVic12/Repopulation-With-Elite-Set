"""
Sistema de Apresentação Controlado por Gestos
Autor: Desenvolvedor Python/React
"""
import argparse
import logging
from pathlib import Path
import sys

from converter import convert_presentation
from presenter import GesturePresenter

# pip install opencv-python mediapipe PyMuPDF pillow python-pptx


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def find_presentation_file(input_dir: Path) -> Path | None:
    """
    Procura arquivo de apresentação no diretório
    
    Args:
        input_dir: Diretório de busca
    
    Returns:
        Caminho do arquivo encontrado ou None
    """
    supported_formats = ['.pdf', '.pptx', '.ppt']
    
    for fmt in supported_formats:
        files = list(input_dir.glob(f'*{fmt}'))
        if files:
            return files[0]
    
    return None





if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Sistema de apresentação controlado por gestos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  # Converter e apresentar arquivo específico
  uv run python main.py --input minha_apresentacao.pdf
  
  # Usar arquivo da pasta input/
  uv run python main.py
  
  # Apenas apresentar slides já convertidos
  uv run python main.py --skip-convert
  
Gestos suportados:
  👉 Mão direita deslizando para esquerda: Próximo slide
  👈 Mão esquerda deslizando para direita: Slide anterior
  ✌️  Sinal de paz (2 dedos): Fechar apresentação
  ⌨️  ESC ou 'q': Sair
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        type=Path,
        help='Arquivo de entrada (PDF ou PowerPoint)'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=Path,
        default=Path('apresentacao-imgs'),
        help='Diretório para salvar imagens (padrão: apresentacao-imgs)'
    )
    
    parser.add_argument(
        '--dpi',
        type=int,
        default=300,
        help='Resolução DPI para conversão (padrão: 300)'
    )
    
    parser.add_argument(
        '--skip-convert',
        action='store_true',
        help='Pular conversão e usar imagens existentes'
    )
    
    args = parser.parse_args()
    
    logger.info("🎯 SISTEMA DE APRESENTAÇÃO COM GESTOS")
    logger.info("=" * 60)
    
    # Determinar arquivo de entrada
    input_file = args.input
    
    if not input_file and not args.skip_convert:
        input_dir = Path('input')
        if not input_dir.exists():
            input_dir.mkdir()
            logger.error("❌ Pasta 'input/' criada. Coloque seu PDF/PPT lá!")
            sys.exit(1)
        
        pdf_files = sorted(list(input_dir.glob('*.pdf'))) # Added sorted() for consistent ordering
        
        if not pdf_files:
            logger.error("❌ Nenhum arquivo PDF encontrado em 'input/'")
            sys.exit(1)
        
        if len(pdf_files) == 1:
            input_file = pdf_files[0]
            logger.info(f"📄 Usando o único arquivo PDF encontrado: {input_file.name}")
        else:
            logger.info("📁 Múltiplos arquivos PDF encontrados na pasta 'input/':")
            for i, pdf in enumerate(pdf_files):
                logger.info(f"  [{i+1}] {pdf.name}")
            
            while True:
                try:
                    choice = input("Selecione o número do arquivo PDF para apresentar: ")
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(pdf_files):
                        input_file = pdf_files[choice_idx]
                        logger.info(f"📄 Arquivo selecionado: {input_file.name}")
                        break
                    else:
                        logger.warning("Número inválido. Por favor, selecione um número da lista.")
                except ValueError:
                    logger.warning("Entrada inválida. Por favor, digite um número.")
    
    # Converter apresentação
    image_paths = []
    
    if not args.skip_convert:
        if not input_file or not input_file.exists():
            logger.error(f"❌ Arquivo não encontrado: {input_file}")
            sys.exit(1)
        
        logger.info(f"📄 Arquivo de entrada: {input_file}")
        logger.info(f"📁 Diretório de saída: {args.output_dir}")
        logger.info(f"🎨 Resolução: {args.dpi} DPI")
        
        try:
            image_paths = convert_presentation(input_file, args.output_dir)
        except Exception as e:
            logger.error(f"❌ Erro na conversão: {e}")
            sys.exit(1)
    else:
        # Usar imagens existentes
        if not args.output_dir.exists():
            logger.error(f"❌ Diretório não encontrado: {args.output_dir}")
            sys.exit(1)
        
        image_paths = sorted(args.output_dir.glob('*.png'))
        if not image_paths:
            logger.error(f"❌ Nenhuma imagem encontrada em: {args.output_dir}")
            sys.exit(1)
        
        logger.info(f"📁 Usando {len(image_paths)} imagens existentes")
    
    # Verificar se há imagens
    if not image_paths:
        logger.error("❌ Nenhuma imagem disponível para apresentação")
        sys.exit(1)
    
    # Iniciar apresentação
    logger.info("")
    logger.info("🎬 Iniciando apresentação...")
    logger.info("")
    logger.info("CONTROLES:")
    logger.info("  👉 Mão direita <- esquerda: Próximo slide")
    logger.info("  👈 Mão esquerda -> direita: Slide anterior")
    logger.info("  ✌️  Sinal de paz (2 dedos): Fechar")
    logger.info("  ⌨️  ESC/Q: Sair")
    logger.info("")
    
    try:
        presenter = GesturePresenter(image_paths)
        presenter.run()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro na apresentação: {e}")
        sys.exit(1)
    
    logger.info("=" * 30)