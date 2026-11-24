import sys
import shutil
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                             QPushButton, QFileDialog, QLabel, QMessageBox)

class OrganizadorArquivos(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Organizador de Arquivos')
        self.setGeometry(100, 100, 400, 200)
        
        layout = QVBoxLayout()
        
        self.label = QLabel('Nenhuma pasta selecionada')
        layout.addWidget(self.label)
        
        btn_selecionar = QPushButton('Selecionar Pasta')
        btn_selecionar.clicked.connect(self.selecionar_pasta)
        layout.addWidget(btn_selecionar)
        
        btn_organizar = QPushButton('Organizar Arquivos')
        btn_organizar.clicked.connect(self.organizar_arquivos)
        layout.addWidget(btn_organizar)
        
        self.setLayout(layout)
        self.pasta_selecionada = ""
        
    def selecionar_pasta(self):
        pasta = QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        if pasta:
            self.pasta_selecionada = pasta
            self.label.setText(f'Pasta: {pasta}')
            
    def organizar_arquivos(self):
        if not self.pasta_selecionada:
            QMessageBox.warning(self, 'Aviso', 'Selecione uma pasta primeiro!')
            return
            
        pasta_base = Path(self.pasta_selecionada)
        
        for arquivo in pasta_base.iterdir():
            if arquivo.is_file():
                # Cria a pasta de destino com base na extensão (ex: .pdf -> PDF)
                extensao = arquivo.suffix[1:].upper()
                if extensao:
                    pasta_destino = pasta_base / extensao
                    pasta_destino.mkdir(exist_ok=True)
                    
                    # Move o arquivo
                    destino = pasta_destino / arquivo.name
                    try:
                        shutil.move(str(arquivo), str(destino))
                    except Exception as e:
                        pass # Trate possíveis erros aqui
                        
        QMessageBox.information(self, 'Sucesso', 'Arquivos organizados com sucesso!')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = OrganizadorArquivos()
    ex.show()
    sys.exit(app.exec())


