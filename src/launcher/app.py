# src/launcher/app.py

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

# Importa as classes da nova estrutura MVC
from .models.config_model import ConfigManager
from .views.main_window import LauncherWindow
from .controllers.main_controller import MainController

# Este é o ponto de entrada principal para a aplicação do launcher.
# Executar este arquivo inicia toda a interface gráfica.

def main():
    """Função principal que monta e executa a aplicação."""
    
    # --- 1. Configuração de Caminhos ---
    # Define os caminhos base para a aplicação. Isso torna o código mais portável,
    # pois não depende de caminhos absolutos fixos.
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    SRC_DIR = BASE_DIR / "src"
    PARAMS_FILE = SRC_DIR / "params.json"
    OPTIONS_FILE = SRC_DIR / "options.json"
    RUN_FRAMEWORK_SCRIPT = SRC_DIR / "run_framework_backup.py"
    DASHBOARD_SCRIPT = SRC_DIR / "DashboardApp" / "dashboard_RCE_APP.py"
    STYLE_FILE = BASE_DIR / "style.py"

    # Dicionário de configuração para passar para o controller.
    # Isso evita que o controller precise conhecer a estrutura de arquivos.
    config = {
        "BASE_DIR": BASE_DIR,
        "SRC_DIR": SRC_DIR,
        "RUN_FRAMEWORK_SCRIPT": RUN_FRAMEWORK_SCRIPT,
        "DASHBOARD_SCRIPT": DASHBOARD_SCRIPT
    }

    # --- 2. Inicialização do QApplication ---
    # Toda aplicação PySide6 precisa de uma (e apenas uma) instância de QApplication.
    # Ela gerencia o loop de eventos principal e os recursos da GUI.
    app = QApplication(sys.argv)

    # --- 3. Montagem do MVC ---
    # Instancia o Model, a View e o Controller.
    
    # O Model gerencia os dados.
    model = ConfigManager(params_file=PARAMS_FILE, options_file=OPTIONS_FILE)
    
    # A View gerencia a interface. Carregamos o estilo aqui.
    try:
        from style import STYLESHEET
    except ImportError:
        STYLESHEET = ""
        print("Aviso: Arquivo style.py não encontrado. Usando estilo padrão.")
        
    view = LauncherWindow(style=STYLESHEET)
    
    # O Controller conecta o Model e a View.
    controller = MainController(model=model, view=view, config=config)

    # --- 4. Execução da Aplicação ---
    # Mostra a janela principal.
    view.show()
    
    # Inicia o loop de eventos da aplicação. O programa ficará aqui até que a janela
    # principal seja fechada. sys.exit garante uma saída limpa.
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
