from PySide6.QtWidgets import QFrame, QVBoxLayout
from PySide6.QtCore import Signal
from ..widgets.py_push_button import PyPushButton

class NavigationMenu(QFrame):
    """
    A widget that holds the main navigation buttons.
    Emits signals when buttons are clicked.
    """
    dashboard_requested = Signal()
    pomodoro_requested = Signal()
    checklist_requested = Signal()
    settings_requested = Signal()
    perdas_duplas_requested = Signal() # Novo sinal para Perdas Duplas ETL

    _NAVIGATION_ITEMS = [
        {"text": "Dashboard", "icon_path": "icon_home.svg", "signal": "dashboard_requested"},
        # {"text": "Pomodoro", "icon_path": "icon_widgets.svg", "signal": "pomodoro_requested"}, # Exemplo de item removido
        #{"text": "Checklist", "icon_path": "icon_widgets.svg", "signal": "checklist_requested"},
        {"text": "Configurações", "icon_path": "icon_settings.svg", "signal": "settings_requested"},
        {"text": "🤖 Perdas Duplas ETL", "icon_path": "icon_rpa.svg", "signal": "perdas_duplas_requested"},
    ]

    def __init__(self):
        super().__init__()
        self.setObjectName("navigation_menu")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(5)

        self.buttons = {}
        for item in self._NAVIGATION_ITEMS:
            btn = PyPushButton(text=item["text"], icon_path=item["icon_path"])
            setattr(self, f"btn_{item['signal'].replace('_requested', '')}", btn) # Atribui o botão a um atributo (ex: self.btn_dashboard)
            self.layout.addWidget(btn)
            self.buttons[item["signal"]] = btn # Armazena para acesso rápido
            btn.clicked.connect(lambda checked, signal_name=item["signal"]: self._emit_navigation_signal(signal_name))
        
    def _emit_navigation_signal(self, signal_name):
        """Emite o sinal de navegação correspondente ao nome do sinal."""
        signal = getattr(self, signal_name)
        if signal:
            signal.emit()

    def set_active_button(self, tab_name):
        """Sets the visual state of the navigation buttons."""
        for item in self._NAVIGATION_ITEMS:
            btn = self.buttons.get(item["signal"])
            if btn:
                btn.set_active(item["text"] == tab_name)
