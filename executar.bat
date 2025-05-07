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



REM Salva o diretório atual novamente (opcional, se pushd/popd forem aninhados)
pushd .

REM Navega para o diretório DashboardApp e inicia a aplicação Streamlit
echo Iniciando aplicação Streamlit em DashboardApp/dashboard_rce_app_v9.py...
cd DashboardApp
REM Usa 'start cmd /k' para abrir uma nova janela de console para o Streamlit
REM '/k' mantém a janela aberta após a execução do comando (útil para ver logs)
REM Se quiser que a janela feche assim que o streamlit iniciar, use '/c' no lugar de '/k'
start cmd /k streamlit run dashboard_rce_app_v9.py

REM Retorna ao diretório original (este popd pode ser alcançado se o start não bloquear)
popd

echo Script de inicialização concluído (a janela do Streamlit deve estar aberta).
exit /b 0