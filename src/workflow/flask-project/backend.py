# backend.py
import os
import sys
import logging
import json
import pandas as pd
import requests
from datetime import datetime

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api

from prefect import task, flow

# --- 1. CONFIGURAÇÃO UNIFICADA ---
logging.basicConfig(filename='output.txt', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'estoque_iot.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
api = Api(app)
logging.info("Backend IOT Store iniciado e componentes configurados.")

# --- 2. MODELOS DE DADOS (A camada 'M' do MVC) ---

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    preco = db.Column(db.Float, nullable=False)
    movimentacoes = db.relationship('Movimentacao', backref='produto', lazy=True, cascade="all, delete-orphan")

class Movimentacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantidade = db.Column(db.Integer, nullable=False)
    tipo = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)

# --- 3. A CLASSE CONTROLADORA COM CRUD COMPLETO QUE VOCÊ PEDIU ---
class ControllerCrud:
    def _calcular_estoque(self, produto_id):
        estoque = db.session.query(db.func.sum(Movimentacao.quantidade)).filter_by(produto_id=produto_id).scalar()
        return estoque or 0

    # GET (para a lista de produtos)
    def get_all(self):
        produtos = Produto.query.all()
        resultado = []
        for p in produtos:
            resultado.append({
                'id': p.id, 'nome': p.nome, 'preco': p.preco,
                'estoque_atual': self._calcular_estoque(p.id)
            })
        logging.info("Listagem de todos os produtos solicitada.")
        return resultado, 200

    # GET (para um produto específico)
    def get_one(self, id):
        produto = Produto.query.get_or_404(id)
        historico = Movimentacao.query.filter_by(produto_id=id).order_by(Movimentacao.timestamp.desc()).all()
        return {
            'id': produto.id, 'nome': produto.nome, 'preco': produto.preco,
            'estoque_atual': self._calcular_estoque(id),
            'historico': [{'tipo': m.tipo, 'quantidade': m.quantidade, 'data': m.timestamp.isoformat()} for m in historico]
        }, 200

    # POST (para criar um novo produto)
    def post(self):
        data = request.get_json()
        if not data or 'nome' not in data or 'preco' not in data:
            return {'message': 'Os campos "nome" e "preco" são obrigatórios.'}, 400
        
        if Produto.query.filter_by(nome=data['nome']).first():
            return {'message': f"O produto '{data['nome']}' já existe."}, 409

        novo_produto = Produto(nome=data['nome'], preco=data['preco'])
        db.session.add(novo_produto)
        db.session.commit()
        logging.info(f"Produto criado: {novo_produto.nome}")
        return {'id': novo_produto.id, 'nome': novo_produto.nome, 'preco': novo_produto.preco}, 201
    
    # PUT (para atualizar um produto - não implementado para a lista, apenas para item único)
    def put(self, id):
        produto = Produto.query.get_or_404(id)
        data = request.get_json()
        
        produto.nome = data.get('nome', produto.nome)
        produto.preco = data.get('preco', produto.preco)
        
        db.session.commit()
        logging.info(f"Produto ID {id} atualizado para: {produto.nome}")
        return self.get_one(id)[0], 200 # Retorna o produto atualizado

    # DELETE (para deletar um produto)
    def delete(self, id):
        produto = Produto.query.get_or_404(id)
        nome_deletado = produto.nome
        db.session.delete(produto)
        db.session.commit()
        logging.info(f"Produto {id} ({nome_deletado}) e seu histórico foram deletados.")
        return {'message': 'Produto e todo seu histórico foram deletados com sucesso!'}, 200

    # Lógica de negócio específica para movimentações
    def registrar_movimentacao(self, produto_id):
        produto = Produto.query.get_or_404(produto_id)
        data = request.get_json()
        if not data or 'tipo' not in data or 'quantidade' not in data:
            return {'message': "Os campos 'tipo' e 'quantidade' são obrigatórios."}, 400

        tipo = data['tipo'].upper()
        quantidade = data['quantidade']

        if tipo not in ['ENTRADA', 'SAIDA']:
            return {'message': "Tipo inválido. Use 'ENTRADA' ou 'SAIDA'."}, 400
        
        if tipo == 'SAIDA':
            estoque_atual = self._calcular_estoque(produto_id)
            if estoque_atual < quantidade:
                return {'message': f"Estoque insuficiente. Disponível: {estoque_atual}"}, 400
            quantidade = -abs(quantidade)

        mov = Movimentacao(produto_id=produto.id, tipo=tipo, quantidade=abs(quantidade) if tipo == 'ENTRADA' else quantidade)
        db.session.add(mov)
        db.session.commit()
        logging.info(f"Movimentação para {produto.nome}: {tipo} de {abs(data['quantidade'])}.")
        return {'message': 'Movimentação registrada!', 'novo_estoque': self._calcular_estoque(produto_id)}, 201

# --- 4. API RESOURCES (Camada de Visão da API) ---
# Classes simples que delegam a lógica para o ControllerCrud.

controller = ControllerCrud()

class ProdutoListResource(Resource):
    def get(self):
        return controller.get_all()
    def post(self):
        return controller.post()

class ProdutoResource(Resource):
    def get(self, id):
        return controller.get_one(id)
    def put(self, id):
        return controller.put(id)
    def delete(self, id):
        return controller.delete(id)

class MovimentacaoResource(Resource):
    def post(self, id):
        return controller.registrar_movimentacao(id)

api.add_resource(ProdutoListResource, '/produtos')
api.add_resource(ProdutoResource, '/produtos/<int:id>')
api.add_resource(MovimentacaoResource, '/produtos/<int:id>/movimentacao')


# --- 5. PIPELINE DE DADOS COM PREFECT ---
API_URL = "http://127.0.0.1:5000"

@task(log_prints=True)
def carregar_produtos_iniciais(produtos: list):
    for prod in produtos:
        try:
            # 1. Cria o produto
            response_post = requests.post(f"{API_URL}/produtos", json={'nome': prod['nome'], 'preco': prod['preco']})
            if response_post.status_code not in [201, 409]:
                print(f"ERRO ao criar produto '{prod['nome']}': {response_post.text}")
                continue
            
            # Pega o ID do produto recém-criado ou já existente
            all_products_resp = requests.get(f"{API_URL}/produtos")
            all_products = all_products_resp.json()
            produto_id = next((p['id'] for p in all_products if p['nome'] == prod['nome']), None)

            if not produto_id:
                print(f"ERRO: Não foi possível encontrar o ID do produto '{prod['nome']}'.")
                continue

            # 2. Registra a entrada inicial de estoque
            response_mov = requests.post(f"{API_URL}/produtos/{produto_id}/movimentacao", 
                                         json={'tipo': 'ENTRADA', 'quantidade': prod['estoque_inicial']})
            if response_mov.status_code == 201:
                print(f"SUCESSO: Estoque inicial de {prod['estoque_inicial']} para '{prod['nome']}' registrado.")
            else:
                print(f"ERRO ao registrar estoque para '{prod['nome']}': {response_mov.text}")
        except requests.RequestException as e:
            print(f"ERRO de conexão: {e}")

@task(log_prints=True)
def processar_csv(caminho_arquivo: str):
    df = pd.read_csv(caminho_arquivo)
    df.rename(columns={'estoque': 'estoque_inicial'}, inplace=True)
    return df.to_dict(orient='records')

@flow(name="Pipeline de Carga Inicial de Estoque", log_prints=True)
def pipeline_carga_inicial():
    print("--- Iniciando Pipeline de Carga Inicial ---")
    dados_csv = processar_csv("output/ferramentas.csv")
    carregar_produtos_iniciais(dados_csv)
    print("--- Pipeline Concluído ---")

# --- 6. FUNÇÃO DE TESTE RÁPIDO COM HTTP REQUESTS ---
def testar_fluxo_completo():
    print("\n--- INICIANDO TESTE DE FLUXO COMPLETO ---")
    BASE_URL = "http://127.0.0.1:5000"
    
    with app.app_context():
        db.drop_all()
        db.create_all()

    # 1. POST: Criar um novo produto
    print("\n1. POST /produtos (Criando 'Resistor 10k Ohm')...")
    produto_payload = {'nome': 'Resistor 10k Ohm', 'preco': 0.50}
    response = requests.post(f"{BASE_URL}/produtos", json=produto_payload)
    assert response.status_code == 201
    produto_id = response.json()['id']
    print(f"   -> SUCESSO! Produto criado com ID: {produto_id}")

    # 2. POST: Registrar ENTRADA de estoque
    print(f"\n2. POST /produtos/{produto_id}/movimentacao (ENTRADA de 200 unidades)...")
    mov_payload = {'tipo': 'ENTRADA', 'quantidade': 200}
    response = requests.post(f"{BASE_URL}/produtos/{produto_id}/movimentacao", json=mov_payload)
    assert response.status_code == 201
    print(f"   -> SUCESSO! Novo estoque: {response.json()['novo_estoque']}")

    # 3. POST: Registrar SAIDA de estoque (venda)
    print(f"\n3. POST /produtos/{produto_id}/movimentacao (SAIDA de 25 unidades)...")
    mov_payload = {'tipo': 'SAIDA', 'quantidade': 25}
    response = requests.post(f"{BASE_URL}/produtos/{produto_id}/movimentacao", json=mov_payload)
    assert response.status_code == 201
    print(f"   -> SUCESSO! Novo estoque: {response.json()['novo_estoque']}")

    # 4. PUT: Atualizar o preço do produto
    print(f"\n4. PUT /produtos/{produto_id} (Atualizando preço para 0.75)...")
    update_payload = {'preco': 0.75}
    response = requests.put(f"{BASE_URL}/produtos/{produto_id}", json=update_payload)
    assert response.status_code == 200
    assert response.json()['preco'] == 0.75
    print(f"   -> SUCESSO! Preço atualizado.")

    # 5. GET: Verificar o estado final do produto
    print(f"\n5. GET /produtos/{produto_id} (Verificando estado final)...")
    response = requests.get(f"{BASE_URL}/produtos/{produto_id}")
    assert response.status_code == 200
    data = response.json()
    print(f"   -> Detalhes: {json.dumps(data, indent=2)}")
    assert data['estoque_atual'] == 175

    # 6. DELETE: Deletar o produto
    print(f"\n6. DELETE /produtos/{produto_id} (Deletando o produto)...")
    response = requests.delete(f"{BASE_URL}/produtos/{produto_id}")
    assert response.status_code == 200
    print("   -> SUCESSO! Produto deletado.")
    
    # 7. GET: Confirmar que o produto foi deletado
    print(f"\n7. GET /produtos/{produto_id} (Confirmando a deleção)...")
    response = requests.get(f"{BASE_URL}/produtos/{produto_id}")
    assert response.status_code == 404
    print("   -> SUCESSO! Produto não encontrado (404), como esperado.")
    
    print("\n--- TESTE DE FLUXO COMPLETO CONCLUÍDO COM SUCESSO! ---\n")

# --- 7. BLOCO DE EXECUÇÃO PRINCIPAL ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    if len(sys.argv) > 1:
        if sys.argv[1] == '--run-flow':
            print("Executando o pipeline de carga inicial do Prefect...")
            print("AVISO: A API Flask deve estar rodando para que o pipeline funcione.")
            pipeline_carga_inicial()
        elif sys.argv[1] == '--test-flow':
            print("AVISO: A API Flask deve estar rodando para que o teste funcione.")
            testar_fluxo_completo()
    else:
        print("Iniciando o servidor da API Flask em http://127.0.0.1:5000")
        app.run(host='0.0.0.0', port=5000, debug=True)