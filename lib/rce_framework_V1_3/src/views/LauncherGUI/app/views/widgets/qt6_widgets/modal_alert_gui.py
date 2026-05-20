import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QDialog,
    QMessageBox,
    QVBoxLayout,
)


class MinhaJanela(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Janela Principal")
        self.setGeometry(100, 100, 300, 200)

        # Variável de controle
        self.abrir_modal = False

        # Botão para testar a abertura
        self.botao = QPushButton("Abrir Modal", self)
        self.botao.setGeometry(100, 80, 100, 40)
        self.botao.clicked.connect(self.verificar_e_abrir)

    def verificar_e_abrir(self):
        # Verifica se a variável é True
        if self.abrir_modal:
            # Cria a modal (QDialog)
            modal = QDialog(self)
            modal.setWindowTitle("Janela Modal")
            modal.resize(200, 150)

            # Adiciona um layout e widget na modal
            layout = QVBoxLayout()
            layout.addWidget(QPushButton("Fechar", modal))
            modal.setLayout(layout)

            QMessageBox.information(
                self, "Aviso", "O MODAL ABRE COM A VARIAVEL EM TRUE."
            )

            # Abre a janela como modal (pausa a execução da principal)
            modal.exec()
        else:
            print("A variável está False.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = MinhaJanela()
    janela.show()
    sys.exit(app.exec())
