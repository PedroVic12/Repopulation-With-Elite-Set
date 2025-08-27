@echo off
cls
echo =================================================
echo  Instalador do Repopulation-With-Elite-Set
echo =================================================
echo.

REM Verifica se o Python esta instalado
echo Verificando a instalacao do Python...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Python nao foi encontrado no seu sistema.
    echo Por favor, instale o Python a partir de https://www.python.org/downloads/
    echo Certifique-se de marcar a opcao "Add Python to PATH" durante a instalacao.
    echo.
    pause
    exit /b 1
)
echo Python encontrado!
echo.

REM Verifica se o PySide6 esta instalado
echo Verificando a biblioteca QT6...
pip show PySide6 >nul 2>nul
if %errorlevel% neq 0 (
    echo PySide6 nao encontrado. Tentando instalar...
    echo.
    python -m pip install PySide6 --break-system-packages
    if %errorlevel% neq 0 (
        echo.
        echo [ERRO] Falha ao instalar o PySide6. Verifique sua conexao com a internet.
        pause
        exit /b 1
    )
    echo QT6 instalado com sucesso!
) else (
    echo QT6 ja esta instalado.
)
echo.

echo Iniciando o programa...
cd src
python instalador.py

