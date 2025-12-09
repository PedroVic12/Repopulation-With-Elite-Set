# src/RCE_Launcher/views/config_tabs.py

import json
from itertools import product
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QSpinBox,
    QLineEdit, QMessageBox, QRadioButton, QButtonGroup, QGridLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QIntValidator, QDoubleValidator


class ConfigTab(QWidget):
    """
    View - Aba para configurar a bateria de testes do AG.
    Emite um sinal `execution_requested` com os detalhes da configuração.
    """
    execution_requested = Signal(list, int)

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.param_widgets = {}
        self.init_ui()
        self.update_summary()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.create_general_settings(layout)
        self.create_ag_params(layout)
        self.create_summary(layout)
        self.create_run_button(layout)
        layout.addStretch()

    def create_general_settings(self, layout):
        group = QGroupBox("Configurações Gerais")
        glayout = QVBoxLayout(group)
        self.runs_per_config_spin = QSpinBox()
        self.runs_per_config_spin.setRange(1, 100)
        self.runs_per_config_spin.setValue(self.config_manager.get_options().get('repeticoes_por_config', 1))
        self.runs_per_config_spin.valueChanged.connect(self.update_summary)
        glayout.addWidget(QLabel("Execuções por Configuração:"))
        glayout.addWidget(self.runs_per_config_spin)
        layout.addWidget(group)

    def create_ag_params(self, layout):
        group = QGroupBox("Parâmetros do Algoritmo Genético (para Bateria de Testes)")
        ag_layout = QGridLayout(group)
        params_to_render = {"MUTACAO": 0.1, "CROSSOVER": 0.8, "NUM_GENERATIONS": 100, "POP_SIZE": 50}
        for i, (name, val) in enumerate(params_to_render.items()):
            widget = self._create_param_widget(name, self.config_manager.get_params().get(name, val))
            ag_layout.addWidget(widget, i // 2, i % 2)
        layout.addWidget(group)

    def create_summary(self, layout):
        group = QGroupBox("Resumo da Execução")
        slay = QHBoxLayout(group)
        self.unique_configs_label = QLabel("Configurações Únicas: 1")
        self.total_runs_label = QLabel()
        slay.addWidget(self.unique_configs_label)
        slay.addWidget(self.total_runs_label)
        layout.addWidget(group)
        self.update_summary()

    def create_run_button(self, layout):
        self.run_button = QPushButton("Salvar e Ir para Execução")
        self.run_button.clicked.connect(self.prepare_and_run)
        layout.addWidget(self.run_button, alignment=Qt.AlignCenter)

    def _create_param_widget(self, name, default_value):
        group = QGroupBox(name)
        layout = QVBoxLayout(group)
        mode_group = QButtonGroup(self)
        fr = QRadioButton("Fixo")
        vr = QRadioButton("Variável")
        fr.setChecked(True)
        mode_group.addButton(fr)
        mode_group.addButton(vr)
        mlay = QHBoxLayout()
        mlay.addWidget(fr)
        mlay.addWidget(vr)
        layout.addLayout(mlay)

        is_int = isinstance(default_value, int)
        fixed_input = QLineEdit(str(default_value))
        validator = QIntValidator(1, 100000) if is_int else QDoubleValidator(0.0, 1.0, 5)
        fixed_input.setValidator(validator)

        var_widget = QWidget()
        vlay = QGridLayout(var_widget)
        v_inputs = []
        for i in range(4):
            inp = QLineEdit()
            inp.setPlaceholderText(f"V{i+1}")
            inp.setValidator(validator)
            vlay.addWidget(inp, i // 2, i % 2)
            v_inputs.append(inp)
        
        var_widget.setVisible(False)
        layout.addWidget(fixed_input)
        layout.addWidget(var_widget)

        fr.toggled.connect(fixed_input.setVisible)
        vr.toggled.connect(var_widget.setVisible)

        self.param_widgets[name] = {"mode": mode_group, "fixed": fixed_input, "variable": v_inputs, "is_int": is_int}

        fixed_input.textChanged.connect(self.update_summary)
        for vi in v_inputs:
            vi.textChanged.connect(self.update_summary)
        mode_group.buttonClicked.connect(self.update_summary)
        return group

    def update_summary(self, _=None):
        arrays = self._get_variable_arrays()
        num_combs = len(list(product(*arrays.values()))) if arrays else 1
        total_execs = num_combs * self.runs_per_config_spin.value()
        self.unique_configs_label.setText(f"Configurações Únicas: {num_combs}")
        self.total_runs_label.setText(f"Total de Execuções: {total_execs}")

    def _get_variable_arrays(self):
        arrays = {}
        for name, info in self.param_widgets.items():
            if info["mode"].checkedButton().text() == "Variável":
                values = [
                    int(vi.text().strip()) if info["is_int"] else float(vi.text().strip())
                    for vi in info["variable"] if vi.text().strip()
                ]
                if values:
                    arrays[name] = list(dict.fromkeys(values)) # Remove duplicates
        return arrays

    def prepare_and_run(self):
        params = self.config_manager.get_params()
        var_arrays = self._get_variable_arrays()
        for name, info in self.param_widgets.items():
            if info["mode"].checkedButton().text() == "Fixo":
                try:
                    params[name] = int(info["fixed"].text()) if info["is_int"] else float(info["fixed"].text())
                except ValueError:
                    QMessageBox.warning(self, "Erro de Valor", f"Valor inválido para o parâmetro '{name}'.")
                    return

        opts = {'repeticoes_por_config': self.runs_per_config_spin.value(), **var_arrays}
        self.config_manager.save_params(params)
        self.config_manager.save_options(opts)

        keys = list(var_arrays.keys())
        combos = [dict(zip(keys, v)) for v in product(*var_arrays.values())] if keys else [{}]
        
        all_configs = [dict(params, **c) for c in combos]
        self.execution_requested.emit(all_configs, self.runs_per_config_spin.value())


class ParamsAGTab(QWidget):
    """
    View - Aba para editar todos os parâmetros do AG (params.json).
    """
    EXCLUDED_PARAMS = {"MUTACAO", "CROSSOVER", "NUM_GENERATIONS", "POP_SIZE"}

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.init_ui()
        self.reload()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Parâmetro", "Valor"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        self.reload_btn = QPushButton("🔄 Recarregar")
        self.save_btn = QPushButton("💾 Salvar")
        self.reload_btn.clicked.connect(self.reload)
        self.save_btn.clicked.connect(self.save)
        btns.addWidget(self.reload_btn)
        btns.addWidget(self.save_btn)
        layout.addLayout(btns)

    def reload(self):
        self.table.clearContents()
        params = {k: v for k, v in self.config_manager.get_params().items() if k not in self.EXCLUDED_PARAMS}
        self.table.setRowCount(len(params))
        for r, (key, value) in enumerate(params.items()):
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, 0, key_item)
            self.table.setItem(r, 1, QTableWidgetItem(json.dumps(value) if isinstance(value, (list, dict)) else str(value)))

    def save(self):
        params = self.config_manager.get_params()
        for r in range(self.table.rowCount()):
            key = self.table.item(r, 0).text()
            val_str = self.table.item(r, 1).text().strip()
            try:
                # Tenta decodificar JSON se parecer uma lista ou dicionário
                if (val_str.startswith('[') and val_str.endswith(']')) or \
                   (val_str.startswith('{') and val_str.endswith('}')):
                    value = json.loads(val_str)
                else: # Tenta converter para número
                    value = float(val_str)
                    if value.is_integer():
                        value = int(value)
            except (json.JSONDecodeError, ValueError):
                value = val_str # Mantém como string se tudo falhar
            params[key] = value

        if self.config_manager.save_params(params):
            QMessageBox.information(self, "Sucesso", "Parâmetros salvos com sucesso.")
        else:
            QMessageBox.critical(self, "Erro", "Falha ao salvar os parâmetros.")
