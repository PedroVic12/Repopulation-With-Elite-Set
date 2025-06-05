@echo off
REM Este script executa a sequência de comandos para iniciar a aplicação.

REM Salva o diretório atual
pushd .

REM Navega para o diretório src e executa o primeiro script Python
cd src

echo Instalando as biblotecas python necessarias...

REM pip install -r requirements.txt --break-system-packages --no-cache-dir --disable-pip-version-check --quiet


@echo Instalacão de bibliotecas necessarias concluida!

call cls 

echo Inicio do Programa...
@REM echo Executando script em src/run_rce_framework.py...
@REM call python run_framework.py


@REM REM Verifica se a execução do script foi bem sucedida (opcional, mas recomendado)
@REM IF %ERRORLEVEL% NEQ 0 (
@REM     echo Erro ao executar run_rce_framework.py. Saindo.
@REM     popd
@REM     pause
@REM     exit /b %ERRORLEVEL%
@REM )


REM Navega para o diretório DashboardApp e inicia a aplicação Streamlit
echo Iniciando aplicação Streamlit em DashboardApp/dashboard_rce_app_v9.py...
pushd DashboardApp


REM Usa 'start cmd /k' para abrir uma nova janela de console para o Streamlit
REM '/k' mantém a janela aberta após a execução do comando (útil para ver logs)
start cmd /k streamlit run dashboard_rce_app_v9.py
popd

echo A janela do Streamlit foi aberta separadamente.

REM Remova o comando 'exit /b 0' se quiser que a janela só feche manualmente
pause

exit /b 0
