#!/usr/bin/env bash
# run.sh - cria template de projeto Python (PySide6) com MVC, controllers e DB simples
# Uso: ./run.sh NomeDoProjeto
set -e

if [ -z "$1" ]; then
  echo "Uso: $0 NomeDoProjeto"
  exit 1
fi

PROJECT="$1"
SRC="$PROJECT/src"
CONTROLLERS="$SRC/controllers"
VIEWS="$SRC/views"
DOMAIN="$SRC/domain"
TEMPLATES="$SRC/templates"
DBDIR="$SRC/db"

echo "Criando estrutura do projeto: $PROJECT"

mkdir -p "$CONTROLLERS" "$VIEWS" "$DOMAIN" "$TEMPLATES" "$DBDIR"

# requirements
cat > "$PROJECT/requirements.txt" <<'TXT'
PySide6>=6.5
# SQLite stdlib usado => sem dependências extras
# adicione aqui outras libs que precisar (SQLAlchemy, redis, pandas, etc.)
TXT

# README
cat > "$PROJECT/README.md" <<'MD'
# Projeto Template PySide6 - MVC

Gerado automaticamente por run.sh

## Como usar

1. Crie e ative um virtualenv:
   python -m venv .venv
   source .venv/bin/activate

2. Instale dependências:
   pip install -r requirements.txt

3. Rode a app:
   python src/app.py

O projeto contém:
- controllers: UiStateController, DatabaseController, RepositoryController
- views: main_window (PySide6)
- domain: models
- templates: page()
MD

# src/app.py
cat > "$SRC/app.py" <<'PY'
#!/usr/bin/env python3
"""
app.py - ponto de entrada do aplicativo PySide6
"""
import sys
from PySide6.QtWidgets import QApplication
from views.main_window import MainWindow

def app():
    qapp = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(qapp.exec())

if __name__ == "__main__":
    app()
PY

# controllers/ui_state_controller.py
cat > "$CONTROLLERS/ui_state_controller.py" <<'PY'
"""UiStateController - gerencia estado da UI com sinais (PySide6 QObject)"""
from PySide6.QtCore import QObject, Signal, Slot

class UiStateController(QObject):
    # sinais que a view pode escutar
    name_changed = Signal(str)
    counter_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._name = ""
        self._counter = 0
        self._counter_max = 10

    # Nome
    def get_name(self):
        return self._name

    @Slot(str)
    def set_name(self, value: str):
        if value is None:
            value = ""
        self._name = value
        self.name_changed.emit(self._name)

    # Contador (0.._counter_max)
    def get_counter(self) -> int:
        return self._counter

    @Slot()
    def increment_counter(self):
        if self._counter < self._counter_max:
            self._counter += 1
        else:
            self._counter = 0  # reinicia após chegar ao max
        self.counter_changed.emit(self._counter)

    @Slot()
    def reset_counter(self):
        self._counter = 0
        self.counter_changed.emit(self._counter)
PY

# controllers/database_controller.py
cat > "$CONTROLLERS/database_controller.py" <<'PY'
"""DatabaseController minimal - usa sqlite3 embutido para persistência simples"""
import sqlite3
import pathlib
from typing import Optional, List, Dict, Any

class DatabaseController:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = str(pathlib.Path(__file__).resolve().parent.parent / "db" / "app.db")
        self.db_path = db_path
        self._ensure_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_db(self):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def insert_task(self, title: str, description: str = "") -> int:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("INSERT INTO tasks (title, description) VALUES (?, ?)", (title, description))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return new_id

    def list_tasks(self) -> List[Dict[str, Any]]:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT id, title, description FROM tasks ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()
        return [{"id": r[0], "title": r[1], "description": r[2]} for r in rows]

    def delete_task(self, task_id: int) -> bool:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        ok = cur.rowcount > 0
        conn.close()
        return ok
PY

# controllers/repository_controller.py
cat > "$CONTROLLERS/repository_controller.py" <<'PY'
"""RepositoryController - camada de abstração sobre DatabaseController"""
from .database_controller import DatabaseController
from typing import Dict, List, Any

class RepositoryController:
    def __init__(self, db_path: str = None):
        self.db = DatabaseController(db_path)

    def add_task(self, title: str, description: str = "") -> int:
        return self.db.insert_task(title, description)

    def get_tasks(self) -> List[Dict[str, Any]]:
        return self.db.list_tasks()

    def remove_task(self, task_id: int) -> bool:
        return self.db.delete_task(task_id)
PY

# domain/models.py
cat > "$DOMAIN/models.py" <<'PY'
"""Modelos de domínio (simples)"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class Task:
    id: Optional[int]
    title: str
    description: str = ""
PY

# templates/page.py
cat > "$TEMPLATES/page.py" <<'PY'
"""page() - template de view (stub)"""
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

def page():
    w = QWidget()
    layout = QVBoxLayout()
    layout.addWidget(QLabel("Página template"))
    w.setLayout(layout)
    return w
PY

# views/main_window.py
cat > "$VIEWS/main_window.py" <<'PY'
"""MainWindow - exemplo simples em PySide6 usando controllers"""
from PySide6.QtWidgets import QMainWindow, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QListWidget
from PySide6.QtCore import Qt, Slot
from controllers.ui_state_controller import UiStateController
from controllers.repository_controller import RepositoryController

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Template Batcaverna - PySide6")
        self.resize(680, 420)

        # controllers
        self.state = UiStateController()
        self.repo = RepositoryController()

        # UI
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()

        # --- Nome + botão mostrar ---
        row = QHBoxLayout()
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Digite seu nome aqui")
        self.btn_show = QPushButton("Mostrar nome")
        row.addWidget(self.input_name)
        row.addWidget(self.btn_show)
        main_layout.addLayout(row)

        # --- Contador ---
        row2 = QHBoxLayout()
        self.lbl_counter = QLabel("Contador: 0")
        self.btn_inc = QPushButton("Incrementar (0→10)")
        self.btn_reset = QPushButton("Reset")
        row2.addWidget(self.lbl_counter)
        row2.addWidget(self.btn_inc)
        row2.addWidget(self.btn_reset)
        main_layout.addLayout(row2)

        # --- Simple Task list usando RepositoryController ---
        main_layout.addWidget(QLabel("Tarefas (persistidas localmente)"))
        tasks_row = QHBoxLayout()
        self.task_title = QLineEdit()
        self.task_title.setPlaceholderText("Título da tarefa")
        self.task_add = QPushButton("Adicionar tarefa")
        tasks_row.addWidget(self.task_title)
        tasks_row.addWidget(self.task_add)
        main_layout.addLayout(tasks_row)

        self.tasks_list = QListWidget()
        main_layout.addWidget(self.tasks_list)

        central.setLayout(main_layout)

        # Conexões
        self.btn_show.clicked.connect(self.on_show_name)
        self.btn_inc.clicked.connect(self.state.increment_counter)
        self.btn_reset.clicked.connect(self.state.reset_counter)
        self.input_name.textChanged.connect(self.state.set_name)

        # state signals -> UI update
        self.state.name_changed.connect(self.on_name_changed)
        self.state.counter_changed.connect(self.on_counter_changed)

        # tasks
        self.task_add.clicked.connect(self.on_add_task)
        self.tasks_list.itemDoubleClicked.connect(self.on_task_double_click)

        # load tasks
        self.load_tasks()

    @Slot()
    def on_show_name(self):
        name = self.input_name.text().strip()
        if not name:
            QMessageBox.information(self, "Nome", "Digite um nome antes.")
            return
        QMessageBox.information(self, "Seu nome", f"Olá, {name}!")

    @Slot(str)
    def on_name_changed(self, new_name):
        # aqui a UI poderia reagir a mudanças do estado global
        print(f"[state] name changed -> {new_name}")

    @Slot(int)
    def on_counter_changed(self, value):
        self.lbl_counter.setText(f"Contador: {value}")

    @Slot()
    def on_add_task(self):
        title = self.task_title.text().strip()
        if not title:
            return
        new_id = self.repo.add_task(title, "")
        self.task_title.setText("")
        self.load_tasks()

    @Slot()
    def load_tasks(self):
        self.tasks_list.clear()
        tasks = self.repo.get_tasks()
        for t in tasks:
            self.tasks_list.addItem(f'{t["id"]} — {t["title"]}')

    @Slot()
    def on_task_double_click(self, item):
        # ao dar duplo click, pergunta se quer deletar
        txt = item.text()
        item_id = int(txt.split(" — ")[0])
        resp = QMessageBox.question(self, "Deletar?", f"Remover tarefa {item_id}?")
        if resp == QMessageBox.StandardButton.Yes:
            self.repo.remove_task(item_id)
            self.load_tasks()
PY

# db/schema.sql
cat > "$DBDIR/schema.sql" <<'SQL'
-- schema.sql - exemplo
CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT,
  description TEXT
);
SQL

# criar __init__ vazios para transformar em pacote
for f in "$CONTROLLERS" "$VIEWS" "$DOMAIN" "$TEMPLATES"; do
  touch "$f/__init__.py"
done

echo "Projeto $PROJECT criado com sucesso!"
echo "Próximos passos:"
echo "  cd $PROJECT"
echo "  python -m venv .venv"
echo "  source .venv/bin/activate"
echo "  pip install -r requirements.txt"
echo "  python src/app.py"
