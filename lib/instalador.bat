@echo off
REM Este script executa a sequência de comandos para iniciar a aplicação.

REM Salva o diretório atual
pushd .

REM Navega para o diretório src e executa o primeiro script Python
cd src/DashboardApp

echo Instalando usando pip do Python...

call pip install -r requirements.txt --break-system-packages 

echo Instalação concluída. 

cd ..

pwd

echo Iniciando o laucher desktop...
