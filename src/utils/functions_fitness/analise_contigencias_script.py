#!/usr/bin/env python
# coding: utf-8

def analise_contigencias_SEP(rede, setupobj, matriz_cenarios , agendamento_df, contingencia_df):
    """
    Executa a análise de contingências para um determinado agendamento de manutenção.

    Args:
        rede: Objeto da rede elétrica.
        setupobj: Objeto de setup do algoritmo genético.
        matriz_cenarios: Matriz com os cenários de operação (perfil de carga e estado dos ramos).
        agendamento_df: DataFrame com o agendamento de manutenção.
        contingencia_df: DataFrame com a lista de contingências a serem avaliadas.

    Returns:
        tuple: Uma tupla contendo o fitness final (float) e um dicionário com os ramos de contingência avaliados.
    """
    contingencias = contingencia_df['contingencia'].to_list()
    num_carregamentos = 3
    num_contingencias = len(contingencias)
    num_desligamentos = len(agendamento_df)
    violacoes_total = []
    
    contigencias_selecionadas = {
        "ramos": [],
        "contingencia": []
    }
    
    try:
        for cenario in matriz_cenarios:
            perfil = cenario[0]
            estado_ramos = cenario[1:]
            rede.ajustar_cargas(perfil)

            for contingencia_atual in range(1, num_contingencias + 1):
                hash_key = rede.hashtableindex(perfil, num_carregamentos, contingencia_atual, num_contingencias, estado_ramos)

                if setupobj.tabela_hash[hash_key] < 0.0:
                    rede.religar_todos_os_ramos_agendamento()
                    rede.desligar_elementos_agendamento(estado_ramos)
                    
                    ramo_contingencia = list(contingencia_df.loc[contingencia_df['contingencia'] == contingencia_atual, ['from', 'to']].values[0])
                    rede.desligar_contingencia(ramo_contingencia)
                    
                    if ramo_contingencia not in contigencias_selecionadas["ramos"]:
                        contigencias_selecionadas["ramos"].append(ramo_contingencia)
                        contigencias_selecionadas["contingencia"].append(contingencia_atual)

                    if rede.executar_fluxo_de_potencia():
                        fitness, _ = rede.calcular_violacoes_fitness()
                    else:
                        fitness = rede.pesos.get("demanda", 9999) # Usar .get para segurança

                    setupobj.tabela_hash[hash_key] = fitness
                    setupobj.objectiveruns += 1
                else:
                    fitness = setupobj.tabela_hash[hash_key]
                    setupobj.hashtablereads += 1
                
                violacoes_total.append(fitness)
            
        fitness_final = sum(violacoes_total)
        return fitness_final, contigencias_selecionadas

    except Exception as e:
        print(f"\nErro durante a análise de contingências: {e}")
        return float('inf'), {}