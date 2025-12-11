@echo off
REM run_launcher.bat - Windows Batch Script to Launch the Program Launcher

SETLOCAL ENABLEDELAYEDEXPANSION

REM Change to the script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ ERRO: Python nao foi encontrado no PATH
    echo.
    echo Por favor, instale Python ou adicione-o ao PATH do sistema.
    echo.
    pause
    exit /b 1
)

REM Set UTF-8 console encoding for proper display of unicode characters
chcp 65001 >nul 2>&1

REM Display header
echo.
echo ================================================================================
echo  ⚡ GERENCIADOR DE PROGRAMAS - POWER SYSTEM DASHBOARD
echo ================================================================================
echo.

REM Run the launcher
python launcher.py

REM Capture exit code
set EXIT_CODE=%errorlevel%

REM Display footer
echo.
echo ================================================================================
echo  Launcher finalizado com código: !EXIT_CODE!
echo ================================================================================
echo.

exit /b !EXIT_CODE!
