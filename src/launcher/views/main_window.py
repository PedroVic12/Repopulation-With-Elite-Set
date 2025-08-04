# src/launcher/views/main_window.py

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel,
    QHBoxLayout, QTextEdit, QProgressBar, QTabWidget, QGroupBox, QSpinBox,
    QLineEdit, QRadioButton, QButtonGroup, QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator, QDoubleValidator

# O PySide6 (e seu antecessor, o PyQt) usa um sistema de "sinais e slots" para comunicação.
# Quando um evento ocorre (ex: um botão é clicado), um "sinal" é emitido.
# Esse sinal pode ser conectado a um "slot" (uma função ou método), que será executado.
# A View (este arquivo) é responsável por definir os widgets e emitir os sinais.
# O Controller (main_controller.py) será responsável por fornecer os slots (a lógica).

class ConfigTab(QWidget):
    """
    Aba de configuração. Contém todos os widgets para definir os parâmetros do AG.
    Herda de QWidget, a classe base para todos os objetos de interface do usuário.
    """
    def __init__(self):
        super().__init__()
        self.param_widgets = {}
        self._init_ui()

    def _init_ui(self):
        """Inicializa a interface do usuário da aba."""
        layout = QVBoxLayout(self) # QVBoxLayout organiza os widgets verticalmente.
        self._create_general_settings(layout)
        self._create_ag_params(layout)
        self._create_summary(layout)
        self._create_run_button(layout)
        layout.addStretch() # Adiciona um espaço flexível no final.

    def _create_general_settings(self, layout):
        """Cria a seção de configurações gerais."""
        # QGroupBox é um contêiner com uma borda e um título.
        general_group = QGroupBox("Configurações Gerais")
        general_layout = QVBoxLayout(general_group)
        
        self.runs_per_config_spin = QSpinBox() # Um campo para valores inteiros.
        self.runs_per_config_spin.setRange(1, 100)
        
        # QLabel é usado para exibir texto.
        general_layout.addWidget(QLabel("Execuções por Configuração:"))
        general_layout.addWidget(self.runs_per_config_spin)
        layout.addWidget(general_group)

    def _create_ag_params(self, layout):
        """Cria a seção de parâmetros do AG."""
        ag_group = QGroupBox("Parâmetros do Algoritmo Genético")
        # QGridLayout organiza os widgets em uma grade.
        self.ag_layout = QGridLayout(ag_group)
        layout.addWidget(ag_group)

    def add_param_widget(self, name: str, default_value):
        """Adiciona um widget de parâmetro dinamicamente."""
        widget_group = QGroupBox(name)
        layout = QVBoxLayout(widget_group)
        
        # QButtonGroup gerencia um grupo de botões, garantindo que apenas um seja selecionado.
        mode_group = QButtonGroup(self)
        fixed_radio = QRadioButton("Fixo") # Botão de opção.
        variable_radio = QRadioButton("Variável")
        fixed_radio.setChecked(True)
        mode_group.addButton(fixed_radio)
        mode_group.addButton(variable_radio)
        
        mode_layout = QHBoxLayout() # QHBoxLayout organiza os widgets horizontalmente.
        mode_layout.addWidget(fixed_radio)
        mode_layout.addWidget(variable_radio)
        layout.addLayout(mode_layout)

        is_int = isinstance(default_value, int)
        fixed_input = QLineEdit() # Campo de texto de uma linha.
        # QValidator garante que a entrada do usuário tenha o formato correto.
        validator = QIntValidator(1, 100000) if is_int else QDoubleValidator(0.0, 1.0, 5)
        fixed_input.setValidator(validator)
        fixed_input.setText(str(default_value))

        variable_inputs_widget = QWidget()
        variable_layout = QHBoxLayout(variable_inputs_widget)
        variable_layout.setContentsMargins(0,0,0,0)
        variable_inputs = []
        for i in range(4):
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"V{i+1}")
            input_field.setText(str(default_value))
            input_field.setValidator(validator)
            variable_layout.addWidget(input_field)
            variable_inputs.append(input_field)
        variable_inputs_widget.setVisible(False)

        layout.addWidget(fixed_input)
        layout.addWidget(variable_inputs_widget)

        # Conecta o sinal 'toggled' dos botões de rádio aos slots 'setVisible' dos widgets.
        # Isso faz com que a interface mude dinamicamente.
        fixed_radio.toggled.connect(fixed_input.setVisible)
        variable_radio.toggled.connect(variable_inputs_widget.setVisible)

        # Armazena os widgets para que o Controller possa acessá-los.
        self.param_widgets[name] = {
            "mode": mode_group, "fixed": fixed_input,
            "variable": variable_inputs, "is_int": is_int
        }
        
        # Adiciona o novo widget de parâmetro ao layout da grade.
        row = (len(self.param_widgets) - 1) // 2
        col = (len(self.param_widgets) - 1) % 2
        self.ag_layout.addWidget(widget_group, row, col)

    def _create_summary(self, layout):
        """Cria a seção de resumo."""
        summary_group = QGroupBox("Resumo da Execução")
        summary_layout = QHBoxLayout(summary_group)
        self.unique_configs_label = QLabel("Configurações Únicas: 1")
        self.total_runs_label = QLabel("Total de Execuções: 1")
        summary_layout.addWidget(self.unique_configs_label)
        summary_layout.addWidget(self.total_runs_label)
        layout.addWidget(summary_group)

    def _create_run_button(self, layout):
        """Cria o botão de execução."""
        self.run_button = QPushButton("💾 Salvar e Executar") # Botão clicável.
        self.run_button.setObjectName("run_button")
        layout.addWidget(self.run_button, alignment=Qt.AlignCenter)

    def show_message(self, title: str, message: str, level: str = "info"):
        """Exibe uma caixa de mensagem para o usuário."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        level_map = {
            "info": QMessageBox.Information,
            "warning": QMessageBox.Warning,
            "critical": QMessageBox.Critical
        }
        msg_box.setIcon(level_map.get(level, QMessageBox.Information))
        msg_box.exec()

class ExecutionTab(QWidget):
    """Aba de execução. Mostra os logs e o progresso."""
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self._create_control_buttons(layout)
        self._create_status_panel(layout)
        self._create_progress_bar(layout)
        self._create_log_area(layout)

    def _create_control_buttons(self, layout):
        control_layout = QHBoxLayout()
        self.run_dashboard_btn = QPushButton("📊 Abrir Dashboard")
        self.stop_btn = QPushButton("⏹️ Parar Execução")
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.run_dashboard_btn)
        control_layout.addWidget(self.stop_btn)
        layout.addLayout(control_layout)

    def _create_status_panel(self, layout):
        self.current_config_group = QGroupBox("Configuração da Execução Atual")
        current_config_layout = QVBoxLayout(self.current_config_group)
        self.current_config_label = QLabel("Aguardando início...")
        self.current_config_label.setAlignment(Qt.AlignCenter)
        current_config_layout.addWidget(self.current_config_label)
        layout.addWidget(self.current_config_group)

    def _create_progress_bar(self, layout):
        self.progress_bar = QProgressBar() # Barra de progresso.
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def _create_log_area(self, layout):
        self.log_text = QTextEdit() # Área de texto com múltiplas linhas.
        self.log_text.setReadOnly(True)
        layout.addWidget(QLabel("Log de Execução:"))
        layout.addWidget(self.log_text)

    def append_log(self, message: str):
        """Adiciona uma mensagem ao log."""
        self.log_text.append(message)
        self.log_text.ensureCursorVisible()

class LauncherWindow(QMainWindow):
    """
    A janela principal da aplicação. Herda de QMainWindow, que fornece uma
    estrutura de janela padrão com barra de menus, barra de status, etc.
    """
    def __init__(self, style: str):
        super().__init__()
        self.setWindowTitle("RCE Framework Launcher - Arquitetura MVC")
        self.setMinimumSize(900, 700)
        self.setStyleSheet(style) # Aplica a folha de estilos CSS.

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        self._create_header(main_layout)
        self._create_tabs(main_layout)
        
        self.statusBar().showMessage("Pronto.")

    def _create_header(self, layout):
        title = QLabel("Repopulation-With-Elite-Set Framework")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Configuração e Execução com Arquitetura MVC")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

    def _create_tabs(self, layout):
        # QTabWidget é um widget que contém múltiplas abas.
        self.tab_widget = QTabWidget()
        self.config_tab = ConfigTab()
        self.execution_tab = ExecutionTab()
        
        self.tab_widget.addTab(self.config_tab, "⚙️ Configuração e Execução")
        self.tab_widget.addTab(self.execution_tab, "📊 Dashboard e Logs")
        
        layout.addWidget(self.tab_widget)
