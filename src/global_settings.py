import pathlib
from pathlib import Path

# =====================================================================================
#  CONFIGURAÇÕES GLOBAIS DE ALTO NÍVEL
# =====================================================================================

# --- Estrutura de Diretórios e Caminhos ---
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR
PROJECT_ROOT = BASE_DIR.parent

# --- Caminhos de Scripts ---
RUN_FRAMEWORK_SCRIPT = SRC_DIR / "run.py"
DASHBOARD_SCRIPT = SRC_DIR / "DashboardApp" / "dashboard_RCE_APP.py" # Definindo um caminho padrão

# --- Constantes do Algoritmo Genético ---
VARYING_KEYS = {"MUTACAO", "CROSSOVER", "NUM_GENERATIONS", "POP_SIZE"}

# --- Funções Objetivo (Objetos Reais) ---
from utils.functions_fitness.function_IEEE_14_contigencias import funcao_objetivo_IEEE14, HASH_TABLE_PATH as HASH_TABLE_PATH_IEEE14, hashtablesize as hashtablesize_IEEE14
from utils.functions_fitness.function_IEEE_30_otimizacao import funcao_objetivo_IEEE30, HASH_TABLE_PATH as HASH_TABLE_PATH_IEEE30, hashtablesize as hashtablesize_IEEE30
from utils.functions_fitness.function_IEEE_57_otimizacao import funcao_objetivo_IEEE57, HASH_TABLE_PATH as HASH_TABLE_PATH_IEEE57, hashtablesize as hashtablesize_IEEE57
from utils.functions_fitness.func_objetivo_SIN_45_otimizado_AG_ONS import funcao_objetivo_SIN45, HASH_TABLE_PATH as HASH_TABLE_PATH_SIN45, hashtablesize as hashtablesize_SIN45
from utils.functions_fitness.function_IEEE_118_otimizacao import funcao_objetivo_IEEE118, HASH_TABLE_PATH as HASH_TABLE_PATH_IEEE118, hashtablesize as hashtablesize_IEEE118

ARRAY_FITNESS_FUNCTIONS = [funcao_objetivo_IEEE14, funcao_objetivo_IEEE30, funcao_objetivo_IEEE57, funcao_objetivo_IEEE118, funcao_objetivo_SIN45]
HASH_TABLE_PATH = [ HASH_TABLE_PATH_IEEE14, HASH_TABLE_PATH_IEEE30, HASH_TABLE_PATH_IEEE57, HASH_TABLE_PATH_IEEE118, HASH_TABLE_PATH_SIN45 ]
HASHTABLE_SIZE_FUNCS = {
    "funcao_objetivo_IEEE14": hashtablesize_IEEE14,
    "funcao_objetivo_IEEE30": hashtablesize_IEEE30,
    "funcao_objetivo_IEEE57": hashtablesize_IEEE57,
    "funcao_objetivo_IEEE118": hashtablesize_IEEE118,
    "funcao_objetivo_SIN45": hashtablesize_SIN45,
}

# --- Flags de Controle ---
CLI = False
DEBUG_MODE = False
BECHMARKING_MODE = False
SHOW_SETTINGS = False
TEST_DEBUG = False # Definindo um valor padrão
