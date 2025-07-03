#!/bin/bash

# run.sh
# Script para iniciar o backend e o frontend da aplicação de estoque.

echo "Iniciando o ambiente de inovação..."

# Função para limpar os processos em segundo plano ao sair (Ctrl+C)
cleanup() {
    echo "Encerrando processos..."
    # Mata o processo do backend que salvamos o PID
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID
    fi
    # O Reflex cuida de si mesmo, mas podemos ser explícitos se necessário
    # pkill -f "reflex run"
    echo "Processos encerrados."
    exit
}

# 'trap' captura o sinal de interrupção (Ctrl+C) e chama a função cleanup
trap cleanup INT

# 1. Inicia o Backend (API Flask) em segundo plano
echo "Iniciando o backend (Flask API)..."
python backend.py &
# Salva o Process ID (PID) do último comando em segundo plano
BACKEND_PID=$!
echo "Backend rodando com PID: $BACKEND_PID"

# Dá um tempo para o servidor Flask iniciar completamente
sleep 3

# 2. Inicializa o ambiente do Reflex (só precisa rodar uma vez)
if [ ! -d ".web" ]; then
    echo "Inicializando o ambiente do Reflex..."
    reflex init
fi

# 3. Inicia o Frontend (Reflex) em primeiro plano
echo "Iniciando o frontend (Reflex)..."
# O frontend ficará rodando aqui, mantendo o script ativo.
# Quando você pressionar Ctrl+C, o 'trap' será acionado.
reflex run

# O trap cuidará da limpeza quando o script terminar