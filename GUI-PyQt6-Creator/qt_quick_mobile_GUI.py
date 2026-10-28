print("chamando arquivo .qml")


import sys
import os
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
def main():
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    
    # Obtém o caminho absoluto do arquivo QML no mesmo diretório
    qml_file = os.path.join(os.path.dirname(__file__), 'main.qml')
    
    engine.load(qml_file)
    
    if not engine.rootObjects():
        sys.exit(-1)
        
    print("Janela Qt Quick iniciada. Feche a janela para encerrar.")
    sys.exit(app.exec())
if __name__ == '__main__':
    main()


