# database.py - Gerenciamento do SQLite
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any

class DatabaseManager:
    def __init__(self, db_path="app_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabela de tarefas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    completed BOOLEAN DEFAULT 0,
                    priority INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    due_date TIMESTAMP,
                    category TEXT DEFAULT 'General'
                )
            ''')
            
            # Tabela de estatísticas do dashboard
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dashboard_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE,
                    total_tasks INTEGER DEFAULT 0,
                    completed_tasks INTEGER DEFAULT 0,
                    pending_tasks INTEGER DEFAULT 0
                )
            ''')
            
            conn.commit()
    
    def add_todo(self, title: str, description: str = "", priority: int = 1, 
                 due_date: str = None, category: str = "General") -> int:
        """Adiciona uma nova tarefa"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO todos (title, description, priority, due_date, category)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, description, priority, due_date, category))
            conn.commit()
            return cursor.lastrowid
    
    def get_todos(self, completed: bool = None, category: str = None) -> List[Dict]:
        """Recupera tarefas do banco"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM todos"
            params = []
            
            if completed is not None:
                query += " WHERE completed = ?"
                params.append(completed)
            elif category:
                query += " WHERE category = ?"
                params.append(category)
            
            query += " ORDER BY priority DESC, created_at DESC"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def update_todo_status(self, todo_id: int, completed: bool):
        """Atualiza o status de uma tarefa"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE todos SET completed = ? WHERE id = ?
            ''', (completed, todo_id))
            conn.commit()
    
    def delete_todo(self, todo_id: int):
        """Remove uma tarefa"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
            conn.commit()
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Recupera estatísticas para o dashboard"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Estatísticas básicas
            cursor.execute('SELECT COUNT(*) FROM todos')
            total = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM todos WHERE completed = 1')
            completed = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM todos WHERE completed = 0')
            pending = cursor.fetchone()[0]
            
            # Tarefas por categoria
            cursor.execute('''
                SELECT category, COUNT(*) as count 
                FROM todos 
                WHERE completed = 0 
                GROUP BY category
            ''')
            categories = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Tarefas por prioridade
            cursor.execute('''
                SELECT priority, COUNT(*) as count 
                FROM todos 
                WHERE completed = 0 
                GROUP BY priority
            ''')
            priorities = {row[0]: row[1] for row in cursor.fetchall()}
            
            return {
                'total': total,
                'completed': completed,
                'pending': pending,
                'completion_rate': (completed / total * 100) if total > 0 else 0,
                'categories': categories,
                'priorities': priorities
            }