#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================="
echo "   COMPILANDO E EXECUTANDO - Bem vindo a nova era digital com Veras Tecnologia!    "
echo "========================================================="

mkdir -p build && cd build
cmake ..
make -j$(nproc)

echo "[✓] Compilação concluída com sucesso! Iniciando aplicação..."
echo "---------------------------------------------------------"
./SereneHybridCore
