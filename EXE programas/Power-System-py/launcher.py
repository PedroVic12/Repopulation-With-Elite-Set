"""
launcher.py - Multi-Program Launcher with Menu

Executes multiple Python scripts in sequence with interactive menu selection.
Supports running individual programs or all programs in order.
"""

import sys
import os

# Force UTF-8 encoding for output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import subprocess
from pathlib import Path
from typing import List, Tuple, Optional


class ProgramLauncher:
    """Manages launching multiple Python programs with menu interface."""
    
    def __init__(self):
        self.current_dir = Path(__file__).parent
        self.programs: List[Tuple[str, str, str]] = [
            ("SYSTEM_ELECTRICAL_PANDAPOWER", "SYSTEM_ELECTRICAL_PANDAPOWER.py", "⚡ Dashboard de Análise de Contingências"),
            ("router_tests", "test_router.py", "🧪 Testes de Roteamento"),
        ]
        self.python_exe = sys.executable
    
    def display_menu(self) -> int:
        """Display interactive menu and return user choice."""
        print("\n" + "="*70)
        print("🚀 GERENCIADOR DE PROGRAMAS - POWER SYSTEM DASHBOARD")
        print("="*70)
        print()
        
        for i, (name, file, desc) in enumerate(self.programs, 1):
            status = "✅" if self._file_exists(file) else "❌"
            print(f"{i}. {status} {desc}")
            print(f"   📄 {file}")
            print()
        
        print(f"{len(self.programs) + 1}. 🔄 Executar TODOS em sequência")
        print(f"{len(self.programs) + 2}. ❌ Sair")
        print()
        print("-"*70)
        
        try:
            choice = input("Escolha uma opção (1-{}): ".format(len(self.programs) + 2)).strip()
            return int(choice)
        except ValueError:
            return -1
    
    def _file_exists(self, filename: str) -> bool:
        """Check if a program file exists."""
        filepath = self.current_dir / filename
        return filepath.exists()
    
    def run_program(self, index: int) -> bool:
        """
        Run a single program by index.
        
        Args:
            index: Program index (0-based)
            
        Returns:
            True if execution was successful, False otherwise
        """
        if index < 0 or index >= len(self.programs):
            return False
        
        name, filename, desc = self.programs[index]
        filepath = self.current_dir / filename
        
        if not filepath.exists():
            print(f"\n❌ ERRO: Arquivo não encontrado: {filepath}")
            return False
        
        print("\n" + "="*70)
        print(f"▶️  Executando: {desc}")
        print(f"📄 Arquivo: {filename}")
        print("="*70 + "\n")
        
        try:
            # Run Python script
            result = subprocess.run(
                [self.python_exe, str(filepath)],
                cwd=str(self.current_dir),
                check=False
            )
            
            if result.returncode == 0:
                print(f"\n✅ {desc} executado com SUCESSO!")
                return True
            else:
                print(f"\n⚠️  {desc} saiu com código: {result.returncode}")
                return False
        
        except KeyboardInterrupt:
            print(f"\n⏸️  {desc} interrompido pelo usuário.")
            return False
        except Exception as e:
            print(f"\n❌ ERRO ao executar {desc}: {e}")
            return False
    
    def run_all_programs(self) -> None:
        """Run all programs in sequence."""
        print("\n" + "="*70)
        print("🔄 EXECUTANDO TODOS OS PROGRAMAS EM SEQUÊNCIA")
        print("="*70)
        
        results = []
        for i, (name, filename, desc) in enumerate(self.programs, 1):
            print(f"\n[{i}/{len(self.programs)}] Iniciando: {desc}")
            print("-"*70)
            
            success = self.run_program(i - 1)
            results.append((desc, success))
            
            if i < len(self.programs):
                try:
                    input("\nPressione ENTER para continuar para o próximo programa...")
                except KeyboardInterrupt:
                    print("\n⏸️  Execução de todos os programas interrompida.")
                    break
        
        # Print summary
        print("\n" + "="*70)
        print("📊 RESUMO DA EXECUÇÃO")
        print("="*70)
        
        for desc, success in results:
            status = "✅" if success else "❌"
            print(f"{status} {desc}")
        
        total = len(results)
        successful = sum(1 for _, s in results if s)
        print(f"\nTotal: {successful}/{total} programas executados com sucesso")
        print("="*70 + "\n")
    
    def run(self) -> None:
        """Main loop for the launcher."""
        while True:
            choice = self.display_menu()
            
            if choice == len(self.programs) + 2:
                print("\n👋 Até logo!")
                break
            elif choice == len(self.programs) + 1:
                self.run_all_programs()
                try:
                    input("\nPressione ENTER para voltar ao menu principal...")
                except KeyboardInterrupt:
                    pass
            elif 1 <= choice <= len(self.programs):
                self.run_program(choice - 1)
                try:
                    input("\nPressione ENTER para voltar ao menu principal...")
                except KeyboardInterrupt:
                    pass
            else:
                print("\n❌ Opção inválida! Por favor, escolha novamente.")
                try:
                    input("Pressione ENTER para continuar...")
                except KeyboardInterrupt:
                    print("\n👋 Até logo!")
                    break


def main():
    """Entry point for the launcher."""
    try:
        launcher = ProgramLauncher()
        launcher.run()
    except KeyboardInterrupt:
        print("\n\n👋 Launcher interrompido pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
