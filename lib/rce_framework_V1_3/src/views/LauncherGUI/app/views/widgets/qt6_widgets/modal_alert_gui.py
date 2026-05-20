import sys
from PySide6.QtCore import QByteArray, QBuffer, QIODevice
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QMessageBox,
    QVBoxLayout,
    QPushButton,
)

# O conteúdo do seu arquivo 'page.ui' em formato de String XML
UI_STRING = """<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>MainWindow</class>
 <widget class="QMainWindow" name="MainWindow">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>300</width>
    <height>200</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>Janela Principal (UI String)</string>
  </property>
  <widget class="QWidget" name="centralwidget">
   <widget class="QPushButton" name="botao">
    <property name="geometry">
     <rect>
      <x>100</x>
      <y>80</y>
      <width>100</width>
      <height>40</height>
     </rect>
    </property>
    <property name="text">
     <string>Abrir Modal</string>
    </property>
   </widget>
  </widget>
 </widget>
 <resources/>
 <connections/>
</ui>
"""


class MinhaJanela:
    def __init__(self):
        # 1. Converte a string XML em dados binários na memória
        loader = QUiLoader()
        dados_ui = QByteArray(UI_STRING.encode("utf-8"))
        buffer = QBuffer(dados_ui)
        buffer.open(QIODevice.ReadOnly)

        # 2. Carrega a interface a partir do buffer de memória
        self.ui = loader.load(buffer)
        buffer.close()

        # Variável de controle (mude para True para testar o modal)
        self.abrir_modal = True

        # 3. Conecta o botão XML (name="botao") à função do script
        self.ui.botao.clicked.connect(self.verificar_e_abrir)

    def verificar_e_abrir(self):
        if self.abrir_modal:
            # Cria o modal (QDialog)
            modal = QDialog(self.ui)
            modal.setWindowTitle("Janela Modal")
            modal.resize(200, 150)

            # Estrutura interna do modal
            layout = QVBoxLayout()
            botao_fechar = QPushButton("Fechar", modal)
            botao_fechar.clicked.connect(modal.close)
            layout.addWidget(botao_fechar)
            modal.setLayout(layout)

            QMessageBox.information(
                self.ui, "Aviso", "O MODAL ABRE COM A VARIAVEL EM TRUE."
            )

            modal.exec()
        else:
            print("A variável está False.")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    programa = MinhaJanela()
    programa.ui.show()

    sys.exit(app.exec())
