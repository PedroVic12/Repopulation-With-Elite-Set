import os
import requests
import logging
import json
import pandas as pd

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, reqparse

from prefect import task, flow

# --- 1. CONFIGURAÇÃO INICIAL ---
logging.basicConfig(filename='output.txt', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
api = Api(app)

# Configura o banco de dados SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'estoque.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
logging.info("Backend iniciado e banco de dados configurado.")

# Função para registrar rotas usando flask_restful
def setup_routes(app, api):
    # Modelo
    class Ferramenta(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        nome = db.Column(db.String(100), unique=True, nullable=False)
        preco = db.Column(db.Float, nullable=False)
        estoque = db.Column(db.Integer, nullable=False)

        def to_dict(self):
            return {
                'id': self.id,
                'nome': self.nome,
                'preco': self.preco,
                'estoque': self.estoque
            }

    # Parser para requisições
    ferramenta_parser = reqparse.RequestParser()
    ferramenta_parser.add_argument('nome', type=str, required=True, help='Nome da ferramenta é obrigatório')
    ferramenta_parser.add_argument('preco', type=float, required=True, help='Preço é obrigatório')
    ferramenta_parser.add_argument('estoque', type=int, required=True, help='Estoque é obrigatório')

    # Resource para lista de ferramentas
    class FerramentaListResource(Resource):
        def get(self):
            ferramentas = Ferramenta.query.all()
            return [f.to_dict() for f in ferramentas], 200

        def post(self):
            args = ferramenta_parser.parse_args()
            if Ferramenta.query.filter_by(nome=args['nome']).first():
                return {'message': 'Ferramenta já existe!'}, 400
            nova_ferramenta = Ferramenta(nome=args['nome'], preco=args['preco'], estoque=args['estoque'])
            db.session.add(nova_ferramenta)
            db.session.commit()
            return nova_ferramenta.to_dict(), 201

    # Resource para ferramenta individual
    class FerramentaResource(Resource):
        def get(self, id):
            ferramenta = Ferramenta.query.get_or_404(id)
            return ferramenta.to_dict(), 200

        def put(self, id):
            ferramenta = Ferramenta.query.get_or_404(id)
            data = request.get_json()
            ferramenta.nome = data.get('nome', ferramenta.nome)
            ferramenta.preco = data.get('preco', ferramenta.preco)
            ferramenta.estoque = data.get('estoque', ferramenta.estoque)
            db.session.commit()
            return ferramenta.to_dict(), 200

        def delete(self, id):
            ferramenta = Ferramenta.query.get_or_404(id)
            db.session.delete(ferramenta)
            db.session.commit()
            return {'message': 'Ferramenta deletada com sucesso!'}, 200

    api.add_resource(FerramentaListResource, '/ferramentas')
    api.add_resource(FerramentaResource, '/ferramentas/<int:id>')

    # Expor o modelo para uso externo
    app.Ferramenta = Ferramenta

# Função de teste usando requests
def test_requests():
    url = "http://127.0.0.1:5000/ferramentas"
    # Teste POST
    r = requests.post(url, json={"nome": "Martelo", "preco": 10.5, "estoque": 20})
    print("POST:", r.status_code, r.json())
    # Teste GET
    r = requests.get(url)
    print("GET:", r.status_code, r.json())
    # Teste PUT
    if r.json():
        id_ = r.json()[0]['id']
        r2 = requests.put(f"{url}/{id_}", json={"estoque": 99})
        print("PUT:", r2.status_code, r2.json())
        # Teste DELETE
        r3 = requests.delete(f"{url}/{id_}")
        print("DELETE:", r3.status_code, r3.json())

# Chama a função para registrar as rotas
setup_routes(app, api)

# --- 2. MODELO (A camada 'M' do MVC) ---
# Define a estrutura da tabela de ferramentas no banco de dados
class Ferramenta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    preco = db.Column(db.Float, nullable=False)
    estoque = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        """Converte o objeto Ferramenta para um dicionário, útil para a resposta JSON."""
        return {
            'id': self.id,
            'nome': self.nome,
            'preco': self.preco,
            'estoque': self.estoque
        }

# --- 3. CONTROLADOR (A camada 'C' do MVC com as rotas da API) ---
# A 'View' aqui é a resposta JSON que cada rota retorna.

# Rota para CRIAR uma nova ferramenta (POST) e LER todas (GET)
@app.route('/ferramentas', methods=['POST', 'GET'])
def handle_ferramentas():
    if request.method == 'POST':
        # CREATE
        data = request.get_json()
        if not data or not 'nome' in data or not 'preco' in data or not 'estoque' in data:
            logging.warning("Tentativa de criação de ferramenta com dados inválidos.")
            return jsonify({'message': 'Dados incompletos!'}), 400
        
        nova_ferramenta = Ferramenta(nome=data['nome'], preco=data['preco'], estoque=data['estoque'])
        db.session.add(nova_ferramenta)
        db.session.commit()
        logging.info(f"Ferramenta criada: {nova_ferramenta.nome}")
        return jsonify(nova_ferramenta.to_dict()), 201
    
    elif request.method == 'GET':
        # READ ALL
        ferramentas = Ferramenta.query.all()
        logging.info("Listagem de todas as ferramentas solicitada.")
        return jsonify([f.to_dict() for f in ferramentas])

# Rota para LER, ATUALIZAR e DELETAR uma ferramenta específica pelo ID
@app.route('/ferramentas/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def handle_ferramenta(id):
    ferramenta = Ferramenta.query.get_or_404(id)

    if request.method == 'GET':
        # READ ONE
        logging.info(f"Detalhes da ferramenta {id} solicitados.")
        return jsonify(ferramenta.to_dict())

    elif request.method == 'PUT':
        # UPDATE
        data = request.get_json()
        ferramenta.nome = data.get('nome', ferramenta.nome)
        ferramenta.preco = data.get('preco', ferramenta.preco)
        ferramenta.estoque = data.get('estoque', ferramenta.estoque)
        db.session.commit()
        logging.info(f"Ferramenta {id} atualizada: {ferramenta.nome}")
        return jsonify(ferramenta.to_dict())

    elif request.method == 'DELETE':
        # DELETE
        db.session.delete(ferramenta)
        db.session.commit()
        logging.info(f"Ferramenta {id} deletada: {ferramenta.nome}")
        return jsonify({'message': 'Ferramenta deletada com sucesso!'})

# --- 4. PIPELINE DE DADOS COM PREFECT ---
# Este pipeline usa a API que acabamos de criar para popular o banco.

API_URL = "http://127.0.0.1:5000/ferramentas"

@task(log_prints=True)
def carregar_dados(ferramentas: list):
    """Task para enviar uma lista de ferramentas para a API via POST."""
    for ferramenta in ferramentas:
        try:
            # Verifica se a ferramenta já existe pelo nome
            response_get = requests.get(f"{API_URL}?nome={ferramenta['nome']}")
            if response_get.status_code == 200 and any(f['nome'] == ferramenta['nome'] for f in response_get.json()):
                 print(f"Ferramenta '{ferramenta['nome']}' já existe. Pulando.")
                 continue

            response = requests.post(API_URL, json=ferramenta)
            if response.status_code == 201:
                print(f"Sucesso: Ferramenta '{ferramenta['nome']}' adicionada.")
            else:
                print(f"Erro ao adicionar '{ferramenta['nome']}': {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Erro de conexão ao adicionar '{ferramenta['nome']}': {e}")

@task(log_prints=True)
def processar_csv(caminho_arquivo: str):
    print(f"Processando arquivo CSV: {caminho_arquivo}")
    df = pd.read_csv(caminho_arquivo)
    return df.to_dict(orient='records')

@task(log_prints=True)
def processar_json(caminho_arquivo: str):
    print(f"Processando arquivo JSON: {caminho_arquivo}")
    with open(caminho_arquivo, 'r') as f:
        data = json.load(f)
    return data

@task(log_prints=True)
def processar_xlsx(caminho_arquivo: str):
    print(f"Processando arquivo XLSX: {caminho_arquivo}")
    df = pd.read_excel(caminho_arquivo)
    return df.to_dict(orient='records')

@task(log_prints=True)
def processar_txt(caminho_arquivo: str):
    print(f"Processando arquivo TXT: {caminho_arquivo}")
    ferramentas = []
    with open(caminho_arquivo, 'r') as f:
        for linha in f:
            nome, preco, estoque = linha.strip().split(';')
            ferramentas.append({'nome': nome, 'preco': float(preco), 'estoque': int(estoque)})
    return ferramentas

@flow(name="Pipeline de Ingestão de Estoque", log_prints=True)
def pipeline_ingestao_estoque():
    """Flow principal que orquestra o processamento de todos os arquivos."""
    print("--- Iniciando Pipeline de Ingestão de Dados ---")
    base_path = "dados_entrada"
    
    dados_csv = processar_csv(os.path.join(base_path, "ferramentas.csv"))
    carregar_dados(dados_csv)

    dados_json = processar_json(os.path.join(base_path, "ferramentas.json"))
    carregar_dados(dados_json)

    dados_xlsx = processar_xlsx(os.path.join(base_path, "ferramentas.xlsx"))
    carregar_dados(dados_xlsx)
    
    dados_txt = processar_txt(os.path.join(base_path, "ferramentas.txt"))
    carregar_dados(dados_txt)
    
    print("--- Pipeline de Ingestão Concluído ---")

# --- 5. EXECUÇÃO ---
if __name__ == '__main__':
    # Para rodar o pipeline, use: python backend.py --run-flow
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--run-flow':
        # Antes de rodar o flow, garantimos que a API está de pé
        print("A API Flask precisa estar rodando em outro terminal para o pipeline funcionar.")
        print("Este comando apenas executa o pipeline de ingestão.")
        pipeline_ingestao_estoque()
    else:
        # Comando padrão: rodar a API Flask
        with app.app_context():
            db.create_all() # Cria a tabela no banco de dados se não existir
        app.run(debug=True, port=5000)