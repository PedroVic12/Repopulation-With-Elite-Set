import sys
from pathlib import Path
import fitz  # PyMuPDF
import cv2
import mediapipe as mp
import time
import numpy as np

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QPushButton, QHBoxLayout, QStyleFactory, QFileDialog
)
from PySide6.QtGui import QPixmap, QImage, QPalette, QColor
from PySide6.QtCore import Qt, Signal, QThread, QTimer, QMutex

# --- Camera Worker Thread ---
class CameraWorker(QThread):
    frame_ready = Signal(QImage)
    camera_error = Signal(str)

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.running = False
        self.cap = None

    def run(self):
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            self.camera_error.emit("Não foi possível abrir a câmera.")
            return

        self.running = True
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                self.camera_error.emit("Falha ao ler o frame da câmera.")
                break

            # Convert frame to RGB for MediaPipe and then to QImage
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            q_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.frame_ready.emit(q_image)

        self.cap.release()
        self.cap = None

    def stop(self):
        self.running = False
        self.wait() # Wait for the thread to finish

# --- Gesture Detector Thread ---
class GestureDetector(QThread):
    gesture_detected = Signal(str) # Emits "next", "prev", "exit"
    processed_frame_ready = Signal(QImage) # Emits frame with landmarks
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.hands_detector = mp.solutions.hands.Hands(
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self._frame_queue = [] # Queue to hold frames for processing
        self._lock = QMutex() # Mutex for thread-safe access to queue

    def run(self):
        self.running = True
        while self.running: # Loop indefinitely while running
            frame_q_image = None
            self._lock.lock()
            if self._frame_queue: # Check if there are frames to process
                frame_q_image = self._frame_queue.pop(0)
            self._lock.unlock()

            if frame_q_image: # Only process if a frame was available
                # Convert QImage to OpenCV format
                # QImage.Format_RGB888 is 3 bytes per pixel
                # Ensure the QImage is not null and has valid data
                if frame_q_image.isNull():
                    continue # Skip processing if image is null

                # Get the buffer from QImage
                buffer = frame_q_image.constBits()
                # Create a numpy array from the buffer
                # The buffer is read-only, so we need to copy it if we want to modify it (e.g., draw landmarks)
                frame_np = np.array(buffer).reshape(frame_q_image.height(), frame_q_image.width(), 3)
                frame_np = frame_np.copy() # Make it writeable for drawing landmarks
                
                # Process with MediaPipe
                results = self.hands_detector.process(frame_np)

                # Draw landmarks
                annotated_frame = frame_np.copy() # Create a copy to draw on
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        self.mp_drawing.draw_landmarks(
                            annotated_frame,
                            hand_landmarks,
                            mp.solutions.hands.HAND_CONNECTIONS,
                            self.mp_drawing_styles.get_default_hand_landmarks_style(),
                            self.mp_drawing_styles.get_default_hand_connections_style()
                        )
                    # Placeholder for gesture logic
                    # For now, just emit a dummy gesture for testing
                    # self.gesture_detected.emit("next")
                
                h, w, ch = annotated_frame.shape
                bytes_per_line = ch * w
                q_image_annotated = QImage(annotated_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.processed_frame_ready.emit(q_image_annotated)
            else:
                time.sleep(0.01) # Sleep if no frames to process to avoid busy-waiting

    def enqueue_frame(self, q_image: QImage):
        self._lock.lock()
        self._frame_queue.append(q_image) # Add frame to queue
        self._lock.unlock()

    def stop(self):
        self.running = False
        self.wait() # Wait for the thread to finish
        self.hands_detector.close()

# --- PDF Display Window ---
class PDFDisplayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Presentation Slides")
        # Removed Qt.FramelessWindowHint to make it draggable
        self.setWindowFlags(Qt.WindowStaysOnTopHint) # Stays on top, but now draggable
        self.setGeometry(100, 100, 1280, 720) # Default size, can be adjusted

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0) # No margins

        self.slide_label = QLabel()
        self.slide_label.setAlignment(Qt.AlignCenter)
        self.slide_label.setStyleSheet("background-color: black;") # Black background for slides
        main_layout.addWidget(self.slide_label)

        self.document = None
        self.current_page_index = 0
        self.total_pages = 0
        self.zoom_level = 1.0 # Initial zoom level

    def wheelEvent(self, event):
        zoom_factor = 1.1 # How much to zoom in/out
        if event.angleDelta().y() > 0: # Scroll up (zoom in)
            self.zoom_level *= zoom_factor
        else: # Scroll down (zoom out)
            self.zoom_level /= zoom_factor
        
        # Limit zoom level
        self.zoom_level = max(0.5, min(self.zoom_level, 5.0)) # Min 0.5x, Max 5.0x
        self.display_page()

    def load_pdf(self, pdf_path: Path):
        if self.document:
            self.document.close()
        self.document = fitz.open(pdf_path)
        self.current_page_index = 0
        self.total_pages = self.document.page_count
        self.display_page()

    def display_page(self):
        if self.document and 0 <= self.current_page_index < self.total_pages:
            page = self.document.load_page(self.current_page_index)
            
            # Render page at a high resolution, adjusted by zoom level
            matrix = fitz.Matrix(self.zoom_level * 3, self.zoom_level * 3) # Adjust resolution by zoom
            pix = page.get_pixmap(matrix=matrix)
            
            # Convert to QImage
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            
            # Scale to fit the label size
            self.slide_label.setPixmap(QPixmap.fromImage(img).scaled(
                self.slide_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        else:
            self.slide_label.clear() # Clear if no document or invalid page

    def next_page(self):
        if self.document and self.current_page_index < self.total_pages - 1:
            self.current_page_index += 1
            self.display_page()

    def prev_page(self):
        if self.document and self.current_page_index > 0:
            self.current_page_index -= 1
            self.display_page()

    def closeEvent(self, event):
        if self.document:
            self.document.close()
        event.accept()

# --- Main Application Window ---
class MainPresenterWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gesture Presentation Control")
        self.setGeometry(50, 50, 800, 600) # Control window size

        self.camera_worker = CameraWorker()
        self.gesture_detector = GestureDetector()
        self.pdf_display_window = PDFDisplayWindow()

        self.init_ui()
        self.apply_dark_theme()
        self.connect_signals()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Camera Feed Label
        self.camera_feed_label = QLabel("Câmera Desligada")
        self.camera_feed_label.setAlignment(Qt.AlignCenter)
        self.camera_feed_label.setStyleSheet("background-color: #333; color: #CCC; border: 1px solid #555;")
        self.camera_feed_label.setScaledContents(True) # Scale content to fit label
        self.camera_feed_label.setFixedSize(640, 480) # Set a fixed size for the camera feed
        main_layout.addWidget(self.camera_feed_label)

        # Controls Layout
        controls_layout = QHBoxLayout()
        
        self.toggle_camera_button = QPushButton("Ligar Câmera")
        self.toggle_camera_button.clicked.connect(self.toggle_camera)
        controls_layout.addWidget(self.toggle_camera_button)

        self.select_pdf_button = QPushButton("Selecionar PDF")
        self.select_pdf_button.clicked.connect(self.select_pdf)
        controls_layout.addWidget(self.select_pdf_button)

        main_layout.addLayout(controls_layout)

        # Navigation buttons (for testing, will be replaced by gestures)
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("Slide Anterior")
        self.prev_button.clicked.connect(self.pdf_display_window.prev_page)
        nav_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Próximo Slide")
        self.next_button.clicked.connect(self.pdf_display_window.next_page)
        nav_layout.addWidget(self.next_button)
        
        main_layout.addLayout(nav_layout)

    def apply_dark_theme(self):
        app.setStyle(QStyleFactory.create("Fusion")) # Use Fusion style for better dark theme support
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        app.setPalette(palette)

    def connect_signals(self):
        self.camera_worker.frame_ready.connect(self.gesture_detector.enqueue_frame) # Camera sends frames to gesture detector
        self.camera_worker.camera_error.connect(self.handle_camera_error)
        self.gesture_detector.processed_frame_ready.connect(self.update_camera_feed) # Gesture detector sends processed frames to UI
        self.gesture_detector.gesture_detected.connect(self.handle_gesture)

    def toggle_camera(self):
        if self.camera_worker.running:
            self.camera_worker.stop()
            self.toggle_camera_button.setText("Ligar Câmera")
            self.camera_feed_label.setText("Câmera Desligada")
            self.camera_feed_label.clear() # Clear previous frame
            self.gesture_detector.stop() # Stop gesture detection as well
        else:
            self.camera_worker.start()
            self.toggle_camera_button.setText("Desligar Câmera")
            self.gesture_detector.start() # Start gesture detection

    def update_camera_feed(self, q_image: QImage):
        # Scale QImage to fit the label
        scaled_image = q_image.scaled(
            self.camera_feed_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.camera_feed_label.setPixmap(QPixmap.fromImage(scaled_image))
        # No longer passing frame to gesture detector here, it's done via signal

    def handle_camera_error(self, message: str):
        self.camera_feed_label.setText(f"Erro na Câmera: {message}")
        self.toggle_camera_button.setText("Ligar Câmera")
        self.camera_worker.stop()
        self.gesture_detector.stop()

    def select_pdf(self):
        # Use QFileDialog for a proper GUI file selection
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Selecionar Arquivo PDF")
        file_dialog.setNameFilter("Arquivos PDF (*.pdf)")
        file_dialog.setDirectory(str(Path('input').absolute())) # Start in the input directory

        if file_dialog.exec() == QFileDialog.Accepted:
            selected_file_path = file_dialog.selectedFiles()[0]
            selected_pdf = Path(selected_file_path)
            print(f"📄 Arquivo selecionado: {selected_pdf.name}")
            self.pdf_display_window.load_pdf(selected_pdf)
            self.pdf_display_window.show()
        else:
            print("Seleção de PDF cancelada.")


    def handle_gesture(self, gesture: str):
        if gesture == "next":
            self.pdf_display_window.next_page()
        elif gesture == "prev":
            self.pdf_display_window.prev_page()
        elif gesture == "exit":
            self.close() # Close main window
            self.pdf_display_window.close() # Close PDF window

    def closeEvent(self, event):
        if self.camera_worker.running:
            self.camera_worker.stop()
        if self.gesture_detector.running:
            self.gesture_detector.stop()
        self.pdf_display_window.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Apply dark theme globally
    app.setStyle(QStyleFactory.create("Fusion"))
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)

    main_window = MainPresenterWindow()
    main_window.show()
    sys.exit(app.exec())
