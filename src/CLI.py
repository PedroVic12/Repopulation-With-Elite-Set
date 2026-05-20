# -*- coding: utf-8 -*-
"""
CLI.py - Professional CLI for RCE Framework using Rich.
Implemented with OOP for the UFF and ONS presentation.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# Ajustar path para encontrar os modelos
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import print as rprint

from run import run_framework_many_executions, ARRAY_FITNESS_FUNCTIONS
from global_settings import OBJECTIVE_FUNCTIONS_METADATA

class RCE_CLI_App:
    def __init__(self):
        self.console = Console()
        self.metadata = OBJECTIVE_FUNCTIONS_METADATA
        self.projects_root = Path(os.getenv("PROJECTS_ROOT", current_dir.parent))

    def display_header(self):
        title = """
[bold cyan]
  _____   _____ ______   ______                                            _    
 |  __ \ / ____|  ____| |  ____|                                          | |   
 | |__) | |    | |__    | |__ _ __ __ _ _ __ ___   _____      _____  _ __| | __
 |  _  /| |    |  __|   |  __| '__/ _` | '_ ` _ \ / _ \ \ /\ / / _ \| '__| |/ /
 | | \ \| |____| |____  | |  | | | (_| | | | | | |  __/\ V  V / (_) | |  |   < 
 |_|  \_\\\\_____|______| |_|  |_|  \__,_|_| |_| |_|\___| \_/\_/ \___/|_|  |_|\_\\
[/bold cyan]
[bold white]Repopulation with Elite Set Framework - UFF / ONS Special Edition[/bold white]
        """
        self.console.print(Panel(title, border_style="cyan"))

    def show_main_menu(self):
        table = Table(title="Menu Principal", expand=True)
        table.add_column("Opção", justify="center", style="cyan", no_wrap=True)
        table.add_column("Programa", style="magenta")
        table.add_column("Descrição", style="white")

        table.add_row("1", "▶️ Executar RCE Framework (Otimização)", "Abre o menu de funções objetivo.")
        table.add_row("2", "▶️ Executar Electrical-Power-System", "Abre a interface do PandaPower (app.py).")
        table.add_row("3", "▶️ Executar PandaPower Case Manager", "Gerenciador de casos SIN45.")
        table.add_row("4", "▶️ Executar Smart Grid Simulator", "Simulador do Smart Grid.")
        table.add_row("0", "Sair", "Encerrar a CLI.")

        self.console.print(table)

    def show_objective_functions_menu(self):
        table = Table(title="Funções Objetivo Disponíveis", expand=True)
        table.add_column("ID", justify="center", style="cyan", no_wrap=True)
        table.add_column("Nome da Função", style="magenta")
        table.add_column("Dimensão (Variáveis)", justify="center", style="green")
        table.add_column("Descrição", style="white")

        for i, func in enumerate(ARRAY_FITNESS_FUNCTIONS):
            func_name = func.__name__
            meta = self.metadata.get(func_name, {"name": func_name, "dim": "N/A"})
            table.add_row(
                str(i),
                meta["name"],
                str(meta["dim"]),
                f"Execução de contingências para rede de {meta['dim']} barras." if "SEP" in func_name else "Caso IEEE padrão."
            )

        self.console.print(table)

    def configure_modes(self):
        modes = {
            "debug": Confirm.ask("Ativar modo [bold red]DEBUG[/bold red]?", default=False),
            "benchmark": Confirm.ask("Ativar modo [bold blue]BENCHMARK[/bold blue] (Rastrigin)?", default=False)
        }
        return modes

    def validate_dimension(self, choice):
        """Verifica se o tamanho das variáveis de decisão no params.json é compatível com a função escolhida."""
        func_name = ARRAY_FITNESS_FUNCTIONS[choice].__name__
        meta = self.metadata.get(func_name, {"name": func_name, "dim": -1})
        expected_dim = meta["dim"]

        params_file = current_dir / "params.json"
        try:
            with open(params_file, "r") as f:
                params = json.load(f)
            current_vars = params.get("VARIAVEIS_DE_DECISAO", [])
            if len(current_vars) != expected_dim and expected_dim != -1:
                self.console.print(f"\n[bold red]❌ ERRO DE DIMENSÃO![/bold red]")
                self.console.print(f"A função '{meta['name']}' espera [bold yellow]{expected_dim}[/bold yellow] variáveis de decisão.")
                self.console.print(f"O arquivo params.json atual possui [bold red]{len(current_vars)}[/bold red].")
                if Confirm.ask("Deseja corrigir o tamanho automaticamente (preenchendo com zeros ou cortando)?", default=True):
                    if len(current_vars) > expected_dim:
                        current_vars = current_vars[:expected_dim]
                    else:
                        current_vars.extend([0] * (expected_dim - len(current_vars)))
                    params["VARIAVEIS_DE_DECISAO"] = current_vars
                    params["IND_SIZE"] = expected_dim
                    if params.get("NUM_VAR_DIFERENTES", 0) >= expected_dim:
                        params["NUM_VAR_DIFERENTES"] = max(0, expected_dim - 1)
                    
                    with open(params_file, "w") as f:
                        json.dump(params, f, indent=4)
                    self.console.print("[bold green]Tamanho corrigido com sucesso no params.json![/bold green]")
                    return True
                return False
        except Exception as e:
            self.console.print(f"[bold red]Erro ao ler params.json: {e}[/bold red]")
            return False
        return True

    def run_rce_simulation(self):
        self.console.clear()
        self.display_header()
        self.show_objective_functions_menu()
        
        choice = Prompt.ask(
            "\n[bold yellow]Selecione o ID da função objetivo (ou 'voltar')[/bold yellow]",
            default="0"
        )
        
        if choice.lower() == 'voltar':
            return

        try:
            choice = int(choice)
            if choice < 0 or choice >= len(ARRAY_FITNESS_FUNCTIONS):
                raise ValueError
        except ValueError:
            self.console.print("[bold red]Opção inválida![/bold red]")
            return

        if not self.validate_dimension(choice):
            self.console.print("[bold red]Execução cancelada devido à incompatibilidade de dimensões.[/bold red]")
            Prompt.ask("\nPressione Enter para continuar")
            return

        modes = self.configure_modes()
        
        func_name = ARRAY_FITNESS_FUNCTIONS[choice].__name__
        self.console.print(f"\n[bold green]>>> Iniciando Simulação: {func_name}[/bold green]\n")
        
        try:
            import run
            run.NUMERO = choice
            run.DEBUG_MODE = modes["debug"]
            run.BECHMARKING_MODE = modes["benchmark"]
            run.CLI = False 
            
            run_framework_many_executions(
                function_bechmarking=modes["benchmark"],
                objective_function_index=choice
            )
            
            self.console.print("\n[bold green]✅ Simulação concluída com sucesso![/bold green]")
        except Exception as e:
            self.console.print(f"\n[bold red]❌ Erro durante a simulação: {e}[/bold red]")
        
        Prompt.ask("\nPressione Enter para continuar")

    def run_external_program(self, script_relative_path, work_dir_relative_path):
        work_dir = current_dir / work_dir_relative_path
        script_path = work_dir / script_relative_path
        
        self.console.print(f"\n[bold cyan]Iniciando: {script_relative_path}[/bold cyan] em {work_dir}...")
        
        if not script_path.exists():
            self.console.print(f"[bold red]Erro: Script não encontrado em {script_path}[/bold red]")
            Prompt.ask("\nPressione Enter para continuar")
            return
            
        try:
            subprocess.run([sys.executable, str(script_path)], cwd=str(work_dir))
        except Exception as e:
            self.console.print(f"\n[bold red]❌ Erro ao executar o programa: {e}[/bold red]")
            Prompt.ask("\nPressione Enter para continuar")

    def main_loop(self):
        while True:
            self.console.clear()
            self.display_header()
            self.show_main_menu()
            
            choice = Prompt.ask("\n[bold yellow]Selecione uma opção[/bold yellow]", default="1")
            
            if choice == "1":
                self.run_rce_simulation()
            elif choice == "2":
                self.run_external_program("app.py", "views/Electrical-System-PandaPower")
            elif choice == "3":
                self.run_external_program("PandaPowerCaseManager.py", "models/RedeEletrica/SimulatorSIN45")
            elif choice == "4":
                self.run_external_program("SmartGridSimulator.py", "models/RedeEletrica/SimulatorSIN45")
            elif choice == "0":
                self.console.print("[bold cyan]Encerrando RCE CLI. Até logo![/bold cyan]")
                break
            else:
                self.console.print("[bold red]Opção inválida![/bold red]")
                import time
                time.sleep(1)

if __name__ == "__main__":
    app = RCE_CLI_App()
    try:
        app.main_loop()
    except KeyboardInterrupt:
        app.console.print("\n[bold red]Execução interrompida pelo usuário.[/bold red]")
        sys.exit(0)
