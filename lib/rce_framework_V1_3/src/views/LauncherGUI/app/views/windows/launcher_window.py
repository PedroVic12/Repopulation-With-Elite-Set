# --- Imports do PySide6 ---
from PySide6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QTabWidget,
    QFrame,
)
from PySide6.QtCore import (
    Signal,
    Slot,
    QPropertyAnimation,
    QEasingCurve,
)

from ..widgets.py_push_button import PyPushButton


class NavigationMenu(QWidget):
    """View - Menu de navegação lateral."""

    config_ag_requested = Signal()
    params_ag_requested = Signal()
    run_ag_requested = Signal()
    power_system_analysis_requested = Signal()
    run_sin45_simulator_requested = Signal()
    cli_requested = Signal()
    dynamic_script_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.buttons = {}

        # Botões padrão
        self._add_nav_button("config_ag", "⚙️ Setup", self.config_ag_requested.emit)
        self._add_nav_button(
            "params_ag", "⌨️ Parâmetros AG", self.params_ag_requested.emit
        )
        self._add_nav_button("run_ag", "▶️ Executar RCE AG", self.run_ag_requested.emit)
        # self._add_nav_button("power_system_analysis", "🔬 Análise de SEP", self.power_system_analysis_requested.emit)
        # self._add_nav_button("run_sin45_simulator", "⚡️ Simular SIN 45", self.run_sin45_simulator_requested.emit)
        self._add_nav_button("cli_terminal", "💻 Console", self.cli_requested.emit)

        # Botões dinâmicos de script
        # for script_id, script_info in CUSTOM_SCRIPTS.items():
        #    handler = partial(self.dynamic_script_requested.emit, script_id)
        #    self._add_nav_button(f"script_{script_id}", script_info["name"], handler)

        self.layout.addStretch()

    def _add_nav_button(self, name, text, signal_handler):
        btn = PyPushButton(
            text=text,
            btn_color="#1a1a1a",
            btn_hover="#007acc",
            btn_pressed="#005a9e",
            text_color="#ffffff",
            text_padding=20,
            height=50,
            minimum_width=240,
        )
        btn.clicked.connect(signal_handler)
        self.layout.addWidget(btn)
        self.buttons[name] = btn

    def set_active_button(self, name):
        # Desativa todos os botões que não são de script dinâmico
        for btn_name, btn_widget in self.buttons.items():
            if not btn_name.startswith("script_"):
                btn_widget.set_active(btn_name == name)


#! Janela Principal do app desktop
class LauncherWindow(QMainWindow):
    closing = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("RCE Framework Launcher MVC")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setObjectName("central_widget")  # Nome para o QSS
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.left_menu = QFrame()
        self.left_menu.setFixedWidth(240)
        self.left_menu.setStyleSheet("background-color: #1a1a1a;")
        left_menu_layout = QVBoxLayout(self.left_menu)
        left_menu_layout.setContentsMargins(0, 0, 0, 0)
        self.toggle_button = QPushButton("☰")
        self.toggle_button.setFixedSize(40, 40)
        self.toggle_button.clicked.connect(self.toggle_menu)
        self.nav_menu = NavigationMenu()
        left_menu_layout.addWidget(self.toggle_button)
        left_menu_layout.addWidget(self.nav_menu)
        self.main_layout.addWidget(self.left_menu)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.main_layout.addWidget(self.tabs)

    def closeEvent(self, event):
        self.closing.emit()
        super().closeEvent(event)

    def add_tab(self, widget, name):
        return self.tabs.addTab(widget, name)

    def set_current_tab(self, widget):
        self.tabs.setCurrentWidget(widget)

    def close_tab(self, index):
        self.tabs.removeTab(index)

    @Slot()
    def toggle_menu(self):
        width = self.left_menu.width()
        target = 0 if width > 0 else 240
        for prop_name in [b"minimumWidth", b"maximumWidth"]:
            anim = QPropertyAnimation(self.left_menu, prop_name)
            anim.setDuration(300)
            anim.setStartValue(width)
            anim.setEndValue(target)
            anim.setEasingCurve(QEasingCurve.InOutCubic)
            anim.start()
