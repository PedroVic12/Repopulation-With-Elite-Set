
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


# Setup object for managing parameters and hash table
"""
params: Dict,
fitness_function: Any,
tamanho_hash: int = 0
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



"""    
# Esta função avalia o agendamento de desligamentos e contingências na rede elétrica, calculando o fitness baseado em violações de tensões e carregamentos.
# A função utiliza a classe RedeEletricaPandaPower para simular o fluxo de carga e calcular as violações com base em um agendamento fornecido.
# a função retorna o fitness total do agendamento, que é a soma das violações de todos os cenários avaliados.
## A função também utiliza uma tabela hash para armazenar os resultados de cenários já avaliados, evitando cálculos redundantes.
# 
Returns:
    float/int: fitness_result
"""
#! Função objetivo para o problema de otimização da rede elétrica IEEE 30 barras

#1) Caso IEEE 30 barras não convergente corrigido
#2) Atualizando hashtbale com Setup e Class RedeEletricaPandaPower
#3) Testes de simulação 28/08/2025


    
def hashtablesize():
    contingencias = contingencia_df['contingencia'].to_list()
    num_carregamentos = 3
    num_contingencias = len(contingencias) # 3
    num_desligamentos = len(agendamento_df) # 10

    # info_df = pd.DataFrame([
    #     "Contingencia": contingencia_df['contingencia'].to_list(),
    #     "Carregamento": range(num_carregamentos),
    #     "Desligamento": range(num_desligamentos),
    # ])
    return num_contingencias* num_carregamentos*(2**num_desligamentos)
    

def get_hash_key_size(individuo):
    """Calcula o tamanho da tabela hash com base nos parâmetros (IND_SIZE)."""
    try:
        num_desligamentos = len(individuo)

        # Valores baseados nas funções de fitness existentes (IEEE14 e IEEE30)
        num_carregamentos = 3
        num_contingencias = 3 
        
        size = num_contingencias * num_carregamentos * (2**num_desligamentos)
        print(f"Tamanho da tabela hash calculado: {size} (baseado em IND_SIZE={num_desligamentos})")
        return size
    except KeyError:
        print("Aviso: 'IND_SIZE' não encontrado nos parâmetros. Usando tamanho de hash de fallback.")
        return 3072 # Fallback size
    except Exception as e:
        print(f"Erro ao calcular o tamanho da hash: {e}. Usando tamanho de fallback.")
        return 3072

def consultaHashTable(rede):
    """Carrega a hash table salva em Excel (coluna única Fitness)."""
    if os.path.exists(HASH_TABLE_PATH):
        try:
            df = pd.read_excel(HASH_TABLE_PATH)  # Apenas 1 coluna "Fitness"
            if "Fitness" in df.columns:
                valores = df["Fitness"].tolist()
                limite = min(len(valores), len(rede.tabela_hash))
                rede.tabela_hash[:limite] = valores[:limite]
                #print(f"[INFO] Hash table carregada com {limite} registros ")
        except Exception as e:
            print(f"[ERRO] ao carregar hash_table.xlsx: {e}")
    else:
        # Se não existir, cria um Excel inicial vazio (preenchido com -1.0)
        df = pd.DataFrame({"Fitness": rede.tabela_hash})
        df.to_excel(HASH_TABLE_PATH, index=False)
        print(f"[INFO] Hash table INICIAL criada com {len(rede.tabela_hash)}")


def exportaHashTable(rede):
    """Exporta a hash table atualizada para Excel (coluna única Fitness)."""
    df = pd.DataFrame({"Fitness": rede.tabela_hash})
    df.to_excel(HASH_TABLE_PATH, index=False)
    #print(f"[INFO] Hash table exportada ({len(rede.tabela_hash)} posições) -> {HASH_TABLE_PATH}")



def funcao_objetivo_IEEE30(individuo, _debug=False):
    """
    Avalia o agendamento de desligamentos e contingências na rede IEEE-30 barras.
    Agora a tabela hash e os contadores estão dentro de RedeEletricaPandaPower.
    """
    try:
        # 1) Criar rede elétrica IEEE-30 barras
        rede = RedeEletricaPandaPower("30", debug=False)

        # Inicializar hash table dentro da rede
        tamanho_hash = hashtablesize()
        rede.tabela_hash = [-1.0] * tamanho_hash
        rede.objectiveruns = 0
        rede.hashtablereads = 0
        
        # Importar hash do Excel (cache de execuções anteriores)
        consultaHashTable(rede)

        # Pesos definidos pelo usuário
        rede.pesos["tensao"] = {"min": 100, "max": 100}
        rede.pesos["loading_linhas"] = 100
        rede.pesos["loading_trafos"] = 100

        # Calcular duração total
        duracao_total_agendamento = (agendamento_df['inicio'] + agendamento_df['duracao']).max()
        rede.validar_dados(agendamento_df, contingencia_df)

        # Passar indivíduo como início dos desligamentos
        agendamento_df["inicio"] = individuo

        # 2) Gerar matriz de cenários
        matriz_cenarios = rede.avalia_cenarios(
            horas=duracao_total_agendamento,
            hora_inicio=agendamento_df['inicio'],
            duracao=agendamento_df['duracao'],
            ls=0, le=8,
            ms=8, me=18,
            hs=18, he=24
        )


        violacoes_total = []

        contingencias = contingencia_df['contingencia'].to_list()
        num_carregamentos = 3
        num_contingencias = len(contingencias)
        num_desligamentos = len(agendamento_df)
        
        # 3) Loop de cenários
        for cenario in matriz_cenarios:
            perfil = cenario[0]
            estado_ramos = cenario[1:]

            # 4) Ajustar carregamento
            rede.ajustar_cargas(perfil)

            # 5) Loop contingências
            for contingencia_atual in range(1, num_contingencias + 1):

                # Gera hash key
                hash_key = rede.hashtableindex(
                    perfil,
                    num_carregamentos,
                    contingencia_atual,
                    num_contingencias,
                    estado_ramos
                )

                # Caso já exista em cache
                if rede.tabela_hash[hash_key] >= 0.0:
                    fitness = rede.tabela_hash[hash_key]
                    rede.hashtablereads += 1

                else:
                    # Ligar tudo e aplicar desligamentos + contingência
                    rede.religar_todos_os_ramos_agendamento()
                    rede.desligar_elementos_agendamento(estado_ramos)
                    ramo_contingencia = list(contingencia_df.loc[
                        contingencia_df['contingencia'] == contingencia_atual, ['from', 'to']
                    ].values[0])
                    rede.desligar_contingencia(ramo_contingencia)

                    # Executa fluxo
                    if rede.executar_fluxo_de_potencia():
                        fitness, _ = rede.calcular_violacoes_fitness()
                    else:
                        fitness = rede.pesos.get("demanda", 99)

                    # Salva no hash
                    rede.tabela_hash[hash_key] = fitness
                    rede.objectiveruns += 1

                violacoes_total.append(fitness)

        # 6) Calcular fitness final
        #print(f"Número de leituras na tabela hash: {rede.hashtablereads}")
        #print(f"Número total de calculos de Fluxo de Potencia: {rede.objectiveruns}")
        fitness_final = sum(violacoes_total)
        exportaHashTable(rede)
        rede.log(f"\nFitness do agendamento = {fitness_final:.2f}\n", level="success")
        return fitness_final 

    except Exception as e:
        print(f"\n[ERRO] na função objetivo: {e}")
        return float("inf"), 0, 0
    

def simulate_IEEE_30_cenario():

    fitness = funcao_objetivo_IEEE30(
        #agendamento proposto em Zanghi(2016)
        #individuo=[15,15,14,18,15,14,10,14,18,15],
        #agendamento ótimo em Zanghi(2016)
        individuo=[15,15,10,21,16,13,10,14,17,18],
        _debug = False
    )
    
    tabela_hash_size = hashtablesize()
    print(f"Fitness: {fitness}\nTamanho da tabela hash: {tabela_hash_size}")

    
    return fitness


#simulate_IEEE_30_cenario()

    
