# --- TEMPLATES ---
TEMPLATES = {
    "pyside6": {
        "1": ("Window", """from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout
from PySide6.QtCore import Qt


class {name}Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('{name}')
        self.setGeometry(100, 100, 800, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        self.setup_ui()
    
    def setup_ui(self):
        \"\"\"Configura os componentes da interface\"\"\"
        pass


if __name__ == "__main__":
    app = QApplication([])
    window = {name}Window()
    window.show()
    app.exec()
"""),
        "2": ("Button", """from PySide6.QtWidgets import QPushButton, QApplication, QWidget, QVBoxLayout
from PySide6.QtCore import Qt


class {name}Btn(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText('{name}')
        self.setMinimumHeight(40)
        self.setMinimumWidth(120)
        self.clicked.connect(self.on_clicked)
    
    def on_clicked(self):
        \"\"\"Callback quando o botão é clicado\"\"\"
        print(f"Botão {{self.text()}} foi clicado!")


class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Teste - {name}Btn')
        self.setGeometry(100, 100, 300, 200)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        btn = {name}Btn()
        layout.addWidget(btn)


if __name__ == "__main__":
    app = QApplication([])
    window = TestWindow()
    window.show()
    app.exec()
"""),
        "3": ("Input", """from PySide6.QtWidgets import QLineEdit, QApplication, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class {name}Input(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText('Digite {name}...')
        self.setMinimumHeight(35)
        self.textChanged.connect(self.on_text_changed)
    
    def on_text_changed(self, text):
        \"\"\"Callback quando o texto é alterado\"\"\"
        print(f"Texto alterado: {{text}}")
    
    def get_value(self):
        \"\"\"Retorna o valor atual do input\"\"\"
        return self.text()
    
    def set_value(self, value):
        \"\"\"Define o valor do input\"\"\"
        self.setText(str(value))


class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Teste - {name}Input')
        self.setGeometry(100, 100, 400, 200)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        label = QLabel('Campo de entrada:')
        layout.addWidget(label)
        
        input_field = {name}Input()
        layout.addWidget(input_field)


if __name__ == "__main__":
    app = QApplication([])
    window = TestWindow()
    window.show()
    app.exec()
"""),
        "4": ("Table", """from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QApplication, QWidget, QVBoxLayout, QHeaderView
from PySide6.QtCore import Qt


class {name}Table(QTableWidget):
    def __init__(self, rows=5, cols=3, parent=None):
        super().__init__(rows, cols, parent)
        self.setup_table()
    
    def setup_table(self):
        \"\"\"Configura a tabela\"\"\"
        # Define cabeçalhos
        headers = [f"Coluna {{i+1}}" for i in range(self.columnCount())]
        self.setHorizontalHeaderLabels(headers)
        
        # Ajusta largura das colunas
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        # Preenche com dados de exemplo
        self.populate_example_data()
    
    def populate_example_data(self):
        \"\"\"Preenche a tabela com dados de exemplo\"\"\"
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                self.setItem(row, col, QTableWidgetItem(f"R{{row+1}}C{{col+1}}"))
    
    def add_row(self, data):
        \"\"\"Adiciona uma nova linha com os dados fornecidos\"\"\"
        row = self.rowCount()
        self.insertRow(row)
        for col, value in enumerate(data):
            if col < self.columnCount():
                self.setItem(row, col, QTableWidgetItem(str(value)))
    
    def get_selected_row_data(self):
        \"\"\"Retorna os dados da linha selecionada\"\"\"
        current_row = self.currentRow()
        if current_row >= 0:
            return [self.item(current_row, col).text() 
                   for col in range(self.columnCount())]
        return None


class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Teste - {name}Table')
        self.setGeometry(100, 100, 600, 400)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        table = {name}Table(5, 3)
        layout.addWidget(table)


if __name__ == "__main__":
    app = QApplication([])
    window = TestWindow()
    window.show()
    app.exec()
"""),
        "5": ("Dialog", """from PySide6.QtWidgets import QDialog, QApplication, QVBoxLayout, QPushButton, QLabel, QDialogButtonBox
from PySide6.QtCore import Qt


class {name}Dialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('{name} Dialog')
        self.setMinimumWidth(400)
        self.setMinimumHeight(200)
        self.setup_ui()
    
    def setup_ui(self):
        \"\"\"Configura a interface do diálogo\"\"\"
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Label de conteúdo
        label = QLabel('Conteúdo do diálogo {name}')
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        # Botões padrão
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def accept(self):
        \"\"\"Callback quando o diálogo é aceito\"\"\"
        print("Diálogo aceito!")
        super().accept()
    
    def reject(self):
        \"\"\"Callback quando o diálogo é rejeitado\"\"\"
        print("Diálogo cancelado!")
        super().reject()


class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Teste - {name}Dialog')
        self.setGeometry(100, 100, 300, 200)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        btn_open = QPushButton('Abrir Diálogo')
        btn_open.clicked.connect(self.open_dialog)
        layout.addWidget(btn_open)
    
    def open_dialog(self):
        \"\"\"Abre o diálogo\"\"\"
        dialog = {name}Dialog(self)
        if dialog.exec():
            print("Usuário confirmou!")


if __name__ == "__main__":
    app = QApplication([])
    window = TestWindow()
    window.show()
    app.exec()
"""),
        "6": ("Card", """from PySide6.QtWidgets import QFrame, QApplication, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette


class {name}Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_card()
    
    def setup_card(self):
        \"\"\"Configura o card\"\"\"
        # Estilo visual
        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(2)
        
        # Layout interno
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Conteúdo do card
        label = QLabel('{name} Card')
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        # Define tamanho mínimo
        self.setMinimumHeight(150)
        self.setMinimumWidth(200)
    
    def set_content(self, content):
        \"\"\"Define o conteúdo do card\"\"\"
        layout = self.layout()
        if layout:
            # Remove widgets antigos (exceto o primeiro se existir)
            while layout.count() > 0:
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Adiciona novo conteúdo
            if isinstance(content, str):
                label = QLabel(content)
                label.setAlignment(Qt.AlignCenter)
                layout.addWidget(label)


class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Teste - {name}Card')
        self.setGeometry(100, 100, 400, 300)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        card = {name}Card()
        layout.addWidget(card)


if __name__ == "__main__":
    app = QApplication([])
    window = TestWindow()
    window.show()
    app.exec()
"""),
        "7": ("Controller", """from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel


class {name}Model:
    \"\"\"Model para {name}\"\"\"
    def __init__(self):
        self.data = None
    
    def get_data(self):
        \"\"\"Retorna os dados do model\"\"\"
        return self.data
    
    def set_data(self, data):
        \"\"\"Define os dados do model\"\"\"
        self.data = data


class {name}View(QWidget):
    \"\"\"View para {name}\"\"\"
    def __init__(self):
        super().__init__()
        self.setWindowTitle('{name} View')
        self.setGeometry(100, 100, 400, 300)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.label = QLabel('Aguardando ação...')
        layout.addWidget(self.label)
        
        self.btn_action = QPushButton('Executar Ação')
        layout.addWidget(self.btn_action)
    
    def update_display(self, message):
        \"\"\"Atualiza a exibição\"\"\"
        self.label.setText(message)


class {name}Controller:
    \"\"\"Controller para {name}\"\"\"
    def __init__(self, view, model):
        self.view = view
        self.model = model
        self.connect_signals()
    
    def connect_signals(self):
        \"\"\"Conecta os sinais da view aos métodos do controller\"\"\"
        self.view.btn_action.clicked.connect(self.handle_action)
    
    def handle_action(self):
        \"\"\"Processa a ação do usuário\"\"\"
        self.model.set_data("Ação executada!")
        data = self.model.get_data()
        self.view.update_display(f"Controller processou: {{data}}")
        print(f"Controller processou: {{data}}")


if __name__ == "__main__":
    app = QApplication([])
    
    # Cria instâncias
    model = {name}Model()
    view = {name}View()
    controller = {name}Controller(view, model)
    
    # Exibe a view
    view.show()
    app.exec()
""")
    },
    "react": {
        "1": ("Component", "class {name} extends React.Component {{ render() {{ return <div>{name}</div> }} }}"),
        "2": ("Navbar", "class {name}Nav extends React.Component {{ render() {{ return <nav className='p-4 bg-black text-white'>{name}</nav> }} }}"),
        "3": ("Button", "class {name}Btn extends React.Component {{ render() {{ return <button className='bg-blue-500 p-2'>{name}</button> }} }}"),
        "4": ("Form", "class {name}Form extends React.Component {{ render() {{ return <form className='p-4 border'><input placeholder='{name}'/></form> }} }}"),
        "5": ("Modal", "class {name}Modal extends React.Component {{ render() {{ return <div className='modal'>{name}</div> }} }}"),
        "6": ("Card", "class {name}Card extends React.Component {{ render() {{ return <div className='shadow-lg p-4'>{name}</div> }} }}"),
        "7": ("Model", "// Model para {name}\nexport const {name}Model = {{ id: null, name: '{name}' }};")
    }
}
