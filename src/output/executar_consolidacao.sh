#!/bin/bash

echo "=== INSTALADOR E EXECUTOR DE CONSOLIDAÇÃO ==="
echo ""

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado. Por favor, instale o Python 3.7+ primeiro."
    exit 1
fi

echo "✅ Python3 encontrado: $(python3 --version)"

# Verificar se pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 não encontrado. Tentando instalar..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-pip
    elif command -v pacman &> /dev/null; then
        sudo pacman -S python-pip
    else
        echo "❌ Não foi possível instalar o pip automaticamente. Instale manualmente."
        exit 1
    fi
fi

echo "✅ pip3 encontrado: $(pip3 --version)"

# Instalar dependências
echo ""
echo "📦 Instalando dependências..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependências instaladas com sucesso!"
else
    echo "❌ Erro ao instalar dependências. Tentando instalar individualmente..."
    pip3 install pandas openpyxl
fi

# Executar consolidação
echo ""
echo "🚀 Executando consolidação..."
python3 consolidar_resultados.py

echo ""
echo "=== CONCLUÍDO ===" 