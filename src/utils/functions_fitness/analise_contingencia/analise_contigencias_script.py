import pandas as pd

def analise_contigencias_SEP(rede, setupobj, matriz_cenarios, df_ag, contingencia_df):
    """
    Executa a análise de contingências para um determinado agendamento de manutenção.
    Modularizado para ser usado por diferentes casos IEEE.
    """
    resultados = []
    violacoes_total = []
    
    num_carregamentos = 3
    num_contingencias = len(contingencia_df)

    for cenario_idx, cenario in enumerate(matriz_cenarios):
        perfil = cenario[0]
        estado_ramos = cenario[1:]

        rede.ajustar_cargas(perfil)

        for contingencia_atual in range(1, num_contingencias + 1):
            hash_key = rede.hashtableindex(
                perfil, num_carregamentos, contingencia_atual, num_contingencias, estado_ramos
            )

            ramo_cont = list(
                contingencia_df.loc[
                    contingencia_df["contingencia"] == contingencia_atual,
                    ["from", "to"],
                ].values[0]
            )

            if setupobj.tabela_hash[hash_key] < 0:
                rede.religar_todos_os_ramos_agendamento()
                rede.desligar_elementos_agendamento(estado_ramos)
                rede.desligar_contingencia(ramo_cont)

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

            # ✅ salvar dados estruturados para o Dashboard
            if fitness > 0:
                for i, estado in enumerate(estado_ramos):
                    if estado == 1:
                        resultados.append(
                            {
                                "cenario": int(cenario_idx),
                                "perfil": int(perfil),
                                "contingencia": int(contingencia_atual),
                                "ramo_cont_from": int(ramo_cont[0]),
                                "ramo_cont_to": int(ramo_cont[1]),
                                "ramo_desligado_from": int(df_ag.iloc[i]["ramo"][0]),
                                "ramo_desligado_to": int(df_ag.iloc[i]["ramo"][1]),
                                "inicio": int(df_ag.iloc[i]["inicio"]),
                                "duracao": int(df_ag.iloc[i]["duracao"]),
                                "fitness": float(fitness),
                            }
                        )

    df_resultados = pd.DataFrame(resultados)
    
    # Armazena no setupobj para ser recuperado pelo runner
    setupobj.df_resultados = df_resultados
    
    return sum(violacoes_total), df_resultados
