#!/usr/bin/env python3
"""
Script de teste para verificar se as correções do dashboard funcionaram.
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

def test_imports():
    """Testa se as importações estão funcionando."""
    try:
        print("🔍 Testando importações...")
        
        # Testa importação do DatabaseController
        from database_controller import DatabaseController
        print("✅ DatabaseController importado com sucesso!")
        
        # Testa importação do FrameworkRCEDashboard
        from src.DashboardApp.views.Screens.RCE_Framework_Page import FrameworkRCEDashboard
        print("✅ FrameworkRCEDashboard importado com sucesso!")
        
        # Testa importação dos componentes
        from src.DashboardApp.views.Screens.components.AgendamentoRedePage import AgendamentoRedePage
        print("✅ AgendamentoRedePage importado com sucesso!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def test_database_controller():
    """Testa se o DatabaseController está funcionando."""
    try:
        print("\n🔍 Testando DatabaseController...")
        
        from database_controller import DatabaseController
        
        # Inicializa o controlador
        controller = DatabaseController()
        print("✅ DatabaseController inicializado!")
        
        # Testa funcionalidades básicas
        params = controller.get_params()
        print(f"✅ Parâmetros carregados: {len(params) if params else 0} itens")
        
        # Testa funcionalidades de orquestração
        summary = controller.get_execution_summary()
        print(f"✅ Resumo de execuções: {summary['total_runs']} execuções")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no DatabaseController: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal de teste."""
    print("🚀 TESTE DO DASHBOARD RCE FRAMEWORK")
    print("=" * 50)
    
    # Testa importações
    if not test_imports():
        print("\n❌ Falha nos testes de importação!")
        return False
    
    # Testa DatabaseController
    if not test_database_controller():
        print("\n❌ Falha nos testes do DatabaseController!")
        return False
    
    print("\n🎯 TODOS OS TESTES PASSARAM!")
    print("✅ O dashboard está funcionando corretamente!")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 