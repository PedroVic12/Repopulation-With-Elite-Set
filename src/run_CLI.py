#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Integrado para Execução do Framework RCE com Dashboard em Tempo Real
Autor: Pedro Victor Veras
Data: 2025
"""

import os
import sys
import json
import time
import threading
import subprocess
import signal
import queue
from pathlib import Path
from datetime import datetime
import multiprocessing as mp
from typing import Dict, Any, Optional

# Configurações
BASE_DIR = Path(__file__).parent
PARAMS_FILE = BASE_DIR / "params.json"
OPTIONS_FILE = BASE_DIR / "options.json"
RESULTS_DIR = BASE_DIR / "resultados"
DASHBOARD_SCRIPT = BASE_DIR / "DashboardApp" /"views" / "Screens" / "RCE_Framework_Page.py"

class RealTimeDataManager:
    """Gerencia dados em tempo real entre framework e dashboard"""
    
    def __init__(self):
        self.data_queue = queue.Queue()
        self.status_queue = queue.Queue()
        self.running = True
        self.lock = threading.Lock()
        
    def add_data(self, data: Dict[str, Any]):
        """Adiciona dados à fila"""
        with self.lock:
            self.data_queue.put({
                'timestamp': datetime.now().isoformat(),
                'data': data
            })
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        """Obtém dados da fila"""
        try:
            return self.data_queue.get_nowait()
        except queue.Empty:
            return None
    
    def update_status(self, status: str):
        """Atualiza status"""
        with self.lock:
            self.status_queue.put({
                'timestamp': datetime.now().isoformat(),
                'status': status
            })
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """Obtém status da fila"""
        try:
            return self.status_queue.get_nowait()
        except queue.Empty:
            return None

class FrameworkRunner:
    """Executa o framework RCE com monitoramento em tempo real"""
    
    def __init__(self, data_manager: RealTimeDataManager):
        self.data_manager = data_manager
        self.process = None
        self.running = False
        
    def run(self, params: Dict[str, Any]):
        """Executa o framework"""
        try:
            self.running = True
            self.data_manager.update_status("Iniciando framework...")
            
            # Atualiza params.json com os parâmetros fornecidos
            self._update_params_file(params)
            
            # Executa o framework
            cmd = [sys.executable, "run_framework.py"]
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=BASE_DIR,
                bufsize=1
            )
            
            self.data_manager.update_status("Framework em execução...")
            
            # Monitora saída em tempo real
            for line in iter(self.process.stdout.readline, ''):
                if not self.running:
                    break
                    
                line = line.strip()
                if line:
                    self._parse_framework_output(line)
            
            return_code = self.process.wait()
            success = return_code == 0
            
            if success:
                self.data_manager.update_status("Framework concluído com sucesso!")
                self._load_results()
            else:
                self.data_manager.update_status(f"Framework falhou com código {return_code}")
                
        except Exception as e:
            self.data_manager.update_status(f"Erro no framework: {e}")
            self.running = False
    
    def stop(self):
        """Para a execução"""
        self.running = False
        if self.process:
            self.process.terminate()
            self.process.wait()
    
    def _update_params_file(self, params: Dict[str, Any]):
        """Atualiza arquivo params.json"""
        try:
            with open(PARAMS_FILE, 'r') as f:
                current_params = json.load(f)
            
            current_params.update(params)
            
            with open(PARAMS_FILE, 'w') as f:
                json.dump(current_params, f, indent=4)
                
            self.data_manager.add_data({
                'type': 'params_updated',
                'params': current_params
            })
            
        except Exception as e:
            print(f"Erro ao atualizar params.json: {e}")
    
    def _parse_framework_output(self, line: str):
        """Analisa saída do framework para extrair dados em tempo real"""
        try:
            # Detecta diferentes tipos de saída
            if "Geração" in line and "Melhor fitness:" in line:
                # Extrai dados da geração atual
                parts = line.split()
                generation = int(parts[1].split('/')[0])
                fitness = float(parts[-1])
                
                self.data_manager.add_data({
                    'type': 'generation_update',
                    'generation': generation,
                    'best_fitness': fitness
                })
                
            elif "Execução" in line and "concluída" in line:
                # Execução concluída
                self.data_manager.add_data({
                    'type': 'execution_complete',
                    'message': line
                })
                
            elif "Erro" in line or "ERROR" in line:
                # Erro detectado
                self.data_manager.add_data({
                    'type': 'error',
                    'message': line
                })
                
        except Exception as e:
            print(f"Erro ao analisar saída: {e}")
    
    def _load_results(self):
        """Carrega resultados finais"""
        try:
            results_files = list(RESULTS_DIR.glob("*.json"))
            if results_files:
                latest_file = max(results_files, key=lambda f: f.stat().st_mtime)
                
                with open(latest_file, 'r') as f:
                    results = json.load(f)
                
                self.data_manager.add_data({
                    'type': 'final_results',
                    'results': results,
                    'file': str(latest_file)
                })
                
        except Exception as e:
            print(f"Erro ao carregar resultados: {e}")

class DashboardRunner:
    """Executa o dashboard Streamlit"""
    
    def __init__(self, data_manager: RealTimeDataManager):
        self.data_manager = data_manager
        self.process = None
        self.running = False
        
    def run(self):
        """Executa o dashboard"""
        try:
            self.running = True
            self.data_manager.update_status("Iniciando dashboard...")
            
            # Verifica se o script existe
            if not DASHBOARD_SCRIPT.exists():
                raise FileNotFoundError(f"Dashboard script não encontrado: {DASHBOARD_SCRIPT}")
            
            # Executa Streamlit
            cmd = [
                sys.executable, "-m", "streamlit", "run", str(DASHBOARD_SCRIPT),
                "--server.port", "8501",
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false"
            ]
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=BASE_DIR
            )
            
            self.data_manager.update_status("Dashboard iniciado em http://localhost:8501")
            
            # Monitora saída do dashboard
            for line in iter(self.process.stdout.readline, ''):
                if not self.running:
                    break
                    
                line = line.strip()
                if line and ("error" in line.lower() or "exception" in line.lower()):
                    self.data_manager.add_data({
                        'type': 'dashboard_error',
                        'message': line
                    })
            
            return_code = self.process.wait()
            if return_code != 0:
                self.data_manager.update_status(f"Dashboard encerrado com código {return_code}")
                
        except Exception as e:
            self.data_manager.update_status(f"Erro no dashboard: {e}")
            self.running = False
    
    def stop(self):
        """Para o dashboard"""
        self.running = False
        if self.process:
            self.process.terminate()
            self.process.wait()

class IntegratedRunner:
    """Runner principal que integra framework e dashboard"""
    
    def __init__(self):
        self.data_manager = RealTimeDataManager()
        self.framework_runner = FrameworkRunner(self.data_manager)
        self.dashboard_runner = DashboardRunner(self.data_manager)
        self.framework_thread = None
        self.dashboard_thread = None
        
    def start(self, params: Dict[str, Any] = None):
        """Inicia execução integrada"""
        try:
            # Parâmetros padrão se não fornecidos
            if params is None:
                params = {
                    "NUM_GENERATIONS": 40,
                    "POP_SIZE": 5,
                    "MUTACAO": 0.25,
                    "CROSSOVER": 0.95,
                    "RCE_REPOPULATION_GENERATIONS": 50,
                    "PORCENTAGEM": 0.2
                }
            
            print("🚀 Iniciando Framework RCE Integrado...")
            print(f"📊 Parâmetros: {params}")
            
            # Inicia dashboard em thread separada
            self.dashboard_thread = threading.Thread(
                target=self.dashboard_runner.run,
                daemon=True
            )
            self.dashboard_thread.start()
            
            # Aguarda um pouco para o dashboard inicializar
            time.sleep(3)
            
            # Inicia framework em thread separada
            self.framework_thread = threading.Thread(
                target=self.framework_runner.run,
                args=(params,),
                daemon=True
            )
            self.framework_thread.start()
            
            # Loop principal de monitoramento
            self._monitor_execution()
            
        except KeyboardInterrupt:
            print("\n⏹️ Interrompendo execução...")
            self.stop()
        except Exception as e:
            print(f"❌ Erro na execução: {e}")
            self.stop()
    
    def _monitor_execution(self):
        """Monitora a execução em tempo real"""
        print("📈 Monitorando execução em tempo real...")
        
        while (self.framework_thread and self.framework_thread.is_alive() or 
               self.dashboard_thread and self.dashboard_thread.is_alive()):
            
            # Verifica dados em tempo real
            data = self.data_manager.get_data()
            if data:
                self._handle_realtime_data(data)
            
            # Verifica status
            status = self.data_manager.get_status()
            if status:
                print(f"[{status['timestamp']}] {status['status']}")
            
            time.sleep(1)
        
        print("✅ Execução concluída!")
    
    def _handle_realtime_data(self, data: Dict[str, Any]):
        """Processa dados em tempo real"""
        data_type = data.get('type')
        
        if data_type == 'generation_update':
            generation = data['generation']
            fitness = data['best_fitness']
            print(f"🔄 Geração {generation}: Melhor fitness = {fitness:.6f}")
            
        elif data_type == 'execution_complete':
            print(f"✅ {data['message']}")
            
        elif data_type == 'error':
            print(f"❌ Erro: {data['message']}")
            
        elif data_type == 'final_results':
            print(f"📊 Resultados finais carregados de: {data['file']}")
            
        elif data_type == 'dashboard_error':
            print(f"⚠️ Dashboard: {data['message']}")
    
    def stop(self):
        """Para a execução"""
        print("🛑 Parando execução...")
        
        if self.framework_runner:
            self.framework_runner.stop()
        
        if self.dashboard_runner:
            self.dashboard_runner.stop()
        
        if self.framework_thread:
            self.framework_thread.join(timeout=5)
        
        if self.dashboard_thread:
            self.dashboard_thread.join(timeout=5)
        
        print("🛑 Execução parada!")

def main():
    """Função principal"""
    print("=" * 60)
    print("🚀 RCE Framework - Launcher Integrado")
    print("=" * 60)
    
    # Verifica dependências
    required_files = [PARAMS_FILE, OPTIONS_FILE, DASHBOARD_SCRIPT]
    for file_path in required_files:
        if not file_path.exists():
            print(f"❌ Arquivo necessário não encontrado: {file_path}")
            return
    
    # Cria runner integrado
    runner = IntegratedRunner()
    
    # Configura signal handlers para graceful shutdown
    def signal_handler(signum, frame):
        print("\n🛑 Sinal de interrupção recebido...")
        runner.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Inicia execução
    runner.start()

if __name__ == "__main__":
    main() 