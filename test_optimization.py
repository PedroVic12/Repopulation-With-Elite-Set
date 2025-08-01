#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Teste para Otimizações do Framework RCE
Autor: Pedro Victor Veras
Data: 2025
"""

import time
import numpy as np
import json
from pathlib import Path
import sys

def test_python_implementation():
    """Testa implementação Python pura"""
    print("🐍 Testando implementação Python...")
    
    def rastrigin_python(x):
        n = len(x)
        result = 10.0 * n
        for i in range(n):
            xi = x[i]
            result += xi * xi - 10.0 * np.cos(2.0 * np.pi * xi)
        return result
    
    start_time = time.time()
    for _ in range(1000):
        x = np.random.random(10)
        rastrigin_python(x)
    python_time = time.time() - start_time
    
    print(f"✅ Tempo Python: {python_time:.4f}s")
    return python_time

def test_cpp_implementation():
    """Testa implementação C++ otimizada"""
    print("⚡ Testando implementação C++...")
    
    try:
        from src.cpp_optimizer import fast_rastrigin
        
        start_time = time.time()
        for _ in range(1000):
            x = np.random.random(10)
            fast_rastrigin(x)
        cpp_time = time.time() - start_time
        
        print(f"✅ Tempo C++: {cpp_time:.4f}s")
        return cpp_time
        
    except ImportError as e:
        print(f"❌ Módulo C++ não disponível: {e}")
        return None

def test_genetic_algorithm():
    """Testa algoritmo genético"""
    print("🧬 Testando algoritmo genético...")
    
    try:
        from src.cpp_optimizer import FastGeneticAlgorithm, fast_rastrigin
        
        # Cria AG otimizado
        ga = FastGeneticAlgorithm(
            pop_size=50,
            chrom_length=10,
            mutation_rate=0.1,
            crossover_rate=0.8
        )
        
        # Executa evolução
        start_time = time.time()
        history = ga.evolve(fast_rastrigin, 50)
        ga_time = time.time() - start_time
        
        print(f"✅ Tempo AG C++: {ga_time:.4f}s")
        print(f"📊 Melhor fitness: {history[-1]:.6f}")
        return ga_time
        
    except ImportError as e:
        print(f"❌ AG C++ não disponível: {e}")
        return None

def test_rce_optimizer():
    """Testa otimizador RCE"""
    print("🔄 Testando otimizador RCE...")
    
    try:
        from src.cpp_optimizer import FastRCEOptimizer, fast_rastrigin
        
        # Cria otimizador RCE
        rce = FastRCEOptimizer(
            pop_size=30,
            chrom_length=10,
            mutation_rate=0.15,
            crossover_rate=0.85,
            elite_size=3,
            repopulation_rate=0.3,
            repopulation_generations=10
        )
        
        # Executa otimização RCE
        start_time = time.time()
        history = rce.run_rce_optimization(fast_rastrigin, 30, 2)
        rce_time = time.time() - start_time
        
        print(f"✅ Tempo RCE C++: {rce_time:.4f}s")
        print(f"📊 Melhor fitness: {history[-1]:.6f}")
        return rce_time
        
    except ImportError as e:
        print(f"❌ RCE C++ não disponível: {e}")
        return None

def test_integrated_runner():
    """Testa runner integrado"""
    print("🚀 Testando runner integrado...")
    
    try:
        from src.integrated_runner import IntegratedRunner
        
        # Cria runner
        runner = IntegratedRunner()
        
        # Testa com parâmetros pequenos
        params = {
            "NUM_GENERATIONS": 5,
            "POP_SIZE": 10,
            "MUTACAO": 0.2,
            "CROSSOVER": 0.8,
            "RCE_REPOPULATION_GENERATIONS": 3,
            "PORCENTAGEM": 0.2
        }
        
        print("✅ Runner integrado disponível")
        return True
        
    except ImportError as e:
        print(f"❌ Runner integrado não disponível: {e}")
        return False

def test_config_files():
    """Testa arquivos de configuração"""
    print("📁 Testando arquivos de configuração...")
    
    base_dir = Path(__file__).parent
    src_dir = base_dir / "src"
    
    # Verifica params.json
    params_file = src_dir / "params.json"
    if params_file.exists():
        try:
            with open(params_file, 'r') as f:
                params = json.load(f)
            print(f"✅ params.json: {len(params)} parâmetros")
        except Exception as e:
            print(f"❌ Erro ao ler params.json: {e}")
    else:
        print("❌ params.json não encontrado")
    
    # Verifica options.json
    options_file = src_dir / "options.json"
    if options_file.exists():
        try:
            with open(options_file, 'r') as f:
                options = json.load(f)
            print(f"✅ options.json: {len(options)} configurações")
        except Exception as e:
            print(f"❌ Erro ao ler options.json: {e}")
    else:
        print("❌ options.json não encontrado")

def test_dashboard():
    """Testa dashboard"""
    print("📊 Testando dashboard...")
    
    base_dir = Path(__file__).parent
    dashboard_file = base_dir / "src" / "DashboardApp" / "dashboard_rce_app_v11.py"
    
    if dashboard_file.exists():
        print("✅ Dashboard encontrado")
        
        # Verifica se streamlit está disponível
        try:
            import streamlit
            print("✅ Streamlit disponível")
        except ImportError:
            print("❌ Streamlit não instalado")
    else:
        print("❌ Dashboard não encontrado")

def main():
    """Função principal de teste"""
    print("🧪 Teste de Otimizações do Framework RCE")
    print("=" * 50)
    
    # Testa implementações
    python_time = test_python_implementation()
    cpp_time = test_cpp_implementation()
    
    if cpp_time and python_time:
        speedup = python_time / cpp_time
        print(f"⚡ Speedup C++: {speedup:.2f}x mais rápido")
    
    # Testa algoritmos
    test_genetic_algorithm()
    test_rce_optimizer()
    
    # Testa integração
    test_integrated_runner()
    
    # Testa arquivos
    test_config_files()
    test_dashboard()
    
    print("=" * 50)
    print("✅ Teste concluído!")
    
    if cpp_time and python_time:
        print(f"🎯 Performance: {speedup:.2f}x mais rápido com C++")
    else:
        print("⚠️ Otimizações C++ não disponíveis")

if __name__ == "__main__":
    main() 