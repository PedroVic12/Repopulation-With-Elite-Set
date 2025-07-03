# run_rce_prefect.py
import os
import json
import pathlib
import subprocess
from datetime import datetime

import pandas as pd
from prefect import task, flow

# Importe suas classes e funções do framework RCE
from AlgEvolutivoRCE.Setup import Setup
from AlgEvolutivoRCE.alg_evolutivo_rce import AlgoritimoEvolutivoRCE
from utils.functions_fitness.functions_benchmarking import funcao_objetivo_IEEE14
from config import entrada_de_dados, format_elapsed_time, options_main_file

BASE_DIR = pathlib.Path(__file__).resolve().parent

# --- ETAPA 1: TRANSFORMAR A LÓGICA EM TAREFAS (TASKS) DO PREFECT ---

@task(log_prints=True)
def carregar_parametros_json(file_path: str) -> dict:
    """Tarefa para carregar um arquivo de configuração JSON."""
    print(f"Carregando parâmetros de: {file_path}")
    with open(file_path, "r") as file:
        params = json.load(file)
    return params

@task(log_prints=True)
def inicializar_setup(params: dict, fitness_function, dados: dict) -> Setup:
    """Tarefa para criar e configurar o objeto Setup."""
    print("Inicializando o objeto Setup com os parâmetros...")
    tamanho_hash = (dados["num_contingencias"] * dados["num_carregamentos"] * (2**dados["num_desligamentos"]))
    setup = Setup(params, fitness_function=fitness_function, tamanho_hash=tamanho_hash)
    
    # Lógica de consulta à hash table foi movida para cá
    hash_file = "hash_table.xlsx"
    if os.path.exists(hash_file):
        print(f"Arquivo {hash_file} encontrado. Tentando carregar cache...")
        try:
            hash_excel = pd.read_excel(hash_file)
            if not hash_excel.empty:
                setup.tabela_hash = hash_excel['Fitness'].to_dict()
                print(f"Cache da hash table carregado com {len(setup.tabela_hash)} cenários.")
        except Exception as e:
            print(f"Erro ao ler {hash_file}: {e}")
    else:
        print(f"Arquivo {hash_file} não encontrado. Iniciando com hash table vazia.")
        
    return setup

@task(log_prints=True)
def executar_algoritmo_rce(setup: Setup, debug: bool = True) -> tuple:
    """Tarefa que executa o coração do seu algoritmo."""
    print("Iniciando a execução do Algoritmo Evolutivo RCE...")
    alg = AlgoritimoEvolutivoRCE(setup, DEBUG=debug)
    pop, logbook, best_variables = alg.run(RCE=True)
    print("Execução do algoritmo concluída.")
    return alg, pop, logbook, best_variables

@task(log_prints=True)
def salvar_e_processar_resultados(alg, logbook, pop, best_variables, setup, start_time):
    """Tarefa para processar e salvar os outputs da execução."""
    print("\n--- Processando Resultados Finais ---")
    print(f"Melhores variáveis encontradas: {best_variables}")

    # Salva a hash table atualizada
    hash_df = pd.DataFrame(list(setup.tabela_hash.items()), columns=['Hash', 'Fitness'])
    hash_df.sort_values(by='Fitness', ascending=False, inplace=True)
    hash_df.to_excel("hash_table.xlsx", index=False)
    print("hash_table.xlsx foi salvo/atualizado.")

    # Gera visualizações (se necessário)
    # x, y, z, fig = alg.dashboard.visualize(logbook, pop)
    # fig.write_image("resultado_visual.png") # Exemplo de como salvar a figura
    # print("Gráfico de visualização salvo.")

    print(f"Execuções da função objetivo: {setup.objectiveruns}")
    print(f"Leituras da hash table: {setup.hashtablereads}")

    end_time = datetime.now()
    elapsed = end_time - start_time
    formatted_time = format_elapsed_time(elapsed)
    print(f"Tempo total de execução: {formatted_time}")
    
    return {"melhores_variaveis": best_variables, "tempo_execucao": formatted_time}

# --- ETAPA 2: CRIAR O FLUXO (FLOW) QUE ORQUESTRA AS TAREFAS ---

@flow(name="Execucao Unica RCE", log_prints=True)
def rce_execucao_unica_flow():
    """Flow que orquestra uma única execução completa do seu framework."""
    start_time = datetime.now()
    
    # 1. Carregar parâmetros e dados de entrada
    params = carregar_parametros_json(f"{BASE_DIR}/params.json")
    dados = entrada_de_dados()
    
    # 2. Inicializar o setup
    setup_obj = inicializar_setup(params, fitness_function=funcao_objetivo_IEEE14, dados=dados)
    
    # 3. Executar o algoritmo
    alg_obj, pop, logbook, best_vars = executar_algoritmo_rce(setup_obj, debug=True)
    
    # 4. Salvar os resultados
    resultado_final = salvar_e_processar_resultados(alg_obj, logbook, pop, best_vars, setup_obj, start_time)
    
    return resultado_final

@flow(name="Multiplas Execucoes RCE", log_prints=True)
def rce_multiplas_execucoes_flow(num_execucoes: int = 3):
    """Flow que chama o flow de execução única várias vezes."""
    print(f"Iniciando fluxo com {num_execucoes} execuções em sequência.")
    resultados = []
    for i in range(num_execucoes):
        print(f"\n--- INICIANDO EXECUÇÃO {i+1} DE {num_execucoes} ---")
        # Chama o flow de execução única como um sub-flow
        resultado = rce_execucao_unica_flow()
        resultados.append(resultado)
    return resultados

# --- ETAPA 3: PONTO DE ENTRADA DO SCRIPT ---

if __name__ == "__main__":
    # O Streamlit irá chamar este script. A lógica de qual flow rodar
    # pode ser passada via argumentos de linha de comando.
    import sys
    
    # Por padrão, roda uma única execução
    modo = "unica"
    if len(sys.argv) > 1:
        modo = sys.argv[1] # ex: 'multipla'

    if modo == "multipla":
        # Você pode definir o número de execuções aqui ou passar como argumento
        num_runs = 3 
        if len(sys.argv) > 2:
            num_runs = int(sys.argv[2])
        rce_multiplas_execucoes_flow(num_execucoes=num_runs)
    else:
        rce_execucao_unica_flow()