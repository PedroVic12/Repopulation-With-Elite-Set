#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Execução Rápida do Framework RCE Otimizado
Autor: Pedro Victor Veras
Data: 2025
"""

import os
import sys
import subprocess
import time
import threading
from pathlib import Path

def check_requirements():
    """Verifica requisitos básicos"""
    print("🔍 Verificando requisitos...")
    
    # Verifica Python
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ necessário")
        return False
    
    # Verifica arquivos essenciais
    base_dir = Path(__file__).parent
    essential_files = [
        base_dir / "src" / "params.json",
        base_dir / "src" / "options.json",
        base_dir / "src" / "run_framework.py"
    ]
    
    for file_path in essential_files:
        if not file_path.exists():
            print(f"❌ Arquivo não encontrado: {file_path}")
            return False
    
    print("✅ Requisitos básicos atendidos")
    return True

def install_dependencies():
    """Instala dependências básicas"""
    print("📦 Instalando dependências...")
    
    try:
        # Dependências essenciais
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "numpy", "streamlit", "pandas", "plotly"
        ], check=True, capture_output=True)
        
        print("✅ Dependências instaladas")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False

def run_framework_simple():
    """Executa framework de forma simples"""
    print("🚀 Executando framework...")
    
    try:
        base_dir = Path(__file__).parent
        framework_script = base_dir / "src" / "run_framework.py"
        
        # Executa com parâmetros reduzidos para teste rápido
        env = os.environ.copy()
        env["QUICK_TEST"] = "1"  # Flag para teste rápido
        
        result = subprocess.run([
            sys.executable, str(framework_script)
        ], cwd=base_dir, env=env, timeout=300)  # 5 minutos timeout
        
        if result.returncode == 0:
            print("✅ Framework executado com sucesso")
            return True
        else:
            print(f"❌ Framework falhou com código {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Timeout - Framework demorou muito")
        return False
    except Exception as e:
        print(f"❌ Erro ao executar framework: {e}")
        return False

def run_dashboard():
    """Executa dashboard Streamlit"""
    print("📊 Iniciando dashboard...")
    
    try:
        base_dir = Path(__file__).parent
        dashboard_script = base_dir / "src" / "DashboardApp" / "dashboard_rce_app_v11.py"
        
        if not dashboard_script.exists():
            print("❌ Dashboard não encontrado")
            return False
        
        # Executa dashboard em thread separada
        def run_streamlit():
            subprocess.run([
                sys.executable, "-m", "streamlit", "run", str(dashboard_script),
                "--server.port", "8501", "--server.headless", "true"
            ], cwd=base_dir)
        
        dashboard_thread = threading.Thread(target=run_streamlit, daemon=True)
        dashboard_thread.start()
        
        # Aguarda um pouco para inicializar
        time.sleep(5)
        
        print("✅ Dashboard iniciado em http://localhost:8501")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao iniciar dashboard: {e}")
        return False

def run_optimization_test():
    """Executa teste de otimização"""
    print("⚡ Testando otimizações...")
    
    try:
        test_script = Path(__file__).parent / "test_optimization.py"
        
        if test_script.exists():
            subprocess.run([sys.executable, str(test_script)], check=True)
            print("✅ Teste de otimização concluído")
            return True
        else:
            print("⚠️ Script de teste não encontrado")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro no teste de otimização: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 Framework RCE - Execução Rápida")
    print("=" * 50)
    
    # Verifica requisitos
    if not check_requirements():
        print("❌ Requisitos não atendidos")
        return
    
    # Instala dependências se necessário
    try:
        import numpy
        import streamlit
        print("✅ Dependências já instaladas")
    except ImportError:
        if not install_dependencies():
            print("❌ Falha ao instalar dependências")
            return
    
    # Executa teste de otimização
    run_optimization_test()
    
    # Pergunta ao usuário o que executar
    print("\n🎯 O que você quer executar?")
    print("1. Apenas Framework")
    print("2. Apenas Dashboard")
    print("3. Framework + Dashboard")
    print("4. Teste completo")
    
    try:
        choice = input("Escolha (1-4): ").strip()
    except KeyboardInterrupt:
        print("\n👋 Saindo...")
        return
    
    if choice == "1":
        # Apenas framework
        run_framework_simple()
        
    elif choice == "2":
        # Apenas dashboard
        run_dashboard()
        input("Pressione Enter para parar o dashboard...")
        
    elif choice == "3":
        # Framework + Dashboard
        print("🔄 Executando framework e dashboard...")
        
        # Inicia dashboard
        if run_dashboard():
            # Executa framework
            run_framework_simple()
            
            print("✅ Execução concluída!")
            print("📊 Dashboard disponível em: http://localhost:8501")
        
    elif choice == "4":
        # Teste completo
        print("🧪 Executando teste completo...")
        
        # Teste de otimização
        run_optimization_test()
        
        # Framework
        run_framework_simple()
        
        # Dashboard
        run_dashboard()
        
        print("✅ Teste completo concluído!")
        
    else:
        print("❌ Opção inválida")
        return
    
    print("\n🎉 Execução concluída!")

if __name__ == "__main__":
    main() 