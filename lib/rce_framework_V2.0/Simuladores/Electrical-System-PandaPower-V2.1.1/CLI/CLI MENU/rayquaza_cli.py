import sys
import os
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from templates import TEMPLATES

# Configuração Rich
console = Console()


def generate(tech, option_idx, name):
    try:
        type_name, template = TEMPLATES[tech][option_idx]
        content = template.format(name=name)
        ext = "py" if tech == "pyside6" else "html"
        filename = f"{name.lower()}_{type_name.lower()}.{ext}"
        
        # Preview
        console.print(Panel(f"[bold yellow]PREVIEW:[/bold yellow] {filename}", border_style="yellow"))
        syntax = Syntax(content, "python" if ext == "py" else "html", theme="monokai")
        console.print(syntax)
        
        if Confirm.ask(f"Salvar {filename}?", default=True):
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            console.print("[bold green]✔ Criado![/bold green]")
    except KeyError:
        console.print("[bold red]Opção inválida![/bold red]")

def show_interactive():
    console.print(Panel("[bold cyan]RAYQUAZA APP GENERATOR[/bold cyan]"))
    tech = Prompt.ask("Escolha a Engine", choices=["pyside6", "react"])
    
    table = Table(title=f"Opções {tech.upper()}")
    table.add_column("ID", style="cyan")
    table.add_column("Template")
    
    for idx, (t_name, _) in TEMPLATES[tech].items():
        table.add_row(idx, t_name)
    console.print(table)
    
    idx = Prompt.ask("Escolha o número do template")
    name = Prompt.ask("Nome do Objeto (ex: User, Main)")
    generate(tech, idx, name)

def main():
    # Suporte a argumentos CLI: python rayquaza.py create User:Window
    if len(sys.argv) > 2 and sys.argv[1] == "create":
        try:
            name, kind = sys.argv[2].split(":")
            # Mapeia nome do tipo para o índice do template
            tech = "pyside6" # default ou lógica de detecção
            idx = next(k for k, v in TEMPLATES[tech].items() if v[0].lower() == kind.lower())
            generate(tech, idx, name)
        except Exception as e:
            console.print(f"[red]Erro nos argumentos. Use Nome:Tipo (ex: User:Window)[/red]")
    else:
        show_interactive()

if __name__ == "__main__":
    main()
