import sqlite3
from PySide6.QtCore import QObject, Signal

class TodoModel(QObject):
    tasks_changed = Signal()

    def __init__(self, db_path='pomodoro_tasks.db'):
        super().__init__()
        self.db_path = db_path
        # Use check_same_thread=False for QTimer compatibility in the controller
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tarefas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                concluida INTEGER NOT NULL DEFAULT 0,
                ciclos_pomodoro INTEGER NOT NULL DEFAULT 0,
                data_criacao TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def get_tasks(self):
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tarefas ORDER BY data_criacao DESC")
        return [dict(row) for row in cursor.fetchall()]

    def add_task(self, description):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO tarefas (descricao) VALUES (?)", (description,))
        self.conn.commit()
        self.tasks_changed.emit()

    def update_task_status(self, task_id, completed):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE tarefas SET concluida = ? WHERE id = ?", (1 if completed else 0, task_id))
        self.conn.commit()
        self.tasks_changed.emit()

    def delete_task(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tarefas WHERE id = ?", (task_id,))
        self.conn.commit()
        self.tasks_changed.emit()
        
    def delete_completed_tasks(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tarefas WHERE concluida = 1")
        self.conn.commit()
        self.tasks_changed.emit()

    def increment_pomodoro_cycle(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE tarefas SET ciclos_pomodoro = ciclos_pomodoro + 1 WHERE id = ?", (task_id,))
        self.conn.commit()
        self.tasks_changed.emit()

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
