# File: Repopulation-With-Elite-Set/lib/domain/models/utils/functions_fitness/simulate_func_objetivo_IEEE14.py

import os
import sys
import pathlib
import pandas as pd
import matplotlib.pyplot as plt  # Import matplotlib
import io
import base64

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
"""
Este módulo pode ser executado como script para debug. Para garantir que os
imports funcionem fora do ambiente do framework, adicionamos dinamicamente o
diretório 'src' ao sys.path quando necessário.
"""
# Garante que /src esteja no sys.path (arquivo atual: /src/utils/functions_fitness/...)
_THIS_DIR = pathlib.Path(__file__).resolve().parent
_SRC_DIR = _THIS_DIR.parent.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from RedeEletrica_backup.rede_eletrica import RedeEletricaPandaPower

from AlgEvolutivoRCE_backup.Setup import Setup


#! TODO -> (10/07/25) Função implementada em Março mas precisa de paralelismo para ficar mais eficiente e melhor uso da hash table
def funcao_objetivo_IEEE14(individuo, setupobj, _debug: bool = False, return_timeline: bool = False):
    
    """    
    # Esta função avalia o agendamento de desligamentos e contingências na rede elétrica, calculando o fitness baseado em violações de tensões e carregamentos.
    # A função utiliza a classe RedeEletricaPandaPower para simular o fluxo de carga e calcular as violações com base em um agendamento fornecido.
    # a função retorna o fitness total do agendamento, que é a soma das violações de todos os cenários avaliados.
    ## A função também utiliza uma tabela hash para armazenar os resultados de cenários já avaliados, evitando cálculos redundantes.
    # 


    Returns:
        float/int: fitness_result
    """
    # Função objetivo para o problema de otimização da rede elétrica IEEE 14 barras

    #! 1) Criar a rede elétrica IEEE 14 barras, Inicializar a classe com a rede e carrega a tabela de agendamento
    rede = RedeEletricaPandaPower("14", debug=_debug)


    #! Colocando pesos como input do usuario e os dados de entrada do agendamento
    rede.pesos["tensao"] = {"min": 100, "max": 100}
    rede.pesos["loading_linhas"] = 100
    rede.pesos["loading_trafos"] = 100


    #=====================================================
    # Tabela agendamentos em xlsx hardcoded
    agendamento_df = pd.DataFrame([
        {"ramo": [1, 4], "inicio": "14:00", "duracao": 6 ,"prioridade": 4},
        {"ramo": [1, 3], "inicio": "15:00", "duracao": 5, "prioridade": 1},
        {"ramo": [3, 6], "inicio": "14:00", "duracao": 6, "prioridade": 1},
        {"ramo": [11, 12], "inicio": "18:00", "duracao": 6, "prioridade": 1},
        {"ramo": [9, 10], "inicio": "15:00", "duracao": 4, "prioridade": 1}
   ] )

    contingencia_df = pd.DataFrame([
            {"contingencia":1,  "from":2 , "to": 3},
            {"contingencia":2,  "from":5 , "to": 12},
            {"contingencia":3,  "from":12 , "to": 13},
    ])

    # Converter horários de início para horas do dia
    agendamento_df['inicio'] = agendamento_df['inicio'].apply(lambda x: int(x.split(':')[0]))

    # Calcular horário de término em horas do dia
    agendamento_df['final'] = agendamento_df.apply(lambda row: (row['inicio'] + row['duracao']) % 24, axis=1)

    # Calcular a duração total do agendamento em horas
    duracao_total_agendamento = (agendamento_df['inicio']+agendamento_df['duracao']).max()
    rede.validar_dados(agendamento_df, contingencia_df)

    # passando a variavel de decisão na função objetivo
    agendamento_df["inicio"] = individuo

    violacoes_total = []
    violacoes_hash_table = {}
    timeline_events: list[dict] = []  # coleta eventos de desligamento por slot/horário

    # Generate hash key values
    #! Variáveis de Calculo  de otimização para achar o fitness de cada cenario
    contingencias = contingencia_df['contingencia'].to_list()
    num_carregamentos = 3
    num_contingencias = len(contingencias) # 3
    num_desligamentos = len(agendamento_df) # 5
    
    #bd_aptidao_cenario = [-1.0]*(num_contingencias* num_carregamentos*(2**num_desligamentos) )

    #=====================================================
    # 2)  Avaliar cenários e criar matriz de cenários
    matriz_cenarios = rede.avalia_cenarios(
            horas = duracao_total_agendamento,
            hora_inicio=agendamento_df['inicio'],
            duracao=agendamento_df['duracao'],
            ls=0, le=8,
            ms=8, me=18,
            hs=18, he=24
        )

    # Helpers para mapear horário e ramos desligados por hora
    min_inicio = int(agendamento_df['inicio'].min()) if not agendamento_df.empty else 0

    def ramos_desligados_no_horario(hora_atual: int) -> list[tuple[int,int]]:
        desligados: list[tuple[int,int]] = []
        for _, row in agendamento_df.iterrows():
            try:
                h0 = int(row['inicio'])
                dur = int(row['duracao'])
                fim = (h0 + dur) % 24
                ramo = row.get('ramo')
                if isinstance(ramo, (list, tuple)) and len(ramo) == 2:
                    ramo_pair = (int(ramo[0]), int(ramo[1]))
                else:
                    # Se vier como id, mantemos como está
                    ramo_pair = ramo

                # janela correta considerando ciclo 24h
                if dur >= 24:
                    in_window = True
                elif h0 + dur < 24:
                    in_window = (hora_atual >= h0) and (hora_atual < h0 + dur)
                else:
                    # janela cruza meia-noite
                    in_window = (hora_atual >= h0) or (hora_atual < fim)

                if in_window:
                    desligados.append(ramo_pair)
            except Exception:
                continue
        return desligados

    try:
        # 3) Processar cada cenário da matriz de cenários
        for t_idx, cenario in enumerate(matriz_cenarios):
            perfil = cenario[0]
            estado_ramos = cenario[1:]
            # Hora do dia alinhada ao índice do slot (0..23)
            hora_atual = t_idx % 24

            # 4) Ajustar carregamento para o perfil do cenário
            rede.ajustar_cargas(perfil)

            # Loop through contingencies before calculating violations for the scenario
            for contingencia_atual in range(num_contingencias):
                contingencia_atual += 1
                
                # Uso da hash key para ja utilizar cenarios calculados
                hash_key = rede.hashtableindex(perfil, num_carregamentos, contingencia_atual, num_contingencias, estado_ramos)
                
                if _debug:
                    print("minha tabela hash:", len(setupobj.tabela_hash))
                #setupobj.tamanho_hash = hash_key
                
                #! RZ_01jun2025 - verifica se o cenário já foi calculado na tabela hash
                if setupobj.tabela_hash[hash_key] < 0.0:
                    #!DEBUG = Cenario 288 calculado, ai calcula o cenario 235 e da erro (porque ainda nao existe!)
                    
                    #! Simulação e modelagem usando pandapower com metodos da RedeEleticaPandawer em subtorinas
                    #5)  Ligar todos os ramos antes de aplicar mudanças
                    rede.religar_todos_os_ramos_agendamento()

                    # 6) Desligamentos por agendamento com base nas variáveis de decisão (horário atual)
                    desligados_agendamento = ramos_desligados_no_horario(hora_atual)
                    # Fallback para "estado_ramos" se não houver mapeamento
                    desligar_lista = desligados_agendamento if desligados_agendamento else estado_ramos
                    rede.desligar_elementos_agendamento(desligar_lista)

                    # 7) Identifica ramos afetados pela contingência
                    ramo_contingencia = list(contingencia_df.loc[contingencia_df['contingencia'] == contingencia_atual, ['from', 'to']].values[0])
                    rede.log(f"\n{contingencia_atual}) Ramo da contingencia = { ramo_contingencia}\n")

                    # 8) Desliga os ramos afetados
                    rede.desligar_contingencia(ramo_contingencia)

                    # 8.1) Registrar evento de timeline (ramos desligados neste slot)
                    if return_timeline:
                        try:
                            # Normaliza estruturas em listas simples de pares para HTML/JSON
                            desligados_cont = [tuple(ramo_contingencia)]
                            timeline_events.append({
                                "time": hora_atual,  # hora real (0-23)
                                "perfil": perfil,
                                "desligados": [tuple(x) if isinstance(x, (list, tuple)) else x for x in (list(desligados_agendamento) + desligados_cont)],
                                "tipo": "ambos"
                            })
                        except Exception:
                            pass

                    # 9) Executar fluxo de potência para o cenário com contingência
                    if rede.executar_fluxo_de_potencia():                            
                            # 10) Calcular violações com pesos e armazenar os resultados
                            fitness, violacoes_df = rede.calcular_violacoes_fitness()

                    else:
                            fitness = rede.pesos["demanda"] # penalidade com valor default de 99



                    # 11) Store violation in the hash table
                    #!debug = Ele esta salvando primeiro cenario, o hashtable existe mas o proximo cenario ainda nao foi calculado... 
                    setupobj.tabela_hash[hash_key] = fitness
                    rede.log(f"Hash key = { hash_key}\n")
                    
                    # incrementa contador de execuções da função objetivo
                    setupobj.objectiveruns += 1

                    #save hash key in excel
                    #pd.DataFrame(list(setupobj.tabela_hash.items())).to_excel("hash_table.xlsx", index=False)
                        
                        

                #! 12) Retorna o valores calculados de fluxo de potencia na variavel fitness
                else:
                  fitness = setupobj.tabela_hash[hash_key]
                  if _debug:
                      print("Fitness do cenario = ", fitness)
                  setupobj.hashtablereads += 1

                violacoes_total.append(fitness)

            #! Ver apenas o true in service de barras e transformadores
            rede.show_status()

        # 12) Calcular fitness final com somatorio das vioações com pesos de todos os cenarios
        fitness_final = sum(violacoes_total)
        rede.log(f"\nFitness do agendamento = {fitness_final:.2f}\n", level = "success")
        if return_timeline:
            return fitness_final, timeline_events
        return fitness_final

    except Exception as e:
        print(f"\nErro ao calcular a função objetivo: {e}")

def generate_chart(data, chart_type: str = 'bar'):
    """
    Generates a chart of the specified type from the given data.

    Args:
        data (list): A list of tuples, where each tuple contains a label and a value.
        chart_type (str): The type of chart to generate ('bar', 'line', 'pie').

    Returns:
        str: A base64 encoded PNG image of the chart, or None if an error occurs.
    """
    try:
        # Prepare data for plotting
        labels, values = zip(*data)

        # Create the plot
        fig, ax = plt.subplots()

        if chart_type == 'bar':
            ax.bar(labels, values)
            ax.set_ylabel('Values')
            ax.set_title('Bar Chart')
        elif chart_type == 'line':
            ax.plot(labels, values, marker='o')
            ax.set_ylabel('Values')
            ax.set_title('Line Chart')
        elif chart_type == 'pie':
            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.set_title('Pie Chart')
        else:
            print(f"Error: Unknown chart type '{chart_type}'.")
            return None

        # Save the plot to a BytesIO object
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)

        # Encode the image to base64
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return image_base64

    except Exception as e:
        print(f"Error generating chart: {e}")
        return None

def simulate_IEEE_14_cenario(chart_type: str = 'bar'):
    """
    Simulates an IEEE 14 scenario and generates a chart of the fitness values.

    Args:
        chart_type (str): The type of chart to generate ('bar', 'line', 'pie').
    """
    horarios = [14,16,18,20,25]
    
    params_json = {
    "NUM_GENERATIONS": 40,
    "CROSSOVER": 0.95,
    "MUTACAO": 0.25,
    "POP_SIZE": 5,
    "IND_SIZE": 5,
    "RCE_REPOPULATION_GENERATIONS": 50,
    "NUM_VAR_DIFERENTES": 1,
    "PORCENTAGEM": 0.2,
    "DELTA_MIN": 2,
    "ARRAY_VAR": [
        14,
        15,
        14,
        18,
        15
    ],
    "LIMITE_VAR": [
        0,
        31
    ]
}
    
    setup_obj = Setup(
            params = params_json,
            fitness_function = funcao_objetivo_IEEE14,
        )
    
    # Collect fitness values for chart
    fitness_values = []
    num_simulations = 5  # Number of simulations
    
    for i in range(num_simulations):
        fitness = funcao_objetivo_IEEE14(
            individuo=horarios,
            setupobj= setup_obj,
            _debug = True,
            return_timeline=False
        )
        fitness_values.append(fitness)

    # Prepare data for chart
    chart_data = [(f"Simulation {i+1}", fitness) for i, fitness in enumerate(fitness_values)]

    # Generate chart
    chart_image = generate_chart(chart_data, chart_type)
    
    if chart_image:
        # The chart_image variable now contains the base64 encoded PNG image
        # You can save this to a file, display it in a web page, etc.
        # For example, to print it to the console:
        print(f"Chart image (base64): {chart_image}")

        # Alternatively, to save it to an HTML file to display it in a web browser:
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Fitness Chart</title>
        </head>
        <body>
            <h1>Fitness Chart</h1>
            <img src="data:image/png;base64,{chart_image}" alt="Fitness Chart">
        </body>
        </html>
        '''
        with open("fitness_chart.html", "w") as f:
            f.write(html_content)
        print("Chart saved to fitness_chart.html")
    else:
        print("Failed to generate chart.")
    
def load_agendamento_from_json(path: str) -> pd.DataFrame:
    """Carrega agendamento a partir de JSON. Espera chave 'agendamento' com itens contendo
    'ramo' (par [from,to] ou id), 'inicio' ("HH:MM" ou int) e 'duracao' (int).
    """
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.DataFrame(data.get('agendamento', []))
    if 'inicio' in df.columns:
        df['inicio'] = df['inicio'].apply(lambda x: int(str(x).split(':')[0]) if isinstance(x, str) else int(x))
    return df


def load_agendamento_from_excel(path: str, sheet_name: str | None = None) -> pd.DataFrame:
    """Carrega agendamento a partir de Excel, normalizando 'inicio' para hora inteira."""
    df = pd.read_excel(path, sheet_name=sheet_name)
    if 'inicio' in df.columns:
        df['inicio'] = df['inicio'].apply(lambda x: int(str(x).split(':')[0]) if isinstance(x, str) else int(x))
    return df


def build_timeline_html(timeline_events: list[dict]) -> str:
    """Gera HTML simples e interativo para a timeline de desligamentos.
    Cada bloco representa um slot/horário; clique para expandir detalhes.
    """
    # Agrupa por time
    slots: dict[int, list[dict]] = {}
    for ev in timeline_events:
        slots.setdefault(int(ev.get('time', 0)), []).append(ev)

    blocks = []
    for t in sorted(slots.keys()):
        items = slots[t]
        detalhes = []
        for ev in items:
            desligados = ev.get('desligados', [])
            tipo = ev.get('tipo', 'desconhecido')
            perfil = ev.get('perfil', '-')
            lista = ', '.join([f"({a},{b})" if isinstance(x, (list, tuple)) and len(x) == 2 and (a:=x[0]) is not None and (b:=x[1]) is not None else str(x) for x in desligados])
            detalhes.append(f"<li><b>Tipo:</b> {tipo} • <b>Perfil:</b> {perfil} • <b>Ramos:</b> {lista}</li>")
        detalhes_html = '<ul style="margin:6px 0 0 18px">' + ''.join(detalhes) + '</ul>'
        block = f"""
        <div class=\"tl-block\" onclick=\"this.classList.toggle('open')\">
            <div class=\"tl-hour\">Hora/Slot {t}</div>
            <div class=\"tl-details\">{detalhes_html}</div>
        </div>
        """
        blocks.append(block)

    style = """
    <style>
      .timeline{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
      .tl-block{border:1px solid #475569;background:#0f172a;color:#e2e8f0;border-radius:10px;padding:10px;cursor:pointer}
      .tl-block .tl-hour{font-weight:700;color:#38bdf8}
      .tl-block .tl-details{display:none;margin-top:6px;font-size:0.92em}
      .tl-block.open .tl-details{display:block}
    </style>
    """
    html = f"""
    {style}
    <div class=\"timeline\">{''.join(blocks)}</div>
    """
    return html


# Example usage (desativado por padrão)
if __name__ == "__main__":
    simulate_IEEE_14_cenario(chart_type='bar')  # 'bar' | 'line' | 'pie'