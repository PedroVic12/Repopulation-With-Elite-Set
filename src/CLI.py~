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
try:
    #sys.path.insert(0, str(Path(__file__).parent / "run"))
    from run.CLI_MENU_UI import CLIMenu

except ImportError as e:
    print(f"Erro: Não foi possível importar CLI_MENU_UI.py: {e}")
    print("Certifique-se de que o arquivo run/CLI_MENU_UI.py existe.")
    sys.exit(1)
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

PROJECTS_ROOT = Path(os.getenv("PROJECTS_ROOT", Path(__file__).parent))

PROGRAMS: Dict[str, Dict[str, str]] = {
    "desktop_dashboard": {
        "name": "Desktop Dashboard (SP Atividades)",
        "script": "desktop_Dashboard_app.py",
        "work_dir": "src/ScrapperPDF",
        "requirements": "requirements.txt",
    },
    "palkia_gui": {
        "name": "Palkia PDF Extractor GUI",
        "script": "Palkia_GUI.py",
        "work_dir": "src/ScrapperPDF",
        "requirements": "requirements.txt",
    },
    "moderno_template": {
        "name": "Moderno Desktop UI Template",
        "script": "app_template_desktop.py",
        "work_dir": "src/NexusPy/Pyside6 - Desktop/pyside6_tab_app",
        "requirements": None,  # no requirements.txt needed
    },
    "organizador": {
        "name": "File Organizer",
        "script": "organizador_arquivos.py",
        "work_dir": ".",
        "requirements": None,
    },
}


# ============================================================================
# FUNCTIONS
# ============================================================================


def resolve_path(relative_or_absolute: str) -> Path:
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


def run_program(program_key: str, menu: CLIMenu) -> bool:
    """Run the selected program."""
    program = PROGRAMS[program_key]
    work_dir = resolve_path(program["work_dir"])
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


def main():
    """Main CLI loop."""
    menu = CLIMenu(PROGRAMS, PROJECTS_ROOT)

    while True:
        menu.display_header()
        selected_key = menu.display_menu()

        if selected_key is None:
            menu.display_goodbye()
            sys.exit(0)

        program = PROGRAMS[selected_key]
        menu.display_program_selected(program["name"])

        if run_program(selected_key, menu):
            menu.display_success_message(program["name"])
        else:
            menu.display_error_message(program["name"])

        if not menu.ask_run_another():
            menu.display_goodbye()
            sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        menu = CLIMenu(PROGRAMS, PROJECTS_ROOT)
        menu.display_interrupted()
        sys.exit(0)

