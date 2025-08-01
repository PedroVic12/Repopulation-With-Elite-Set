import pandapower as pp
import pandapower.networks as pw
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import display

from rich.console import Console
from rich.theme import Theme
from rich.traceback import install
import logging

from pandapower.plotting import simple_plot, simple_plotly, pf_res_plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

logging.basicConfig(
    filename='logs.txt',
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w',
    level=logging.DEBUG
)

install()

class Logger:
    def __init__(self):
        self.console = Console(theme=Theme({
            "success": "bold green",
            "warning": "yellow",
            "error": "bold red",
            "info": "white"
        }))

    def log(self, message, level="info"):
        if level == "success":
            self.console.print(f"[success]{message}[/]")
        elif level == "warning":
            self.console.print(f"[warning]{message}[/]")
        elif level == "error":
            self.console.print(f"[error]{message}[/]")
        else:
            self.console.print(f"[info]{message}[/]")

class SmartGridNetwork:
    def __init__(self, network_name = None, debug=False):
        self.net = self.loading_networks_cases(network_name)
        self.debug = debug
        self.nome_rede = ""
        self.console = Logger()
        self.criar_mapeamento_ramos()
        self.pesos = {
            "tensao": {"min": 100, "max": 100},
            "loading_linhas": 100,
            "loading_trafos": 150,
            "demanda": 99,
        }
        self.agendamento = pd.DataFrame()
        self.contingencia= pd.DataFrame()

    def loading_networks_cases(self, network_name = "14"):
        match network_name:
            case "14":
                self.nome_rede = "Case 14"
                network = pw.case14()
            case "30":
                self.nome_rede = "Case 30"
                network = pw.case_ieee30()
            case "57":
                network = pw.case57()
                self.nome_rede = "Case 57"
            case "118":
                network = pw.case118()
                self.nome_rede ="Case 118"
            case "nova":
                network = pw.create_empty_network()
                nome_rede = input("Digite o nome da sua rede que voce quer simular")
                if nome_rede != "":
                    self.nome_rede = "Nova Rede (desconheçida)"
                else:
                    self.nome_rede = nome_rede
            case _:
                print("Rede não encontrada, forneça o numero como string como: IEEE 14 = '14'")
                print(f"Rede '{network_name}' não reconhecida. Usando 'case14'.")
                network = pw.case14()
        return network

    def criar_mapeamento_ramos(self):
        self.mapeamento_ramos = {
            'linhas': {},
            'trafos': {}
        }
        for idx, row in self.net.line.iterrows():
            key = tuple(sorted((row['from_bus'], row['to_bus'])))
            self.mapeamento_ramos['linhas'][key] = idx
        for idx, row in self.net.trafo.iterrows():
            key = tuple(sorted((row['hv_bus'], row['lv_bus'])))
            self.mapeamento_ramos['trafos'][key] = idx
        return self.mapeamento_ramos

    def resetar_rede(self):
        self.net.line['in_service'] = True
        if not self.net.trafo.empty:
            self.net.trafo['in_service'] = True
            
    def aplicar_contingencia(self, tipo_elemento, elemento_id):
        if tipo_elemento == 'Linha' and elemento_id in self.net.line.index:
            self.net.line.loc[elemento_id, 'in_service'] = False
        elif tipo_elemento == 'Transformador' and elemento_id in self.net.trafo.index:
            self.net.trafo.loc[elemento_id, 'in_service'] = False

    def validar_dados(self, df_agendamento, df_contingencia):
        required_agendamento = ["ramo", "inicio", "duracao", "prioridade"]
        if not all(col in df_agendamento.columns for col in required_agendamento):
            print("Colunas faltantes no agendamento_df")
        for _, row in df_agendamento.iterrows():
            ramo = tuple(sorted(row['ramo']))
            if not (ramo in self.mapeamento_ramos['linhas'] or ramo in self.mapeamento_ramos['trafos']):
                print(f"Ramo {row['ramo']} não existe na rede")
        self.agendamento = df_agendamento
        self.contingencia = df_contingencia

    def hashtableindex (self, carregamento, n_carregamentos, contingencia, n_contingencias, desligamentos):
        num_desligamentos= len(desligamentos)
        digits = ['0', '1']
        k = int("".join([ digits[y] for y in desligamentos ]), 2)
        return (k * (n_carregamentos) * (n_contingencias) ) + ((carregamento-1) * (n_contingencias))  + (contingencia-1)

    def log(self, mensagem,level="info"):
        if self.debug:
            self.console.log(mensagem,level)

    def show_status(self, debug = False):
        if self.debug:
            print("="*80)
            print("Rede atual")
            print("="*80)
            print("\nStatus Linhas")
            display(self.net.line[["from_bus","to_bus","in_service"]])
            try:
                trafo_status = self.net.trafo["in_service"].values
                line_status = self.net.line["in_service"].values
                print("\nStatus Transformadores")
                display(self.net.trafo[["hv_bus","lv_bus","in_service"]])
            except Exception as erro:
                print("Erro ao plotar", erro)

    def calcular_violacoes_fitness(self):
        violacoes = {
            "tensao_barramentos_min": 0,
            "tensao_barramentos_max": 0,
            "loading_linhas": 0,
            "loading_trafos": 0,
        }
        for idx, row in self.net.res_bus.iterrows():
            tensao_pu = row["vm_pu"]
            limite_max = self.net.bus.at[idx, "max_vm_pu"]
            limite_min = self.net.bus.at[idx, "min_vm_pu"]
            if tensao_pu > limite_max:
                violacoes["tensao_barramentos_max"] += tensao_pu - limite_max
            elif tensao_pu < limite_min:
                violacoes["tensao_barramentos_min"] += limite_min - tensao_pu
        for idx, row in self.net.res_line.iterrows():
            carregamento = row["loading_percent"]
            limite_max = self.net.line.at[idx, "max_loading_percent"]
            if carregamento > limite_max:
                self.log("\n\nUltrapassou limite maximo nas linhas",level = "warning")
                self.log(f"{carregamento:.2f} > {limite_max} %",level = "warning")
                violacoes["loading_linhas"] += (carregamento - limite_max)
        for idx, row in self.net.res_trafo.iterrows():
            carregamento = row["loading_percent"]
            limite_max = self.net.trafo.at[idx, "max_loading_percent"]
            if carregamento > limite_max:
                self.log("\n\nUltrapassou limite maximo nos transformadores",level = "warning")
                self.log(f"{carregamento:.2f} > {limite_max} %",level = "warning")
                violacoes["loading_trafos"] += (carregamento - limite_max)
        fitness = (
            self.pesos["tensao"]["min"] * violacoes["tensao_barramentos_min"]
            + self.pesos["tensao"]["max"] * violacoes["tensao_barramentos_max"]
            + self.pesos["loading_linhas"] * violacoes["loading_linhas"]
            + self.pesos["loading_trafos"] * violacoes["loading_trafos"]
        )
        violacoes_df = pd.DataFrame([violacoes])
        if self.debug:
            print("\nTotal de violações e salvando num banco de dados...")
            display(violacoes_df)
            self.console.log(f"\n\nAptidão do cenário nos barramentos, linhas e transformadores ", level = "success")
            self.console.log(f"VIOLAÇÃO TOTAL  = {fitness:.2f}\n", level = "success")
        return fitness, violacoes_df

    def calcular_perfil(self,j, ls, le, ms, me, hs, he):
        if ls <= j % 24 < le:
            return 1
        elif ms <= j % 24 < me:
            return 2
        elif hs <= j % 24 < he:
            return 3
        return 0

    def avalia_cenarios(self, horas: int, hora_inicio: list, duracao: list, ls, le, ms, me, hs, he , debug = False):
        matriz_cenarios = []
        num_desligamentos = len(hora_inicio)
        for i in range(num_desligamentos):
            if horas < (hora_inicio[i] + duracao[i]):
                horas = hora_inicio[i] + duracao[i]
        matriz_desligamentos_horas = np.zeros((num_desligamentos, horas), dtype=int)
        matriz_horas = np.zeros(horas, dtype=int)
        for j in range(horas):
            for k in range(num_desligamentos):
                if hora_inicio[k] <= j < (hora_inicio[k] + duracao[k]):
                    matriz_desligamentos_horas[k, j] = 1
                matriz_horas[j] += matriz_desligamentos_horas[k, j] * (2 ** k)
        for horario in range(horas):
            if horario == 0:
                if matriz_horas[horario] > 0:
                    perfil = self.calcular_perfil(horario, ls, le, ms, me, hs, he)
                    matriz_cenarios.append([perfil] + matriz_desligamentos_horas[:, horario].tolist())
            else:
                if matriz_horas[horario] != matriz_horas[horario - 1] and matriz_horas[horario] > 0:
                    perfil = self.calcular_perfil(horario, ls, le, ms, me, hs, he)
                    matriz_cenarios.append([perfil] + matriz_desligamentos_horas[:, horario].tolist())
                else:
                    if horario - 1 in [ms, hs] and matriz_cenarios:
                        perfil = self.calcular_perfil(horario, ls, le, ms, me, hs, he)
                        matriz_cenarios[-1][0] = max(matriz_cenarios[-1][0], perfil)
        if self.debug:
            self.log("\nMatriz Cenarios:")
            for linha in matriz_cenarios:
                self.log(linha)
            self.log(f"Avaliando um total de {len(matriz_cenarios)} cenários ")
        return matriz_cenarios

    def executar_fluxo_de_potencia(self, fast = True):
        try:
            pp.runpp(self.net, algorithm="nr", numba = fast)
            self.log("\nFluxo de potência executado com sucesso!",level = "success")
            return True
        except pp.LoadflowNotConverged:
            self.console.log("\nErro: Fluxo de potência não convergiu...", level = "error")
            Pdem = 99
            print("Penalidade de não convergência do fluxo de potência aplicada:", Pdem)
            self.calcular_violacoes_fitness()
            return False

    def ajustar_cargas(self, perfil):
        tipo = " "
        if perfil == 1:
            fator = 0.941
            tipo = "leve"
            self.log(f"Ajustando cargas para o perfil {perfil} ({tipo})...")
        elif perfil == 2:
            fator = 1.0
            tipo = "media"
            self.log(f"Ajustando cargas para o perfil {perfil} ({tipo})...")
        elif perfil == 3:
            fator = 1.177
            tipo = "pesada"
            self.log(f"Ajustando cargas para o perfil {perfil} ({tipo})...")
        else:
            fator = 1.0
            tipo = "padrão"
            self.log(f"Ajustando cargas para o perfil {perfil} ({tipo})...")
        self.net.load.scaling = fator
        self.net.gen.scaling = fator
        self.log("Cargas ajustadas.", level = "success")

    def desligar_elementos_agendamento(self, estados):
        linhas_desligar = []
        trafos_desligar = []
        for i, estado in enumerate(estados):
            if estado == 1:
                ramo = self.agendamento.iloc[i]["ramo"]
                for k in range(len(self.net.line)):
                    if (self.net.line["from_bus"][k] == ramo[0] and self.net.line["to_bus"][k] == ramo[1]) or (self.net.line["from_bus"][k] == ramo[1] and self.net.line["to_bus"][k] == ramo[0] ):
                        linhas_desligar.append(ramo)
                for k in range(len(self.net.trafo)):
                    if (self.net.trafo["hv_bus"][k] == ramo[0] and self.net.trafo["lv_bus"][k] == ramo[1]) or (self.net.trafo["hv_bus"][k] == ramo[1] and self.net.trafo["lv_bus"][k] == ramo[0] ):
                        trafos_desligar.append(ramo)
        self.log(f"\n\nLinhas a serem desligadas: {linhas_desligar}")
        self.log(f"Trafos a serem desligados: {trafos_desligar}\n")
        self.desligar_elementos(linhas_desligar, trafos_desligar)

    def desligar_contingencia(self, ramo):
        linhas_desligar = []
        trafos_desligar = []
        self.log("Ramo selecionado",ramo)
        for k in range(len(self.net.line)):
            if (self.net.line["from_bus"][k] == ramo[0] and self.net.line["to_bus"][k] == ramo[1]) or (self.net.line["from_bus"][k] == ramo[1] and self.net.line["to_bus"][k] == ramo[0] ):
                    linhas_desligar.append(ramo)
        for k in range(len(self.net.trafo)):
            if (self.net.trafo["hv_bus"][k] == ramo[0] and self.net.trafo["lv_bus"][k] == ramo[1]) or (self.net.trafo["hv_bus"][k] == ramo[1] and self.net.trafo["lv_bus"][k] == ramo[0] ):
                    trafos_desligar.append(ramo)
        self.log(f"\n\nLinhas a serem desligadas: {linhas_desligar}")
        self.log(f"Trafos a serem desligados: {trafos_desligar}\n")
        self.desligar_elementos(linhas_desligar, trafos_desligar)

    def desligar_elementos(self, linhas_desligar, trafos_desligar):
        if not linhas_desligar:
            self.log("Nenhuma linha para desligar")
        else:
            for l in linhas_desligar:
                index_linha = self.net.line.loc[(self.net.line['from_bus'] == l[0]) & (self.net.line['to_bus'] == l[1])].index
                if not index_linha.empty:
                    self.net.line.loc[index_linha, 'in_service'] = False
                else:
                    print(f"Linha {l} não encontrada na rede.")
        if not trafos_desligar:
            self.log("Nenhum transformador para desligar")
        else:
            for t in trafos_desligar:
                index_trafo = self.net.trafo.loc[(self.net.trafo['hv_bus'] == t[0]) & (self.net.trafo['lv_bus'] == t[1])].index
                if not index_trafo.empty:
                    self.net.trafo.loc[index_trafo, 'in_service'] = False
                else:
                    print(f"Transformador {t} não encontrado na rede.")

    def religar_todos_os_ramos_agendamento(self):
        self.net.line['in_service'] = True
        self.net.trafo['in_service'] = True
        self.log("Todos os ramos religados.", level="success")