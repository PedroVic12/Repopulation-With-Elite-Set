#!/usr/bin/env python3
"""
Script interativo para criar um projeto Django usando uv no macOS, Ubuntu, Fedora ou Windows (WSL).
Autor: ChatGPT (GPT-5)
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
import re


def run(cmd, cwd=None, check=True):
    """Executa um comando e mostra no terminal."""
    print(f"→ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=check)


def ensure_uv(system_choice):
    """Verifica se o uv está instalado; se não estiver, mostra instruções específicas por sistema."""
    uv_path = shutil.which("uv")
    if uv_path:
        return uv_path

    print("\n⚠️  'uv' não encontrado no sistema.")

    if system_choice == "1":  # macOS
        print("👉 Instale com:")
        print("   brew install uv")
        print("ou:")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
    elif system_choice == "2":  # Ubuntu
        print("👉 Instale com:")
        print("   sudo apt update && sudo apt install curl -y")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
    elif system_choice == "3":  # Fedora
        print("👉 Instale com:")
        print("   sudo dnf install curl -y")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
    elif system_choice == "4":  # Windows (WSL)
        print("👉 No WSL, instale com:")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("   # e depois adicione ao PATH:")
        print('   export PATH="$HOME/.cargo/bin:$PATH"')
    else:
        print("⚠️ Sistema não reconhecido, instale manualmente via:")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")

    sys.exit(1)


def write_gitignore(project_dir: Path):
    gi = project_dir / ".gitignore"
    gi.write_text(
        "# Python\n__pycache__/\n*.py[cod]\n*.sqlite3\n.DS_Store\n"
        "\n# uv venv\n.venv/\n"
        "\n# Django\nstaticfiles/\nmedia/\n.env\n"
    )


def tweak_allowed_hosts(settings_path: Path):
    """Ajusta ALLOWED_HOSTS para incluir localhost, 127.0.0.1 e 0.0.0.0."""
    text = settings_path.read_text(encoding="utf-8")
    new_text = re.sub(
        r"ALLOWED_HOSTS\s*=\s*\[[^\]]*\]",
        "ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']",
        text,
        count=1,
    )
    settings_path.write_text(new_text, encoding="utf-8")


def main():
    print("🐍 Criador de Projeto Django com uv\n")

    print("Selecione seu sistema operacional:")
    print("  [1] macOS")
    print("  [2] Ubuntu / Debian")
    print("  [3] Fedora / Red Hat")
    print("  [4] Windows (WSL)")
    system_choice = input("👉 Digite o número correspondente: ").strip()

    name = input("\n📦 Nome do projeto (ex: meu_site): ").strip()
    if not name:
        print("❌ Nome do projeto é obrigatório.")
        sys.exit(1)

    base_dir = input("📁 Diretório onde criar (Enter = atual): ").strip() or "."

    run_server = input("🚀 Rodar servidor ao final? (s/n): ").strip().lower() == "s"

    project_root = Path(base_dir).expanduser().resolve() / name
    if project_root.exists() and any(project_root.iterdir()):
        print(f"❌ O diretório {project_root} já existe e não está vazio.")
        sys.exit(1)
    project_root.mkdir(parents=True, exist_ok=True)

    # verificar uv
    uv = ensure_uv(system_choice)

    print("\n⚙️ Criando ambiente virtual com uv…")
    run([uv, "venv", ".venv"], cwd=str(project_root))

    venv_bin = project_root / ".venv" / "bin"
    py = venv_bin / "python"
    django_admin = venv_bin / "django-admin"

    print("📦 Instalando Django…")
    run([uv, "pip", "install", "django>=5.0,<6.0"], cwd=str(project_root))

    print("🏗️ Criando projeto Django…")
    run([str(django_admin), "startproject", name, "."], cwd=str(project_root))

    settings_path = project_root / name / "settings.py"
    tweak_allowed_hosts(settings_path)
    write_gitignore(project_root)

    print("🧱 Aplicando migrações iniciais…")
    run([str(py), "manage.py", "migrate"], cwd=str(project_root))

    print("\n✅ Projeto criado com sucesso!\n")
    print(f"📂 Local: {project_root}")
    print("\nPróximos passos:")
    print(f"  cd {project_root}")
    print("  uv run python manage.py runserver\n")

    if run_server:
        print("🚀 Iniciando servidor de desenvolvimento (Ctrl+C para parar)…")
        run(
            [uv, "run", "python", "manage.py", "runserver", "0.0.0.0:8000"],
            cwd=str(project_root),
            check=False,
        )


if __name__ == "__main__":
    main()
