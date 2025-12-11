from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

class PomodoroWidget(QWidget):
    def __init__(self, side_menu=None):
        super().__init__()
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignCenter)

        # Timer setup
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update_timer)
        self._time_left = 0

        self._create_timer_display()
        self._create_buttons()
        
        self.set_time(25 * 60) # Default to Pomodoro time

    def _create_timer_display(self):
        self.timer_label = QLabel()
        self.timer_label.setFont(QFont("Arial", 80, QFont.Bold))
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.timer_label)

    def _create_buttons(self):
        buttons_layout = QHBoxLayout()
        
        self.pomodoro_button = QPushButton("Pomodoro (25 min)")
        self.pomodoro_button.clicked.connect(self.start_pomodoro)
        
        self.short_break_button = QPushButton("Pausa Curta (5 min)")
        self.short_break_button.clicked.connect(self.start_short_break)
        
        self.long_break_button = QPushButton("Pausa Longa (15 min)")
        self.long_break_button.clicked.connect(self.start_long_break)
        
        self.stop_button = QPushButton("Parar")
        self.stop_button.clicked.connect(self.stop_timer)

        buttons_layout.addWidget(self.pomodoro_button)
        buttons_layout.addWidget(self.short_break_button)
        buttons_layout.addWidget(self.long_break_button)
        buttons_layout.addWidget(self.stop_button)
        
        self.main_layout.addLayout(buttons_layout)

    def set_time(self, seconds):
        self._time_left = seconds
        self.update_display()

    def start_timer(self):
        if not self._timer.isActive() and self._time_left > 0:
            self._timer.start(1000)

    def stop_timer(self):
        self._timer.stop()

    def start_pomodoro(self):
        self.stop_timer()
        self.set_time(25 * 60)
        self.start_timer()

    def start_short_break(self):
        self.stop_timer()
        self.set_time(5 * 60)
        self.start_timer()

    def start_long_break(self):
        self.stop_timer()
        self.set_time(15 * 60)
        self.start_timer()

    def update_timer(self):
        if self._time_left > 0:
            self._time_left -= 1
            self.update_display()
        else:
            self._timer.stop()
            # Here you can add notification logic in the future
            # For now, it just stops at 00:00

    def update_display(self):
        minutes = self._time_left // 60
        seconds = self._time_left % 60
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

    def closeEvent(self, event):
        """Ensure the timer stops when the widget is closed."""
        self.stop_timer()
        super().closeEvent(event)
