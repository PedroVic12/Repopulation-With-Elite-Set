# Navegue até sua pasta (repare nas barras e aspas obrigatórias para o Git Bash)
cd "/c/Users/Pedro Victor R V/Documents/programas"

# Crie um script de teste chamado script.sh
cat << 'EOF' > script.sh
#!/bin/bash
echo "=== 1. TESTANDO CMAKE NO GIT BASH ==="
cmake --version

echo -e "\n=== 2. RODANDO COMANDO DO POWERSHELL ==="
powershell.exe -Command "Get-Date"

echo -e "\n=== 3. EXECUTANDO COMANDO COM MÓDULO DO POWERSHELL ==="
powershell.exe -Command "Write-Output 'Módulos e PowerShell integrados no Git Bash!'"
EOF

# Execute o script que você acabou de criar
sh script.sh
