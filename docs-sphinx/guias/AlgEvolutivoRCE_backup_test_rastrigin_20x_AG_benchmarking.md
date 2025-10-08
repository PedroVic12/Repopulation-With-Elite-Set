# test_rastrigin_20x_AG_benchmarking.py

```python
"""
Script de teste para executar o algoritmo genético com a função Rastrigin.
"""
import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path
import numpy as np

# Adiciona o diretório pai ao path para permitir importações de outros módulos do projeto
sys.path.append(str(Path(__file__).parent.parent))

from AlgEvolutivoRCE_backup.Setup import Setup
from AlgEvolutivoRCE_backup.alg_evolutivo_rce import AlgoritimoEvolutivoRCE
from AlgEvolutivoRCE_backup.benchmarking_functions import rastrigin as rastrigin_benchmark

# --- Constantes ---
RASTRIGIN_LOWER_BOUND = -5.12  # Limite inferior recomendado para a função Rastrigin
RASTRIGIN_UPPER_BOUND = 5.12   # Limite superior recomendado para a função Rastrigin
DEFAULT_PARAMS_FILE = 'params_default.json'  # Arquivo de parâmetros padrão
OUTPUT_DIR = os.path.join('output', 'rastrigin_tests') # Diretório para salvar os resultados

# --- Configuração do Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

def print_separator(char='=', length=80):
    """Imprime uma linha separadora para organizar a saída no console."""
    print(char * length)

def load_params(params_file):
    """Carrega os parâmetros de um arquivo JSON."""
    try:
        with open(params_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Arquivo de parâmetros não encontrado: {params_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        logging.error(f"Erro ao decodificar o JSON do arquivo: {params_file}")
        sys.exit(1)

def scale_individual(individual, source_bounds, target_bounds):
    """Converte (escala) um indivíduo de uma faixa de valores para outra usando numpy."""
    source_low, source_high = source_bounds
    target_low, target_high = target_bounds
    
    individual_np = np.array(individual, dtype=float)
    
    # Fórmula para escalar um valor de [a, b] para [c, d]
    # valor_escalado = c + (d - c) * (valor_original - a) / (b - a)
    scaled_individual = target_low + (target_high - target_low) * \
                        (individual_np - source_low) / (source_high - source_low)
                        
    return scaled_individual

def run_rastrigin_test(run_num, total_runs, params):
    """Executa um único teste com a função Rastrigin."""
    print_separator()
    logging.info(f"EXECUÇÃO {run_num + 1}/{total_runs} - Iniciando")
    print_separator()

    # --- Configuração dos Parâmetros ---
    params['funcao_objetivo'] = 'rastrigin'
    params['decision_variables'] = params.get('IND_SIZE', 5)
    
    # Cria um diretório de saída para esta execução específica
    run_output_dir = os.path.join(OUTPUT_DIR, f'run_{run_num + 1}')
    os.makedirs(run_output_dir, exist_ok=True)

    # Obtém os limites (bounds) dos parâmetros para o escalonamento
    source_bounds = tuple(params.get('LIMITE_VAR', [0, 30]))
    target_bounds = (RASTRIGIN_LOWER_BOUND, RASTRIGIN_UPPER_BOUND)

    def rastrigin(individual):
        """Função wrapper para escalar o indivíduo e avaliar o fitness."""
        try:
            # Escala o indivíduo da faixa original para a faixa da função Rastrigin
            scaled_individual = scale_individual(individual, source_bounds, target_bounds)
            # Calcula o fitness usando a função de benchmark importada
            fitness = rastrigin_benchmark(scaled_individual)
            return (fitness,)
        except Exception as e:
            logging.error(f"Erro na função wrapper da Rastrigin: {e}", exc_info=True)
            return (float('inf'),) # Retorna um fitness infinito em caso de erro

    logging.info("Executando com os seguintes parâmetros:")
    logging.info(f"- Tamanho da população: {params['POP_SIZE']}")
    logging.info(f"- Número de gerações: {params['NUM_GENERATIONS']}")
    logging.info(f"- Taxa de mutação: {params['MUTACAO']}")
    logging.info(f"- Taxa de crossover: {params['CROSSOVER']}")
    logging.info(f"- Limites das variáveis (original): {source_bounds}")

    # --- Execução do Algoritmo Genético ---
    # Configura o ambiente do DEAP com os parâmetros e a função de fitness
    setup = Setup(params, fitness_function=rastrigin, tamanho_hash=0)
    # Cria a instância do algoritmo evolutivo
    alg = AlgoritimoEvolutivoRCE(setup, DEBUG=False)

    start_time = time.time()
    # Executa o algoritmo
    _, _, best_individual, _ = alg.run(RCE=True)
    elapsed_time = time.time() - start_time

    # --- Resultados ---
    print_separator('-')
    logging.info(f"EXECUÇÃO {run_num + 1} COMPLETA")
    
    best_fitness = float('inf')
    if best_individual.fitness.valid:
        best_fitness = best_individual.fitness.values[0]

    logging.info(f"Melhor solução encontrada: {best_individual}")
    logging.info(f"Melhor fitness: {best_fitness:.4f}")
    logging.info(f"Tempo de execução: {elapsed_time:.2f} segundos")
    print_separator('-')

    return {
        'run': run_num + 1,
        'best_solution': best_individual,
        'best_fitness': best_fitness,
        'elapsed_time': elapsed_time,
    }

def main(num_executions):
    """Função principal para executar os testes de benchmarking."""
    params_path = os.path.join(os.path.dirname(__file__), DEFAULT_PARAMS_FILE)
    params = load_params(params_path)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    logging.info(f"Iniciando simulação com Rastrigin para {num_executions} execuções!")
    
    # Executa os testes em um loop e armazena os resultados
    results = [run_rastrigin_test(i, num_executions, params.copy()) for i in range(num_executions)]
    
    # --- Sumário dos Resultados ---
    print_separator()
    logging.info("SUMÁRIO DOS TESTES")
    print_separator()

    for result in results:
        logging.info(
            f"Execução {result['run']:>2}: Fitness = {result['best_fitness']:.6f}, "
            f"Tempo = {result['elapsed_time']:.2f}s, "
            f"Solução = {result['best_solution']}"
        )
    
    # Filtra valores infinitos antes de calcular a média
    valid_fitnesses = [r['best_fitness'] for r in results if r['best_fitness'] != float('inf')]
    if valid_fitnesses:
        avg_fitness = sum(valid_fitnesses) / len(valid_fitnesses)
        logging.info(f"\nFitness médio (execuções válidas): {avg_fitness:.6f}")
    else:
        logging.warning("\nNenhum valor de fitness válido encontrado para calcular a média.")

    avg_time = sum(r['elapsed_time'] for r in results) / len(results)
    logging.info(f"Tempo médio de execução: {avg_time:.2f} segundos")
    print_separator()

if __name__ == "__main__":
    # Configura o parser de argumentos da linha de comando
    parser = argparse.ArgumentParser(description="Executa o Algoritmo Genético com a função Rastrigin.")
    parser.add_argument(
        "-n", "--num_executions",
        type=int,
        default=5,
        help="Número de vezes que a simulação deve ser executada (padrão: 5)"
    )
    args = parser.parse_args()
    
    # Chama a função principal com o número de execuções especificado
    main(args.num_executions)
```