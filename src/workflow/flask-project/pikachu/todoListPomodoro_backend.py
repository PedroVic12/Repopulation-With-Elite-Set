# backend_restful.py
import os
from flask import Flask
from flask_restful import reqparse, Api, Resource
from flask_sqlalchemy import SQLAlchemy

# --- 1. CONFIGURAÇÃO INICIAL ---
app = Flask(__name__)
api = Api(app)

# Configura o banco de dados SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'tasks.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 2. MODELO (A camada 'M' do MVC) ---
# Define a estrutura da tabela de tarefas no banco de dados
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False, default='Geral')
    completed = db.Column(db.Boolean, default=False)

    def to_dict(self):
        """Converte o objeto Task para um dicionário para a resposta JSON."""
        return {
            'id': self.id,
            'description': self.description,
            'category': self.category,
            'completed': self.completed
        }

# Parser para validar e extrair os argumentos das requisições
parser = reqparse.RequestParser()
parser.add_argument('description', type=str, help='Descrição da tarefa não pode ser vazia', required=False)
parser.add_argument('category', type=str, default='Geral')
parser.add_argument('completed', type=bool)

# --- 3. CONTROLADOR (A camada 'C' do MVC com as classes Resource) ---
# A 'View' é a resposta JSON que cada método retorna.

# Recurso para uma única tarefa: GET (por ID), DELETE, PUT (Update)
class Todo(Resource):
    def get(self, task_id):
        task = Task.query.get_or_404(task_id, description=f"Tarefa com ID {task_id} não encontrada")
        return task.to_dict()

    def delete(self, task_id):
        task = Task.query.get_or_404(task_id)
        db.session.delete(task)
        db.session.commit()
        return '', 204 # Resposta 'No Content' para sucesso na exclusão

    def put(self, task_id):
        task = Task.query.get_or_404(task_id)
        args = parser.parse_args()
        
        # Atualiza apenas os campos que foram passados na requisição
        if args.get('description') is not None:
            task.description = args['description']
        if args.get('category') is not None:
            task.category = args['category']
        if args.get('completed') is not None:
            task.completed = args['completed']
            
        db.session.commit()
        return task.to_dict(), 200

# Recurso para a lista de tarefas: GET (todas), POST (Criar nova)
class TodoList(Resource):
    def get(self):
        tasks = Task.query.all()
        return [task.to_dict() for task in tasks]

    def post(self):
        args = parser.parse_args()
        if not args.get('description'):
             return {'message': 'O campo "description" é obrigatório'}, 400

        new_task = Task(
            description=args['description'],
            category=args['category']
        )
        db.session.add(new_task)
        db.session.commit()
        return new_task.to_dict(), 201 # Resposta 'Created'

##
## Roteamento dos recursos da API
##
api.add_resource(TodoList, '/tasks')
api.add_resource(Todo, '/tasks/<int:task_id>')

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Cria as tabelas no banco de dados se não existirem
    app.run(debug=True, port=5000)