# =====================================================================================
# CONFIG.PY — Configurações Globais do RCE Framework
# Todas as constantes, caminhos e configurações centralizadas aqui.
# Use: from config import *
# =====================================================================================

from pathlib import Path

# --- Caminhos Base ---
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"

# --- Scripts Principais ---
RUN_FRAMEWORK_SCRIPT    = SRC_DIR / "run.py"
RUN_AGENDAMENTO_SCRIPT  = SRC_DIR / "run_agendamento.py"
RUN_SIMULATOR_SCRIPT    = SRC_DIR / "RedeEletrica/SimulatorSIN45/PandaPowerCaseManager.py"
CLI_SCRIPT_PATH         = SRC_DIR / "CLI.py"

# --- Parâmetros do AG que são variáveis (usados na bateria de testes) ---
VARYING_KEYS = {"MUTACAO", "CROSSOVER", "NUM_GENERATIONS", "POP_SIZE"}

# --- Funções Objetivo Disponíveis (definidas em src/__init__.py) ---
OBJECTIVE_FUNCTIONS = [
    "funcao_objetivo_IEEE14",
    "funcao_objetivo_IEEE30",
    "funcao_objetivo_IEEE57",
    "funcao_objetivo_IEEE118",
    "funcao_objetivo_SIN45",
]

# --- Casos de Análise de Contingência ---
ANALYSIS_CASES = {
    "case_ieee14": {
        "name": "Análise de Contingência - IEEE 14",
        "module_path": SRC_DIR
        / "utils/functions_fitness/analise_contingencia/analise_contingencia_ieee14.py",
        "agendamento_df_name": "agendamento_df_ieee14",
        "contingencia_df_name": "contingencia_df_ieee14",
        "network_name": "case14",
    },
    "case_ieee30": {
        "name": "Análise de Contingência - IEEE 30",
        "module_path": SRC_DIR
        / "utils/functions_fitness/analise_contingencia/analise_contingencia_ieee30.py",
        "agendamento_df_name": "agendamento_df_ieee30",
        "contingencia_df_name": "contingencia_df_ieee30",
        "network_name": "case30",
    },
    "case_ieee118": {
        "name": "Análise de Contingência - IEEE 118",
        "module_path": SRC_DIR
        / "utils/functions_fitness/analise_contingencia/analise_contingencia_ieee118.py",
        "agendamento_df_name": "agendamento_df_ieee118",
        "contingencia_df_name": "contingencia_df_ieee118",
        "network_name": "case118",
    },
}

# =====================================================================================
#  DICIONÁRIO DE SCRIPTS CUSTOMIZADOS
# =====================================================================================
# Adicione novas entradas aqui para criar botões de script no menu lateral.
# O 'path' deve ser o caminho completo para o seu script.
CUSTOM_SCRIPTS = {
    "IEEE_CASES": {
        "name": "▶️ Executar Electrical-Power-System",
        "path": SRC_DIR
        / "LauncherGUI/frontend/Electrical-System-pandapower/SYSTEM_ELECTRICAL_PANDAPOWER.py",
    },
    "PandaPowerCaseManager": {
        "name": "▶️ Executar PandaPower Case Manager",
        "path": SRC_DIR / "RedeEletrica/SimulatorSIN45/PandaPowerCaseManager.py",
    },
    "SmartGridSimulator": {
        "name": "▶️ Executar Smart Grid Simulator",
        "path": SRC_DIR / "RedeEletrica/SimulatorSIN45/SmartGridSimulator.py",
    },
    # "outro_script": {
    #     "name": "▶️ Outro Script",
    #     "path": SRC_DIR / "caminho/para/outro_script.py"
    # },
}

# --- Configurações de Loading Screen ---
LAZY_LOADING           = True
TEMPO_MINIMO_SEGUNDOS  = 3

# --- Ícone da Aplicação ---
ICON_PATH = BASE_DIR / "src/assets/IconRCELancher.png"
