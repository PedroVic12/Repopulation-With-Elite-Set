from qt_core import *

class PyIframeHeader(QWidget):
    """Um widget de cabeçalho reutilizável para Iframes, exibindo um título personalizável."""
    def __init__(self, title_text, parent=None):
        """
        Inicializa o PyIframeHeader.

        Args:
            title_text (str): O texto do título a ser exibido no cabeçalho.
            parent (QWidget, optional): O widget pai. Defaults to None.
        """
        super().__init__(parent)
        self.setFixedHeight(50) # Altura fixa para o cabeçalho
        self.setStyleSheet("background-color: #2c313a; border-bottom: 1px solid #3d444f;") # Estilos CSS básicos

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0) # Margens internas
        layout.setSpacing(10) # Espaçamento entre os widgets

        self.title_label = QLabel(title_text)
        self.title_label.setObjectName("iframe_header_title") # Nome do objeto para estilização CSS
        self.title_label.setStyleSheet("color: #f0f0f0; font-size: 14pt; font-weight: bold;") # Estilos do título
        layout.addWidget(self.title_label)
        layout.addStretch() # Empurra o título para a esquerda

    def set_title(self, title_text):
        """
        Define o texto do título do cabeçalho.

        Args:
            title_text (str): O novo texto do título.
        """
        self.title_label.setText(title_text)
