import os
import sys
import pandas as pd
import pathlib

# Configuração de caminhos para encontrar os modelos do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from models.RedeEletrica.rede_eletrica import RedeEletricaPandaPower
from models.AlgEvolutivoRCE.Setup import Setup
from utils.functions_fitness.analise_contingencia.analise_contigencias_script import analise_contigencias_SEP

BASE_DIR = pathlib.Path(__file__).resolve().parent
HASH_TABLE_PATH = BASE_DIR.parent.parent.parent / "output" / "hash_table_ieee118.xlsx"

# =========================================================
# 📊 DADOS BASE IEEE 118
# =========================================================

agendamento_base = pd.DataFrame(
    [
        {"ramo": [7, 29], "inicio": "20:00", "duracao": 6, "prioridade": 4},
        {"ramo": [44, 48], "inicio": "18:00", "duracao": 5, "prioridade": 1},
        {"ramo": [16, 112], "inicio": "21:00", "duracao": 6, "prioridade": 1},
        {"ramo": [61, 65], "inicio": "27:00", "duracao": 6, "prioridade": 1},
        {"ramo": [75, 117], "inicio": "01:00", "duracao": 4, "prioridade": 1},
        {"ramo": [46, 68], "inicio": "21:00", "duracao": 5, "prioridade": 1},
        {"ramo": [84, 88], "inicio": "20:00", "duracao": 6, "prioridade": 1},
        {"ramo": [18, 33], "inicio": "14:00", "duracao": 5, "prioridade": 1},
        {"ramo": [3, 10], "inicio": "19:00", "duracao": 4, "prioridade": 1},
        {"ramo": [11, 15], "inicio": "20:00", "duracao": 5, "prioridade": 1},
    ]
)

contingencia_df = pd.DataFrame(
    [
        {"contingencia": 1, "from": 48, "to": 49},
        {"contingencia": 2, "from": 10, "to": 11},
        {"contingencia": 3, "from": 16, "to": 17},
    ]
)

def hashtablesize():
    return len(contingencia_df) * 3 * (2 ** len(agendamento_base))

# =========================================================
# 🎯 FUNÇÃO OBJETIVO
# =========================================================

def funcao_objetivo_IEEE118(individuo, setupobj, _debug=False):
    rede = RedeEletricaPandaPower("118", debug=_debug)
    rede.pesos.update({"tensao": {"min": 100, "max": 100}, "loading_linhas": 100, "loading_trafos": 100})

    df_ag = agendamento_base.copy()
    df_ag["inicio"] = individuo
    
    # ✅ salvar info de agendamento no setup para o Dashboard
    setupobj.agendamento_info = df_ag.to_dict(orient="records")

    rede.validar_dados(df_ag, contingencia_df)

    matriz = rede.avalia_cenarios(
        horas=(df_ag["inicio"] + df_ag["duracao"]).max(),
        hora_inicio=df_ag["inicio"],
        duracao=df_ag["duracao"],
        ls=0, le=8, ms=8, me=18, hs=18, he=24
    )

    fitness, _ = analise_contigencias_SEP(rede, setupobj, matriz, df_ag, contingencia_df)
    return fitness,

if __name__ == "__main__":
    print("Módulo IEEE 118 carregado.")
