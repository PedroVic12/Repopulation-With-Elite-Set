# File: Repopulation-With-Elite-Set/src/utils/functions_fitness/__init__.py
import os
import sys
import pathlib
from typing import Any, Dict, Iterable, Tuple, Optional

import pandas as pd

# --- sys.path para imports do seu projeto ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from RedeEletrica_backup.rede_eletrica import RedeEletricaPandaPower
from AlgEvolutivoRCE_backup.Setup import Setup

# =============================================================================
# Config & paths
# =============================================================================
BASE_DIR = pathlib.Path(__file__).resolve().parent
HASH_TABLE_PATH = BASE_DIR.parent.parent / "output" / "hash_table.xlsx"
HASH_AUTOSAVE = True          # salva hash table periodicamente em XLSX
HASH_AUTOSAVE_EVERY = 200     # a cada N escritas

# =============================================================================
# Dados hardcoded (mantidos)
# =============================================================================
agendamento_df = pd.DataFrame([
    {"ramo": [1, 3],  "inicio": "15:00", "duracao": 6, "prioridade": 4},
    {"ramo": [1, 5],  "inicio": "15:00", "duracao": 5, "prioridade": 1},
    {"ramo": [5, 8],  "inicio": "14:00", "duracao": 6, "prioridade": 1},
    {"ramo": [13,14], "inicio": "18:00", "duracao": 6, "prioridade": 1},
    {"ramo": [15,16], "inicio": "15:00", "duracao": 4, "prioridade": 1},
    {"ramo": [21,23], "inicio": "14:00", "duracao": 5, "prioridade": 1},
    {"ramo": [7, 27], "inicio": "10:00", "duracao": 6, "prioridade": 1},
    {"ramo": [26,28], "inicio": "14:00", "duracao": 5, "prioridade": 1},
    {"ramo": [9, 21], "inicio": "18:00", "duracao": 4, "prioridade": 1},
    {"ramo": [14,17], "inicio": "15:00", "duracao": 5, "prioridade": 1},
])

contingencia_df = pd.DataFrame([
    {"contingencia": 1, "from": 1,  "to": 3},
    {"contingencia": 2, "from": 11, "to": 14},
    {"contingencia": 3, "from": 14, "to": 17},
])

# Converter horários "HH:MM" -> hora (int)
agendamento_df['inicio'] = agendamento_df['inicio'].apply(lambda x: int(str(x).split(':')[0]))
# Horário de término (não é usado diretamente, mas mantido)
agendamento_df['final'] = agendamento_df.apply(
    lambda row: (int(row['inicio']) + int(row['duracao'])) % 24, axis=1
)

# =============================================================================
# Helpers de Hash Table
# =============================================================================
class DefaultHash(dict):
    """
    Dict com default -1.0 (não calculado) e contagem de saves.
    Compatível com o uso atual: setupobj.tabela_hash[hash_key] < 0.0
    """
    def __missing__(self, key):
        return -1.0

def _normalize_hash_key(*parts: Any) -> Tuple:
    """
    Garante uma key hashable determinística (tuplas imutáveis).
    Converte listas para tuplas recursivamente.
    """
    def to_hashable(x):
        if isinstance(x, dict):
            return tuple(sorted((k, to_hashable(v)) for k, v in x.items()))
        if isinstance(x, (list, tuple)):
            return tuple(to_hashable(i) for i in x)
        if isinstance(x, pd.Series):
            return to_hashable(x.tolist())
        return x
    return tuple(to_hashable(p) for p in parts)

def _save_hash_to_excel(table: Dict, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # explode dict em duas colunas: key (str) e value (float)
    rows = [{"key": str(k), "value": v} for k, v in table.items()]
    if not rows:
        return
    df = pd.DataFrame(rows)
    df.to_excel(path, index=False)

# =============================================================================
# API esperada externamente
# =============================================================================
def your_fitness_function(ind):
    """
    Wrapper simples caso a infra do GA espere esse nome.
    Cria Setup, chama função objetivo com injeção de setup.
    """
    setup = Setup()
    return funcao_objetivo_IEEE30(individuo=ind, setupobj=setup, _debug=False)

# =============================================================================
# Função Objetivo (IEEE30)
# =============================================================================
def funcao_objetivo_IEEE30(individuo, setupobj: Setup, _debug: bool = False):
    """
    Avalia o agendamento de desligamentos (individuo) sob contingências.
    Usa RedeEletricaPandaPower para runpp e calcular violações.
    Hash table:
      - Preferência: usar setupobj.tabela_hash, mas também injetamos na 'rede'
        para que métodos internos possam reutilizar sem depender do Setup.
      - Default: -1.0 => não calculado.
    Retorna: fitness_final (float)
    """
    # --- 0) Preparação de hash table e contadores ---
    if not hasattr(setupobj, "tabela_hash") or setupobj.tabela_hash is None:
        setupobj.tabela_hash = DefaultHash()
    elif not isinstance(setupobj.tabela_hash, DefaultHash):
        # embrulha dict existente
        d = DefaultHash()
        d.update(setupobj.tabela_hash)
        setupobj.tabela_hash = d
    if not hasattr(setupobj, "objectiveruns"):   setupobj.objectiveruns = 0
    if not hasattr(setupobj, "hashtablereads"):  setupobj.hashtablereads = 0
    if not hasattr(setupobj, "_hash_autosave_n"): setupobj._hash_autosave_n = 0

    # --- 1) Validar individuo e preparar agendamento ---
    individuo = list(individuo)
    if len(individuo) != len(agendamento_df):
        raise ValueError(f"Tamanho do indivíduo ({len(individuo)}) difere do agendamento ({len(agendamento_df)})")

    # Sanitiza horas [0,23]
    individuo = [int(x) % 24 for x in individuo]

    # Clona agendamento base para não poluir global
    agenda = agendamento_df.copy(deep=True)
    agenda["inicio"] = individuo

    # Recalcula duração total após alterar inícios
    duracao_total_agendamento = int((agenda['inicio'] + agenda['duracao']).max())

    # --- 2) Instancia rede e injeta pesos + validações ---
    rede = RedeEletricaPandaPower("30", debug=False)
    # pesos conforme seu código
    rede.pesos["tensao"] = {"min": 100, "max": 100}
    rede.pesos["loading_linhas"] = 100
    rede.pesos["loading_trafos"] = 100

    # opcionalmente some penalty default se não existir
    if "demanda" not in rede.pesos:
        rede.pesos["demanda"] = 99.0

    # passa a hash table para o objeto da rede (para uso interno se necessário)
    if hasattr(rede, "attach_hash_table"):
        try:
            rede.attach_hash_table(setupobj.tabela_hash)  # método recomendado na sua classe
        except Exception:
            pass
    else:
        # fallback: tenta atribuir atributo simples
        try:
            setattr(rede, "tabela_hash", setupobj.tabela_hash)
        except Exception:
            pass

    # valida dados de entrada
    rede.validar_dados(agenda, contingencia_df)

    # --- 3) Geração da matriz de cenários ---
    matriz_cenarios = rede.avalia_cenarios(
        horas=duracao_total_agendamento,
        hora_inicio=agenda['inicio'],
        duracao=agenda['duracao'],
        ls=0,  le=8,     # madrugada
        ms=8,  me=18,    # médio
        hs=18, he=24     # pesado
    )

    violacoes_total = []

    contingencias = contingencia_df['contingencia'].tolist()
    num_carregamentos = 3
    num_contingencias = len(contingencias)   # 3
    num_desligamentos = len(agenda)          # 10

    # --- 4) Loop de cenários ---
    try:
        for cenario in matriz_cenarios:
            perfil = cenario[0]          # nível de carregamento (0,1,2) esperado
            estado_ramos = cenario[1:]   # vetor binário dos desligamentos do cenário

            # Ajusta cargas conforme perfil
            rede.ajustar_cargas(perfil)

            # Para cada contingência no cenário
            for contingencia_atual in range(1, num_contingencias + 1):
                # Hash key determinística (usando helper interno OU nossa normalização)
                if hasattr(rede, "hashtableindex"):
                    try:
                        hash_key = rede.hashtableindex(perfil, num_carregamentos,
                                                       contingencia_atual, num_contingencias,
                                                       estado_ramos)
                    except Exception:
                        hash_key = _normalize_hash_key(perfil, num_carregamentos,
                                                       contingencia_atual, num_contingencias,
                                                       tuple(estado_ramos))
                else:
                    hash_key = _normalize_hash_key(perfil, num_carregamentos,
                                                   contingencia_atual, num_contingencias,
                                                   tuple(estado_ramos))

                # Cache hit?
                cached = setupobj.tabela_hash[hash_key]
                if cached < 0.0:
                    # --- Cache miss: simular ---
                    # Religa tudo antes de aplicar mudanças do cenário
                    try:
                        rede.religar_todos_os_ramos_agendamento()
                    except Exception:
                        pass

                    # Aplica desligamentos do cenário
                    rede.desligar_elementos_agendamento(estado_ramos)

                    # Aplica contingência
                    ramo = list(
                        contingencia_df.loc[
                            contingencia_df['contingencia'] == contingencia_atual,
                            ['from', 'to']
                        ].values[0]
                    )
                    rede.log(f"\n{contingencia_atual}) Ramo da contingência = {ramo}\n")
                    rede.desligar_contingencia(ramo)

                    # Executa fluxo
                    if rede.executar_fluxo_de_potencia():
                        fitness, _violacoes_df = rede.calcular_violacoes_fitness()
                    else:
                        # penalidade
                        fitness = float(rede.pesos.get("demanda", 99.0))

                    # Armazena no cache
                    setupobj.tabela_hash[hash_key] = float(fitness)
                    setupobj.objectiveruns += 1
                    setupobj._hash_autosave_n += 1

                    # autosave periódico
                    if HASH_AUTOSAVE and (setupobj._hash_autosave_n % HASH_AUTOSAVE_EVERY == 0):
                        try:
                            _save_hash_to_excel(setupobj.tabela_hash, HASH_TABLE_PATH)
                        except Exception:
                            pass
                else:
                    # Cache hit
                    fitness = float(cached)
                    setupobj.hashtablereads += 1
                    if _debug:
                        print(f"[HASH HIT] perfil={perfil} cont={contingencia_atual} fitness={fitness}")

                violacoes_total.append(fitness)

            # status opcional (não quebra se método não existir)
            try:
                rede.show_status()
            except Exception:
                pass

        # --- 5) Fitness global = soma das violações ---
        fitness_final = float(sum(violacoes_total))
        rede.log(f"\nFitness do agendamento = {fitness_final:.2f}\n", level="success")

        # save final da hash table (opcional)
        if HASH_AUTOSAVE:
            try:
                _save_hash_to_excel(setupobj.tabela_hash, HASH_TABLE_PATH)
            except Exception:
                pass

        return fitness_final

    except Exception as e:
        print(f"\nErro ao calcular a função objetivo: {e}")
        raise

# =============================================================================
# Utilities
# =============================================================================
def hashtablesize():
    """
    Calcula o tamanho teórico da hash table:
    contingências * carregamentos * 2^(n desligamentos)
    """
    contingencias = contingencia_df['contingencia'].to_list()
    num_carregamentos = 3
    num_contingencias = len(contingencias)    # 3
    num_desligamentos = len(agendamento_df)   # 10
    return num_contingencias * num_carregamentos * (2 ** num_desligamentos)

def simulate_IEEE_30_cenario():
    """
    Função utilitária de teste rápido.
    """
    setup = Setup(
        
    )
    fitness = funcao_objetivo_IEEE30(
        setupobj=setup,
        # agendamento ótimo de referência (exemplo)
        individuo=[15, 15, 10, 21, 16, 13, 10, 14, 17, 18],
        _debug=False
    )
    tabela_hash_size = hashtablesize()
    return f"Fitness: {fitness}\nTamanho da tabela hash: {tabela_hash_size}"
