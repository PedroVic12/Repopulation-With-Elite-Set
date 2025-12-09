from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QFontComboBox, QSpinBox, QPushButton, QMessageBox
)
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QFont

class SettingsWidget(QWidget):
    # Signal to notify the main window of changes, sending all settings at once
    settings_saved = Signal(dict)

    def __init__(self, side_menu=None):
        super().__init__()
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(20)
        
        self._create_theme_selector()
        self._create_font_selector()
        self._create_font_size_selector()
        
        self.main_layout.addStretch()
        
        self._create_save_button()

    def _create_theme_selector(self):
        theme_layout = QHBoxLayout()
        label = QLabel("Tema da Aplicação:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        theme_layout.addWidget(label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        self.main_layout.addLayout(theme_layout)

    def _create_font_selector(self):
        font_layout = QHBoxLayout()
        label = QLabel("Fonte da Aplicação:")
        self.font_combo = QFontComboBox()
        font_layout.addWidget(label)
        font_layout.addWidget(self.font_combo)
        font_layout.addStretch()
        self.main_layout.addLayout(font_layout)

    def _create_font_size_selector(self):
        font_size_layout = QHBoxLayout()
        label = QLabel("Tamanho da Fonte:")
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 30)
        font_size_layout.addWidget(label)
        font_size_layout.addWidget(self.font_size_spinbox)
        font_size_layout.addStretch()
        self.main_layout.addLayout(font_size_layout)

    def _create_save_button(self):
        self.save_button = QPushButton("Salvar Configurações")
        self.save_button.clicked.connect(self.save_settings)
        self.main_layout.addWidget(self.save_button)

    @Slot()
    def save_settings(self):
        """
        Reads current values from controls, packs them in a dict,
        and emits the settings_saved signal.
        """
        settings = {
            "theme": self.theme_combo.currentText().lower(),
            "font_family": self.font_combo.currentFont().family(),
            "font_size": self.font_size_spinbox.value()
        }
        self.settings_saved.emit(settings)
        QMessageBox.information(self, "Sucesso", "Configurações salvas e aplicadas!")

    def set_initial_values(self, theme, font_family, font_size):
        """
        Allows the main window to set the initial state of the controls
        to match the application's current settings.
        """
        # Block signals temporarily to prevent them from firing
        # when we set the initial values.
        self.theme_combo.blockSignals(True)
        self.font_combo.blockSignals(True)
        self.font_size_spinbox.blockSignals(True)

        self.theme_combo.setCurrentText(theme.title())
        self.font_combo.setCurrentFont(QFont(font_family))
        self.font_size_spinbox.setValue(font_size)

        # Re-enable signals
        self.theme_combo.blockSignals(False)
        self.font_combo.blockSignals(False)
        self.font_size_spinbox.blockSignals(False)
