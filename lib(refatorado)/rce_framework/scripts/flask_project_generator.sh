#!/bin/bash

# Flask Project Generator - Cria estrutura completa MVC com CLI
# Autor: Sistema de Geração Automática
# Data: $(date +%Y-%m-%d)

PROJECT_NAME=${1:-"flask_api_project"}
echo "🚀 Criando projeto Flask: $PROJECT_NAME"

# Criar estrutura de diretórios
mkdir -p "$PROJECT_NAME"/{app/{controllers,models,services,templates,static/{css,js}},tests,docs}

cd "$PROJECT_NAME"

echo "📁 Estrutura de pastas criada..."

# ============================================================================
# ARQUIVO: requirements.txt
# ============================================================================
cat > requirements.txt << 'EOF'
Flask==3.0.0
Flask-CORS==4.0.0
Flask-SQLAlchemy==3.0.5
requests==2.31.0
python-dotenv==1.0.0
click==8.1.7
Jinja2==3.1.2
Werkzeug==3.0.1
gunicorn==21.2.0
EOF

# ============================================================================
# ARQUIVO: main.py (Ponto de entrada principal)
# ============================================================================
cat > main.py << 'EOF'
#!/usr/bin/env python3
"""
Flask API Project - Main Entry Point
Padrão Facade para orquestração da aplicação
"""
import os
from app.app import create_app
from app.models.base import db

def main():
    """Ponto de entrada principal da aplicação"""
    app = create_app()
    
    # Configuração de desenvolvimento
    if os.getenv('FLASK_ENV') == 'development':
        app.config['DEBUG'] = True
        
    # Criar tabelas do banco se não existirem
    with app.app_context():
        db.create_all()
        print("✅ Banco de dados inicializado")
    
    print("🚀 Servidor Flask iniciado em http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()
EOF

# ============================================================================
# ARQUIVO: app/app.py (Aplicação Flask Principal)
# ============================================================================
cat > app/app.py << 'EOF'
"""
Aplicação Flask Principal - Arquitetura MVC
"""
from flask import Flask, render_template
from flask_cors import CORS
from app.models.base import db
from app.controllers.task_controller import task_bp
from app.controllers.api_controller import api_bp

def create_app():
    """Factory da aplicação Flask"""
    app = Flask(__name__)
    
    # Configurações
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializar extensões
    db.init_app(app)
    CORS(app)
    
    # Registrar Blueprints (Controllers)
    app.register_blueprint(task_bp, url_prefix='/tasks')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Rota principal - renderiza o frontend
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # Handler de erro 404
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
        
    return app
EOF

# ============================================================================
# ARQUIVO: app/models/base.py (Base do SQLAlchemy)
# ============================================================================
cat > app/models/base.py << 'EOF'
"""
Base models para SQLAlchemy
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class BaseModel(db.Model):
    """Modelo base com campos comuns"""
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Converte modelo para dicionário"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
EOF

# ============================================================================
# ARQUIVO: app/models/task.py (Model Task)
# ============================================================================
cat > app/models/task.py << 'EOF'
"""
Model Task - Representação de tarefas
"""
from app.models.base import db, BaseModel

class Task(BaseModel):
    """Modelo de Tarefa"""
    __tablename__ = 'tasks'
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    
    def __repr__(self):
        return f'<Task {self.title}>'
    
    def to_dict(self):
        """Override para incluir campos específicos"""
        data = super().to_dict()
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['updated_at'] = self.updated_at.isoformat() if self.updated_at else None
        return data
EOF

# ============================================================================
# ARQUIVO: app/services/task_service.py (Lógica de Negócio)
# ============================================================================
cat > app/services/task_service.py << 'EOF'
"""
Task Service - Lógica de negócio para tarefas
"""
from app.models.base import db
from app.models.task import Task
from typing import List, Optional

class TaskService:
    """Serviço para operações de tarefas"""
    
    @staticmethod
    def get_all_tasks() -> List[Task]:
        """Retorna todas as tarefas"""
        return Task.query.order_by(Task.created_at.desc()).all()
    
    @staticmethod
    def get_task_by_id(task_id: int) -> Optional[Task]:
        """Retorna tarefa por ID"""
        return Task.query.get(task_id)
    
    @staticmethod
    def create_task(data: dict) -> Task:
        """Cria nova tarefa"""
        task = Task(
            title=data.get('title'),
            description=data.get('description', ''),
            priority=data.get('priority', 'medium')
        )
        db.session.add(task)
        db.session.commit()
        return task
    
    @staticmethod
    def update_task(task_id: int, data: dict) -> Optional[Task]:
        """Atualiza tarefa existente"""
        task = Task.query.get(task_id)
        if not task:
            return None
            
        task.title = data.get('title', task.title)
        task.description = data.get('description', task.description)
        task.completed = data.get('completed', task.completed)
        task.priority = data.get('priority', task.priority)
        
        db.session.commit()
        return task
    
    @staticmethod
    def delete_task(task_id: int) -> bool:
        """Remove tarefa"""
        task = Task.query.get(task_id)
        if not task:
            return False
            
        db.session.delete(task)
        db.session.commit()
        return True
    
    @staticmethod
    def get_tasks_by_status(completed: bool) -> List[Task]:
        """Retorna tarefas por status"""
        return Task.query.filter_by(completed=completed).all()
EOF

# ============================================================================
# ARQUIVO: app/controllers/task_controller.py (Controller REST)
# ============================================================================
cat > app/controllers/task_controller.py << 'EOF'
"""
Task Controller - Endpoints REST para tarefas
"""
from flask import Blueprint, request, jsonify
from app.services.task_service import TaskService

task_bp = Blueprint('tasks', __name__)

@task_bp.route('', methods=['GET'])
def get_tasks():
    """GET /tasks - Lista todas as tarefas"""
    try:
        tasks = TaskService.get_all_tasks()
        return jsonify({
            'success': True,
            'data': [task.to_dict() for task in tasks],
            'count': len(tasks)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@task_bp.route('', methods=['POST'])
def create_task():
    """POST /tasks - Cria nova tarefa"""
    try:
        data = request.get_json()
        
        if not data or not data.get('title'):
            return jsonify({'success': False, 'error': 'Título é obrigatório'}), 400
        
        task = TaskService.create_task(data)
        return jsonify({
            'success': True,
            'data': task.to_dict(),
            'message': 'Tarefa criada com sucesso'
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@task_bp.route('/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """GET /tasks/<id> - Busca tarefa por ID"""
    try:
        task = TaskService.get_task_by_id(task_id)
        if not task:
            return jsonify({'success': False, 'error': 'Tarefa não encontrada'}), 404
            
        return jsonify({
            'success': True,
            'data': task.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@task_bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """PUT /tasks/<id> - Atualiza tarefa"""
    try:
        data = request.get_json()
        task = TaskService.update_task(task_id, data)
        
        if not task:
            return jsonify({'success': False, 'error': 'Tarefa não encontrada'}), 404
            
        return jsonify({
            'success': True,
            'data': task.to_dict(),
            'message': 'Tarefa atualizada com sucesso'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@task_bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """DELETE /tasks/<id> - Remove tarefa"""
    try:
        success = TaskService.delete_task(task_id)
        
        if not success:
            return jsonify({'success': False, 'error': 'Tarefa não encontrada'}), 404
            
        return jsonify({
            'success': True,
            'message': 'Tarefa removida com sucesso'
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
EOF

# ============================================================================
# ARQUIVO: app/controllers/api_controller.py (Controller API Geral)
# ============================================================================
cat > app/controllers/api_controller.py << 'EOF'
"""
API Controller - Endpoints gerais da API
"""
from flask import Blueprint, jsonify
from app.services.task_service import TaskService

api_bp = Blueprint('api', __name__)

@api_bp.route('/status', methods=['GET'])
def api_status():
    """GET /api/status - Status da API"""
    return jsonify({
        'status': 'online',
        'version': '1.0.0',
        'message': 'Flask API funcionando corretamente'
    })

@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """GET /api/stats - Estatísticas da aplicação"""
    try:
        all_tasks = TaskService.get_all_tasks()
        completed_tasks = TaskService.get_tasks_by_status(True)
        pending_tasks = TaskService.get_tasks_by_status(False)
        
        return jsonify({
            'success': True,
            'data': {
                'total_tasks': len(all_tasks),
                'completed_tasks': len(completed_tasks),
                'pending_tasks': len(pending_tasks),
                'completion_rate': len(completed_tasks) / len(all_tasks) * 100 if all_tasks else 0
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
EOF

# ============================================================================
# ARQUIVO: app/templates/index.html (Frontend Bootstrap)
# ============================================================================
cat > app/templates/index.html << 'EOF'
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flask API - Gerenciador de Tarefas</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        .task-card { transition: all 0.3s ease; }
        .task-card:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .completed { opacity: 0.7; text-decoration: line-through; }
        .priority-high { border-left: 4px solid #dc3545; }
        .priority-medium { border-left: 4px solid #ffc107; }
        .priority-low { border-left: 4px solid #28a745; }
    </style>
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-4">
        <div class="container">
            <a class="navbar-brand" href="#"><i class="bi bi-check-circle me-2"></i>TaskManager API</a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text me-3">Status: <span id="apiStatus" class="badge bg-success">Online</span></span>
            </div>
        </div>
    </nav>

    <div class="container">
        <!-- Stats Cards -->
        <div class="row mb-4" id="statsCards">
            <!-- Stats serão inseridos aqui via JavaScript -->
        </div>

        <!-- Add Task Form -->
        <div class="card mb-4">
            <div class="card-header">
                <h5><i class="bi bi-plus-circle me-2"></i>Adicionar Nova Tarefa</h5>
            </div>
            <div class="card-body">
                <form id="taskForm">
                    <div class="row">
                        <div class="col-md-6">
                            <input type="text" class="form-control" id="taskTitle" placeholder="Título da tarefa" required>
                        </div>
                        <div class="col-md-3">
                            <select class="form-select" id="taskPriority">
                                <option value="low">Baixa Prioridade</option>
                                <option value="medium" selected>Média Prioridade</option>
                                <option value="high">Alta Prioridade</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <button type="submit" class="btn btn-primary w-100">
                                <i class="bi bi-plus"></i> Adicionar
                            </button>
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-12">
                            <textarea class="form-control" id="taskDescription" placeholder="Descrição (opcional)" rows="2"></textarea>
                        </div>
                    </div>
                </form>
            </div>
        </div>

        <!-- Tasks List -->
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5><i class="bi bi-list-task me-2"></i>Lista de Tarefas</h5>
                <button class="btn btn-sm btn-outline-primary" onclick="loadTasks()">
                    <i class="bi bi-arrow-clockwise"></i> Atualizar
                </button>
            </div>
            <div class="card-body" id="tasksContainer">
                <div class="text-center">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Carregando...</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Toast Container -->
    <div class="toast-container position-fixed bottom-0 end-0 p-3" id="toastContainer"></div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        // API Base URL
        const API_BASE = '';
        
        // Estado da aplicação
        let tasks = [];
        let stats = {};

        // Inicializar aplicação
        document.addEventListener('DOMContentLoaded', function() {
            checkApiStatus();
            loadStats();
            loadTasks();
            
            // Event listener para o formulário
            document.getElementById('taskForm').addEventListener('submit', handleAddTask);
        });

        // Verificar status da API
        async function checkApiStatus() {
            try {
                const response = await fetch(`${API_BASE}/api/status`);
                const data = await response.json();
                document.getElementById('apiStatus').textContent = data.status === 'online' ? 'Online' : 'Offline';
                document.getElementById('apiStatus').className = `badge bg-${data.status === 'online' ? 'success' : 'danger'}`;
            } catch (error) {
                document.getElementById('apiStatus').textContent = 'Offline';
                document.getElementById('apiStatus').className = 'badge bg-danger';
            }
        }

        // Carregar estatísticas
        async function loadStats() {
            try {
                const response = await fetch(`${API_BASE}/api/stats`);
                const result = await response.json();
                
                if (result.success) {
                    stats = result.data;
                    renderStats();
                }
            } catch (error) {
                console.error('Erro ao carregar estatísticas:', error);
            }
        }

        // Renderizar estatísticas
        function renderStats() {
            const container = document.getElementById('statsCards');
            container.innerHTML = `
                <div class="col-md-3">
                    <div class="card text-center border-primary">
                        <div class="card-body">
                            <h4 class="card-title text-primary">${stats.total_tasks || 0}</h4>
                            <p class="card-text">Total de Tarefas</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center border-success">
                        <div class="card-body">
                            <h4 class="card-title text-success">${stats.completed_tasks || 0}</h4>
                            <p class="card-text">Completadas</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center border-warning">
                        <div class="card-body">
                            <h4 class="card-title text-warning">${stats.pending_tasks || 0}</h4>
                            <p class="card-text">Pendentes</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center border-info">
                        <div class="card-body">
                            <h4 class="card-title text-info">${Math.round(stats.completion_rate || 0)}%</h4>
                            <p class="card-text">Taxa de Conclusão</p>
                        </div>
                    </div>
                </div>
            `;
        }

        // Carregar tarefas
        async function loadTasks() {
            try {
                const response = await fetch(`${API_BASE}/tasks`);
                const result = await response.json();
                
                if (result.success) {
                    tasks = result.data;
                    renderTasks();
                    loadStats(); // Atualizar stats
                } else {
                    showToast('Erro ao carregar tarefas', 'error');
                }
            } catch (error) {
                console.error('Erro ao carregar tarefas:', error);
                showToast('Erro de conexão', 'error');
            }
        }

        // Renderizar tarefas
        function renderTasks() {
            const container = document.getElementById('tasksContainer');
            
            if (tasks.length === 0) {
                container.innerHTML = `
                    <div class="text-center text-muted">
                        <i class="bi bi-inbox display-1"></i>
                        <p class="mt-2">Nenhuma tarefa encontrada</p>
                    </div>
                `;
                return;
            }

            const tasksHTML = tasks.map(task => `
                <div class="card task-card mb-3 priority-${task.priority}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <h6 class="card-title ${task.completed ? 'completed' : ''}">${task.title}</h6>
                                <p class="card-text text-muted small">${task.description || 'Sem descrição'}</p>
                                <small class="text-muted">
                                    Criado em: ${new Date(task.created_at).toLocaleDateString('pt-BR')}
                                    | Prioridade: <span class="badge bg-${getPriorityColor(task.priority)}">${getPriorityText(task.priority)}</span>
                                </small>
                            </div>
                            <div class="btn-group" role="group">
                                <button class="btn btn-sm btn-${task.completed ? 'warning' : 'success'}" 
                                        onclick="toggleTask(${task.id}, ${!task.completed})">
                                    <i class="bi bi-${task.completed ? 'arrow-clockwise' : 'check'}"></i>
                                </button>
                                <button class="btn btn-sm btn-danger" onclick="deleteTask(${task.id})">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
            
            container.innerHTML = tasksHTML;
        }

        // Manipular adição de tarefa
        async function handleAddTask(event) {
            event.preventDefault();
            
            const title = document.getElementById('taskTitle').value;
            const description = document.getElementById('taskDescription').value;
            const priority = document.getElementById('taskPriority').value;
            
            try {
                const response = await fetch(`${API_BASE}/tasks`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, description, priority })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showToast('Tarefa adicionada com sucesso!', 'success');
                    document.getElementById('taskForm').reset();
                    loadTasks();
                } else {
                    showToast(result.error || 'Erro ao adicionar tarefa', 'error');
                }
            } catch (error) {
                console.error('Erro:', error);
                showToast('Erro de conexão', 'error');
            }
        }

        // Alternar status da tarefa
        async function toggleTask(taskId, completed) {
            try {
                const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ completed })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showToast(`Tarefa ${completed ? 'concluída' : 'reaberta'}!`, 'success');
                    loadTasks();
                } else {
                    showToast(result.error || 'Erro ao atualizar tarefa', 'error');
                }
            } catch (error) {
                console.error('Erro:', error);
                showToast('Erro de conexão', 'error');
            }
        }

        // Deletar tarefa
        async function deleteTask(taskId) {
            if (!confirm('Tem certeza que deseja excluir esta tarefa?')) return;
            
            try {
                const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showToast('Tarefa excluída com sucesso!', 'success');
                    loadTasks();
                } else {
                    showToast(result.error || 'Erro ao excluir tarefa', 'error');
                }
            } catch (error) {
                console.error('Erro:', error);
                showToast('Erro de conexão', 'error');
            }
        }

        // Utilitários
        function getPriorityColor(priority) {
            const colors = { low: 'success', medium: 'warning', high: 'danger' };
            return colors[priority] || 'secondary';
        }

        function getPriorityText(priority) {
            const texts = { low: 'Baixa', medium: 'Média', high: 'Alta' };
            return texts[priority] || priority;
        }

        // Sistema de Toast
        function showToast(message, type = 'info') {
            const toastId = 'toast-' + Date.now();
            const bgClass = type === 'success' ? 'bg-success' : type === 'error' ? 'bg-danger' : 'bg-info';
            
            const toastHTML = `
                <div class="toast ${bgClass} text-white" role="alert" id="${toastId}">
                    <div class="d-flex">
                        <div class="toast-body">${message}</div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                    </div>
                </div>
            `;
            
            document.getElementById('toastContainer').insertAdjacentHTML('beforeend', toastHTML);
            const toast = new bootstrap.Toast(document.getElementById(toastId));
            toast.show();
            
            // Remove o toast após 5 segundos
            setTimeout(() => {
                const toastEl = document.getElementById(toastId);
                if (toastEl) toastEl.remove();
            }, 5000);
        }
    </script>
</body>
</html>
EOF

# ============================================================================
# ARQUIVO: app/templates/404.html (Página de Erro 404)
# ============================================================================
cat > app/templates/404.html << 'EOF'
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>404 - Página Não Encontrada</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container">
        <div class="row justify-content-center align-items-center min-vh-100">
            <div class="col-md-6 text-center">
                <h1 class="display-1">404</h1>
                <h2>Página Não Encontrada</h2>
                <p class="lead">A página que você está procurando não existe.</p>
                <a href="/" class="btn btn-primary">Voltar ao Início</a>
            </div>
        </div>
    </div>
</body>
</html>
EOF

# ============================================================================
# ARQUIVO: cli.py (CLI para geração de código)
# ============================================================================
cat > cli.py << 'EOF'
#!/usr/bin/env python3
"""
CLI Generator - Ferramenta para gerar controllers e models automaticamente
Uso: python cli.py generate controller User
     python cli.py generate model Product
"""
import click
import os
from datetime import datetime

@click.group()
def cli():
    """Flask Project CLI Generator"""
    pass

@cli.group()
def generate():
    """Comandos para gerar código"""
    pass

@generate.command()
@click.argument('name')
def controller(name):
    """Gera um novo controller"""
    controller_name = name.lower()
    class_name = name.capitalize()
    
    controller_content = f'''"""
{class_name} Controller - Endpoints REST para {controller_name}
Gerado automaticamente em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
from flask import Blueprint, request, jsonify
from app.services.{controller_name}_service import {class_name}Service

{controller_name}_bp = Blueprint('{controller_name}s', __name__)

@{controller_name}_bp.route('', methods=['GET'])
def get_{controller_name}s():
    """GET /{controller_name}s - Lista todos os {controller_name}s"""
    try:
        {controller_name}s = {class_name}Service.get_all_{controller_name}s()
        return jsonify({{
            'success': True,
            'data': [{controller_name}.to_dict() for {controller_name} in {controller_name}s],
            'count': len({controller_name}s)
        }})
    except Exception as e:
        return jsonify({{'success': False, 