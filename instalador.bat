@echo off
REM Este script executa a sequência de comandos para iniciar a aplicação.

REM Salva o diretório atual
pushd .

REM Navega para o diretório src e executa o primeiro script Python
echo Executando script em src/run_rce_framework.py...
cd src

echo Instalando...

call pip install -r requirements.txt --break-system-packages 

echo Instalação concluída. 

