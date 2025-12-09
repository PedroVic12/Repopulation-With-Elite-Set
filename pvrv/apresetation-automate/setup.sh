#!/bin/bash

# Criar estrutura do projeto
mkdir -p gesture-presentation
cd gesture-presentation

# Criar pastas necessárias
mkdir -p apresentacao-imgs
mkdir -p input

# Inicializar projeto UV
uv venv
source .venv/bin/activate

# instala depdencias com pip
#uv pip install opencv-python mediapipe PyMuPDF fitz pillow python-pptx 




# Criar pyproject.toml
cat > pyproject.toml << 'EOF'
[project]
name = "gesture-presentation"
version = "0.1.0"
description = "Controle de apresentações por gestos usando MediaPipe"
requires-python = ">=3.9,<3.12"
dependencies = [
    "opencv-python>=4.8.0",
    "mediapipe>=0.10.21",
    "PyMuPDF>=1.23.0",
    "Pillow>=10.0.0",
    "python-pptx>=0.6.21",
    "fitz",
]

[tool.uv]
dev-dependencies = []
EOF


# Instalar dependências
uv pip install -e .

echo "✅ Projeto configurado com sucesso!"
echo "📁 Coloque seus arquivos PDF/PPT na pasta 'input/'"
echo "🚀 Execute: uv run python main.py"