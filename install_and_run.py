#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Instalação e Execução Otimizada do Framework RCE
Autor: Pedro Victor Veras
Data: 2025
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
import json
import time

class FrameworkInstaller:
    """Instalador e executor do framework RCE"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.src_dir = self.base_dir / "src"
        self.requirements_file = self.base_dir / "requirements.txt"
        
    def check_system_requirements(self):
        """Verifica requisitos do sistema"""
        print("🔍 Verificando requisitos do sistema...")
        
        # Verifica Python
        python_version = sys.version_info
        if python_version < (3, 8):
            print("❌ Python 3.8+ é necessário")
            return False
        
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Verifica sistema operacional
        system = platform.system()
        print(f"✅ Sistema: {system}")
        
        # Verifica compilador C++
        if system == "Windows":
            try:
                result = subprocess.run(["cl"], capture_output=True, shell=True)
                print("✅ Compilador MSVC encontrado")
            except:
                print("⚠️ Compilador MSVC não encontrado. Instale Visual Studio Build Tools")
        else:
            try:
                result = subprocess.run(["g++", "--version"], capture_output=True, text=True)
                print("✅ Compilador GCC encontrado")
            except:
                print("⚠️ Compilador GCC não encontrado. Instale build-essential")
        
        return True
    
    def install_dependencies(self):
        """Instala dependências"""
        print("📦 Instalando dependências...")
        
        try:
            # Instala dependências básicas
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "numpy>=1.21.0", "cython>=0.29.0", "setuptools", "wheel"
            ], check=True)
            
            # Instala outras dependências se requirements.txt existir
            if self.requirements_file.exists():
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(self.requirements_file, "--break-system-packages")
                ], check=True)
            
            print("✅ Dependências instaladas com sucesso!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar dependências: {e}")
            return False
    
    def compile_cpp_modules(self):
        """Compila módulos C++"""
        print("🔧 Compilando módulos C++...")
        
        try:
            # Muda para diretório do projeto
            os.chdir(self.base_dir)
            
            # Compila módulos Cython
            subprocess.run([
                sys.executable, "setup.py", "build_ext", "--inplace"
            ], check=True)
            
            print("✅ Módulos C++ compilados com sucesso!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao compilar módulos C++: {e}")
            print("⚠️ Continuando sem otimizações C++...")
            return False
    
    def create_optimized_runner(self):
        """Cria runner otimizado"""
        print("🚀 Criando runner otimizado...")
        
        runner_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Runner Otimizado do Framework RCE
"""

import sys
import os
from pathlib import Path

# Adiciona src ao path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

try:
    # Tenta importar módulo C++ otimizado
    from cpp_optimizer import FastRCEOptimizer, fast_rastrigin, fast_sphere, fast_rosenbrock
    USE_CPP_OPTIMIZER = True
    print("🚀 Usando otimizações C++")
except ImportError:
    USE_CPP_OPTIMIZER = False
    print("⚠️ Usando implementação Python padrão")

# Importa módulos do framework
from integrated_runner import IntegratedRunner

def main():
    """Função principal"""
    print("🚀 Iniciando Framework RCE Otimizado...")
    
    # Cria runner integrado
    runner = IntegratedRunner()
    
    # Parâmetros otimizados
    params = {
        "NUM_GENERATIONS": 40,
        "POP_SIZE": 5,
        "MUTACAO": 0.25,
        "CROSSOVER": 0.95,
        "RCE_REPOPULATION_GENERATIONS": 50,
        "PORCENTAGEM": 0.2
    }
    
    # Inicia execução
    runner.start(params)

if __name__ == "__main__":
    main()
'''
        
        runner_file = self.base_dir / "run_optimized.py"
        with open(runner_file, 'w', encoding='utf-8') as f:
            f.write(runner_content)
        
        # Torna executável no Linux/Mac
        if platform.system() != "Windows":
            os.chmod(runner_file, 0o755)
        
        print("✅ Runner otimizado criado!")
        return runner_file
    
    def setup_streamlit_dashboard(self):
        """Configura dashboard Streamlit"""
        print("📊 Configurando dashboard Streamlit...")
        
        try:
            # Verifica se streamlit está instalado
            subprocess.run([
                sys.executable, "-m", "streamlit", "--version"
            ], check=True, capture_output=True)
            
            print("✅ Streamlit configurado!")
            return True
            
        except subprocess.CalledProcessError:
            print("📦 Instalando Streamlit...")
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "streamlit"
                ], check=True)
                print("✅ Streamlit instalado!")
                return True
            except subprocess.CalledProcessError as e:
                print(f"❌ Erro ao instalar Streamlit: {e}")
                return False
    
    def create_launcher_script(self):
        """Cria script de launcher otimizado"""
        print("🎯 Criando launcher otimizado...")
        
        launcher_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Launcher Otimizado do Framework RCE
"""

import sys
import os
import subprocess
import threading
import time
from pathlib import Path

def run_framework():
    """Executa o framework"""
    try:
        subprocess.run([sys.executable, "run_optimized.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro no framework: {e}")

def run_dashboard():
    """Executa o dashboard"""
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "src/DashboardApp/dashboard_rce_app_v11.py",
            "--server.port", "8501"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro no dashboard: {e}")

def main():
    """Função principal"""
    print("🚀 Launcher Otimizado do Framework RCE")
    print("=" * 50)
    
    # Executa framework e dashboard em paralelo
    framework_thread = threading.Thread(target=run_framework, daemon=True)
    dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
    
    framework_thread.start()
    time.sleep(2)  # Aguarda framework inicializar
    dashboard_thread.start()
    
    try:
        # Aguarda threads
        framework_thread.join()
        dashboard_thread.join()
    except KeyboardInterrupt:
        print("\\n⏹️ Interrompendo execução...")
        sys.exit(0)

if __name__ == "__main__":
    main()
'''
        
        launcher_file = self.base_dir / "launch_optimized.py"
        with open(launcher_file, 'w', encoding='utf-8') as f:
            f.write(launcher_content)
        
        # Torna executável no Linux/Mac
        if platform.system() != "Windows":
            os.chmod(launcher_file, 0o755)
        
        print("✅ Launcher otimizado criado!")
        return launcher_file
    
    def run_performance_test(self):
        """Executa teste de performance"""
        print("⚡ Executando teste de performance...")
        
        try:
            # Teste simples de performance
            import time
            import numpy as np
            
            # Teste com numpy
            start_time = time.time()
            data = np.random.random((1000, 1000))
            result = np.dot(data, data.T)
            numpy_time = time.time() - start_time
            
            print(f"✅ Teste NumPy: {numpy_time:.4f}s")
            
            # Teste com otimizações C++ se disponível
            try:
                from src.cpp_optimizer import fast_sphere
                start_time = time.time()
                for _ in range(1000):
                    x = np.random.random(10)
                    fast_sphere(x)
                cpp_time = time.time() - start_time
                print(f"✅ Teste C++: {cpp_time:.4f}s")
            except ImportError:
                print("⚠️ Otimizações C++ não disponíveis")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro no teste de performance: {e}")
            return False
    
    def install(self):
        """Instala o framework completo"""
        print("🚀 Instalando Framework RCE Otimizado...")
        print("=" * 60)
        
        # Verifica requisitos
        if not self.check_system_requirements():
            return False
        
        # Instala dependências
        if not self.install_dependencies():
            return False
        
        # Compila módulos C++
        cpp_available = self.compile_cpp_modules()
        
        # Configura dashboard
        if not self.setup_streamlit_dashboard():
            return False
        
        # Cria runners otimizados
        self.create_optimized_runner()
        self.create_launcher_script()
        
        # Teste de performance
        self.run_performance_test()
        
        print("=" * 60)
        print("✅ Instalação concluída!")
        print("🚀 Para executar: python launch_optimized.py")
        print("📊 Dashboard: http://localhost:8501")
        
        return True

def main():
    """Função principal"""
    installer = FrameworkInstaller()
    
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        # Modo execução
        print("🚀 Executando Framework RCE...")
        try:
            subprocess.run([sys.executable, "run_optimized.py"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro na execução: {e}")
    else:
        # Modo instalação
        installer.install()

if __name__ == "__main__":
    main() 