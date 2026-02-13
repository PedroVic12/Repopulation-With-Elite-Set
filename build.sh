#!/bin/bash

# Nome do executável
NAME="app"

# Diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# Navegar para o diretório do projeto
cd "$PROJECT_DIR"

# Criar/ativar venv com uv
echo "Configurando ambiente virtual com uv..."
uv venv

# Ativar o ambiente virtual
source .venv/bin/activate

# Instalar PySide6 isoladamente para depuração
echo "Attempting to install PySide6 independently for debugging..."
uv pip install PySide6
if [ $? -ne 0 ]; then
    echo "Error: Failed to install PySide6 independently. Please check compatibility with Python 3.14.2."
    exit 1
fi
echo "PySide6 independent installation attempt complete."

# Instalar dependências se existir requirements.txt (temporariamente desativado para testar PySide6)
if [ -f "requirements.txt" ]; then
    echo "Instalando dependências..."
    uv pip install -r requirements.txt
fi

# Verificar a instalação do PySide6
echo "Verifying PySide6 installation..."
python -c "import PySide6; print('PySide6 imported successfully.')"
if [ $? -ne 0 ]; then
    echo "Error: PySide6 not importable in venv. Please ensure it's installed."
    exit 1
fi
echo "PySide6 verification complete!!!"

# Instalar PyInstaller
echo "Instalando PyInstaller..."
uv pip install pyinstaller

# Gerar o executável
echo "Gerando executável com PyInstaller..."
pyinstaller "$NAME.py" \
    --onefile \
    --noconsole \
    --clean \
    --add-data "src:src" \
    --collect-all PySide6

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