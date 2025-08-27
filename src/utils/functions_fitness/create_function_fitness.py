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

