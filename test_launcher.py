#!/usr/bin/env python3
"""
Teste simples para identificar problema com parâmetros variáveis
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QCheckBox, QLineEdit, QLabel
from PySide6.QtCore import Qt

class TestWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Teste Parâmetros Variáveis")
        layout = QVBoxLayout(self)
        
        # Checkbox
        self.checkbox = QCheckBox("Habilitar parâmetros variáveis")
        layout.addWidget(self.checkbox)
        
        # Caixas de texto
        self.inputs = []
        for i in range(4):
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"Valor {i+1}")
            input_field.setEnabled(False)  # Inicialmente desabilitado
            layout.addWidget(QLabel(f"V{i+1}:"))
            layout.addWidget(input_field)
            self.inputs.append(input_field)
        
        # Conecta checkbox
        self.checkbox.toggled.connect(self.toggle_inputs)
        
        # Label de status
        self.status_label = QLabel("Status: Fixo")
        layout.addWidget(self.status_label)
    
    def toggle_inputs(self, checked):
        print(f"Toggle chamado: {checked}")
        for inp in self.inputs:
            inp.setEnabled(checked)
        
        if checked:
            self.status_label.setText("Status: Variável - Caixas habilitadas")
        else:
            self.status_label.setText("Status: Fixo - Caixas desabilitadas")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = TestWidget()
    widget.show()
    sys.exit(app.exec())
