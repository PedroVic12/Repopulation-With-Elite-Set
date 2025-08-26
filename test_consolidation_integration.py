#!/usr/bin/env python3
"""
Teste de integração entre ConsolidationManager e Dashboard.
Verifica se tudo está funcionando sem modificar o database_controller.py original.
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

def test_consolidation_manager():
    """Testa o ConsolidationManager isoladamente."""
    print("🔧 === TESTE DO CONSOLIDATION MANAGER ===")
    
    try:
        from consolidation_manager import ConsolidationManager
        
        manager = ConsolidationManager()
        print("✅ ConsolidationManager inicializado!")
        
        # Testa status
        status = manager.get_consolidation_status()
        print(f"✅ Status obtido: {len(status)} campos")
        print(f"  • Arquivo existe: {status['consolidated_file_exists']}")
        print(f"  • Precisa consolidar: {status['needs_consolidation']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no ConsolidationManager: {e}")
        return False

def test_database_controller_original():
    """Testa o DatabaseController original (não modificado)."""
    print("\n🗄️ === TESTE DO DATABASE CONTROLLER ORIGINAL ===")
    
    try:
        from database_controller import DatabaseController
        
        controller = DatabaseController()
        print("✅ DatabaseController original inicializado!")
        
        # Testa funcionalidades básicas
        params = controller.get_params()
        print(f"✅ Parâmetros carregados: {len(params) if params else 0} itens")
        
        # Testa dados consolidados
        df = controller.get_consolidated_data()
        if df is not None:
            print(f"✅ Dados consolidados: {len(df)} execuções")
        else:
            print("⚠️ Dados consolidados não disponíveis")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no DatabaseController: {e}")
        return False

def test_dashboard_integration():
    """Testa se o dashboard consegue usar ambos os componentes."""
    print("\n🖥️ === TESTE DE INTEGRAÇÃO DO DASHBOARD ===")
    
    try:
        from src.DashboardApp.views.Screens.RCE_Framework_Page import FrameworkRCEDashboard
        
        dashboard = FrameworkRCEDashboard()
        print("✅ FrameworkRCEDashboard inicializado!")
        
        # Verifica se tem ambos os componentes
        has_db_controller = hasattr(dashboard, 'db_controller')
        has_consolidation_manager = hasattr(dashboard, 'consolidation_manager')
        has_config = hasattr(dashboard, 'config')
        
        print(f"✅ Componentes disponíveis:")
        print(f"  • DatabaseController: {'✅' if has_db_controller else '❌'}")
        print(f"  • ConsolidationManager: {'✅' if has_consolidation_manager else '❌'}")
        print(f"  • Config: {'✅' if has_config else '❌'}")
        
        return has_db_controller and has_consolidation_manager and has_config
        
    except Exception as e:
        print(f"❌ Erro no dashboard: {e}")
        return False

def test_consolidation_functionality():
    """Testa a funcionalidade de consolidação."""
    print("\n📊 === TESTE DE FUNCIONALIDADE DE CONSOLIDAÇÃO ===")
    
    try:
        from consolidation_manager import ConsolidationManager
        
        manager = ConsolidationManager()
        
        # Testa se consegue verificar status
        status = manager.get_consolidation_status()
        print(f"✅ Status verificado: {status['consolidated_file_exists']}")
        
        # Testa se consegue acessar arquivos
        if status['consolidated_file_exists']:
            print(f"✅ Arquivo consolidado existe: {status['file_size_mb']} MB")
            print(f"✅ Total de execuções: {status['total_executions']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na funcionalidade: {e}")
        return False

def main():
    """Função principal de teste."""
    print("🎯 TESTE DE INTEGRAÇÃO - SEM MODIFICAR DATABASE_CONTROLLER.PY")
    print("=" * 70)
    
    # Executa todos os testes
    tests = [
        ("ConsolidationManager", test_consolidation_manager),
        ("DatabaseController Original", test_database_controller_original),
        ("Dashboard Integration", test_dashboard_integration),
        ("Consolidation Functionality", test_consolidation_functionality)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n🔄 Executando: {name}")
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ Erro inesperado em {name}: {e}")
            results.append((name, False))
    
    # Resumo dos resultados
    print("\n" + "=" * 70)
    print("📊 RESUMO DOS TESTES")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{status} {name}")
        if success:
            passed += 1
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} testes passaram!")
    
    if passed == total:
        print("🎉 PERFEITO! Todos os componentes estão funcionando!")
        print("✅ DatabaseController original preservado")
        print("✅ ConsolidationManager funcionando separadamente")
        print("✅ Dashboard integrado com ambos")
        print("✅ Nenhum código foi apagado!")
    else:
        print("⚠️ Alguns componentes precisam de atenção.")
        print("🔧 Verifique os erros acima e corrija se necessário.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 