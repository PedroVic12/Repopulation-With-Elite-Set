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

# =====================================================================================
# HEADER DE IMPORTAÇÃO COMPLETO
# =====================================================================================
import sys
import os
import json
import time
from pathlib import Path
from collections import deque


from src.LauncherGUI.gui.widgets.py_push_button import PyPushButton
from src.LauncherGUI.gui.iframes.LoadingWidget import LoadingWidget


# --- Imports para Análise de SEP ---
import pandas as pd
import pandapower as pp
import pandapower.networks as pn
import pandapower.plotting as plot
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# --- Imports do PySide6 ---
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
    QHBoxLayout,
    QTextEdit,
    QProgressBar,
    QTabWidget,
    QGroupBox,
    QSpinBox,
    QLineEdit,
    QComboBox,
    QMessageBox,
    QRadioButton,
    QButtonGroup,
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
    QFrame,
    QHeaderView,
    QListWidget,
    QListWidgetItem,
    QStackedLayout,
    QSplitter,
    QFileDialog,
)
from PySide6.QtCore import (
    Qt,
    QThread,
    Signal,
    QTimer,
    Slot,
    QObject,
    QPropertyAnimation,
    QEasingCurve,
)
from PySide6.QtGui import (
    QIntValidator,
    QDoubleValidator,
    QFont,
    QColor,
    QTextCursor,
    QIcon,
)

# --- Checagem de dependências opcionais ---
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    import plotly.graph_objects as go
    import plotly.io as pio

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# O import do database_controller permanece, pois é um módulo externo essencial
from src.tools.database_controller import DatabaseController


class ConfigManager:
    """Model - Gerencia o acesso aos arquivos de configuração JSON."""

    def __init__(self):
        self.db_controller = DatabaseController(SRC_DIR)

    def get_params(self):
        return self.db_controller.get_params()

    def get_options(self):
        return self.db_controller.get_options()

    def save_params(self, params):
        return self.db_controller.save_params(params)

    def save_options(self, options):
        return self.db_controller.save_options(options)

    def consolidate_results(self):
        self.db_controller.consolidate_results()


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
from src.LauncherGUI.app.models.process_output_reader import ProcessOutputReader

# from models.config_manager         import ConfigManager
# from models.script_worker          import ScriptWorker
# from models.execution_model        import ExecutionModel
from src.LauncherGUI.app.models.executer_model import ScriptWorker, ExecutionModel

from src.LauncherGUI.app.models.power_system_model import PowerSystemModel
from src.LauncherGUI.app.controllers.results_repository import ResultsRepository

from src.LauncherGUI.app.views.windows.launcher_window import (
    LauncherWindow,
    NavigationMenu,
)

from src.LauncherGUI.app.controllers.main_controller import MainController
from src.LauncherGUI.app.controllers.power_system_controller import (
    PowerSystemController,
)
