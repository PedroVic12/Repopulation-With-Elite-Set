# File: Repopulation-With-Elite-Set/src/utils/functions_fitness/function_SIN_45_otimizacao.py
import os
import sys
import pandas as pd
import pathlib
import pandapower as pp

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from RedeEletrica_backup.rede_eletrica import RedeEletricaPandaPower
from AlgEvolutivoRCE_backup.Setup import Setup

# --- DADOS DO CASO SIN 45 ---
# Extraídos de SIMULATOR_SIN_45.py
def _get_sin45_dataframes():
    """Retorna os dataframes com os dados brutos da rede de 45 barras."""
    bus_data = {'Barra': list(range(1, 46)),'Nome': ['IVAIPORA.525', 'LONDRINA.525', 'BARRACAO13.8', 'SIDEROPOL230', 'FARROUPIL230','P.FUNDO.13.8', 'P.FUNDO.230', 'XANXERE.230', 'P.BRANCO.230', 'S.OSORIO13.8','S.OSORIO.230', 'AREIA.230', 'S.MATEUS.230', 'CURITIBA.230', 'JOINVILE.230','BLUMENAU.230', 'R.QUEIMAD230', 'F.AREIA.13.8', 'AREIA.525', 'CURITIBA.525','CUR.NORTE525', 'BLUMENAU.525', 'BARRACAO.525', 'GRAVATAI.525', 'V.AIRES.525','PINHEIRO.525', 'S.SANTIA13.8', 'S.SANTIAG525', 'J.LAC.A.13.8', 'J.LACERDA138','J.LAC.B.13.8', 'J.LAC.C.13.8', 'J.LACERDA230', 'SEGREDO.13.8', 'SEGREDO.525','CECI.230', 'GRAVATAI.230', 'ITAUBA.13.8', 'ITAUBA.230', 'V.AIRES.230','APUCARANA230', 'LONDRINA.230', 'MARINGA.230', 'C.MOURAO.230', 'FORQUILHI230']}
    line_data = {'De': [1, 1, 1, 2, 3, 4, 4, 4, 5, 5, 6, 7, 7, 8, 8, 9, 10, 11, 11, 12, 12, 13, 14, 14, 15, 16, 16, 17, 18, 19, 19, 19, 19, 20, 20, 23, 24, 25, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 36, 36, 38, 39, 41, 41, 41, 42, 43],'Para': [2, 19, 28, 42, 23, 5, 33, 45, 7, 36, 7, 8, 39, 9, 11, 11, 11, 12, 44, 13, 19, 14, 15, 20, 16, 17, 22, 33, 19, 20, 21, 23, 35, 21, 22, 24, 37, 26, 40, 28, 28, 35, 30, 33, 33, 33, 45, 35, 37, 40, 39, 40, 42, 43, 44, 43, 44],'R(pu)': [0.00035, 0.0018, 0.0014, 0.0, 0.0, 0.0386, 0.0096, 0.0033, 0.02315, 0.00885, 0.0, 0.00815, 0.025, 0.0163, 0.0316, 0.0153, 0.0, 0.0306, 0.0172, 0.0245, 0.0, 0.0088, 0.0091, 0.0, 0.0077, 0.0108, 0.0, 0.009, 0.0, 0.0019, 0.0019, 0.0014, 0.0005, 0.0005, 0.0012, 0.0021, 0.0, 0.0022, 0.0, 0.0014, 0.0, 0.0005, 0.0, 0.0, 0.0, 0.0129, 0.0, 0.0006971, 0.0061315, 0.0, 0.0202, 0.0051987, 0.011, 0.0229, 0.0086, 0.0181],'X(pu)': [0.00725, 0.0227, 0.0204, 0.0063, 0.0136, 0.1985, 0.0491, 0.0167, 0.1189, 0.0455, 0.046, 0.04175, 0.1548, 0.0835, 0.1621, 0.0861, 0.0114, 0.1523, 0.088, 0.1256, 0.03, 0.0415, 0.04675, 0.0062, 0.0388, 0.05525, 0.0062, 0.046, 0.0067, 0.028, 0.0274, 0.0195, 0.007, 0.0069, 0.0175, 0.0309, 0.0062, 0.03, 0.0062, 0.0195, 0.0114, 0.007, 0.0871, 0.059, 0.0701, 0.045, 0.0657, 0.0068, 0.0035819, 0.0316242, 0.0236, 0.1129, 0.0268149, 0.1184, 0.1174, 0.0442, 0.0929],'B(pu)': [0.8305, 2.2721, 2.4475, 0.0, 0.0, 0.34, 0.0842, 0.2859, 0.2042, 0.07925, 0.0, 0.072, 0.469, 0.144, 0.2784, 0.1344, 0.0, 0.2702, 0.152, 0.2041, 0.0, 0.5211, 0.07975, 0.0, 0.0675, 0.09315, 0.0, 0.07765, 0.0, 3.3576, 3.2867, 2.3968, 0.8392, 0.8216, 2.097, 3.7183, 0.0, 3.83, 0.0, 2.397, 0.0, 0.8392, 0.0, 0.0, 0.0, 0.0, 0.1128, 0.0, 0.0668, 0.5236, 0.0, 0.2062, 0.1905, 0.2027, 0.2027, 0.2868, 0.1607]}
    return {
        'bus': pd.DataFrame(bus_data),
        'line': pd.DataFrame(line_data),
        'load_gen': pd.DataFrame(load_gen_data),
        'shunt': pd.DataFrame(shunt_data)
    }

def _create_sin45_pandapower_net():
    """Cria e retorna um objeto de rede pandapower para o caso SIN45."""
    dataframes = _get_sin45_dataframes()
    net = pp.create_empty_network()
    df_bus = dataframes['bus']
    df_load_gen = dataframes['load_gen']
    bus_map = {int(row['Barra']): pp.create_bus(net, name=row['Nome'], vn_kv=float(str(row['Nome']).split('.')[-1])) for _, row in df_bus.iterrows()}

    for _, row in df_load_gen.iterrows():
        bus_idx = bus_map.get(int(row['Barra']))
        if bus_idx is None: continue
        if row['Carga Ativa (MW)'] > 0:
            pp.create_load(net, bus=bus_idx, p_mw=row['Carga Ativa (MW)'], q_mvar=row['Carga Reativa (Mvar)'])
        if row['Potência Ativa (MW)'] > 0:
            if row['Tipo de Barra (*)'] == 2:
                pp.create_ext_grid(net, bus=bus_idx, vm_pu=1.0, name="Slack Bus")
            else:
                pp.create_gen(net, bus=bus_idx, p_mw=row['Potência Ativa (MW)'], vm_pu=1.0)

    df_line = dataframes['line']
    s_base_mva = 100.0
    for _, row in df_line.iterrows():
        from_bus, to_bus = bus_map.get(int(row['De'])), bus_map.get(int(row['Para']))
        if from_bus is None or to_bus is None: continue
        from_vn_kv, to_vn_kv = net.bus.vn_kv.at[from_bus], net.bus.vn_kv.at[to_bus]
        if abs(from_vn_kv - to_vn_kv) > 1e-3:
            hv_bus, lv_bus = (from_bus, to_bus) if from_vn_kv > to_vn_kv else (to_bus, from_bus)
            pp.create_transformer_from_parameters(net, hv_bus, lv_bus, sn_mva=s_base_mva, vn_hv_kv=max(from_vn_kv, to_vn_kv), vn_lv_kv=min(from_vn_kv, to_vn_kv), vkr_percent=row['R(pu)'] * 100.0, vk_percent=row['X(pu)'] * 100.0, pfe_kw=0, i0_percent=0)
        else:
            z_base_ohm = (from_vn_kv ** 2) / s_base_mva
            pp.create_line_from_parameters(net, from_bus, to_bus, length_km=1.0, r_ohm_per_km=row['R(pu)'] * z_base_ohm, x_ohm_per_km=row['X(pu)'] * z_base_ohm, c_nf_per_km=(row['B(pu)'] / (2 * 3.14159 * 60 * z_base_ohm)) * 1e9, max_i_ka=0.5)
    return net

# --- DADOS DE AGENDAMENTO E CONTINGÊNCIA (EXEMPLO) ---
# IMPORTANTE: Estes são dados de exemplo e devem ser ajustados para o caso real.
agendamento_df = pd.DataFrame([
    {"ramo": [1, 2], "duracao": 5, "prioridade": 1},   # IVAIPORA -> LONDRINA
    {"ramo": [7, 8], "duracao": 4, "prioridade": 2},   # P.FUNDO -> XANXERE
    {"ramo": [20, 21], "duracao": 6, "prioridade": 1}, # CURITIBA -> CUR.NORTE
    {"ramo": [24, 37], "duracao": 3, "prioridade": 3}, # GRAVATAI -> GRAVATAI.230
    {"ramo": [41, 42], "duracao": 5, "prioridade": 1}  # APUCARANA -> LONDRINA.230
])

contingencia_df = pd.DataFrame([
    {"contingencia": 1, "from": 1, "to": 19},  # IVAIPORA -> AREIA.525
    {"contingencia": 2, "from": 24, "to": 26}, # GRAVATAI -> PINHEIRO
    {"contingencia": 3, "from": 35, "to": 28}  # SEGREDO -> S.SANTIAG525
])

def hashtablesize_sin45():
    return len(contingencia_df) * 3 * (2**len(agendamento_df))

def funcao_objetivo_SIN45(individuo, setupobj, _debug=False):
    try:
        pp_net = _create_sin45_pandapower_net()
        rede = RedeEletricaPandaPower(custom_net=pp_net, debug=_debug)

        rede.pesos["tensao"] = {"min": 100, "max": 100}
        rede.pesos["loading_linhas"] = 100
        rede.pesos["loading_trafos"] = 100

        # Clona DFs para não modificar os originais
        agenda_local = agendamento_df.copy()
        contingencia_local = contingencia_df.copy()

        agenda_local["inicio"] = individuo
        duracao_total_agendamento = (agenda_local['inicio'] + agenda_local['duracao']).max()
        rede.validar_dados(agenda_local, contingencia_local)

        matriz_cenarios = rede.avalia_cenarios(
            horas=duracao_total_agendamento,
            hora_inicio=agenda_local['inicio'],
            duracao=agenda_local['duracao'],
            ls=0, le=8, ms=8, me=18, hs=18, he=24
        )

        violacoes_total = []
        contingencias = contingencia_local['contingencia'].to_list()
        num_carregamentos = 3
        num_contingencias = len(contingencias)

        contigencias_selecionadas = {
            "ramos": [],
            "contingencia": []
        }


        for cenario in matriz_cenarios:
            perfil = cenario[0]
            estado_ramos = cenario[1:]
            rede.ajustar_cargas(perfil)

            for contingencia_atual in range(1, num_contingencias + 1):
                hash_key = rede.hashtableindex(
                    perfil, num_carregamentos, contingencia_atual, num_contingencias, estado_ramos
                )

                if setupobj.tabela_hash[hash_key] >= 0.0:
                    fitness = setupobj.tabela_hash[hash_key]
                    setupobj.hashtablereads += 1
                else:
                    rede.religar_todos_os_ramos_agendamento()
                    rede.desligar_elementos_agendamento(estado_ramos)
                    ramo_contingencia = list(contingencia_local.loc[
                        contingencia_local['contingencia'] == contingencia_atual, ['from', 'to']
                    ].values[0])
                    rede.desligar_contingencia(ramo_contingencia)

                    #! salva os ramos selecionados
                    contigencias_selecionadas["ramos"].append(ramo_contingencia)
                    contigencias_selecionadas["contingencia"].append(contingencia_atual)


                    if rede.executar_fluxo_de_potencia():
                        fitness, _ = rede.calcular_violacoes_fitness()
                    else:
                        fitness = rede.pesos.get("demanda")

                    setupobj.tabela_hash[hash_key] = fitness
                    setupobj.objectiveruns += 1
                
                violacoes_total.append(fitness)

        # 12) Calcular fitness final com somatorio das vioações com pesos de todos os cenarios
        fitness_final = sum(violacoes_total)
        rede.log(f"\nFitness do agendamento = {fitness_final:.2f}\n", level="success")

        # Criar DataFrames para o retorno
        fitness_df = pd.DataFrame([{'fitness_final': fitness_final}])
        melhores_variaveis_df = pd.DataFrame(individuo, columns=['inicio_otimizado'])
        ramos_selecionados_df = agendamento_df.copy()
        contingencias_avaliadas_df = pd.DataFrame(contigencias_selecionadas)

        return {
            "fitness": fitness_df,
            "melhores_variaveis": melhores_variaveis_df,
            "ramos_selecionados": ramos_selecionados_df,
            "contingencias": contingencias_avaliadas_df
        }
    
    except Exception as e:
        print(f"\n[ERRO] na função objetivo SIN45: {e}")
        import traceback
        traceback.print_exc()
        return float("inf")

# Dicionário de parâmetros para a função de teste
params_json_teste = {
    "NUM_GENERATIONS": 10,
    "CROSSOVER": 0.9,
    "MUTACAO": 0.1,
    "POP_SIZE": 4,
    "IND_SIZE": 10,
    "RCE_REPOPULATION_GENERATIONS": 5,
    "NUM_VAR_DIFERENTES": 1,
    "PORCENTAGEM": 0.2,
    "DELTA_MIN": 2,
    "ARRAY_VAR": [15, 15, 10, 21, 16, 13, 10, 14, 17, 18],
    "LIMITE_VAR": [0, 31]
}
    
def run_simulate_SIN45():
    tabela_hash = hashtablesize_sin45()

    setup = Setup(
        params= params_json_teste,
        fitness_function= funcao_objetivo_SIN45,
        tamanho_hash= tabela_hash,
    )

    fitness, best_vars, ramos_selecionados, contingencias_avaliadas = funcao_objetivo_SIN45(
        individuo= [15, 15, 10, 21, 16, 13, 10, 14, 17, 18],
        setupobj= setup,
        _debug= False
    )







run_simulate_SIN45()
