"""
Sistema de apresentação controlado por gestos
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Callable
import logging
from gesture_detector import GestureDetector, Gesture

logger = logging.getLogger(__name__)


class GesturePresenter:
    """Apresentador de slides controlado por gestos"""
    
    def __init__(self, image_paths: list[Path], window_name: str = "Apresentação"):
        self.image_paths = sorted(image_paths)
        self.current_slide = 0
        self.total_slides = len(image_paths)
        self.window_name = window_name
        self.gesture_detector = GestureDetector()
        self.running = True
        
        if self.total_slides == 0:
            raise ValueError("Nenhuma imagem encontrada para apresentação")
        
        logger.info(f"📊 Apresentação carregada: {self.total_slides} slides")
    
    def load_slide(self, index: int) -> np.ndarray:
        """
        Carrega slide por índice
        
        Args:
            index: Índice do slide (0-based)
        
        Returns:
            Imagem do slide como numpy array
        """
        if 0 <= index < self.total_slides:
            slide_path = self.image_paths[index]
            slide = cv2.imread(str(slide_path))
            if slide is None:
                logger.error(f"Erro ao carregar: {slide_path}")
                return np.zeros((720, 1280, 3), dtype=np.uint8)
            return slide
        return np.zeros((720, 1280, 3), dtype=np.uint8)
    
    def next_slide(self):
        """Avança para o próximo slide"""
        if self.current_slide < self.total_slides - 1:
            self.current_slide += 1
            logger.info(f"➡️  Slide {self.current_slide + 1}/{self.total_slides}")
        else:
            logger.info("⚠️  Já está no último slide")
    
    def previous_slide(self):
        """Volta para o slide anterior"""
        if self.current_slide > 0:
            self.current_slide -= 1
            logger.info(f"⬅️  Slide {self.current_slide + 1}/{self.total_slides}")
        else:
            logger.info("⚠️  Já está no primeiro slide")
    
    def render_slide_with_camera(self, slide: np.ndarray, 
                                 camera_frame: np.ndarray) -> np.ndarray:
        """
        Renderiza slide com miniatura da câmera
        
        Args:
            slide: Imagem do slide principal
            camera_frame: Frame da câmera processado
        
        Returns:
            Imagem combinada
        """
        # Redimensionar slide para tela cheia
        screen_height, screen_width = 1080, 1920
        slide_resized = cv2.resize(slide, (screen_width, screen_height))
        
        # Redimensionar câmera para miniatura (canto inferior direito)
        camera_height, camera_width = 240, 320
        camera_resized = cv2.resize(camera_frame, (camera_width, camera_height))
        
        # Criar cópia do slide
        output = slide_resized.copy()
        
        # Posicionar miniatura da câmera
        y_offset = screen_height - camera_height - 20
        x_offset = screen_width - camera_width - 20
        
        # Adicionar borda à miniatura
        cv2.rectangle(output, 
                     (x_offset - 2, y_offset - 2),
                     (x_offset + camera_width + 2, y_offset + camera_height + 2),
                     (255, 255, 255), 2)
        
        # Inserir miniatura
        output[y_offset:y_offset + camera_height, 
               x_offset:x_offset + camera_width] = camera_resized
        
        # Adicionar informações do slide
        info_text = f"Slide {self.current_slide + 1}/{self.total_slides}"
        cv2.putText(output, info_text, (20, screen_height - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Adicionar instruções
        instructions = [
            "Mao direita <- esquerda: Proximo",
            "Mao esquerda -> direita: Anterior", 
            "Paz (2 dedos): Sair",
            "ESC: Sair"
        ]
        
        for i, text in enumerate(instructions):
            cv2.putText(output, text, (20, 30 + i * 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        return output
    
    def run(self):
        """Executa a apresentação"""
        # Inicializar câmera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            logger.error("❌ Erro ao abrir câmera")
            return
        
        # Configurar câmera para melhor qualidade
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Criar janela em tela cheia
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, 
                            cv2.WINDOW_FULLSCREEN)
        
        logger.info("🎬 Apresentação iniciada!")
        logger.info("👋 Use gestos para controlar os slides")
        
        try:
            while self.running:
                # Capturar frame da câmera
                ret, frame = cap.read()
                if not ret:
                    logger.error("❌ Erro ao capturar frame")
                    break
                
                # Espelhar frame horizontalmente
                frame = cv2.flip(frame, 1)
                
                # Processar gestos
                annotated_frame, gesture = self.gesture_detector.process_frame(frame)
                
                # Executar ação baseada no gesto
                if gesture == Gesture.SWIPE_LEFT:
                    self.next_slide()
                elif gesture == Gesture.SWIPE_RIGHT:
                    self.previous_slide()
                elif gesture == Gesture.PEACE:
                    logger.info("👋 Encerrando apresentação...")
                    break
                
                # Carregar slide atual
                current_slide_img = self.load_slide(self.current_slide)
                
                # Renderizar slide com miniatura da câmera
                presentation_frame = self.render_slide_with_camera(
                    current_slide_img, annotated_frame
                )
                
                # Exibir
                cv2.imshow(self.window_name, presentation_frame)
                
                # Verificar teclas
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC
                    logger.info("⌨️  ESC pressionado - Encerrando...")
                    break
                elif key == ord('n') or key == 83:  # 'n' ou seta direita
                    self.next_slide()
                elif key == ord('p') or key == 81:  # 'p' ou seta esquerda
                    self.previous_slide()
                elif key == ord('q'):
                    break
        
        finally:
            # Liberar recursos
            cap.release()
            cv2.destroyAllWindows()
            self.gesture_detector.release()
            logger.info("✅ Apresentação finalizada")