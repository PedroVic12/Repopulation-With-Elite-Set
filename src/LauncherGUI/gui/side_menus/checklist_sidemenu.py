from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal

class ChecklistSideMenu(QWidget):
    # Signal to be emitted when a filter button is clicked
    filter_changed = Signal(str)

    def __init__(self):
        super().__init__()
        
        self.layout = QVBoxLayout(self)
        
        title = QLabel("Filtros do Checklist")
        title.setStyleSheet("font-weight: bold;")
        self.layout.addWidget(title)
        
        self.btn_all = QPushButton("Todas as Tarefas")
        self.btn_pending = QPushButton("Pendentes")
        self.btn_completed = QPushButton("Concluídas")
        
        self.layout.addWidget(self.btn_all)
        self.layout.addWidget(self.btn_pending)
        self.layout.addWidget(self.btn_completed)
        
        self.layout.addStretch()

        # Connect buttons to a handler that emits the signal
        self.btn_all.clicked.connect(lambda: self.filter_changed.emit("all"))
        self.btn_pending.clicked.connect(lambda: self.filter_changed.emit("pending"))
        self.btn_completed.clicked.connect(lambda: self.filter_changed.emit("completed"))
