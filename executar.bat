@echo off
REM Este script executa a sequência de comandos para iniciar a aplicação.

REM Salva o diretório atual
pushd .

REM Navega para o diretório src e executa o primeiro script Python
echo Executando script em src/run_rce_framework.py...
cd src
call python run_rce_framework.py
REM Verifica se a execução do script foi bem sucedida (opcional, mas recomendado)
IF %ERRORLEVEL% NEQ 0 (
    echo Erro ao executar run_rce_framework.py. Saindo.
    popd
    pause
    exit /b %ERRORLEVEL%
)


REM Navega para o diretório DashboardApp e inicia a aplicação Streamlit
echo Iniciando aplicação Streamlit em DashboardApp/dashboard_rce_app_v9.py...
pushd DashboardApp
REM Usa 'start cmd /k' para abrir uma nova janela de console para o Streamlit
REM '/k' mantém a janela aberta após a execução do comando (útil para ver logs)
start cmd /k streamlit run dashboard_rce_app_v9.py
popd

echo Script de inicialização concluído na janela principal.
echo A janela do Streamlit foi aberta separadamente.

REM Adiciona um pause para manter esta janela do terminal aberta
REM Remova o comando 'exit /b 0' se quiser que a janela só feche manualmente
pause

exit /b 0