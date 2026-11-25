#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================="
echo "   COMPILANDO E EXECUTANDO - Serene & Performance Suite    "
echo "========================================================="

# Garante uma compilação limpa removendo o cache se mudar de SO
mkdir -p build && cd build

# Identifica se está rodando no Windows (Git Bash/MINGW) ou Linux
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    echo "[!] Detectado ambiente Windows. Usando MinGW Makefiles..."
    cmake -G "MinGW Makefiles" ..
    # Comando universal do CMake para compilar usando todos os núcleos do processador
    cmake --build . --parallel $(nproc 2>/dev/null || echo 4)
    EXE_NAME="./SereneHybridCore.exe"
else
    echo "[!] Detectado ambiente Linux."
    cmake ..
    cmake --build . --parallel $(nproc)
    EXE_NAME="./SereneHybridCore"
fi

echo "[✓] Compilação concluída com sucesso! Iniciando aplicação..."
echo "---------------------------------------------------------"

if [ -f "$EXE_NAME" ]; then
    $EXE_NAME
else
    echo "[X] Erro: Executável $EXE_NAME não encontrado no diretório de build."
    exit 1
fi
