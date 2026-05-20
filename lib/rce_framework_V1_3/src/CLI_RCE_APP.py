
# -*- coding: utf-8 -*-
"""
CLI_RCE_APP.py - Professional CLI for RCE Framework using Rich.
Implemented with OOP for the UFF and ONS presentation.
"""

import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import print as rprint
from rich.layout import Layout
from rich.live import Layout

# Ajustar path para encontrar os modelos
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

from run import run_framework_many_executions, ARRAY_FITNESS_FUNCTIONS
from global_settings import OBJECTIVE_FUNCTIONS_METADATA

class RCE_CLI_App:
    def __init__(self):
        self.console = Console()
        self.metadata = OBJECTIVE_FUNCTIONS_METADATA

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

    def show_menu(self):
        table = Table(title="Funções Objetivo Disponíveis", expand=True)
        table.add_column("ID", justify="center", style="cyan", no_wrap=True)
        table.add_column("Nome da Função", style="magenta")
        table.add_column("Dimensão (Variáveis)", justify="center", style="green")
        table.add_column("Descrição", style="white")

        # Mapeamento do ARRAY_FITNESS_FUNCTIONS do run.py
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

    def get_user_choice(self):
        choice = Prompt.ask(
            "\n[bold yellow]Selecione o ID da função objetivo[/bold yellow]",
            choices=[str(i) for i in range(len(ARRAY_FITNESS_FUNCTIONS))],
            default="0"
        )
        return int(choice)

    def configure_modes(self):
        modes = {
            "debug": Confirm.ask("Ativar modo [bold red]DEBUG[/bold red]?", default=False),
            "benchmark": Confirm.ask("Ativar modo [bold blue]BENCHMARK[/bold blue] (Rastrigin)?", default=False)
        }
        return modes

    def run_simulation(self, choice, modes):
        func_name = ARRAY_FITNESS_FUNCTIONS[choice].__name__
        self.console.print(f"\n[bold green]>>> Iniciando Simulação: {func_name}[/bold green]\n")
        
        try:
            # Importamos o run aqui para garantir que possamos injetar as flags
            import run
            run.NUMERO = choice
            run.DEBUG_MODE = modes["debug"]
            run.BECHMARKING_MODE = modes["benchmark"]
            run.CLI = False # Desativa o input manual interno do run.py, pois já pegamos aqui
            
            run_framework_many_executions(
                function_bechmarking=modes["benchmark"],
                objective_function_index=choice
            )
            
            self.console.print("\n[bold green]✅ Simulação concluída com sucesso![/bold green]")
        except Exception as e:
            self.console.print(f"\n[bold red]❌ Erro durante a simulação: {e}[/bold red]")

    def main_loop(self):
        while True:
            self.console.clear()
            self.display_header()
            self.show_menu()
            
            choice = self.get_user_choice()
            modes = self.configure_modes()
            
            self.run_simulation(choice, modes)
            
            if not Confirm.ask("\nDeseja realizar outra simulação?"):
                self.console.print("[bold cyan]Encerrando RCE CLI. Até logo![/bold cyan]")
                break

if __name__ == "__main__":
    app = RCE_CLI_App()
    app.main_loop()
