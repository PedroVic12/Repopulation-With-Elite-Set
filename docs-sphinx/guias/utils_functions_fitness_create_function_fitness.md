# create_function_fitness.py

```python

# File: Repopulation-With-Elite-Set/src/utils/functions_fitness/
import os
import sys
import pandas as pd
import pathlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from RedeEletrica_backup.rede_eletrica import RedeEletricaPandaPower
from AlgEvolutivoRCE_backup.Setup import Setup

BASE_DIR = pathlib.Path(__file__).resolve().parent
HASH_TABLE_PATH = BASE_DIR.parent.parent / "output" / "hash_table.xlsx"


def your_fitness_function(ind):
    """Here you create your objetive function with your decision variable (ind) """
    pass

import math
import numpy as np

def rastriginFunction(individual ):
    """Rastrigin function implementation."""
    evaluations = 0
    rastrigin = 10 * len(individual)

    for i in range(len(individual)):
        rastrigin += individual[i] * individual[i] - 10 * (
            math.cos(2 * np.pi * individual[i])
        )
        evaluations += 1

    return rastrigin

def rosenbrock (x):

    var = np.array(x)

    return np.sum(100 * (var[1:] - var[:-1] ** 2) ** 2 + (1 - var[:-1]) ** 2)

# Setup object for managing parameters and hash table
"""
params: Dict,
fitness_function: Any,
tamanho_hash: int = 0
setupobj = Setup(
    
)
setupobj.tabela_hash = [-1.0] * 3072  # Inicializa a tabela hash com -1.0 (indicando cenários não calculados)
setupobj.objectiveruns = 0
setupobj.hashtablereads = 0


"""

#! Tabela agendamentos em xlsx hardcoded - EXEMPLO CASO IEEE 30 BARRAS
agendamento_df = pd.DataFrame([
    {"ramo": [1, 3], "inicio": "15:00", "duracao": 6 ,"prioridade": 4},
    {"ramo": [1, 5], "inicio": "15:00", "duracao": 5, "prioridade": 1},
    {"ramo": [5, 8], "inicio": "14:00", "duracao": 6, "prioridade": 1},
    {"ramo": [13, 14], "inicio": "18:00", "duracao": 6, "prioridade": 1},
    {"ramo": [15, 16], "inicio": "15:00", "duracao": 4, "prioridade": 1},
    {"ramo": [21, 23], "inicio": "14:00", "duracao": 5, "prioridade": 1},
    {"ramo": [7, 27], "inicio": "10:00", "duracao": 6, "prioridade": 1},
    {"ramo": [26, 28], "inicio": "14:00", "duracao": 5, "prioridade": 1},
    {"ramo": [9, 21], "inicio": "18:00", "duracao": 4, "prioridade": 1},
    {"ramo": [14, 17], "inicio": "15:00", "duracao": 5, "prioridade": 1},

])

contingencia_df = pd.DataFrame([
        {"contingencia":1,  "from":1 , "to": 3},
        {"contingencia":2,  "from":11 , "to": 14},
        {"contingencia":3,  "from":14 , "to": 17},
])

# Converter horários de início para horas do dia
agendamento_df['inicio'] = agendamento_df['inicio'].apply(lambda x: int(x.split(':')[0]))

# Calcular horário de término em horas do dia
agendamento_df['final'] = agendamento_df.apply(lambda row: (row['inicio'] + row['duracao']) % 24, axis=1)



```