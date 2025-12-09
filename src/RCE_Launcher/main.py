# src/RCE_Launcher/main.py

import sys
from PySide6.QtWidgets import QApplication, QMessageBox

# Adiciona o diretório 'src' ao path para permitir importações relativas
# como 'from RCE_Launcher.controllers...'
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from RCE_Launcher.controllers.main_controller import MainController
from RCE_Launcher.styles import STYLESHEET
from RCE_Launcher.views.power_analysis_tab import PLOTLY_AVAILABLE

def main():
    """Ponto de entrada principal da aplicação."""
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    # Adverte o usuário se a dependência opcional não estiver instalada
    if not PLOTLY_AVAILABLE:
        QMessageBox.warning(
            None,
            "Dependência Opcional Faltando",
            "O pacote 'PySide6-WebEngine' não foi encontrado. "
            "Os gráficos interativos na aba de Análise de SEP não serão exibidos."
        )

    # Instancia e inicia o controller principal
    controller = MainController(app)
    controller.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
