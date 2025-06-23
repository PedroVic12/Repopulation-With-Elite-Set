@echo off
REM Este script executa a sequência de comandos para iniciar a aplicação.

REM Salva o diretório atual
pushd .

REM Navega para o diretório src e executa o primeiro script Python
cd src



echo Inicio do Programa...
REM call python run_framework.py

REM Navega para o diretório DashboardApp e inicia a aplicação Streamlit
echo Iniciando aplicação Streamlit em DashboardApp/dashboard_rce_app_v9.py...
cd DashboardApp

@echo Instalando as bibliotecas python necessarias...

@REM pip install -r requirements.txt --break-system-packages --no-cache-dir --disable-pip-version-check --quiet

timeout /t 1 >nul
ping -n 2 127.0.0.1 >nul

echo Instalacao de bibliotecas necessarias concluida!

call cls

REM Executa o Streamlit no mesmo terminal
streamlit run dashboard_rce_app_v9.py

REM Volta para o diretório anterior
cd ..

REM Volta para o diretório original
popd

pause
exit /b 0
