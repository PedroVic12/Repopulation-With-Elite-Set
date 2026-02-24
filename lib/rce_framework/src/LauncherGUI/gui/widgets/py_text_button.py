# ///////////////////////////////////////////////////////////////
#
# BY: WANDERSON M.PIMENTA (Adapted by Pedro Veras)
# PROJECT MADE WITH: Qt Designer and PySide6
# V: 1.0.0
#
# This project can be used freely for all uses, as long as they maintain the
# respective credits only in the Python scripts, any information in the visual
# interface (GUI) can be modified without any implication.
#
# ///////////////////////////////////////////////////////////////

from qt_core import *

class PyTextButton(QPushButton):
    def __init__(
        self,
        text = "",
        height = 30,
        text_color = "#c3ccdf",
        hover_color = "#4f5368",
        pressed_color = "#282a36"
    ):
        super().__init__()

        # Set default parameters
        self.setText(text)
        self.setMaximumHeight(height)
        self.setMinimumHeight(height)
        self.setCursor(Qt.PointingHandCursor)

        # Custom parameters
        self._text_color = text_color
        self._hover_color = hover_color
        self._pressed_color = pressed_color

        # Set style
        self.set_style(
            text_color = self._text_color,
            hover_color = self._hover_color,
            pressed_color = self._pressed_color
        )

    def set_style(
        self,
        text_color,
        hover_color,
        pressed_color
    ):
        style = f"""
        QPushButton {{
            color: {text_color};
            background-color: transparent;
            border: none;
            padding: 5px;
            border-radius: 5px;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        QPushButton:pressed {{
            background-color: {pressed_color};
        }}
        """
        self.setStyleSheet(style)
