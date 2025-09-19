import os
import sys
import pandas as pd
import pathlib
import pandapower as pp
from datetime import datetime
from plotly.subplots import make_subplots
import plotly.graph_objects as go



sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from RedeEletrica_backup.rede_eletrica import RedeEletricaPandaPower
from AlgEvolutivoRCE_backup.Setup import Setup
from AlgEvolutivoRCE_backup.alg_evolutivo_rce import AlgoritimoEvolutivoRCE


from IPython.display import display, HTML





# Hash map de resultados
resultados = {

}

# --- DADOS DE AGENDAMENTO E CONTINGÊNCIA (Retirado da tese de RZ na pagina 132-133) ---
agendamento_df = pd.DataFrame([
    {"ramo": [8, 11],"inicio": "08:00",  "duracao": 4, "prioridade": 4},   # IVAIPORA -> LONDRINA
    {"ramo": [43, 44],"inicio": "10:00", "duracao": 5, "prioridade": 1},   # P.FUNDO -> XANXERE
    {"ramo": [4, 33], "inicio": "14:00", "duracao": 4, "prioridade": 1}, # CURITIBA -> CUR.NORTE
    {"ramo": [7, 39], "inicio": "18:00", "duracao": 6 ,"prioridade": 1},
    {"ramo": [41, 44], "inicio": "15:00", "duracao": 4, "prioridade": 1},
    {"ramo": [20, 21], "inicio": "08:00", "duracao": 4, "prioridade": 1},
    {"ramo": [39, 40], "inicio": "10:00", "duracao": 5, "prioridade": 1},
    {"ramo": [42, 43], "inicio": "14:00", "duracao": 4, "prioridade": 1},
    {"ramo": [4, 45], "inicio": "18:00", "duracao": 6, "prioridade": 1},
    {"ramo": [5, 7], "inicio": "15:00", "duracao": 4, "prioridade": 1},

])

contingencia_df = pd.DataFrame([
    {"contingencia": 1, "from": 4, "to": 5},  
    {"contingencia": 2, "from": 9, "to": 11}, 
    {"contingencia": 3, "from": 19, "to": 23}  
])



def hashtablesize_sin45():
    return len(contingencia_df) * 3 * (2**len(agendamento_df))



##############################################################################################################################################################


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

                ramo_contingencia = list(contingencia_df.loc[contingencia_df['contingencia'] == contingencia_atual, ['from', 'to']].values[0])
                
                if ramo_contingencia not in contigencias_selecionadas["ramos"]:
                    contigencias_selecionadas["ramos"].append(ramo_contingencia)
                    contigencias_selecionadas["contingencia"].append(contingencia_atual)

                if setupobj.tabela_hash[hash_key] < 0.0:
                    rede.religar_todos_os_ramos_agendamento()
                    rede.desligar_elementos_agendamento(estado_ramos)
                    
                    rede.desligar_contingencia(ramo_contingencia)

                    if rede.executar_fluxo_de_potencia():
                        fitness, _ = rede.calcular_violacoes_fitness()
                    else:
                        fitness = rede.pesos.get("demanda", 99) # Usar .get para segurança

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


######################################################################################################################################
# Extraídos de SIMULATOR_SIN_45.py
class SmartGridSin45:
    """
    Gere todos os dados, criação da rede pandapower e cálculos.
    """
    def __init__(self):
        self.net = None
        self.dataframes = {}
        self.bus_map = {} # Adicionado para mapear IDs de barras para índices do pandapower
        self.line_loading_threshold = 100 # Novo atributo para o limite de carregamento das linhas

    def plot_network(self, filename='sin45_network_plot.html', grafico_rce_fig=None):
        """ Gera um gráfico interativo da rede e guarda como HTML. """
        if self.net is None:
            print("Rede não criada. Não é possível gerar o gráfico.")
            return
        print(f"gráfico da rede em '{filename}'...")
        try:

            # Crie uma figura com 5 subplots
            fig = make_subplots(
                rows=4, cols=1,
                subplot_titles=(
                    "Diagrama da Rede SIN45 (Tensões nas Barras de Carga e Geração)", 
                    "Perfil de Tensões nas Barras", 
                    "Carregamento das Linhas em %",
                    "Evolução do Algoritmo Genético (RCE)",
                ),
                vertical_spacing=0.12,

            )

            # 1. Diagrama da Rede (agora com vlevel_plotly)
            fig_network = pp.plotting.plotly.vlevel_plotly(
                self.net,
                respect_switches=True,
                line_width=1.2,
                bus_size=12,
                auto_open=False
            )
            for trace in fig_network.data:
                fig.add_trace(trace, row=1, col=1)

            # Ajusta o tamanho da figura para ser maior (por exemplo, altura de 3000)
    

            # 2. Resultado do Fluxo de Potência
            self.run_power_flow()
            power_flow_plot = pp.plotting.plotly.pf_res_plotly(
                self.net,
                auto_open=False,
            )


            # 3. Perfil de Tensões
            fig_voltage = self.plot_voltage_profile() 
            for trace in fig_voltage.data:
                fig.add_trace(trace, row=2, col=1)

            # 4. Carregamento das Linhas
            fig_loading = self.plot_line_loading(self.line_loading_threshold) 
            for trace in fig_loading.data:
                fig.add_trace(trace, row=3, col=1)
            
            # 5. Gráfico de Evolução do AG (se fornecido)
            if grafico_rce_fig:
                for trace in grafico_rce_fig.data:
                    fig.add_trace(trace, row=4, col=1)


            # Atualizar layout geral da figura
    
            fig.update_layout(
                title_text="Análise Completa da Rede SIN45 e Otimização",
                height=2200,
                showlegend=True
            )
            # Adiciona scroll vertical via CSS no HTML exportado (caso necessário)
            fig.write_html(
                filename,
                full_html=True,
                #include_plotlyjs='cdn',
                #include_mathjax ="cdn",
                config={"scrollZoom": True},
                auto_open=True
            )

            print(f"Diagrama completo da Rede Elétrica carregado com sucesso! Pode abrir o ficheiro '{filename}' no navegador.")
        except Exception as e:
            print(f"Erro ao gerar o gráfico: {e}")
            import traceback
            traceback.print_exc()



    def plot_voltage_profile(self, ):
        """ Gera um gráfico do perfil de tensões nas barras. """
        if self.net is None:
            print("Rede não criada. Não é possível gerar o gráfico de tensões.")
            return
        try:
            bus_voltages = self.net.res_bus['vm_pu']
            bus_names = self.net.bus['name']

            fig = go.Figure(data=[go.Bar(x=bus_names, y=bus_voltages)])
            fig.update_layout(title_text='Perfil de Tensões nas Barras (p.u.)',
                              xaxis_title='Barra',
                              yaxis_title='Tensão (p.u.)')

            print(f"Gráfico de perfil de tensões criado com sucesso.")
            return fig 

        except Exception as e:
            print(f"Erro ao gerar o gráfico de perfil de tensões: {e}")

    def plot_line_loading(self, threshold_percent=None):
        """ Gera um gráfico do carregamento das linhas. """
        if self.net is None:
            print("Rede não criada. Não é possível gerar o gráfico de carregamento das linhas.")
            return
        try:
            line_loading = self.net.res_line['loading_percent']
            line_names = [f"Linha {i}" for i in self.net.line.index]

            fig = go.Figure(data=[go.Bar(x=line_names, y=line_loading)])
            fig.update_layout(title_text='Carregamento das Linhas (%)',
                              xaxis_title='Linha',
                              yaxis_title='Carregamento (%)')

            if threshold_percent is not None:
                fig.add_hline(y=threshold_percent, annotation_text=f"Limite: {threshold_percent}%", 
                              annotation_position="bottom right", line_color="red", line_dash="dash")

            print(f"Gráfico de carregamento das linhas criado com sucesso.")
            return fig 

        except Exception as e:
            print(f"Erro ao gerar o gráfico de carregamento das linhas: {e}")

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

        # Converte colunas relevantes para numérico, tratando erros
        for col in ['Barra', 'Tipo de Barra (*)', 'Potência Ativa (MW)', 'Carga Ativa (MW)', 'Carga Reativa (Mvar)']:
            if col in df_load_gen.columns:
                df_load_gen[col] = pd.to_numeric(df_load_gen[col], errors='coerce').fillna(0)
        
        df_bus['Barra'] = pd.to_numeric(df_bus['Barra'], errors='coerce').fillna(0)

        for _, row in df_bus.iterrows():
            bus_id = int(row['Barra'])
            try:
                # Lógica para extrair a tensão nominal do nome da barra
                name_str = str(row['Nome'])
                parts = name_str.replace(',', '.').split('.')
                vn_kv = float(parts[-1]) if len(parts) > 1 and parts[-1].isdigit() else 230.0
            except (ValueError, IndexError):
                vn_kv = 230.0 # Valor padrão

            new_idx = pp.create_bus(self.net, name=row['Nome'], vn_kv=vn_kv)
            self.bus_map[bus_id] = new_idx

        #print("\n--- Bus Map after creation ---")
        #print(self.bus_map)

        # Adiciona limites de tensão para todas as barras para evitar KeyError
        self.net.bus['min_vm_pu'] = 0.95
        self.net.bus['max_vm_pu'] = 1.05

        # Adiciona cargas
        for _, row in df_load_gen.iterrows():
            if row['Carga Ativa (MW)'] > 0:
                bus_idx = self.bus_map.get(int(row['Barra']))
                if bus_idx is not None:
                    pp.create_load(self.net, bus=bus_idx, p_mw=row['Carga Ativa (MW)'], q_mvar=row['Carga Reativa (Mvar)'])

        # Adiciona geradores e a rede externa (Swing)
        for _, row in df_load_gen.iterrows():
            bus_idx = self.bus_map.get(int(row['Barra']))
            if bus_idx is None: continue
            
            is_slack = row['Tipo de Barra (*)'] == 2
            is_gen = row['Potência Ativa (MW)'] > 0

            if is_gen:
                if is_slack:
                    pp.create_ext_grid(self.net, bus=bus_idx, vm_pu=1.0, name="Swing Bus")
                else:
                    pp.create_gen(self.net, bus=bus_idx, p_mw=row['Potência Ativa (MW)'], vm_pu=1.0)

        # Adiciona linhas e transformadores
        df_line = self.dataframes.get('line')
        if df_line is not None:
            
            #print("\n--- df_line before iteration ---")
            #print(df_line[['De', 'Para']].to_string(index=False))
            
            # Converte colunas para numérico
            for col in ['De', 'Para', 'R(pu)', 'X(pu)', 'B(pu)']:
                 if col in df_line.columns:
                    df_line[col] = pd.to_numeric(df_line[col], errors='coerce').fillna(0)

            s_base_mva = 100.0
            for _, row in df_line.iterrows():
                from_bus_id = int(row['De'])
                to_bus_id = int(row['Para'])
                from_bus = self.bus_map.get(from_bus_id)
                to_bus = self.bus_map.get(to_bus_id)
                if from_bus is None or to_bus is None:
                    print(f"Skipping line/transformer from bus {from_bus_id} to bus {to_bus_id}: One or both buses not found in network.")
                    continue
                
                from_vn_kv = self.net.bus.vn_kv.at[from_bus]
                to_vn_kv = self.net.bus.vn_kv.at[to_bus]

                #! Se as tensões das barras forem diferentes, é um transformador
                if abs(from_vn_kv - to_vn_kv) > 1e-3:
                    hv_bus, lv_bus = (from_bus, to_bus) if from_vn_kv > to_vn_kv else (to_bus, from_bus)
                    pp.create_transformer_from_parameters(
                        self.net, hv_bus=hv_bus, lv_bus=lv_bus, sn_mva=s_base_mva,
                        vn_hv_kv=max(from_vn_kv, to_vn_kv), vn_lv_kv=min(from_vn_kv, to_vn_kv),
                        vkr_percent=row['R(pu)'] * 100.0, vk_percent=row['X(pu)'] * 100.0,
                        pfe_kw=0, i0_percent=0
                    )
                else: #! Caso contrário, é uma linha de transmissão
                    z_base_ohm = (from_vn_kv ** 2) / s_base_mva
                    r_ohm = row['R(pu)'] * z_base_ohm
                    x_ohm = row['X(pu)'] * z_base_ohm
                    c_nf = (row['B(pu)'] / (2 * 3.14159 * 60 * z_base_ohm)) * 1e9
                    pp.create_line_from_parameters(self.net, from_bus=from_bus, to_bus=to_bus, length_km=1.0,
                                                   r_ohm_per_km=r_ohm, x_ohm_per_km=x_ohm,
                                                   c_nf_per_km=c_nf, max_i_ka=0.5)
        return self.net

    def run_power_flow(self):
        if self.net is None:
            raise ValueError("A rede não foi criada.")
        try:
            pp.runpp(self.net)
            return True, "Fluxo de potência executado com sucesso."
        except Exception as e:
            return False, f"Falha no Cálculo de fluxo de potência: {e}"



##############################################################################################################################################################

#! Inicialização de objetos
SmartGrid_SIN45 = SmartGridSin45()
filepath = "SIN_45_barras_dataset.xlsx"

SmartGrid_SIN45.load_data_from_excel(filepath)
nome_rede = "SIN 45"


def funcao_objetivo_SIN45(individuo, setupobj, _debug=False):

    rede = RedeEletricaPandaPower(network_name = "nova", debug=False)
    #! Criando a rede do pandapower por arquivo Excel e .PWF
    pp_network_SIN = SmartGrid_SIN45.create_network_from_dataframes()
    bus_map = SmartGrid_SIN45.bus_map # Obtém o mapa de barras


    try:
        rede.net = pp_network_SIN
        rede.criar_mapeamento_ramos() # Força a atualização do mapeamento de ramos interno

        print("Carregando a Rede Elétrica: ", nome_rede)
        print(rede.net)
        print("\n")


        # Limites Operativos da rede
        rede.pesos["tensao"] = {"min": 0.90, "max": 1.10}
        rede.pesos["loading_linhas"] = 100
        rede.pesos["loading_trafos"] = 100
        rede.pesos["demanda"] = 99
        
        print(f"\nInicializando com limites operacionais nas barras com: Tensão: {rede.pesos['tensao']} e Linhas de trasmissão em: {rede.pesos['loading_linhas']} %\n")

        #! Set voltage limits on buses in net object of pandapower
        rede.net.bus['min_vm_pu'] = rede.pesos["tensao"]["min"]
        rede.net.bus['max_vm_pu'] = rede.pesos["tensao"]["max"]
        rede.net.line['max_loading_percent'] = rede.pesos["loading_linhas"]
        rede.net.trafo['max_loading_percent'] = rede.pesos["loading_trafos"]

        SmartGrid_SIN45.line_loading_threshold = rede.pesos["loading_linhas"]

        #! Clona DFs e traduz os IDs das barras para os índices do pandapower
        agenda_local = agendamento_df.copy()
        contingencia_local = contingencia_df.copy()

        # CORREÇÃO: Traduz os IDs das barras para os índices corretos do pandapower
        agenda_local['ramo'] = agenda_local['ramo'].apply(
            lambda r: [bus_map.get(r[0]), bus_map.get(r[1])]
        )
        contingencia_local['from'] = contingencia_local['from'].map(bus_map)
        contingencia_local['to'] = contingencia_local['to'].map(bus_map)

        # Remove linhas com mapeamento falho (se houver)
        agenda_local.dropna(subset=['ramo'], inplace=True)
        contingencia_local.dropna(subset=['from', 'to'], inplace=True)
        contingencia_local = contingencia_local.astype({'from': int, 'to': int})


        #! DEBUG HERE
        agenda_local["inicio"] = individuo
        duracao_total_agendamento = (agenda_local['inicio'] + agenda_local['duracao']).max()
        rede.validar_dados(agenda_local, contingencia_local)

        # Matriz cenários
        matriz_cenarios = rede.avalia_cenarios(
            horas=duracao_total_agendamento,
            hora_inicio=agenda_local['inicio'],
            duracao=agenda_local['duracao'],
            ls=0, le=8, ms=8, me=18, hs=18, he=24
        )
        
        print("\nMatriz Cenários")
        
        print("1) Carga Leve, 2) Carga Média, 3) Carga Pesada")
        print("0/1 - Ramos desligado/ligado\n")
        
        #print(matriz_cenarios)
        
        print(f"Total de Cenários de contigencias = {len(matriz_cenarios)}\n", )

        fitness_final, contigencias_selecionadas = analise_contigencias_SEP(
            rede=rede,
            setupobj=setupobj,
            matriz_cenarios=matriz_cenarios,
            agendamento_df=agenda_local,
            contingencia_df=contingencia_local
        )
        print(f"\nFitness da função aptidão agendamento = {fitness_final:.2f}\n")
        resultados["fitness"] = pd.DataFrame([{'fitness_final': fitness_final}])
        resultados["ramos_selecionados"] = contigencias_selecionadas
        return fitness_final, 
    
    except Exception as e:
        print(f"\n[ERRO] na função objetivo SIN45: {e}")
        import traceback
        traceback.print_exc()
        return float("inf"), {}


# horarios aleatorios para teste para o artigo
HORARIOS_COND_INICIAL = [15, 15, 10, 21, 20, 12, 15, 8, 19,23]

# Dicionário de parâmetros para a função de teste
params_json_teste = {
    "NUM_GENERATIONS": 250,
    "CROSSOVER": 0.92,
    "MUTACAO": 0.77,
    "POP_SIZE": 10,
    "IND_SIZE": 10,
    "RCE_REPOPULATION_GENERATIONS": 50,
    "NUM_VAR_DIFERENTES": 1,
    "PORCENTAGEM": 0.2,
    "DELTA_MIN": 2,
    "ARRAY_VAR": HORARIOS_COND_INICIAL, 
    "LIMITE_VAR": [0, 31]
}


def get_resultados_agendamento_otimo(setup, resultados, plot=False, grafico_rce_fig=None):

    # Resultados do algoritmo
    print(f"Objective functions runs: {setup.objectiveruns}")
    print(f"Consultas HashTable: {setup.hashtablereads}\n")

    print("="*80)
    print(">>> Análise Detalhada da Melhor Solução Encontrada <<<")
    print("="*80)

    df_contingencias = pd.DataFrame(resultados.get("ramos_selecionados", {}))

    if not df_contingencias.empty:
        print("\nRamos de contingência avaliados na melhor solução:")
        
        try:
            df_contingencias['from_bus_idx'] = df_contingencias['ramos'].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else None)
            df_contingencias['to_bus_idx'] = df_contingencias['ramos'].apply(lambda x: x[1] if isinstance(x, list) and len(x) > 1 else None)
            
            print(df_contingencias[['contingencia', 'from_bus_idx', 'to_bus_idx']].to_string(index=False))
        except Exception as e:
            print(f"Erro ao formatar o DataFrame de contingências: {e}")
            print("Dados do dataframe de contingências:")
            print(df_contingencias)

    else:
        print("\nNenhum ramo de contingência foi avaliado ou registrado para a melhor solução.")
        
        
    if plot:
        # Passa a figura do RCE para a função de plotagem da rede
        SmartGrid_SIN45.plot_network(grafico_rce_fig=grafico_rce_fig)



    print(f"\nMelhores horários de agendamento (melhor indivíduo):")
    print(set(resultados["best_variables"]))
    print(f"Na melhor geração encontrada = {resultados["best_generation"]} de {setup.params['NUM_GENERATIONS']} ")
    print("="*80)



##############################################################################################################################################################
#! Função principal para executar s
def run_simulate_SIN45(plot = False):
    tabela_hash = hashtablesize_sin45()

    setup = Setup(
        params= params_json_teste,
        fitness_function= funcao_objetivo_SIN45,
        tamanho_hash= tabela_hash,
    )

    fitness  = funcao_objetivo_SIN45(
        individuo= HORARIOS_COND_INICIAL,
        setupobj= setup,
        _debug= False
    )


    # Inicia o cronômetro para esta execução específica
    start_exec = datetime.now()

    #! 6) Executa algoritmo
    alg = AlgoritimoEvolutivoRCE(setup, DEBUG=False)
    print(f"Algoritmo Evolutivo iniciado")
    pop_with_repopulation, logbook_with_repopulation, best_individual, all_individual_values = alg.run(RCE=True)


    # Finaliza o cronômetro e calcula a duração desta execução
    end_exec = datetime.now()
    elapsed_exec = end_exec - start_exec

    #! Re-executa a função objetivo com o melhor indivíduo para obter os dados detalhados
    print("\nAnalisando a melhor solução encontrada para gerar o relatório final...")
    funcao_objetivo_SIN45(best_individual, setup, _debug=False)

    #! 7) Visualize os Resultados
    print("\n--- Resultados Finais ---")
    resultados["best_variables"] = list(best_individual)
    print("\nEvolução concluída  - 100%")
    
    # camada dashboard com arquivos .html e logbook do DEAP
    best_solution_index, best_solution_variables, best_solution_fitness, grafico_RCE = alg.dashboard.visualize(
        logbook_with_repopulation,
        pop_with_repopulation,
        config_num=1,
        execution_num=1,
    )
    
    resultados["best_generation"] = best_solution_index

    # Exibe os tempos e contadores de forma clara
    print(f"\nDuração da Execução do Algoritmo: {elapsed_exec}")

    # Resultados do algoritmo
    get_resultados_agendamento_otimo(setup, resultados, plot = True, grafico_rce_fig=grafico_RCE)



run_simulate_SIN45(plot = True)

