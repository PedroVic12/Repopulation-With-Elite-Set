from PySide6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel

class Principal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Principal - RayquazaQt6")
        self.resize(400, 300)
        
        # Central Widget e Layout
        self.main_widget = QWidget()
        self.layout = QVBoxLayout(self.main_widget)
        self.setCentralWidget(self.main_widget)

        self.init_ui()

    def init_ui(self):
        self.label = QLabel("Bem-vindo à Principal")
        self.btn = QPushButton("Clique Aqui")
        self.btn.clicked.connect(self.on_click)
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.btn)

    def on_click(self):
        print("Botão em Principal foi clicado!")


