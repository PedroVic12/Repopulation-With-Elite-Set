import sys
import os
import json
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel,
    QHBoxLayout, QGroupBox, QSpinBox, QDoubleSpinBox, QCheckBox, QLineEdit, 
    QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt, Signal

# Configuração
BASE_DIR = Path(__file__).parent
PARAMS_FILE = BASE_DIR / "lib" / "params.json"
OPTIONS_FILE = BASE_DIR / "lib" / "options.json"

class ConfigManager:
    def __init__(self):
        self.global_params = self.load_json(PARAMS_FILE)
        self.execution_options = self.load_json(OPTIONS_FILE)

    def load_json(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar {file_path}: {e}")
            return {}

    def save_options_json(self, options_data):
        try:
            with open(OPTIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(options_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar options.json: {e}")
            return False

class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.param_widgets = {}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("🚀 Launcher - Teste de Interface")
        self.setMinimumSize(800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Título
        title = QLabel("🧬 Configuração de Parâmetros")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E86AB; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Execuções por configuração
        exec_group = QGroupBox("📊 Configurações Gerais")
        exec_layout = QVBoxLayout(exec_group)
        
        self.runs_spin = QSpinBox()
        self.runs_spin.setRange(1, 100)
        self.runs_spin.setValue(7)
        self.runs_spin.valueChanged.connect(self.update_summary)
        
        exec_layout.addWidget(QLabel("🔁 Execuções por Configuração:"))
        exec_layout.addWidget(self.runs_spin)
        layout.addWidget(exec_group)

        # Parâmetros
        params_group = QGroupBox("🔧 Parâmetros do Algoritmo Genético")
        params_layout = QVBoxLayout(params_group)
        
        # 4 parâmetros principais
        self.main_params = {
            "MUTACAO": self.config_manager.global_params.get("MUTACAO", 0.25),
            "CROSSOVER": self.config_manager.global_params.get("CROSSOVER", 0.95),
            "NUM_GENERATIONS": self.config_manager.global_params.get("NUM_GENERATIONS", 40),
            "POP_SIZE": self.config_manager.global_params.get("POP_SIZE", 5),
        }

        for param_name, default_value in self.main_params.items():
            param_widget = self.create_param_widget(param_name, default_value)
            params_layout.addWidget(param_widget)
        
        layout.addWidget(params_group)

        # Resumo
        self.summary_label = QLabel("📊 Configurações: 1 | Execuções: 7")
        self.summary_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2E86AB; padding: 10px;")
        layout.addWidget(self.summary_label)

        # Botão
        self.save_button = QPushButton("💾 Salvar Configuração")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #2E86AB;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #A23B72;
            }
        """)
        self.save_button.clicked.connect(self.save_config)
        layout.addWidget(self.save_button, alignment=Qt.AlignmentFlag.AlignCenter)

    def create_param_widget(self, name, default_value):
        """Cria widget para um parâmetro com checkbox e campos de entrada"""
        group = QGroupBox(f"📊 {name}")
        group.setStyleSheet("QGroupBox { font-weight: bold; margin: 5px; }")
        layout = QVBoxLayout(group)

        # Checkbox para alternar modo
        checkbox = QCheckBox(f"🔒 Usar valor fixo para {name}")
        checkbox.setChecked(True)  # Padrão: fixo
        checkbox.setStyleSheet("QCheckBox { font-weight: bold; color: #2E86AB; margin: 5px; }")
        layout.addWidget(checkbox)

        # Container para campos de entrada
        fields_container = QWidget()
        fields_layout = QVBoxLayout(fields_container)

        # Campo para valor fixo
        fixed_container = QWidget()
        fixed_layout = QHBoxLayout(fixed_container)
        fixed_layout.addWidget(QLabel("Valor Fixo:"))
        
        is_int = isinstance(default_value, int)
        if is_int:
            fixed_input = QSpinBox()
            fixed_input.setRange(1, 10000)
            fixed_input.setValue(default_value)
        else:
            fixed_input = QDoubleSpinBox()
            fixed_input.setRange(0.0, 1.0)
            fixed_input.setSingleStep(0.01)
            fixed_input.setValue(default_value)
            fixed_input.setDecimals(3)
        
        fixed_input.setStyleSheet("padding: 5px; font-size: 12px; min-width: 100px;")
        fixed_layout.addWidget(fixed_input)
        fixed_layout.addStretch()
        fields_layout.addWidget(fixed_container)

        # Campos para valores variáveis (2x2)
        variable_container = QWidget()
        variable_layout = QGridLayout(variable_container)
        variable_layout.addWidget(QLabel("Valores Variáveis (máximo 4):"), 0, 0, 1, 4)
        
        variable_inputs = []
        for i in range(4):
            row = (i // 2) + 1
            col = (i % 2) * 2
            
            label = QLabel(f"V{i+1}:")
            label.setStyleSheet("font-weight: bold;")
            
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"Ex: {default_value}")
            input_field.setText(str(default_value))
            input_field.setStyleSheet("""
                QLineEdit {
                    padding: 5px;
                    border: 2px solid #ddd;
                    border-radius: 4px;
                    font-size: 12px;
                    min-width: 80px;
                }
                QLineEdit:focus {
                    border-color: #2E86AB;
                }
            """)
            input_field.textChanged.connect(self.update_summary)
            
            variable_layout.addWidget(label, row, col)
            variable_layout.addWidget(input_field, row, col + 1)
            variable_inputs.append(input_field)
        
        # Inicialmente escondido (modo fixo)
        variable_container.setVisible(False)
        fields_layout.addWidget(variable_container)
        
        layout.addWidget(fields_container)

        # Conecta checkbox para alternar visibilidade
        def toggle_mode(checked):
            fixed_container.setVisible(checked)
            variable_container.setVisible(not checked)
            
            if checked:
                checkbox.setText(f"🔒 Usar valor fixo para {name}")
                checkbox.setStyleSheet("QCheckBox { font-weight: bold; color: #2E86AB; margin: 5px; }")
            else:
                checkbox.setText(f"🔀 Usar valores variáveis para {name}")
                checkbox.setStyleSheet("QCheckBox { font-weight: bold; color: #A23B72; margin: 5px; }")
            
            self.update_summary()

        checkbox.toggled.connect(toggle_mode)
        fixed_input.valueChanged.connect(self.update_summary)

        # Armazena widgets
        self.param_widgets[name] = {
            "checkbox": checkbox,
            "fixed": fixed_input,
            "variable": variable_inputs,
            "is_int": is_int
        }

        return group

    def update_summary(self):
        """Atualiza o resumo de configurações"""
        total_configs = 1
        variable_count = 0
        
        for name, widgets in self.param_widgets.items():
            if not widgets["checkbox"].isChecked():  # Modo variável
                # Conta valores válidos
                valid_values = 0
                for inp in widgets["variable"]:
                    text = inp.text().strip()
                    if text:
                        try:
                            if widgets["is_int"]:
                                value = int(text)
                                if value > 0:
                                    valid_values += 1
                            else:
                                value = float(text)
                                if 0 <= value <= 1:
                                    valid_values += 1
                        except ValueError:
                            pass
                
                if valid_values > 0:
                    total_configs *= valid_values
                    variable_count += 1
        
        total_executions = total_configs * self.runs_spin.value()
        
        if variable_count > 0:
            self.summary_label.setText(
                f"📊 Configurações: {total_configs} | Execuções: {total_executions} | Variáveis: {variable_count}"
            )
        else:
            self.summary_label.setText(f"📊 Configurações: 1 (todos fixos) | Execuções: {total_executions}")

    def save_config(self):
        """Salva a configuração no options.json"""
        try:
            parametros_opcionais = []
            
            for name, widgets in self.param_widgets.items():
                if widgets["checkbox"].isChecked():  # Modo fixo
                    value = widgets["fixed"].value()
                    parametros_opcionais.append({name: [value]})
                else:  # Modo variável
                    values = []
                    for inp in widgets["variable"]:
                        text = inp.text().strip()
                        if text:
                            try:
                                if widgets["is_int"]:
                                    value = int(text)
                                    if value > 0:
                                        values.append(value)
                                else:
                                    value = float(text)
                                    if 0 <= value <= 1:
                                        values.append(value)
                            except ValueError:
                                continue
                    
                    if values:
                        parametros_opcionais.append({name: values})
                    else:
                        # Se não tem valores válidos, usa o fixo
                        parametros_opcionais.append({name: [widgets["fixed"].value()]})
            
            options_data = {
                "repeticoes_por_config": self.runs_spin.value(),
                "parametros_opcionais": parametros_opcionais
            }
            
            if self.config_manager.save_options_json(options_data):
                QMessageBox.information(self, "Sucesso", "Configuração salva com sucesso!")
            else:
                QMessageBox.critical(self, "Erro", "Falha ao salvar configuração.")
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro inesperado: {e}")

def main():
    app = QApplication(sys.argv)
    
    # Estilo global
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 5px;
            margin: 5px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
    """)
    
    window = LauncherWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
