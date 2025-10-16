from pathlib import Path
import sys
import pytest
from unittest.mock import MagicMock, patch


#! pip install pytest pytest-qt pytest-mock


# Adicione o diretório do seu projeto ao path para que o pytest possa encontrar os módulos
sys.path.insert(0, str(Path(__file__).parent))

# Importe as classes que você quer testar
from launcher import ScriptWorker, ConfigTab, ConfigManager

# Mock para o DatabaseController, para que os testes não dependam de arquivos reais
@pytest.fixture
def mock_db_controller():
    """Cria um mock do DatabaseController."""
    mock = MagicMock()
    mock.get_params.return_value = {
        "MUTACAO": 0.1, "CROSSOVER": 0.8, "NUM_GENERATIONS": 100, "POP_SIZE": 50
    }
    mock.get_options.return_value = {"repeticoes_por_config": 1}
    return mock

@pytest.fixture
def config_manager(mock_db_controller):
    """Cria uma instância do ConfigManager com o DB mockado."""
    # Usamos 'patch' para substituir a classe real pela mockada durante o teste
    with patch('main.DatabaseController', return_value=mock_db_controller):
        return ConfigManager()

def test_config_manager_clean_options(config_manager):
    """Testa se a função clean_options remove chaves indesejadas e duplicatas."""
    # Simula um options.json "sujo"
    config_manager.options = {
        "repeticoes_por_config": 5,
        "MUTACAO": [0.1, 0.2, 0.1],  # Tem duplicata
        "POP_SIZE": [50, 100],
        "CHAVE_INVALIDA": "valor"     # Chave não permitida
    }
    config_manager.clean_options()

    # Verifica o resultado
    assert "CHAVE_INVALIDA" not in config_manager.options
    assert config_manager.options["MUTACAO"] == [0.1, 0.2] # Duplicata removida
    assert config_manager.options["POP_SIZE"] == [50, 100]


# Os testes a seguir usam 'qtbot' do pytest-qt para interagir com widgets e sinais
def test_config_tab_generate_configurations(qtbot, config_manager):
    """Testa a lógica de geração de configurações na ConfigTab."""
    # Cria uma instância da aba de configuração
    tab = ConfigTab(config_manager)
    qtbot.addWidget(tab) # Adiciona ao bot para gerenciamento

    # Simula a entrada do usuário:
    # 1. Mudar MUTACAO para modo variável e preencher valores
    tab.param_widgets["MUTACAO"]["mode"].buttons()[1].setChecked(True) # Clica em "Variável"
    tab.param_widgets["MUTACAO"]["variable"][0].setText("0.5")
    tab.param_widgets["MUTACAO"]["variable"][1].setText("0.6")

    # 2. Mudar POP_SIZE para modo variável e preencher valores
    tab.param_widgets["POP_SIZE"]["mode"].buttons()[1].setChecked(True)
    tab.param_widgets["POP_SIZE"]["variable"][0].setText("10")
    tab.param_widgets["POP_SIZE"]["variable"][1].setText("20")

    # 3. Mudar o número de repetições
    tab.runs_per_config_spin.setValue(3)

    # Usa um spy para capturar o sinal emitido
    from PySide6.QtCore import QSignalSpy
    spy = QSignalSpy(tab.execution_requested)
    
    # Clica no botão para executar a lógica
    tab.run_button.click()

    # Validações
    assert len(spy) == 1 # Verifica se o sinal foi emitido exatamente uma vez
    
    # Pega os argumentos emitidos pelo sinal
    configurations = spy[0][0]
    runs = spy[0][1]

    assert runs == 3
    assert len(configurations) == 4 # 2 valores de MUTACAO * 2 valores de POP_SIZE = 4 configs

    # Verifica se as combinações estão corretas
    expected_mutations = {c["MUTACAO"] for c in configurations}
    expected_pop_sizes = {c["POP_SIZE"] for c in configurations}
    assert expected_mutations == {0.5, 0.6}
    assert expected_pop_sizes == {10, 20}


def test_script_worker_success(qtbot, mocker):
    """
    Testa o ScriptWorker em um cenário de sucesso,
    usando mock para simular o subprocess.
    """
    # 1. Mock do subprocess.Popen
    mock_process = MagicMock()
    # Simula a saída do script: 2 linhas de log e depois o fim
    mock_process.stdout.readline.side_effect = ["Log line 1\n", "Log line 2\n", ""]
    mock_process.wait.return_value = 0 # Simula um código de saída de sucesso (0)
    
    # Substitui a chamada real de Popen pela nossa mock
    mocker.patch("subprocess.Popen", return_value=mock_process)

    # 2. Cria o worker e conecta seus sinais para teste
    worker = ScriptWorker("dummy_script.py", args=["--arg1"])
    
    # 3. Executa o worker e espera pelos sinais
    with qtbot.waitSignal(worker.execution_started, timeout=1000) as start_blocker:
        worker.run_script() # Chama a função diretamente para teste
    
    # Captura os logs
    logs = []
    worker.progress_update.connect(logs.append)
    
    with qtbot.waitSignal(worker.execution_finished, timeout=1000) as finish_blocker:
        # A execução continua a partir de onde o start parou
        qtbot.wait(100) # dá tempo para o loop de leitura rodar

    # 4. Asserts: Verifica se tudo ocorreu como esperado
    assert start_blocker.args[0].startswith("Executando comando:")
    
    assert "Log line 1" in logs
    assert "Log line 2" in logs
    
    # Verifica o sinal de finalização
    assert finish_blocker.args[0] is True  # Sucesso
    assert finish_blocker.args[1] == "Processo finalizado com código: 0"