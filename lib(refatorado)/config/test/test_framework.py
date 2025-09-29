import unittest
import pandas as pd
from pathlib import Path
import sys
import os

# Adiciona o diretório raiz ao sys.path
# Adiciona o diretório raiz ao sys.path para permitir a importação de módulos do projeto
sys.path.append(str(Path(__file__).resolve().parent.parent))

from lib.rce_framework.domain.models.AG.setup import Setup
from lib.rce_framework.domain.models.AG.alg_evolutivo_rce import AlgoritimoEvolutivoRCE
from lib.rce_framework.utils.functions_fitness.function_IEEE_14_contigencias import funcao_objetivo_IEEE14
from lib.rce_framework.main import entrada_de_dados, load_json

class TestRCEFramework(unittest.TestCase):

    def setUp(self):
        """Configura o ambiente de teste antes de cada teste."""
        self.base_dir = Path(__file__).resolve().parent.parent
        self.params = load_json(self.base_dir / "src" / "params.json")
        self.dados = entrada_de_dados()
        
        # Instancia o Setup para ser usado nos testes
        self.setup = Setup(
            self.params,
            fitness_function=lambda ind: funcao_objetivo_IEEE14(ind, self.setup),
            tamanho_hash=(self.dados["num_contingencias"] * self.dados["num_carregamentos"] * (2**self.dados["num_desligamentos"]))
        )

    def test_instanciacao_setup(self):
        """Testa se a classe Setup é instanciada corretamente."""
        self.assertIsInstance(self.setup, Setup)
        self.assertEqual(self.setup.pop_size, self.params['POP_SIZE'])
        print("✅ Teste de instanciação do Setup passou.")

    def test_instanciacao_algoritmo(self):
        """Testa se a classe AlgoritimoEvolutivoRCE é instanciada corretamente."""
        alg = AlgoritimoEvolutivoRCE(self.setup, DEBUG=False)
        self.assertIsInstance(alg, AlgoritimoEvolutivoRCE)
        print("✅ Teste de instanciação do AlgoritmoEvolutivoRCE passou.")

    def test_fluxo_potencia_simples(self):
        """
        Testa a execução de um fluxo de potência simples para garantir
        que a integração com o pandapower está funcionando.
        """
        try:
            from lib.rce_framework.components.rede_eletrica import RedeEletricaPandaPower
            rede = RedeEletricaPandaPower("14")
            convergiu = rede.executar_fluxo_de_potencia()
            self.assertTrue(convergiu, "O fluxo de potência não convergiu.")
            print("✅ Teste de fluxo de potência simples passou.")
        except ImportError as e:
            self.fail(f"Não foi possível importar RedeEletricaPandaPower: {e}")
        except Exception as e:
            self.fail(f"Erro inesperado durante o fluxo de potência: {e}")

if __name__ == '__main__':
    unittest.main()
