#!/bin/bash

# Nome do executável
NAME="run"

# Diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Navegar para o diretório do projeto
cd "$PROJECT_DIR"

# Criar/ativar venv com uv
echo "Configurando ambiente virtual com uv..."
uv venv

# Ativar o ambiente virtual
source .venv/bin/activate

# Instalar dependências se existir requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Instalando dependências..."
    uv pip install -r requirements.txt
fi

# Instalar PyInstaller
echo "Instalando PyInstaller..."
uv pip install pyinstaller

# Gerar o executável
echo "Gerando executável com PyInstaller..."
pyinstaller "$NAME.py" \
    --onefile \
    --noconsole \
    --clean \
    --add-data "app/data:app/data"

# Mover o executável
if [ -f "dist/$NAME" ]; then
    mv "dist/$NAME" "$SCRIPT_DIR/"
    echo "Executável movido para $SCRIPT_DIR/$NAME"
else
    echo "Erro: Executável não foi gerado!"
    exit 1
fi

# Limpar arquivos temporários
rm -rf build dist
rm -f "$NAME.spec"

# Desativar ambiente virtual
deactivate

# Voltar para o diretório do script
cd "$SCRIPT_DIR"

echo "Processo concluído!"