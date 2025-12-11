"""
CLI.py - Program Launcher with Rich TUI

A simple CLI launcher that displays a menu of Python programs to run.
Each program can have its own working directory, main script, and requirements.txt.

Programs are defined in a dict config. To add a new program, add an entry to PROGRAMS dict.

UI components are imported from run/CLI_MENU_UI.py.

Usage:
    python CLI.py
    # or via launcher scripts (run_cli.bat / run_cli.sh)

Environment variables (optional):
    PROJECTS_ROOT: base path for all projects (defaults to script dir)
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import Dict

# Import UI components from run/CLI_MENU_UI.py
"""
CLI_MENU_UI.py - Rich TUI Components for CLI Launcher

Provides reusable UI components for the CLI menu:
- Header display
- Menu rendering
- Program selection
- Status messages
"""

from typing import Dict, List, Tuple, Optional
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.style import Style
except ImportError:
    raise ImportError(
        "A biblioteca 'rich' é necessária. Instale com: pip install rich"
    )

console = Console()


class CLIMenu:
    """Rich TUI menu handler for program selection."""

    def __init__(self, programs: Dict[str, Dict[str, str]], projects_root: Path):
        """
        Initialize menu with programs config.

        Args:
            programs: Dict of program configs
            projects_root: Base path for all projects
        """
        self.programs = programs
        self.projects_root = projects_root

    def display_header(self):
        """Display welcome header with project info."""
        console.clear()
        console.print(
            Panel(
                "[bold cyan]🚀 Program Launcher CLI[/bold cyan]\n\n"
                f"[dim]Projects Root: {self.projects_root}[/dim]",
                border_style="blue",
                padding=(1, 2),
            )
        )

    def display_menu(self) -> Optional[str]:
        """
        Display menu and get user choice.

        Returns:
            Selected program key or None if user chooses to exit.
        """
        programs_list: List[Tuple[str, str]] = [
            (key, prog["name"]) for key, prog in self.programs.items()
        ]

        console.print("\n[bold]Available Programs:[/bold]\n")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ID", style="yellow")
        table.add_column("Program", style="white")

        for i, (key, name) in enumerate(programs_list, 1):
            table.add_row(str(i), name)

        table.add_row(str(len(programs_list) + 1), "[red]Exit[/red]")
        console.print(table)

        choices = [str(i) for i in range(1, len(programs_list) + 2)]
        choice = Prompt.ask(
            "\n[bold]Select a program[/bold]", choices=choices, default="1"
        )

        choice_int = int(choice)
        if choice_int == len(programs_list) + 1:
            return None

        selected_key = programs_list[choice_int - 1][0]
        return selected_key

    def display_program_info(self, program_key: str, work_dir: Path, script: str):
        """Display information about the selected program."""
        program = self.programs[program_key]
        console.print(f"\n[bold cyan]📂 Working Directory: {work_dir}[/bold cyan]")
        console.print(f"[bold cyan]📄 Script: {script}[/bold cyan]")

    def display_startup_message(self, program_name: str):
        """Display startup message before running program."""
        console.print(
            f"\n[bold green]▶️  Starting {program_name}...[/bold green]\n"
        )

    def display_success_message(self, program_name: str):
        """Display success message after program completes."""
        console.print(f"\n[green]✓ {program_name} finished successfully.[/green]")

    def display_error_message(self, program_name: str, error: str = ""):
        """Display error message."""
        msg = f"\n[red]✗ {program_name} encountered an error"
        if error:
            msg += f": {error}"
        else:
            msg += " or was interrupted."
        console.print(msg + "[/red]")

    def display_script_not_found(self, script_path: Path):
        """Display message when script is not found."""
        console.print(f"[red]✗ Script not found: {script_path}[/red]")

    def display_requirements_installing(self, requirements_file: str):
        """Display message when installing requirements."""
        console.print(
            f"\n[cyan]📦 Installing requirements from {requirements_file}...[/cyan]"
        )

    def display_requirements_not_found(self, req_path: Path):
        """Display message when requirements.txt is not found."""
        console.print(f"[yellow]⚠️  Requirements file not found: {req_path}[/yellow]")

    def display_requirements_success(self):
        """Display success message for requirements installation."""
        console.print("[green]✓ Requirements installed successfully.[/green]")

    def display_requirements_failed(self) -> bool:
        """Display failure message and ask to continue anyway."""
        console.print("[red]✗ Failed to install requirements.[/red]")
        return Confirm.ask("Continue anyway?", default=True)

    def display_goodbye(self):
        """Display goodbye message."""
        console.print("\n[bold cyan]👋 Goodbye![/bold cyan]\n")

    def display_interrupted(self):
        """Display interrupted message."""
        console.print("\n\n[yellow]Interrupted by user.[/yellow]")

    def display_python_not_found(self):
        """Display message when Python is not found."""
        console.print("[red]✗ Python is not installed or not in PATH.[/red]")

    def display_cli_py_not_found(self, script_dir: Path):
        """Display message when CLI.py is not found."""
        console.print(f"[red]✗ CLI.py not found in {script_dir}[/red]")

    def display_rich_installing(self):
        """Display message when installing rich package."""
        console.print("[INFO] Installing required package 'rich'...")

    def ask_run_another(self) -> bool:
        """Ask if user wants to run another program."""
        return Confirm.ask("\n[bold]Run another program?[/bold]", default=True)

    def display_program_selected(self, program_name: str):
        """Display program selection confirmation."""
        console.print(f"\n[bold]Selected: {program_name}[/bold]")

    def display_interrupted(self):
        """Display message when CLI is interrupted by user."""
        console.print("\n\n[yellow]Interrupted by user.[/yellow]")


# ============================================================================
# CONFIG: Programs Dictionary
# ============================================================================
# Each program entry:
# {
#     "name": Display name in menu,
#     "script": Main Python script to run (relative to work_dir),
#     "work_dir": Working directory (relative to PROJECTS_ROOT, or absolute),
#     "requirements": Path to requirements.txt (relative to work_dir, or None if not needed)
# }


# ============================================================================
# FUNCTIONS
# ============================================================================


def resolve_path(PROJECTS_ROOT: Path, relative_or_absolute: str) -> Path:
    """Resolve a path relative to PROJECTS_ROOT or as absolute."""
    p = Path(relative_or_absolute)
    if p.is_absolute():
        return p
    return PROJECTS_ROOT / p


def install_requirements(work_dir: Path, requirements_file: str, menu: CLIMenu) -> bool:
    """Install requirements if requirements.txt exists."""
    req_path = work_dir / requirements_file
    if not req_path.exists():
        menu.display_requirements_not_found(req_path)
        return True  # continue anyway

    menu.display_requirements_installing(requirements_file)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_path)],
            cwd=str(work_dir),
            check=False,
        )
        if result.returncode == 0:
            menu.display_requirements_success()
            return True
        else:
            return menu.display_requirements_failed()
    except Exception as e:
        menu.display_error_message("Requirements installation", str(e))
        return False


def run_program(PROGRAMS,PROJECTS_ROOT: Path,program_key: str, menu: CLIMenu) -> bool:
    """Run the selected program."""
    program = PROGRAMS[program_key]
    work_dir = resolve_path(PROJECTS_ROOT,program["work_dir"])
    script = program["script"]
    script_path = work_dir / script

    menu.display_program_info(program_key, work_dir, script)

    # Verify script exists
    if not script_path.exists():
        menu.display_script_not_found(script_path)
        return False

    # Install requirements if specified
    requirements = program.get("requirements")
    if requirements:
        if not install_requirements(work_dir, requirements, menu):
            return False

    # Run the program
    menu.display_startup_message(program["name"])
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(work_dir),
            check=False,
        )
        return result.returncode == 0
    except Exception as e:
        menu.display_error_message(program["name"], str(e))
        return False

#===============================================================
