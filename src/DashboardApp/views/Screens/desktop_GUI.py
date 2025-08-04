# Salve este código como desktop_app.py e execute.
# Requer: pip install PySide6

import sys
import os
import json
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFormLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QSpinBox, QCheckBox, QLineEdit, QSlider, QGroupBox, QHeaderView
)
from PySide6.QtCore import QObject, Signal, QThread, Qt

# ===================================================================
# 1. ESTILO (QSS) - Para uma aparência moderna
# ===================================================================
STYLE_QSS = """
QWidget {
    background-color: #282c34;
    color: #abb2bf;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 14px;
}
QGroupBox {
    font-size: 16px;
    font-weight: bold;
    color: #98c379; /* Verde */
    border: 1px solid #3e4451;
    border-radius: 5px;
    margin-top: 1ex;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 3px;
    left: 10px;
}
QLabel#metric_label {
    font-size: 14px;
    color: #abb2bf;
}
QLabel#metric_value {
    font-size: 28px;
    font-weight: bold;
    color: #e5c07b; /* Amarelo */
}
QPushButton#run_button {
    background-color: #98c379; /* Verde */
    color: #282c34;
    font-size: 16px;
    font-weight: bold;
    padding: 12px;
    border-radius: 5px;
}
QPushButton#run_button:hover {
    background-color: #a9d188;
}
QSpinBox, QLineEdit {
    background-color: #21252b;
    border: 1px solid #3e4451;
    border-radius: 4px;
    padding: 8px;
    color: #e6e6e6;
}
QSlider::groove:horizontal {
    border: 1px solid #3e4451;
    height: 4px;
    background: #3e4451;
    margin: 2px 0;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #61afef; /* Azul */
    border: 1px solid #61afef;
    width: 18px;
    margin: -8px 0;
    border-radius: 9px;
}
QTableWidget {
    background-color: #21252b;
    border: 1px solid #3e4451;
    gridline-color: #3e4451;
}
QHeaderView::section {
    background-color: #282c34;
    color: #98c379;
    padding: 4px;
    border: 1px solid #3e4451;
    font-weight: bold;
}
QCheckBox::indicator {
    width: 20px;
    height: 20px;
}
QCheckBox::indicator:unchecked {
    image: url(unchecked.png); /* Placeholder - use QSS for real toggles */
}
QCheckBox::indicator:checked {
    image: url(checked.png); /* Placeholder */
}
"""

# ===================================================================
# 2. MODEL - Gerencia os dados e a lógica de negócio
# ===================================================================
class ConfigurationModel(QObject):
    """Guarda e manipula todos os dados de configuração."""
    config_updated = Signal()
    log_message = Signal(str)
    simulation_finished = Signal(int)

    def __init__(self):
        super().__init__()
        # Valores padrão
        self.num_execucoes = 7
        self.taxa_mutacao_enabled = False
        self.num_geracoes_enabled = False
        # ... outros parâmetros
        self.parametros_rce = {
            "POP_SIZE": 50,
            "RCE_POPULATION": 1,
            "NUM_GER_FERENTES": 1,
            "PORCENTAGEM": 0.1,
            "DELTA_MIN": 0.2
        }

    def set_num_execucoes(self, value):
        self.num_execucoes = value
        self.log_message.emit(f"Número de execuções alterado para: {value}")
        self.config_updated.emit()

    def get_total_execucoes(self):
        # Lógica mais complexa pode ser adicionada aqui
        # com base nos parâmetros AG habilitados.
        return self.num_execucoes

    def run_simulation(self):
        """
        Método que será executado em uma thread separada.
        Aqui entra a sua lógica pesada com DEAP e Pandapower.
        """
        self.log_message.emit("Iniciando simulação...")
        try:
            for i in range(self.get_total_execucoes()):
                self.log_message.emit(f"Executando simulação {i+1}/{self.get_total_execucoes()}...")
                time.sleep(1) # Simula trabalho pesado
            self.log_message.emit("Simulação concluída com sucesso!")
            self.simulation_finished.emit(0) # 0 = sucesso
        except Exception as e:
            self.log_message.emit(f"Erro na simulação: {e}")
            self.simulation_finished.emit(1) # 1 = erro

# ===================================================================
# 3. VIEW - A interface gráfica do usuário (UI)
# ===================================================================
class MainView(QMainWindow):
    """Cria e organiza todos os widgets da UI."""
    run_button_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configurador do Framework RCE")
        self.setGeometry(100, 100, 900, 800)

        # Widget central e layout principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Criação dos painéis da UI
        main_layout.addWidget(self._create_geral_group())
        main_layout.addWidget(self._create_ag_params_group())
        main_layout.addWidget(self._create_quantidade_group())
        main_layout.addWidget(self._create_rce_params_group())
        main_layout.addStretch() # Empurra tudo para cima

    def _create_geral_group(self):
        group_box = QGroupBox("Configurações Gerais")
        layout = QFormLayout()
        self.num_execucoes_spinbox = QSpinBox()
        self.num_execucoes_spinbox.setMinimum(1)
        self.num_execucoes_spinbox.setMaximum(1000)
        layout.addRow("Número de Execuções por Configuração:", self.num_execucoes_spinbox)
        group_box.setLayout(layout)
        return group_box

    def _create_ag_params_group(self):
        group_box = QGroupBox("Parâmetros AG (Algoritmo Genético)")
        layout = QGridLayout()
        self.mutacao_check = QCheckBox("Configurar Taxa de Mutação?")
        self.crossover_check = QCheckBox("Configurar Taxa de Crossover?")
        self.geracoes_check = QCheckBox("Configurar Número de Gerações?")
        self.populacao_check = QCheckBox("Configurar Tamanho da População?")
        layout.addWidget(self.mutacao_check, 0, 0)
        layout.addWidget(self.crossover_check, 1, 0)
        layout.addWidget(self.geracoes_check, 0, 1)
        layout.addWidget(self.populacao_check, 1, 1)
        group_box.setLayout(layout)
        return group_box

    def _create_quantidade_group(self):
        group_box = QGroupBox("Quantidade de Execuções Configuradas")
        layout = QHBoxLayout()
        # Layout para Configurações Únicas
        config_layout = QVBoxLayout()
        config_label = QLabel("Configurações Únicas")
        config_label.setObjectName("metric_label")
        self.config_value = QLabel("1")
        self.config_value.setObjectName("metric_value")
        config_layout.addWidget(config_label)
        config_layout.addWidget(self.config_value)
        # Layout para Total de Execuções
        total_layout = QVBoxLayout()
        total_label = QLabel("Total de Execuções")
        total_label.setObjectName("metric_label")
        self.total_value = QLabel("7")
        self.total_value.setObjectName("metric_value")
        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_value)
        # Botão de Execução
        self.run_button = QPushButton("Salvar e Executar")
        self.run_button.setObjectName("run_button")
        self.run_button.clicked.connect(self.run_button_clicked.emit)

        layout.addLayout(config_layout)
        layout.addStretch()
        layout.addLayout(total_layout)
        layout.addStretch()
        layout.addWidget(self.run_button)
        group_box.setLayout(layout)
        return group_box

    def _create_rce_params_group(self):
        group_box = QGroupBox("Parâmetros AG - RCE utilizados em params.json")
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        self.vars_decisao_input = QLineEdit("14, 15, 14, 18, 15")
        self.limites_slider = QSlider(Qt.Horizontal)
        self.limites_slider.setRange(0, 50)
        self.limites_slider.setValue(31)
        form_layout.addRow("Variáveis de Decisão do Problema:", self.vars_decisao_input)
        form_layout.addRow("Selecione os limites dos valores:", self.limites_slider)
        
        self.params_table = QTableWidget(5, 2)
        self.params_table.setHorizontalHeaderLabels(["Parâmetro", "Valor"])
        self.params_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.params_table)
        group_box.setLayout(layout)
        return group_box

    def update_metrics(self, total_execucoes, configs_unicas):
        """Atualiza os labels de métricas na UI."""
        self.total_value.setText(str(total_execucoes))
        self.config_value.setText(str(configs_unicas))

    def populate_table(self, data):
        """Preenche a tabela com dados do modelo."""
        self.params_table.setRowCount(len(data))
        for row, (key, value) in enumerate(data.items()):
            self.params_table.setItem(row, 0, QTableWidgetItem(key))
            self.params_table.setItem(row, 1, QTableWidgetItem(str(value)))

# ===================================================================
# 4. CONTROLLER - O cérebro que conecta Model e View
# ===================================================================
class AppController(QObject):
    def __init__(self, model, view):
        super().__init__()
        self._model = model
        self._view = view
        self._thread = None
        self._connect_signals()
        self._initial_ui_update()

    def _connect_signals(self):
        """Conecta todos os sinais e slots."""
        self._view.num_execucoes_spinbox.valueChanged.connect(self._model.set_num_execucoes)
        self._model.config_updated.connect(self.on_config_updated)
        self._view.run_button_clicked.connect(self.start_simulation)
        self._model.simulation_finished.connect(self.on_simulation_finish)

    def _initial_ui_update(self):
        """Atualiza a UI com os dados iniciais do modelo."""
        self._view.num_execucoes_spinbox.setValue(self._model.num_execucoes)
        self._view.update_metrics(self._model.get_total_execucoes(), 1)
        self._view.populate_table(self._model.parametros_rce)

    def on_config_updated(self):
        """Chamado quando qualquer configuração no modelo muda."""
        total = self._model.get_total_execucoes()
        # A lógica de "configurações únicas" seria mais complexa
        configs = 1 
        self._view.update_metrics(total, configs)

    def start_simulation(self):
        """Inicia a simulação em uma thread separada."""
        self._view.run_button.setEnabled(False)
        self._thread = QThread()
        # Move o modelo para a thread para que a simulação não trave a UI
        self._model.moveToThread(self._thread)
        self._thread.started.connect(self._model.run_simulation)
        self._thread.start()

    def on_simulation_finish(self):
        """Limpa a thread e reativa a UI."""
        self._thread.quit()
        self._thread.wait()
        self._view.run_button.setEnabled(True)

# ===================================================================
# 5. PONTO DE ENTRADA DA APLICAÇÃO
# ===================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE_QSS)

    # Cria as instâncias MVC
    model = ConfigurationModel()
    view = MainView()
    controller = AppController(model=model, view=view)

    # Exibe a View e inicia o loop da aplicação
    view.show()
    sys.exit(app.exec())
