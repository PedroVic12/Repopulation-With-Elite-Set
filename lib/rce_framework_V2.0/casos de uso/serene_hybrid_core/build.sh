#!/usr/bin/env bash
set -e
echo "[+] Compilando Serene Hybrid Core..."
mkdir -p build && cd build
cmake ..
make -j$(nproc)
echo "[✓] Compilação concluída com sucesso! Para rodar: ./build/SereneHybridCore"
