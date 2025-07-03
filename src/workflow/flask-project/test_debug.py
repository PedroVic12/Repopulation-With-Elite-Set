# test_backend.py
import pytest
import requests
import os

# URL base da nossa API rodando localmente
BASE_URL = "http://127.0.0.1:5000"

# Garante que o banco de dados de teste esteja limpo antes de começar
# Em um projeto real, usaríamos um banco de dados de teste separado.
@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    # Antes dos testes, podemos limpar o banco
    db_file = 'estoque.db'
    if os.path.exists(db_file):
        # Para simplificar, vamos assumir que o backend recria o DB.
        # Numa app real, teríamos uma função de 'reset_db'.
        pass
    yield
    # Depois dos testes, podemos limpar novamente se necessário
    pass

def test_1_create_ferramenta():
    """Testa a criação de uma nova ferramenta."""
    payload = {"nome": "Chave de Fenda Teste", "preco": 19.99, "estoque": 150}
    response = requests.post(f"{BASE_URL}/ferramentas", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data['nome'] == payload['nome']
    assert 'id' in data
    # Guarda o ID para os próximos testes
    pytest.ferramenta_id = data['id']

def test_2_get_all_ferramentas():
    """Testa a listagem de todas as ferramentas."""
    response = requests.get(f"{BASE_URL}/ferramentas")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

def test_3_get_one_ferramenta():
    """Testa a busca de uma ferramenta específica."""
    assert hasattr(pytest, 'ferramenta_id'), "ID da ferramenta não foi criado no teste 1"
    response = requests.get(f"{BASE_URL}/ferramentas/{pytest.ferramenta_id}")
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == pytest.ferramenta_id
    assert data['nome'] == "Chave de Fenda Teste"

def test_4_update_ferramenta():
    """Testa a atualização de uma ferramenta."""
    assert hasattr(pytest, 'ferramenta_id'), "ID da ferramenta não foi criado no teste 1"
    payload = {"nome": "Chave de Fenda Teste Atualizada", "estoque": 200}
    response = requests.put(f"{BASE_URL}/ferramentas/{pytest.ferramenta_id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data['nome'] == "Chave de Fenda Teste Atualizada"
    assert data['estoque'] == 200
    assert data['preco'] == 19.99 # O preço não foi alterado

def test_5_delete_ferramenta():
    """Testa a exclusão de uma ferramenta."""
    assert hasattr(pytest, 'ferramenta_id'), "ID da ferramenta não foi criado no teste 1"
    response = requests.delete(f"{BASE_URL}/ferramentas/{pytest.ferramenta_id}")
    assert response.status_code == 200
    
    # Verifica se a ferramenta foi realmente deletada
    response_get = requests.get(f"{BASE_URL}/ferramentas/{pytest.ferramenta_id}")
    assert response_get.status_code == 404