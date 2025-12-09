"""
Script de teste para verificar câmera e MediaPipe
Execute antes de usar o sistema principal
"""
import cv2
import mediapipe as mp
import sys

def test_camera():
    """Testa se a câmera está funcionando"""
    print("🎥 Testando câmera...")
    print(cv2.__version__)
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ ERRO: Não foi possível abrir a câmera")
        print("   Verifique se:")
        print("   - A câmera está conectada")
        print("   - Nenhum outro programa está usando a câmera")
        print("   - Você tem permissões para acessar a câmera")
        return False
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("❌ ERRO: Não foi possível capturar frame da câmera")
        return False
    
    print(f"✅ Câmera OK - Resolução: {frame.shape[1]}x{frame.shape[0]}")
    return True


def test_mediapipe():
    """Testa se o MediaPipe está funcionando"""
    print("\n🤖 Testando MediaPipe...")
    
    try:
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5
        )
        hands.close()
        print("✅ MediaPipe OK")
        return True
    except Exception as e:
        print(f"❌ ERRO no MediaPipe: {e}")
        print("   Instale com: uv pip install mediapipe")
        return False


def test_gesture_detection():
    """Teste interativo de detecção de gestos"""
    print("\n👋 Testando detecção de gestos...")
    print("   Pressione 'q' para sair\n")
    
    cap = cv2.VideoCapture(0)
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    
    cv2.namedWindow("Teste de Gestos", cv2.WINDOW_NORMAL)
    
    print("📹 Mostrando câmera com detecção de mãos...")
    print("   Mostre suas mãos para a câmera")
    
    frame_count = 0
    hands_detected = False
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)
            
            if results.multi_hand_landmarks:
                hands_detected = True
                for hand_landmarks, handedness in zip(results.multi_hand_landmarks,
                                                     results.multi_handedness):
                    # Desenhar landmarks
                    mp_drawing.draw_landmarks(
                        frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                    )
                    
                    # Mostrar qual mão
                    hand_label = handedness.classification[0].label
                    cv2.putText(frame, f"Mao: {hand_label}", (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Instruções
            cv2.putText(frame, "Pressione 'q' para sair", (10, frame.shape[0] - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow("Teste de Gestos", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            
            frame_count += 1
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        hands.close()
    
    if hands_detected:
        print("✅ Detecção de mãos funcionando!")
    else:
        print("⚠️  Nenhuma mão detectada")
        print("   Dicas:")
        print("   - Melhore a iluminação")
        print("   - Fique mais próximo da câmera")
        print("   - Use fundo neutro")
    
    return hands_detected


def main():
    """Executa todos os testes"""
    print("=" * 60)
    print("🔍 TESTE DO SISTEMA DE GESTOS")
    print("=" * 60)
    
    # Teste 1: Câmera
    if not test_camera():
        print("\n❌ Teste falhou: Câmera")
        sys.exit(1)
    
    # Teste 2: MediaPipe
    if not test_mediapipe():
        print("\n❌ Teste falhou: MediaPipe")
        sys.exit(1)
    
    # Teste 3: Detecção de gestos (interativo)
    print("\n" + "=" * 60)
    input("Pressione ENTER para testar detecção de gestos...")
    test_gesture_detection()
    
    print("\n" + "=" * 60)
    print("✅ TODOS OS TESTES CONCLUÍDOS")
    print("=" * 60)
    print("\n🚀 Você pode executar o sistema principal agora:")
    print("   uv run python main.py")


if __name__ == "__main__":
    main()