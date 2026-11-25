import sys
import os

# Templates de Código
WINDOW_TEMPLATE = """from PySide6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel

class {name}(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("{name} - RayquazaQt6")
        self.resize(400, 300)
        
        # Central Widget e Layout
        self.main_widget = QWidget()
        self.layout = QVBoxLayout(self.main_widget)
        self.setCentralWidget(self.main_widget)

        self.init_ui()

    def init_ui(self):
        self.label = QLabel("Bem-vindo à {name}")
        self.btn = QPushButton("Clique Aqui")
        self.btn.clicked.connect(self.on_click)
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.btn)

    def on_click(self):
        print("Botão em {name} foi clicado!")
"""

MODEL_TEMPLATE = """class {name}Model:
    def __init__(self, data=None):
        self.data = data or {{}}

    def save(self):
        print(f"Salvando dados de {name}...")
"""

def create_file(type_name, class_name):
    filename = f"{class_name.lower()}.py"
    template = WINDOW_TEMPLATE if type_name == "Window" else MODEL_TEMPLATE
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(template.format(name=class_name))
    print(f"✅ [Rayquaza] {type_name} '{class_name}' criada em: {filename}")

if __name__ == "__main__":
    # Simula o comando: python rayquaza.py create Client:Model
    if len(sys.argv) > 2 and sys.argv[1] == "create":
        parts = sys.argv[2].split(":")
        if len(parts) == 2:
            name, kind = parts
            create_file(kind, name)
        else:
            print("Erro: Use o formato Nome:Tipo (ex: Janela:Window)")

"""
Com o script acima na pasta do seu projeto, você pode gerar módulos instantaneamente:

Para criar uma janela:
python3 rayquaza.py create Principal:Window

Para criar um modelo de dados:
python3 rayquaza.py create Cliente:Model

"""