# src/RCE_Launcher/views/navigation_menu.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QButtonGroup
from PySide6.QtCore import Signal

class NavigationMenu(QWidget):
    """
    View - O menu de navegação lateral.
    Apenas emite sinais quando os botões são clicados.
    """
    config_ag_requested = Signal()
    params_ag_requested = Signal()
    run_ag_requested = Signal()
    run_agendamento_requested = Signal()
    power_system_analysis_requested = Signal()

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.buttons = {}
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        # Adiciona os botões de navegação
        self._add_nav_button("config_ag", "⚙️ Configurar AG", self.config_ag_requested)
        self._add_nav_button("params_ag", "⌨️ Parâmetros AG", self.params_ag_requested)
        self._add_nav_button("run_ag", "▶️ Executar AG", self.run_ag_requested)
        self._add_nav_button("run_agendamento", "📅 Executar Agendamento", self.run_agendamento_requested)
        self._add_nav_button("power_system_analysis", "🔬 Análise de SEP", self.power_system_analysis_requested)

        self.layout.addStretch()

    def _add_nav_button(self, name: str, text: str, signal: Signal):
        """Método auxiliar para criar e configurar um botão de navegação."""
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setProperty("class", "nav-button")
        btn.clicked.connect(signal.emit)
        self.layout.addWidget(btn)
        self.buttons[name] = btn
        self.button_group.addButton(btn)

    def set_active_button(self, name: str):
        """Marca um botão como ativo com base no nome da aba."""
        if name in self.buttons:
            self.buttons[name].setChecked(True)
