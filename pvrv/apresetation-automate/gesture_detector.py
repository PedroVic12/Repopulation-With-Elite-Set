"""
Detector de gestos usando MediaPipe Hands
"""
import cv2
import mediapipe as mp
from enum import Enum
from dataclasses import dataclass
import time
import logging

logger = logging.getLogger(__name__)


class Gesture(Enum):
    """Tipos de gestos suportados"""
    NONE = 0
    SWIPE_LEFT = 1   # Mão direita deslizando para esquerda - próximo slide
    SWIPE_RIGHT = 2  # Mão esquerda deslizando para direita - slide anterior
    PEACE = 3        # Sinal de paz (2 dedos) - fechar apresentação
    OPEN_PALM = 4    # Mão aberta - pausar


@dataclass
class HandPosition:
    """Posição da mão detectada"""
    x: float
    y: float
    label: str  # 'Left' ou 'Right'
    timestamp: float


class GestureDetector:
    """Detector de gestos com MediaPipe"""
    
    def __init__(self, min_detection_confidence: float = 0.7, 
                 min_tracking_confidence: float = 0.5):
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        # Histórico de posições para detectar swipes
        self.position_history: dict[str, list[HandPosition]] = {
            'Left': [],
            'Right': []
        }
        self.history_size = 10
        self.swipe_threshold = 0.15  # 15% da largura da tela
        self.gesture_cooldown = 1.0  # 1 segundo entre gestos
        self.last_gesture_time = 0
        
    def count_fingers(self, hand_landmarks, handedness: str) -> int:
        """
        Conta quantos dedos estão levantados
        
        Args:
            hand_landmarks: Landmarks da mão do MediaPipe
            handedness: 'Left' ou 'Right'
        
        Returns:
            Número de dedos levantados (0-5)
        """
        fingers = []
        
        # Polegar (lógica diferente para esquerda/direita)
        if handedness == "Right":
            if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
                fingers.append(1)
            else:
                fingers.append(0)
        else:
            if hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x:
                fingers.append(1)
            else:
                fingers.append(0)
        
        # Outros dedos
        finger_tips = [8, 12, 16, 20]  # Indicador, médio, anelar, mindinho
        finger_pips = [6, 10, 14, 18]
        
        for tip, pip in zip(finger_tips, finger_pips):
            if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
                fingers.append(1)
            else:
                fingers.append(0)
        
        return sum(fingers)
    
    def detect_swipe(self, hand_label: str) -> Gesture | None:
        """
        Detecta movimento de swipe baseado no histórico de posições
        
        Args:
            hand_label: 'Left' ou 'Right'
        
        Returns:
            Gesto detectado ou None
        """
        history = self.position_history[hand_label]
        
        if len(history) < self.history_size:
            return None
        
        # Calcular movimento horizontal
        start_x = history[0].x
        end_x = history[-1].x
        displacement = end_x - start_x
        
        # Verificar tempo decorrido
        time_diff = history[-1].timestamp - history[0].timestamp
        if time_diff < 0.3:  # Movimento deve ser rápido (< 0.3s)
            return None
        
        # Detectar swipe baseado na mão e direção
        if hand_label == "Right" and displacement < -self.swipe_threshold:
            # Mão direita para esquerda -> próximo slide
            return Gesture.SWIPE_LEFT
        elif hand_label == "Left" and displacement > self.swipe_threshold:
            # Mão esquerda para direita -> slide anterior
            return Gesture.SWIPE_RIGHT
        
        return None
    
    def process_frame(self, frame):
        """
        Processa frame e detecta gestos
        
        Args:
            frame: Frame BGR do OpenCV
        
        Returns:
            tuple: (frame_anotado, gesto_detectado)
        """
        # Converter BGR para RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        gesture = Gesture.NONE
        current_time = time.time()
        
        # Verificar cooldown
        if current_time - self.last_gesture_time < self.gesture_cooldown:
            if results.multi_hand_landmarks:
                for hand_landmarks, handedness in zip(results.multi_hand_landmarks, 
                                                     results.multi_handedness):
                    self.mp_drawing.draw_landmarks(
                        frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                    )
            return frame, Gesture.NONE
        
        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, 
                                                 results.multi_handedness):
                # Desenhar landmarks
                self.mp_drawing.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                )
                
                # Identificar mão
                hand_label = handedness.classification[0].label
                
                # Obter posição do pulso
                wrist = hand_landmarks.landmark[0]
                
                # Adicionar ao histórico
                position = HandPosition(
                    x=wrist.x,
                    y=wrist.y,
                    label=hand_label,
                    timestamp=current_time
                )
                
                self.position_history[hand_label].append(position)
                if len(self.position_history[hand_label]) > self.history_size:
                    self.position_history[hand_label].pop(0)
                
                # Contar dedos
                fingers_up = self.count_fingers(hand_landmarks, hand_label)
                
                # Detectar gesto de paz (2 dedos)
                if fingers_up == 2:
                    gesture = Gesture.PEACE
                    self.last_gesture_time = current_time
                    logger.info("✌️ Gesto de paz detectado - Fechar apresentação")
                    break
                
                # Detectar mão aberta (5 dedos)
                elif fingers_up == 5:
                    gesture = Gesture.OPEN_PALM
                    # Não atualizar last_gesture_time para permitir pausas contínuas
                
                # Detectar swipe
                swipe_gesture = self.detect_swipe(hand_label)
                if swipe_gesture:
                    gesture = swipe_gesture
                    self.last_gesture_time = current_time
                    if gesture == Gesture.SWIPE_LEFT:
                        logger.info("👉 Swipe esquerda - Próximo slide")
                    elif gesture == Gesture.SWIPE_RIGHT:
                        logger.info("👈 Swipe direita - Slide anterior")
                    # Limpar histórico após gesto
                    self.position_history[hand_label].clear()
                
                # Adicionar texto com info da mão
                cv2.putText(frame, f"{hand_label}: {fingers_up} dedos", 
                          (10, 30 if hand_label == "Right" else 60),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return frame, gesture
    
    def release(self):
        """Libera recursos"""
        self.hands.close()