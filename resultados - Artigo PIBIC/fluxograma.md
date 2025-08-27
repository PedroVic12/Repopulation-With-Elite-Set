graph TD

A[Launcher.py - GUI em PySide6] --> B[run.py - Execução principal]

B--> C[Algorítimo Genético com dados de entrada do problema]

C--> D[Salva Resultados e Gráficos na pasta 'output']

D--> E[dashboard_RCE_APP.py - Streamlit]

E--> F[Atualiza Dashboard com base nos arquivos em 'output']
