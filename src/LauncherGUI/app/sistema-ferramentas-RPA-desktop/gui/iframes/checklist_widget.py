from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QListWidget, QLineEdit, QListWidgetItem
)
from PySide6.QtCore import Qt, Slot

# We need to adjust the import path to find the model
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


from app.models.todo_model import TodoModel



class ChecklistWidget(QWidget):
    def __init__(self, side_menu=None):
        super().__init__()
        
        self.model = TodoModel()
        self.side_menu = side_menu
        self.current_filter = "all" # Default filter

        self.main_layout = QVBoxLayout(self)
        
        self._create_input_widgets()
        self._create_list_widget()
        self._create_action_buttons()
        
        # Connect signals
        self.model.tasks_changed.connect(self.render_tasks)
        if self.side_menu:
            self.side_menu.filter_changed.connect(self.apply_filter)
        
        # Initial render
        self.render_tasks()

    def _create_input_widgets(self):
        input_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Adicionar nova tarefa e pressionar Enter...")
        self.task_input.returnPressed.connect(self.add_task)
        
        self.add_button = QPushButton("Adicionar")
        self.add_button.clicked.connect(self.add_task)
        
        input_layout.addWidget(self.task_input)
        input_layout.addWidget(self.add_button)
        self.main_layout.addLayout(input_layout)

    def _create_list_widget(self):
        self.task_list = QListWidget()
        self.task_list.itemChanged.connect(self.toggle_task_status)
        self.main_layout.addWidget(self.task_list)

    def _create_action_buttons(self):
        self.delete_button = QPushButton("Remover Tarefas Concluídas")
        self.delete_button.clicked.connect(self.delete_completed)
        self.main_layout.addWidget(self.delete_button)

    @Slot()
    def add_task(self):
        description = self.task_input.text().strip()
        if description:
            self.model.add_task(description)
            self.task_input.clear()

    @Slot(QListWidgetItem)
    def toggle_task_status(self, item):
        task_id = item.data(Qt.UserRole)
        is_completed = item.checkState() == Qt.Checked
        self.model.update_task_status(task_id, is_completed)

    @Slot()
    def delete_completed(self):
        self.model.delete_completed_tasks()

    @Slot(str)
    def apply_filter(self, filter_str):
        self.current_filter = filter_str
        self.render_tasks()

    @Slot()
    def render_tasks(self):
        all_tasks = self.model.get_tasks()
        
        # Filter tasks based on the current filter
        if self.current_filter == "pending":
            tasks_to_show = [task for task in all_tasks if not task['concluida']]
        elif self.current_filter == "completed":
            tasks_to_show = [task for task in all_tasks if task['concluida']]
        else: # "all"
            tasks_to_show = all_tasks

        self.task_list.blockSignals(True)
        self.task_list.clear()
        
        for task in tasks_to_show:
            item = QListWidgetItem(task['descricao'])
            item.setData(Qt.UserRole, task['id'])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            
            if task['concluida']:
                item.setCheckState(Qt.Checked)
                font = item.font()
                font.setStrikeOut(True)
                item.setFont(font)
                item.setForeground(Qt.gray)
            else:
                item.setCheckState(Qt.Unchecked)
            
            self.task_list.addItem(item)
            
        self.task_list.blockSignals(False)

    def closeEvent(self, event):
        self.model.close()
        super().closeEvent(event)
