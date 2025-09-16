# -*- coding: utf-8 -*-
"""
Arquivo: objetivo_contingencia_sin45.py

Objetivo: Função objetivo unificada para análise de contingências do sistema SEP-SIN 45,
com execução do algoritmo genético e apresentação dos resultados.
"""

import os
import sys
import pandas as pd
import pandapower as pp
from datetime import datetime

# Adiciona o caminho do projeto ao sys.path para importação dos módulos locais
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from RedeEletrica_backup.rede_eletrica import RedeEletricaPandaPower
from AlgEvolutivoRCE_backup.Setup import Setup
from AlgEvolutivoRCE_backup.alg_evolutivo_rce import AlgoritimoEvolutivoRCE


class SmartGridSin45:
    """
    Classe para gerenciar os dados e a criação da rede elétrica do sistema SIN 45 Barras.
    """
    def __init__(self):
        self.net = None
        self.dataframes = {}
        self.bus_map = {}

    def create_sin45_dataset_file(self, filename='SIN_45_barras_dataset.xlsx'):
        """
        Cria um arquivo Excel com os dados do sistema SIN 45 Barras.
        """
        # Dicionários com os dados do SIN 45 Barras
        nomes_barras = {'Barra': list(range(1, 46)),'Nome': ['IVAIPORA.525', 'LONDRINA.525', 'BARRACAO13.8', 'SIDEROPOL230', 'FARROUPIL230','P.FUNDO.13.8', 'P.FUNDO.230', 'XANXERE.230', 'P.BRANCO.230', 'S.OSORIO13.8','S.OSORIO.230', 'AREIA.230', 'S.MATEUS.230', 'CURITIBA.230', 'JOINVILE.230','BLUMENAU.230', 'R.QUEIMAD230', 'F.AREIA.13.8', 'AREIA.525', 'CURITIBA.525','CUR.NORTE525', 'BLUMENAU.525', 'BARRACAO.525', 'GRAVATAI.525', 'V.AIRES.525','PINHEIRO.525', 'S.SANTIA13.8', 'S.SANTIAG525', 'J.LAC.A.13.8', 'J.LACERDA138','J.LAC.B.13.8', 'J.LAC.C.13.8', 'J.LACERDA230', 'SEGREDO.13.8', 'SEGREDO.525','CECI.230', 'GRAVATAI.230', 'ITAUBA.13.8', 'ITAUBA.230', 'V.AIRES.230','APUCARANA230', 'LONDRINA.230', 'MARINGA.230', 'C.MOURAO.230', 'FORQUILHI230']}
        reatores = {'Barra': [1, 20, 21, 23, 24, 25],'Susceptância Shunt B(pu)': [-2.000, -1.500, -1.500, -1.000, -1.500, -1.500]}
        dados_rede = {'De': [1, 1, 1, 2, 3, 4, 4, 4, 5, 5, 6, 7, 7, 8, 8, 9, 10, 11, 11, 12, 12, 13, 14, 14, 15, 16, 16, 17, 18, 19, 19, 19, 19, 20, 20, 23, 24, 25, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 36, 36, 38, 39, 41, 41, 41, 42, 43],'Para': [2, 19, 28, 42, 23, 5, 33, 45, 7, 36, 7, 8, 39, 9, 11, 11, 11, 12, 44, 13, 19, 14, 15, 20, 16, 17, 22, 33, 19, 20, 21, 23, 35, 21, 22, 24, 37, 26, 40, 28, 28, 35, 30, 33, 33, 33, 45, 35, 37, 40, 39, 40, 42, 43, 44, 43, 44],'R(pu)': [0.00035, 0.0018, 0.0014, 0.0, 0.0, 0.0386, 0.0096, 0.0033, 0.02315, 0.00885, 0.0, 0.00815, 0.025, 0.0163, 0.0316, 0.0153, 0.0, 0.0306, 0.0172, 0.0245, 0.0, 0.0088, 0.0091, 0.0, 0.0077, 0.0108, 0.0, 0.009, 0.0, 0.0019, 0.0019, 0.0014, 0.0005, 0.0005, 0.0012, 0.0021, 0.0, 0.0022, 0.0, 0.0014, 0.0, 0.0005, 0.0, 0.0, 0.0, 0.0, 0.0129, 0.0, 0.0006971, 0.0061315, 0.0, 0.0202, 0.0051987, 0.011, 0.0229, 0.0086, 0.0181],'X(pu)': [0.00725, 0.0227, 0.0204, 0.0063, 0.0136, 0.1985, 0.0491, 0.0167, 0.1189, 0.0455, 0.046, 0.04175, 0.1548, 0.0835, 0.1621, 0.0861, 0.0114, 0.1523, 0.088, 0.1256, 0.03, 0.0415, 0.04675, 0.0062, 0.0388, 0.05525, 0.0062, 0.046, 0.0067, 0.028, 0.0274, 0.0195, 0.007, 0.0069, 0.0175, 0.0309, 0.0062, 0.03, 0.0062, 0.0195, 0.0114, 0.007, 0.0871, 0.059, 0.0701, 0.045, 0.0657, 0.0068, 0.0035819, 0.0316242, 0.0236, 0.1129, 0.0268149, 0.1184, 0.1174, 0.0442, 0.0929],'B(pu)': [0.8305, 2.2721, 2.4475, 0.0, 0.0, 0.34, 0.0842, 0.2859, 0.2042, 0.07925, 0.0, 0.072, 0.469, 0.144, 0.2784, 0.1344, 0.0, 0.2702, 0.152, 0.2041, 0.0, 0.5211, 0.07975, 0.0, 0.0675, 0.09315, 0.0, 0.07765, 0.0, 3.3576, 3.2867, 2.3968, 0.8392, 0.8216, 2.097, 3.7183, 0.0, 3.83, 0.0, 2.397, 0.0, 0.8392, 0.0, 0.0, 0.0, 0.0, 0.1128, 0.0, 0.0668, 0.5236, 0.0, 0.2062, 0.1905, 0.2027, 0.2027, 0.2868, 0.1607]}
        carga_leve = {'Barra': list(range(1, 46)),'Tipo de Barra (*)': [0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 2, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],'Potência Ativa (MW)': [0.0, 0.0, 1000.0, 0.0, 0.0, 172.0, 0.0, 0.0, 0.0, 736.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1248.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1060.0, 0.0, 72.0, 0.0, 96.0, 192.8, 0.0, 1060.8, 0.0, 0.0, 0.0, 392.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],'Carga Ativa (MW)': [720.1334, 0.0, 0.0, 141.6, 153.0934, 0.0, 136.8, 100.8, 37.2534, 0.0, 224.8, 223.7067, 104.16, 342.36, 248.3734, 339.4934, 94.24, 0.0, 0.0, 0.0, 294.4, 0.0, 139.656, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 100.832, 0.0, 0.0, 0.0, 0.0, 0.0, 650.4, 489.6, 0.0, 323.2, 314.4, 209.6, 183.2, 147.2, 111.2, 72.08],'Carga Reativa (Mvar)': [0.0, 0.0, 0.0, 54.4, 33.6, 0.0, 14.8, 37.6, 11.76, 0.0, 45.2, 48.56, 23.52, -20.0, 112.8, 72.48, 42.48, 0.0, 0.0, 0.0, 55.68, 0.0, -6.56, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 31.84, 0.0, 0.0, 0.0, 0.0, 0.0, 88.0, -364.0, 0.0, 108.0, -88.8, 10.56, 146.4, 48.16, 42.96, 44.24]}
        
        filepath = os.path.join(os.getcwd(), filename)
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            pd.DataFrame(nomes_barras).to_excel(writer, sheet_name='bus', index=False)
            pd.DataFrame(dados_rede).to_excel(writer, sheet_name='line', index=False)
            pd.DataFrame(carga_leve).to_excel(writer, sheet_name='load_gen', index=False)
            pd.DataFrame(reatores).to_excel(writer, sheet_name='shunt', index=False)
        return filepath

    def load_data_from_excel(self, filepath):
        """Carrega dados de um ficheiro Excel para um dicionário de DataFrames."""
        try:
            xls = pd.ExcelFile(filepath)
            self.dataframes = {sheet_name: pd.read_excel(xls, sheet_name) for sheet_name in xls.sheet_names}
            return self.dataframes
        except Exception as e:
            raise ValueError(f"Não foi possível ler o ficheiro Excel: {e}")

    def create_network_from_dataframes(self):
        """Cria uma rede pandapower a partir dos DataFrames carregados."""
        if not self.dataframes:
            raise ValueError("Nenhum dado carregado para criar a rede.")

        self.net = pp.create_empty_network()
        
        df_bus = self.dataframes.get('bus')
        df_load_gen = self.dataframes.get('load_gen')
        if df_bus is None or df_load_gen is None:
            raise ValueError("As folhas 'bus' e 'load_gen' são necessárias.")

        for col in ['Barra', 'Tipo de Barra (*)', 'Potência Ativa (MW)', 'Carga Ativa (MW)', 'Carga Reativa (Mvar)']:
            if col in df_load_gen.columns:
                df_load_gen[col] = pd.to_numeric(df_load_gen[col], errors='coerce').fillna(0)
        
        df_bus['Barra'] = pd.to_numeric(df_bus['Barra'], errors='coerce').fillna(0)

        self.bus_map.clear()
        for _, row in df_bus.iterrows():
            bus_id = int(row['Barra'])
            try:
                name_str = str(row['Nome'])
                parts = name_str.replace(',', '.').split('.')
                vn_kv = float(parts[-1]) if len(parts) > 1 and parts[-1].isdigit() else 230.0
            except (ValueError, IndexError):
                vn_kv = 230.0

            new_idx = pp.create_bus(self.net, name=row['Nome'], vn_kv=vn_kv)
            self.bus_map[bus_id] = new_idx

        self._add_elements_to_network()
        
        return self.net

    def _add_elements_to_network(self):
        """Adiciona os elementos (cargas, geradores, etc.) à rede."""
        df_load_gen = self.dataframes.get('load_gen')

        for _, row in df_load_gen.iterrows():
            if row['Carga Ativa (MW)'] > 0:
                bus_idx = self.bus_map.get(int(row['Barra']))
                if bus_idx is not None:
                    pp.create_load(self.net, bus=bus_idx, p_mw=row['Carga Ativa (MW)'], q_mvar=row['Carga Reativa (Mvar)'])

        for _, row in df_load_gen.iterrows():
            bus_idx = self.bus_map.get(int(row['Barra']))
            if bus_idx is None: continue
            
            is_slack = row['Tipo de Barra (*)'] == 2
            is_gen = row['Potência Ativa (MW)'] > 0

            if is_gen:
                if is_slack:
                    pp.create_ext_grid(self.net, bus=bus_idx, vm_pu=1.0, name="Slack Bus")
                else:
                    pp.create_gen(self.net, bus=bus_idx, p_mw=row['Potência Ativa (MW)'], vm_pu=1.0)

        df_line = self.dataframes.get('line')
        if df_line is not None:
            s_base_mva = 100.0
            for _, row in df_line.iterrows():
                from_bus = self.bus_map.get(int(row['De']))
                to_bus = self.bus_map.get(int(row['Para']))
                if from_bus is None or to_bus is None: continue
                
                from_vn_kv = self.net.bus.vn_kv.at[from_bus]
                to_vn_kv = self.net.bus.vn_kv.at[to_bus]

                if abs(from_vn_kv - to_vn_kv) > 1e-3:
                    hv_bus, lv_bus = (from_bus, to_bus) if from_vn_kv > to_vn_kv else (to_bus, from_bus)
                    pp.create_transformer_from_parameters(
                        self.net, hv_bus=hv_bus, lv_bus=lv_bus, sn_mva=s_base_mva,
                        vn_hv_kv=max(from_vn_kv, to_vn_kv), vn_lv_kv=min(from_vn_kv, to_vn_kv),
                        vkr_percent=row['R(pu)'] * 100.0, vk_percent=row['X(pu)'] * 100.0,
                        pfe_kw=0, i0_percent=0
                    )
                else:
                    z_base_ohm = (from_vn_kv ** 2) / s_base_mva
                    r_ohm = row['R(pu)'] * z_base_ohm
                    x_ohm = row['X(pu)'] * z_base_ohm
                    c_nf = (row['B(pu)'] / (2 * 3.14159 * 60 * z_base_ohm)) * 1e9
                    pp.create_line_from_parameters(self.net, from_bus=from_bus, to_bus=to_bus, length_km=1.0,
                                                   r_ohm_per_km=r_ohm, x_ohm_per_km=x_ohm,
                                                   c_nf_per_km=c_nf, max_i_ka=0.5)

def analise_contigencias_sep(rede, setupobj, matriz_cenarios, agendamento_df, contingencia_df):
    """
    Executa a análise de contingências para um determinado agendamento de manutenção.
    """
    violacoes_total = []
    contigencias_selecionadas = {"ramos": [], "contingencia": []}
    num_contingencias = len(contingencia_df)

    try:
        for cenario in matriz_cenarios:
            perfil = cenario[0]
            estado_ramos = cenario[1:]
            rede.ajustar_cargas(perfil)

            for _, contingencia_row in contingencia_df.iterrows():
                contingencia_atual = contingencia_row['contingencia']
                hash_key = rede.hashtableindex(perfil, 3, contingencia_atual, num_contingencias, estado_ramos)

                if setupobj.tabela_hash[hash_key] < 0.0:
                    rede.religar_todos_os_ramos_agendamento()
                    rede.desligar_elementos_agendamento(estado_ramos)
                    
                    ramo_contingencia = [contingencia_row['from'], contingencia_row['to']]
                    rede.desligar_contingencia(ramo_contingencia)
                    
                    if ramo_contingencia not in contigencias_selecionadas["ramos"]:
                        contigencias_selecionadas["ramos"].append(ramo_contingencia)
                        contigencias_selecionadas["contingencia"].append(contingencia_atual)

                    if rede.executar_fluxo_de_potencia():
                        fitness, _ = rede.calcular_violacoes_fitness()
                    else:
                        fitness = rede.pesos.get("demanda", 99)

                    setupobj.tabela_hash[hash_key] = fitness
                    setupobj.objectiveruns += 1
                else:
                    fitness = setupobj.tabela_hash[hash_key]
                    setupobj.hashtablereads += 1
                
                violacoes_total.append(fitness)
            
        return sum(violacoes_total), contigencias_selecionadas

    except Exception as e:
        print(f"\nErro durante a análise de contingências: {e}")
        return float('inf'), {}


def funcao_objetivo_contingencia_sin45(individuo, setupobj, _debug=False, return_details=False):
    """
    Função objetivo principal para a análise de contingências do SIN 45.
    """
    smart_grid = SmartGridSin45()
    filepath = smart_grid.create_sin45_dataset_file()
    smart_grid.load_data_from_excel(filepath)
    pp_network = smart_grid.create_network_from_dataframes()
    bus_map = smart_grid.bus_map

    try:
        rede = RedeEletricaPandaPower(network_name="nova", debug=_debug)
        rede.net = pp_network

        rede.pesos.update({
            "tensao": {"min": 0.95, "max": 1.05},
            "loading_linhas": 100,
            "loading_trafos": 100,
            "demanda": 9999
        })

        rede.net.bus['min_vm_pu'] = rede.pesos["tensao"]["min"]
        rede.net.bus['max_vm_pu'] = rede.pesos["tensao"]["max"]
        rede.net.line['max_loading_percent'] = rede.pesos["loading_linhas"]
        rede.net.trafo['max_loading_percent'] = rede.pesos["loading_trafos"]

        agendamento_local = agendamento_df.copy()
        contingencia_local = contingencia_df.copy()

        # Traduz IDs de barras para índices do pandapower
        agendamento_local['ramo'] = agendamento_local['ramo'].apply(lambda r: [bus_map.get(r[0]), bus_map.get(r[1])])
        contingencia_local['from'] = contingencia_local['from'].map(bus_map)
        contingencia_local['to'] = contingencia_local['to'].map(bus_map)

        agendamento_local.dropna(subset=['ramo'], inplace=True)
        contingencia_local.dropna(subset=['from', 'to'], inplace=True)
        contingencia_local = contingencia_local.astype({'from': int, 'to': int})

        agendamento_local["inicio"] = individuo
        duracao_total = (agendamento_local['inicio'] + agendamento_local['duracao']).max()
        
        matriz_cenarios = rede.avalia_cenarios(
            horas=duracao_total,
            hora_inicio=agendamento_local['inicio'],
            duracao=agendamento_local['duracao'],
            ls=0, le=8, ms=8, me=18, hs=18, he=24
        )

        fitness_final, contigencias_selecionadas = analise_contigencias_sep(
            rede, setupobj, matriz_cenarios, agendamento_local, contingencia_local
        )
        
        if return_details:
            return fitness_final, contigencias_selecionadas
        else:
            return fitness_final,

    except Exception as e:
        print(f"\n[ERRO] na função objetivo: {e}")
        import traceback
        traceback.print_exc()
        return float("inf"),

# --- Dados de Exemplo e Execução ---
agendamento_df = pd.DataFrame([
    {"ramo": [1, 2], "duracao": 5, "prioridade": 1},
    {"ramo": [7, 8], "duracao": 4, "prioridade": 2},
    {"ramo": [20, 21], "duracao": 6, "prioridade": 1},
    {"ramo": [24, 37], "duracao": 3, "prioridade": 3},
    {"ramo": [41, 42], "duracao": 5, "prioridade": 1}
])

contingencia_df = pd.DataFrame([
    {"contingencia": 1, "from": 1, "to": 19},
    {"contingencia": 2, "from": 24, "to": 26},
    {"contingencia": 3, "from": 35, "to": 28}
])

if __name__ == '__main__':
    params = {
        "NUM_GENERATIONS": 10,
        "CROSSOVER": 0.9,
        "MUTACAO": 0.1,
        "POP_SIZE": 10,
        "IND_SIZE": len(agendamento_df),
        "RCE_REPOPULATION_GENERATIONS": 5,
        "NUM_VAR_DIFERENTES": 1,
        "PORCENTAGEM": 0.2,
        "DELTA_MIN": 2,
        "ARRAY_VAR": [15, 15, 10, 21, 16],
        "LIMITE_VAR": [0, 31]
    }
    
    tabela_hash_size = len(contingencia_df) * 3 * (2**len(agendamento_df))
    setup = Setup(params=params, fitness_function=funcao_objetivo_contingencia_sin45, tamanho_hash=tabela_hash_size)
    
    print("Iniciando a execução do algoritmo genético...")
    alg = AlgoritimoEvolutivoRCE(setup, DEBUG=False)
    pop, logbook, best_ind, _ = alg.run(RCE=False)
    
    best_fitness = logbook.select("min")[-1]
    best_horarios = best_ind

    # Para obter os ramos selecionados, precisamos executar a função objetivo mais uma vez com o melhor indivíduo
    _, contigencias_selecionadas = funcao_objetivo_contingencia_sin45(best_horarios, setup, return_details=True)

    # Criando o DataFrame final
    resultados_df = pd.DataFrame({
        'Fitness': [best_fitness],
        'Melhores Horarios': [best_horarios],
        'Ramos Selecionados': [contigencias_selecionadas['ramos']]
    })

    print("\n--- Resultados Finais da Otimização ---")
    print(resultados_df.to_string(index=False))