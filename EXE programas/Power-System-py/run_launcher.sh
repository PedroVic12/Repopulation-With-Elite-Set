#!/bin/bash
# run_launcher.sh - Unix/Linux/Mac Shell Script to Launch the Program Launcher

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR" || exit 1

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo ""
        echo "❌ ERRO: Python não foi encontrado"
        echo ""
        echo "Por favor, instale Python 3 usando:"
        echo "  Ubuntu/Debian: sudo apt-get install python3"
        echo "  macOS: brew install python3"
        echo "  Ou visite: https://www.python.org/downloads/"
        echo ""
        exit 1
    fi
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

# Display header
echo ""
echo "================================================================================"
echo "  ⚡ GERENCIADOR DE PROGRAMAS - POWER SYSTEM DASHBOARD"
echo "================================================================================"
echo ""

# Run the launcher
$PYTHON_CMD launcher.py

# Capture exit code
EXIT_CODE=$?

# Display footer
echo ""
echo "================================================================================"
echo "  Launcher finalizado com código: $EXIT_CODE"
echo "================================================================================"
echo ""

exit $EXIT_CODE
