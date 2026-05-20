"""
Arquivo principal do launcher unificado do RCE Framework.

Este arquivo implementa uma arquitetura Model-View-Controller (MVC) e integra
a funcionalidade completa de análise de sistemas de potência em um único script,
conforme solicitado.

- Model: Camada de dados e lógica de negócio.
- View: A interface gráfica.
- Controller: O orquestrador que conecta Model e View.
"""

#! Bug Fix 18/12/25 execução única
"""
1) self.thread.quit(): Esta função envia um sinal para a thread indicando que ela deve encerrar seu loop de eventos. É um pedido para que a thread termine suas tarefas pendentes e saia de forma limpa. Ela não interrompe a thread imediatamente.

2) self.thread.wait(): Esta função bloqueia a thread que está chamando o wait() até que a self.thread (a thread de trabalho) tenha realmente terminado sua execução.

No nosso caso, com as mudanças que fizemos para usar Qt.QueuedConnection, o método _on_process_finished (e os outros slots que corrigimos) é executado na thread principal da sua aplicação (a thread da GUI).

Quando a thread principal chama self.thread.wait(), ela está esperando pela thread de trabalho (onde o ProcessOutputReader estava rodando) terminar.
"""


import sys
import time

# --- Imports do PySide6 ---
from PySide6.QtWidgets import (
    QApplication,
)

from PySide6.QtGui import (
    QIcon,
)

# --- Checagem de dependências opcionais ---
import matplotlib.pyplot as plt


# =====================================================================================
#  CONFIGURAÇÕES, ESTILOS E CONSTANTES
# =====================================================================================

# --- Estilos (QSS) ---
from style import STYLESHEET

# --- Importa todas as constantes do config central ---
from src.global_settings import *

# =====================================================================================
#  CAMADA MVC — importa Models, Views e Controllers das subpastas
# =====================================================================================

from src.views.LauncherGUI.app.views.iframes.LoadingWidget import LoadingWidget

from src.views.LauncherGUI.app.controllers.main_controller import MainController


# =====================================================================================
#  PONTO DE ENTRADA DA APLICAÇÃO
# =====================================================================================
if __name__ == "__main__":

    # Configurações de Loading
    lazyLoading = LAZY_LOADING
    tempo_minimo_segundos = TEMPO_MINIMO_SEGUNDOS

    app = QApplication(sys.argv)
    plt.ioff()

    # Inicia a tela de loading
    print("Iniciando a tela de loading do sistema...")
    loading_screen = LoadingWidget(tempo_minimo_segundos * 1000)
    loading_screen.show()

    # Processa os eventos para a tela aparecer imediatamente
    app.processEvents()

    # Configurações visuais
    app.setWindowIcon(QIcon(str(ICON_PATH)))
    app.setStyleSheet(STYLESHEET)

    # Marca o início do carregamento
    start_time = time.time()

    # Carrega o controller (Parte pesada)
    controller = MainController(app)

    if lazyLoading:
        # Calcula quanto tempo ainda falta para completar os segundos
        elapsed = time.time() - start_time
        remaining = max(0, tempo_minimo_segundos - elapsed)

        # Em vez de time.sleep, usamos um loop de eventos curto ou QTimer
        # para manter a interface responsiva enquanto espera
        wait_until = time.time() + remaining
        while time.time() < wait_until:
            app.processEvents()
            time.sleep(0.05)  # Pequena pausa para não fritar o processador

    # Finaliza e mostra a principal
    loading_screen.close()
    controller.view.showMaximized()

    sys.exit(app.exec())
